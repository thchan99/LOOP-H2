import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import dash_leaflet as dl

import pandas as pd

from pages.helper_functions import generate_map

dash.register_page(__name__, path='/trade-studies', name="Trade Studies", order=2)

layout = dbc.Container([
    dcc.Store(id="scenario-store", storage_type="local"),
    dbc.Row([
        html.Div([
            html.H2("Trade Study Explorer", className="text-dark fw-bold"),
            html.P("Compare two cached infrastructure scenarios side-by-side. Results are loaded instantly from local storage.", className="text-muted"),
        ], className="mb-4 mt-3 border-bottom pb-2")
    ]),

    # Scenario Selection
    dbc.Row([
        dbc.Col([
            html.Label("Select Baseline (Scenario A)", className="fw-semibold text-primary"),
            dcc.Dropdown(id="compare-select-a", placeholder="Select Scenario A...", className="shadow-sm border-primary"),
        ], xs=12, md=5),
        dbc.Col(html.Div("VS", className="h-100 d-flex align-items-center justify-content-center fw-bold text-muted mt-3 fs-4"), xs=12, md=2),
        dbc.Col([
            html.Label("Select Experiment (Scenario B)", className="fw-semibold text-success"),
            dcc.Dropdown(id="compare-select-b", placeholder="Select Scenario B...", className="shadow-sm border-success"),
        ], xs=12, md=5),
    ], className="mb-4"),

    # Statically Loaded Results
    html.Div(id="comparison-results-container", style={"display": "none"}, children=[
        dbc.Row([
            dbc.Col([
                html.H5(id="map-title-a", className="text-center fw-bold text-primary mb-2"),
                html.Div(id="map-container-a", className="shadow-sm border border-2 border-primary rounded mb-4")
            ], xs=12, lg=6),
            dbc.Col([
                html.H5(id="map-title-b", className="text-center fw-bold text-success mb-2"),
                html.Div(id="map-container-b", className="shadow-sm border border-2 border-success rounded mb-4")
            ], xs=12, lg=6),
        ]),
        
        # Metrics Board Header
        html.Div(html.H4("Key Performance Indicators", className="fw-bold text-center border-bottom pb-2 mb-4 mt-2")),
        
        dbc.Row([
            dbc.Col(id="col-metrics-a", xs=12, lg=5, className="mb-3 mb-lg-0"),
            dbc.Col(id="col-deltas", xs=12, lg=2, className="bg-light border rounded shadow-sm pb-2 mb-3 mb-lg-0"),
            dbc.Col(id="col-metrics-b", xs=12, lg=5),
        ])
    ])
], fluid=True, className="mb-5")

@callback(
    Output("compare-select-a", "options"),
    Output("compare-select-b", "options"),
    Input("scenario-store", "data")
)
def populate_compare_dropdowns(store_data):
    if isinstance(store_data, dict) and store_data:
        options = [{"label": str(k), "value": str(k)} for k in store_data.keys()]
        return options, options
    return [], []

@callback(
    Output("comparison-results-container", "style"),
    Output("map-title-a", "children"),
    Output("map-title-b", "children"),
    Output("map-container-a", "children"),
    Output("map-container-b", "children"),
    Output("col-metrics-a", "children"),
    Output("col-metrics-b", "children"),
    Output("col-deltas", "children"),
    Input("compare-select-a", "value"),
    Input("compare-select-b", "value"),
    State("scenario-store", "data"),
    prevent_initial_call=True
)
def load_trade_study(name_a, name_b, store_data):
    if not store_data or (not name_a and not name_b):
        return {"display": "none"}, "", "", "", "", ""

    map_a, map_b, kpi_a, kpi_b, deltas = "", "", "", "", ""
    sum_a, sum_b = None, None

    title_a = f"Scenario A: {name_a}" if name_a else "Scenario A"
    title_b = f"Scenario B: {name_b}" if name_b else "Scenario B"

    # Helper function to wrap layers in a Map context
    def build_trade_map(layers, map_id):
        map_component = dl.Map(
            children=layers,
            center=[32.8, -83.4],
            zoom=7,
            minZoom=6,
            maxZoom=10,
            style={"width": "100%", "height": "45vh", "borderRadius": "8px", "minHeight": "300px"},
            id=map_id
        )
        
        legend_component = html.Div(
            className="d-flex flex-wrap justify-content-center gap-2 mt-2 pt-2 border-top",
            children=[
                html.Span([html.I(className="fa-solid fa-trash me-1", style={"color": "#28a745"}), "Landfill (BCS)"], className="small text-muted"),
                html.Span([html.I(className="fa-solid fa-trash me-1", style={"color": "#dc3545"}), "Landfill (No BCS)"], className="small text-muted"),
                html.Span([html.I(className="fa-solid fa-bolt me-1", style={"color": "#6f42c1"}), "Plug"], className="small text-muted"),
                html.Span([html.I(className="fa-solid fa-industry me-1", style={"color": "#6f42c1"}), "Savannah"], className="small text-muted"),
                html.Span([html.I(className="fa-solid fa-droplet me-1", style={"color": "#fd7e14"}), "Hydrofleet"], className="small text-muted"),
                html.Span([html.I(className="fa-solid fa-truck me-1", style={"color": "#007bff"}), "Truck Stop"], className="small text-muted"),
                html.Span([html.I(className="fa-solid fa-box me-1", style={"color": "#ffc107"}), "Amazon"], className="small text-muted"),
                html.Span([html.I(className="fa-solid fa-cart-shopping me-1", style={"color": "#6c757d"}), "Walmart"], className="small text-muted"),
                html.Span([html.I(className="fa-solid fa-warehouse me-1", style={"color": "#ffd700"}), "Warehouse"], className="small text-muted"),
                html.Span([html.I(className="fa-solid fa-minus me-1", style={"color": "#2C3E50"}), "Route"], className="small text-muted"),
            ]
        )
        
        return html.Div([map_component, legend_component], className="p-2")

    # KPI Definitions
    kpi_defs = [
        {"id": "profit", "label": "Net Annual Cashflow", "icon": "fa-chart-line", "fmt": "${:,.0f}", "dir": 1},
        {"id": "payback", "label": "Payback Period", "icon": "fa-clock", "fmt": "{:,.1f} yrs", "dir": -1},
        {"id": "built_capacity", "label": "Total H2 Supply", "icon": "fa-bolt", "fmt": "{:,.0f} kg/day", "dir": 1},
        {"id": "built_demand", "label": "Total H2 Demand", "icon": "fa-gas-pump", "fmt": "{:,.0f} kg/day", "dir": 1},
        {"id": "active_sites", "label": "Active Facilities", "icon": "fa-industry", "fmt": "{:,.0f}", "dir": 1},
        {"id": "utilization", "label": "Network Utilization", "icon": "fa-gauge-high", "fmt": "{:,.1f}%", "dir": -1},
        {"id": "graphene", "label": "Graphene Produced", "icon": "fa-cubes", "fmt": "{:,.0f} kg/day", "dir": 1},
        {"id": "capex", "label": "Total Capital Exp.", "icon": "fa-money-bill-transfer", "fmt": "${:,.0f}", "dir": -1},
        {"id": "opex", "label": "Annual Operating Exp.", "icon": "fa-money-bill-trend-up", "fmt": "${:,.0f}", "dir": -1},
        {"id": "unit_opex", "label": "Unit OpEx ($/kg)", "icon": "fa-scale-unbalanced", "fmt": "${:,.2f} /kg", "dir": -1},
    ]

    def extract_metrics(summary, df_demand):
        if not summary: 
            return {}
            
        capex = summary.get("capex_term", 0)
        opex = summary.get("opex_term", 0) + summary.get("transport_term", 0)
        revenue = summary.get("total_revenue", 0)
        
        yearly_net = revenue - opex
        payback = (capex / yearly_net) if yearly_net > 0 else float('inf')
        
        total_demand = summary.get("total_demand", 0)
        total_supply = summary.get("total_built_capacity", 0)
        
        utilization = (total_demand / total_supply * 100) if total_supply > 0 else 0
        unit_opex = (opex / (total_demand * 365)) if total_demand > 0 else 0
        
        graphene_produced = summary.get("total_graphene_kg_day", 0)
        
        return {
            "active_sites": summary.get("n_prod", summary.get("active_sites", 0)), 
            "utilization": utilization,
            "profit": yearly_net, 
            "payback": payback,
            "built_demand": total_demand,
            "built_capacity": total_supply,
            "graphene": graphene_produced,
            "capex": capex,
            "opex": opex,
            "unit_opex": unit_opex,
        }

    def build_kpi_column(metrics, color_class, title):
        items = [html.H5(title, className=f"text-center fw-bold mb-3 {color_class} pt-2")]
        
        for d in kpi_defs:
            val = metrics.get(d["id"], 0)
            val_str = "Never" if val == float('inf') else d["fmt"].format(val)
            items.append(
                html.Div([
                    html.I(className=f"fa-solid {d['icon']} {color_class} me-2 fs-4"),
                    html.Div([
                        html.Span(d["label"], className="text-muted fw-semibold small d-block"),
                        html.Span(val_str, className="fw-bold fs-3")
                    ], className="text-center")
                ], className="d-flex align-items-center justify-content-center mb-3 p-2 border rounded shadow-sm bg-white", style={"height": "85px"})
            )
        return items

    # Evaluate Scenario A
    if name_a and name_a in store_data:
        res_a = store_data[name_a].get("results")
        if res_a:
            df_prod_a = pd.DataFrame(res_a["prod"])
            df_dem_a = pd.DataFrame(res_a["demand"])
            df_ship_a = pd.DataFrame(res_a["ship"])
            sum_a = res_a["summary"]
            
            map_a = build_trade_map(generate_map(df_prod_a, df_dem_a, df_ship_a, render_token="static-a"), "trade-map-a")
            kpi_a = build_kpi_column(extract_metrics(sum_a, df_dem_a), "text-primary", name_a)
        else:
            map_a = html.P(f"Error: Scenario '{name_a}' missing data.", className="text-danger")

    # Evaluate Scenario B
    if name_b and name_b in store_data:
        res_b = store_data[name_b].get("results")
        if res_b:
            df_prod_b = pd.DataFrame(res_b["prod"])
            df_dem_b = pd.DataFrame(res_b["demand"])
            df_ship_b = pd.DataFrame(res_b["ship"])
            sum_b = res_b["summary"]
            
            map_b = build_trade_map(generate_map(df_prod_b, df_dem_b, df_ship_b, render_token="static-b"), "trade-map-b")
            kpi_b = build_kpi_column(extract_metrics(sum_b, df_dem_b), "text-success", name_b)
        else:
            map_b = html.P(f"Error: Scenario '{name_b}' missing data.", className="text-danger")

   # Calculate Visual Deltas
    if sum_a and sum_b:
        m_a = extract_metrics(sum_a, df_dem_a)
        m_b = extract_metrics(sum_b, df_dem_b)
        delta_items = [html.H6("DELTAS", className="text-center fw-bold mb-3 text-secondary pt-2")]
        
        for d in kpi_defs:
            v_a = m_a.get(d["id"], 0)
            v_b = m_b.get(d["id"], 0)
            diff = v_b - v_a
            
            # Format both the absolute difference and a true zero using the KPI's specific format
            formatted_diff = d["fmt"].format(abs(diff))
            formatted_zero = d["fmt"].format(0)
            
            if v_a == float('inf') or v_b == float('inf') or formatted_diff == formatted_zero:
                diff_str = "0" if formatted_diff == formatted_zero else "N/A"
                pct_str = "" 
                icon = "fa-minus"
                color = "text-muted"
            else:
                diff_str = formatted_diff
                
                # Safely calculate percentage change (avoids ZeroDivisionError)
                if v_a != 0:
                    pct = (abs(diff) / abs(v_a)) * 100
                    pct_str = f"({pct:.1f}%)"
                else:
                    pct_str = "" 
                    
                if diff > 0:
                    diff_str = "+" + diff_str
                    icon = "fa-arrow-up"
                    color = "text-success" if d["dir"] == 1 else "text-danger"
                else:
                    diff_str = "-" + diff_str
                    icon = "fa-arrow-down"
                    color = "text-success" if d["dir"] == -1 else "text-danger"
                    
            delta_items.append(
                html.Div([
                    
                    html.Div([
                        html.I(className=f"fa-solid {icon} {color} me-1"),
                        html.Span(diff_str, className=f"fw-bold {color} fs-5"),
                    ], className="d-flex align-items-center justify-content-center"),
                    
                    html.Div(pct_str, className=f"{color} small text-center lh-1 mt-1") if pct_str else ""
                    
                ], className="d-flex flex-column justify-content-center mb-3 p-1 bg-white border rounded shadow-sm", style={"height": "85px"})
            )
        deltas = delta_items

    return {"display": "block"}, title_a, title_b, map_a, map_b, kpi_a, kpi_b, deltas