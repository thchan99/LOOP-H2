# Import packages
import plotly.graph_objects as go
import pandas as pd

import dash
from dash import dcc, html, Input, Output, State, ctx, callback
import dash_bootstrap_components as dbc

import dash_leaflet as dl

import os
import sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from model.model import Model
import pages.helper_functions as hf

dash.register_page(__name__, path='/dashboard', name="Dashboard", order=1)

opt_model = Model()

### INPUTS ###
demand_segment_options = [
    {"label": "All Truck Stops", "value": 0},
    {"label": "RaceTrac Only", "value": 1},
]
hydrogenDemand = dbc.Card(
    className="custom-card shadow-sm border-2 h-100",
    children=[
        dbc.CardBody([
            html.H5([html.I(className="fa-solid fa-truck-fast me-2 text-primary"), "Hydrogen Demand"], 
                    className="card-title border-bottom pb-2 mb-2 fw-bold"),
            html.P("Set statewide fleet conversion goals and hydrogen adoption rates at major distribution centers.", 
                   className="text-muted small mb-3"),

            html.Label("Demand Location Segment", className="fw-semibold small"),
            dcc.Dropdown(
                id="demand-segment-select",
                options=demand_segment_options,
                value=0,
                clearable=False,
                className="mb-3 shadow-sm",
            ),
            
            html.Label("Initial Truck Fleet Conversion (%)", className="fw-semibold small"),
            dcc.Slider(0, 100, 0.1, value=2, id="slider-fleetconv", className="mb-2"),

            html.Label("Annual Truck Conversion (%)", className="fw-semibold small"),
            dcc.Slider(0, 100, 0.1, value=1.0, id="k_techpen", className="mb-2"),
            
            html.Label("Distribution Centers (H2 Forklifts) Conversion (%)", className="fw-semibold small mt-2"),
            html.Div("Amazon (%)", className="text-muted small ms-1"),
            dcc.Slider(0, 100, 0.1, value=5, id="slider-distcenter-az", className="mb-2"),
            
            html.Div("Walmart (%)", className="text-muted small ms-1"),
            dcc.Slider(0, 100, 0.1, value=5, id="slider-distcenter-wm", className="mb-2"),
            
            html.Div("Warehouse (%)", className="text-muted small ms-1"),
            dcc.Slider(0, 100, 0.1, value=5, id="slider-distcenter-hd"),
        ]),
    ],
)

prodOptions = dbc.Card(
    className="custom-card shadow-sm border-2 h-100",
    children=[
        dbc.CardBody([
            html.H5([html.I(className="fa-solid fa-industry me-2 text-primary"), "Production Options"], 
                    className="card-title border-bottom pb-2 mb-2 fw-bold"),
            html.P("Select active facility types and set network capacity margins.", 
                   className="text-muted small mb-3"),

            html.Label("Production Capacity Oversize Index (%)", className="text-muted small mb-2"),
            dcc.Slider(0, 200, 1, value=0, id="slider-oversize", className="mb-2"),

            html.Label("Allowed Facility Types:", className="text-muted small mb-2"),
            dbc.Checklist(
                options=[
                    {"label": "Use Existing Landfills (with BCS)", "value": "landfill with bcs"},
                    {"label": "Create New Biogas Systems (no BCS)", "value": "landfill without bcs"},
                    {"label": "Add Plug Power Facility", "value": "plug"},
                    {"label": "Add Planned Savannah Facility", "value": "savannah"},
                    {"label": "Add Hydrofleet Infrastructure", "value": "hydrofleet"}
                ],
                value=["landfill with bcs"],
                id="checklist-prodoptions",
                switch=True,
                className="d-flex flex-column gap-2"
            ),
            html.Label("Maximum Hydrofleet Facilities", className="fw-semibold small mt-3"),
            dcc.Slider(1, 10, 1, value=5, id="slider-max-hydrofleet", className="mb-2"),
        ]),
    ],
)

route_options = [
    {"label": "Interstate 16", "value": "I-16"},
    {"label": "Interstate 20", "value": "I-20"},
    {"label": "Interstate 75", "value": "I-75"},
    {"label": "Interstate 85", "value": "I-85"},
    {"label": "Interstate 95", "value": "I-95"},
]
tradeOff = dbc.Card(
    className="custom-card shadow-sm border-2 h-100",
    children=[
        dbc.CardBody([
            html.H5([html.I(className="fa-solid fa-scale-balanced me-2 text-primary"), "Trade-off Weights"], 
                    className="card-title border-bottom pb-2 mb-2 fw-bold"),
            html.P("Adjust the LP solver's objective weights and constrain the network to a preferred interstate route.", 
                   className="text-muted small mb-3"),
            
            html.Label("Minimize Transportation Costs", className="fw-semibold small"),
            dcc.Slider(0, 1, 0.01, value=0.0, id="k_transport", className="mb-2"),
            
            html.Label("Minimize Water Usage", className="fw-semibold small"),
            dcc.Slider(0, 1, 0.01, value=0.0, id="k_water", className="mb-2"),
            
            html.Label("Route(s) of Interest", className="fw-semibold small mt-2"),
            dcc.Dropdown(
                id="routeselect",
                options=route_options,
                value=[opt["value"] for opt in route_options],
                multi=True,
                className="shadow-sm"
            ),
        ]),
    ],
)

econOptions = dbc.Card(
    className="custom-card shadow-sm border-2 h-100",
    children=[
        dbc.CardBody([
            html.H5([html.I(className="fa-solid fa-coins me-2 text-primary"), "Economic Inputs"], 
                    className="card-title border-bottom pb-2 mb-2 fw-bold"),
            html.P("Define market price assumptions for hydrogen and byproduct graphene to drive the revenue analysis.", 
                   className="text-muted small mb-3"),
            
            html.Label("Hydrogen Market Price (per kg)", className="fw-semibold small"),
            dbc.InputGroup([
                dbc.InputGroupText("$"),
                dbc.Input(id="h2_sales", type="number", value=32, step=0.10),
            ], className="mb-3 shadow-sm"),
            
            html.Label("Graphene Market Price (per kg)", className="fw-semibold small"),
            dbc.InputGroup([
                dbc.InputGroupText("$"),
                dbc.Input(id="graphene_sales", type="number", value=2500.00, step=0.01),
            ], className="mb-4 shadow-sm"),
            
            html.Label("Graphene Sold (%)", className="fw-semibold small"),
            dcc.Slider(0, 100, 0.1, value=20, id="graphene_percent"),

            html.Label("Years-to-Forecast", className="fw-semibold small mt-2"),
            dcc.Slider(5, 30, 5, value=15, id="slider-forecast-years", className="mb-2"),
        ]),
    ],
)

errorAlert = html.Div(
    id="error-alert",
    className="alert alert-danger",
    style={"display": "none"},
    role="alert",
    children=[]
)

scenarioCard = dbc.Card(
    className="custom-card shadow-sm border-2 h-100",
    children=[
        dbc.CardBody([
            html.H5([html.I(className="fa-solid fa-floppy-disk me-2 text-primary"), "Scenario Manager"], 
                    className="card-title border-bottom pb-2 mb-3 fw-bold"),
            html.P("Save and load your desired inputs to your local cache to quickly compare trade studies.", 
                   className="text-muted small mb-3"),
            
            dbc.Row([
                # Save Column
                dbc.Col([
                    html.Label("Save Current Configuration", className="fw-semibold small"),
                    dbc.InputGroup([
                        dbc.Input(id="scenario-name-input", placeholder="e.g., Aggressive Adoption (20%)", type="text"),
                        dbc.Button("Save", id="btn-save-scenario", color="success", outline=True),
                    ], className="shadow-sm")
                ], xs=12, md=6, className="mb-3 mb-md-0"),
                
                # Load Column
                dbc.Col([
                    
                    html.Label("Load Saved Configuration", className="fw-semibold small"),
                    dcc.Dropdown(
                        id="scenario-select", 
                        placeholder="Select a scenario...", 
                        className="shadow-sm mb-2" # Stacked above buttons for cleaner UI
                    ),
                    dbc.InputGroup([
                        dbc.Button("Load", id="btn-load-scenario", color="primary", className="w-50"),
                        dbc.Button("Clear All", id="btn-clear-scenarios", color="danger", outline=True, className="w-50"),
                    ], className="shadow-sm")
                ], xs=12, md=6),
            ]),
            # Alert banner for save confirmation
            html.Div(id="scenario-alert", className="mt-3")
        ]),
    ],
)

@callback(
    Output("scenario-store", "data"),
    Output("scenario-alert", "children"),
    Input("btn-save-scenario", "n_clicks"),
    Input("btn-clear-scenarios", "n_clicks"),
    State("scenario-name-input", "value"),
    State("scenario-store", "data"),
    # Inputs
    State("demand-segment-select", "value"),
    State("slider-fleetconv", "value"),
    State("slider-distcenter-az", "value"),
    State("slider-distcenter-wm", "value"),
    State("slider-distcenter-hd", "value"),
    State("slider-oversize", "value"), 
    State("checklist-prodoptions", "value"),
    State("slider-max-hydrofleet", "value"),
    State("k_transport", "value"),
    State("k_water", "value"),
    State("k_techpen", "value"),
    State("routeselect", "value"),
    State("h2_sales", "value"),
    State("graphene_sales", "value"),
    State("graphene_percent", "value"),
    State("slider-forecast-years", "value"),
    #
    State("latest-results-store", "data"),
    prevent_initial_call=True
)
def manage_scenarios(save_clicks, clear_clicks, name, store_data, demand_sheet, fleet, az, wm, hd, oversize, prod, n_hydro, trans, water, tech, route, h2, graph, pct, years, latest_results):
    triggered_id = ctx.triggered_id
    
    if triggered_id == "btn-clear-scenarios":
        alert = dbc.Alert("All saved configurations cleared from local storage.", color="warning", duration=3000)
        return {}, alert 
        
    elif triggered_id == "btn-save-scenario":
        if not name:
            return dash.no_update, dbc.Alert("Please enter a scenario name.", color="danger", duration=3000)
        
        if not latest_results:
            return dash.no_update, dbc.Alert("You must run the optimization before saving!", color="danger", duration=3000)
            
        new_store = store_data.copy() if store_data else {}
        
        new_store[name] = {
            "inputs": {
                "demand_sheet": demand_sheet,
                "fleet": fleet, "az": az, "wm": wm, "hd": hd, "oversize": oversize,
                "prod": prod, "n_hydro": n_hydro, "trans": trans, "water": water, "tech": tech,
                "route": route, "h2": h2, "graph": graph, "pct": pct, "years": years
            },
            "results": latest_results
        }
        
        alert = dbc.Alert(f"Scenario '{name}' saved successfully.", color="success", duration=3000)
        return new_store, alert 
    
    return dash.no_update, dash.no_update

@callback(
    Output("scenario-select", "options"),
    Input("scenario-store", "data")
)
def update_dropdown_on_load(store_data):
    if isinstance(store_data, dict) and store_data:
        return [{"label": str(k), "value": str(k)} for k in store_data.keys()]
    return []

@callback(
    # --- INPUTS (16 total) ---
    Output("demand-segment-select", "value"),
    Output("slider-fleetconv", "value"),
    Output("slider-distcenter-az", "value"),
    Output("slider-distcenter-wm", "value"),
    Output("slider-distcenter-hd", "value"),
    Output("slider-oversize", "value"),
    Output("checklist-prodoptions", "value"),
    Output("slider-max-hydrofleet", "value"),
    Output("k_transport", "value"),
    Output("k_water", "value"),
    Output("k_techpen", "value"),
    Output("routeselect", "value"),
    Output("h2_sales", "value"),
    Output("graphene_sales", "value"),
    Output("graphene_percent", "value"),
    Output("slider-forecast-years", "value"),
    # --- RESULTS (Duplicates of the main generator) ---
    Output("dl_map", "children", allow_duplicate=True),
    Output("error-alert", "children", allow_duplicate=True),
    Output("error-alert", "style", allow_duplicate=True),
    Output("grid-prod", "rowData", allow_duplicate=True),
    Output("grid-prod", "columnDefs", allow_duplicate=True),
    Output("grid-demand", "rowData", allow_duplicate=True),
    Output("grid-demand", "columnDefs", allow_duplicate=True),
    Output("grid-ship", "rowData", allow_duplicate=True),
    Output("grid-ship", "columnDefs", allow_duplicate=True),
    Output("roi-projection-content", "children", allow_duplicate=True),
    Output("supply-demand-content", "children", allow_duplicate=True),
    Output("expense-content", "children", allow_duplicate=True),
    Output("revenue-content", "children", allow_duplicate=True),
    Output("fuel-imports-content", "children", allow_duplicate=True),
    Output("roi-projection-math", "children", allow_duplicate=True),
    Output("fuel-imports-math", "children", allow_duplicate=True),
    Output("roi-projection-chart", "figure", allow_duplicate=True),
    Output("supply-demand-chart", "figure", allow_duplicate=True),
    Output("expense-chart", "figure", allow_duplicate=True),
    Output("revenue-chart", "figure", allow_duplicate=True),
    Output("fuel-imports-chart", "figure", allow_duplicate=True),
    Output("latest-results-store", "data", allow_duplicate=True),
    Output("scenario-alert", "children", allow_duplicate=True),
    # --- TRIGGER ---
    Input("btn-load-scenario", "n_clicks"),
    State("scenario-select", "value"),
    State("scenario-store", "data"),
    # --- SPINNER ---
    running=[
        (Output("btn-load-scenario", "disabled"), True, False),
        (
            Output("btn-load-scenario", "children"),
            [dbc.Spinner(size="sm", spinnerClassName="me-2"), "Loading..."],
            "Load"
        ),
    ],
    prevent_initial_call=True
)
def load_scenario(n_clicks, selected_name, store_data):
    if not selected_name or not store_data or selected_name not in store_data:
        return (dash.no_update,) * 37 + (dbc.Alert("Select a valid scenario", color="danger"),)
    
    scenario = store_data[selected_name]
    inputs = scenario.get("inputs")
    results = scenario.get("results")

    # Reconstruct Data
    df_prod = pd.DataFrame(results['prod'])
    df_demand = pd.DataFrame(results['demand'])
    df_ship = pd.DataFrame(results['ship'])
    summary = results['summary']

    # Aggregated Values
    yrs = inputs.get("years")
    tech = inputs.get("tech")
    fleet = inputs.get("fleet")
    h2_p = inputs.get("h2")
    graph_p = inputs.get("graph")
    graph_pct = inputs.get("pct") / 100.0
    az = inputs.get("az")
    wm = inputs.get("wm")
    hd = inputs.get("hd")

    # Generate Components via Helper Functions
    prod_data, prod_cols = hf.df_to_ag_grid(df_prod[df_prod["H2 Production Capacity (kg/day)"] > 0])
    demand_data, demand_cols = hf.df_to_ag_grid(df_demand)
    ship_data, ship_cols = hf.df_to_ag_grid(df_ship)

    fig_sd, sd_html = hf.build_supply_demand_card(df_prod, df_demand, summary)
    fig_f, f_html, f_math = hf.build_fuel_forecast_card(df_prod, df_demand, tech, fleet, az, wm, hd, yrs)
    fig_roi, roi_html, roi_math = hf.build_roi_card(summary, yrs)
    fig_rev, rev_html = hf.build_revenue_card(df_prod, df_demand, df_ship, summary, h2_p, graph_p, graph_pct)
    fig_exp, exp_html = hf.build_expense_card(df_prod, df_demand, df_ship, summary, h2_p, graph_p, graph_pct)
    map_layers = hf.generate_map(df_prod, df_demand, df_ship, render_token=f"load-{selected_name}")

    return (
        # Inputs (16)
        inputs.get("demand_sheet"), inputs.get("fleet"), inputs.get("az"), inputs.get("wm"), 
        inputs.get("hd"), inputs.get("oversize"), inputs.get("prod"), 
        inputs.get("n_hydro"), inputs.get("trans"), inputs.get("water"), 
        inputs.get("tech"), inputs.get("route"), inputs.get("h2"), inputs.get("graph"), inputs.get("pct"), inputs.get("years"),
        # Results/Charts (21)
        map_layers, "", {"display": "none"},
        prod_data, prod_cols, demand_data, demand_cols, ship_data, ship_cols,
        roi_html, sd_html, exp_html, rev_html, f_html, 
        roi_math, f_math,
        fig_roi, fig_sd, fig_exp, fig_rev, fig_f,
        results,
        dbc.Alert(f"Scenario '{selected_name}' loaded.", color="success")
    )


### ECONOMICS ###

supplyDemandCard = dbc.Card(
    className="custom-card shadow-sm border-2 h-100", 
    children=[
        dbc.CardBody([
            html.H5([html.I(className="fa-solid fa-chart-pie me-2 text-primary"), "Supply-Demand Outlook"], 
                    className="card-title border-bottom pb-2 mb-2 fw-bold"),
            html.P("Comparison of total daily hydrogen production capacity against localized fleet demand.", 
                   className="text-muted small mb-3"),
            
            dcc.Graph(id="supply-demand-chart", style={"height": ""}), 
            html.Div(id="supply-demand-content", className="mt-3", children=[
                html.P("Run optimization to view data.", className="text-muted")
            ]),
        ]),
    ],
)

fuelImportsCard = dbc.Card(
    className="custom-card shadow-sm border-2 h-100",
    children=[
        dbc.CardBody([
            html.H5([html.I(className="fa-solid fa-gas-pump me-2 text-primary"), "Fuel Imports Forecast"], 
                    className="card-title border-bottom pb-2 mb-2 fw-bold"),
            html.P("Projection of future infrastructure deficits based on technology penetration and fleet conversion rates.", 
                   className="text-muted small mb-2"),
                      
            dcc.Graph(id="fuel-imports-chart", style={"height": "30vh"}),
            dcc.Markdown(
                id="fuel-imports-math",
                mathjax=True,
                className="small text-muted bg-light p-2 rounded mb-3 border shadow-sm overflow-auto",
            ),
            html.Div(id="fuel-imports-content", className="mt-3", children=[
                html.P("Run optimization to view forecast.", className="text-muted")
            ]),
        ]),
    ],
)

roiProjectionCard = dbc.Card(
    className="custom-card shadow-sm border-2 h-100",
    children=[
        dbc.CardBody([
            html.H5([html.I(className="fa-solid fa-chart-line me-2 text-primary"), "Cumulative Cashflow"], 
                    className="card-title border-bottom pb-2 mb-2 fw-bold"),
            html.P("Cumulative cash flow analysis mapping the timeline to capital recovery and ROI over the forecasted period.", 
                   className="text-muted small mb-2"),

            dcc.Graph(id="roi-projection-chart", style={"height": "30vh"}),
            dcc.Markdown(
                id="roi-projection-math",
                mathjax=True,
                className="small text-muted bg-light p-2 rounded mb-3 border shadow-sm overflow-auto",
            ),
            html.Div(id="roi-projection-content", className="mt-3", children=[
                html.P("Run optimization to view data.", className="text-muted")
            ]),
        ]),
    ],
)

revenueCard = dbc.Card(
    className="custom-card shadow-sm border-2 h-100",
    children=[
        dbc.CardBody([
            html.H5([html.I(className="fa-solid fa-coins me-2 text-primary"), "Revenue Generation"], 
                    className="card-title border-bottom pb-2 mb-2 fw-bold"),
            dcc.Graph(id="revenue-chart", style={"height": "30vh"}),
            html.Div(id="revenue-content", className="mt-2", children=[
                html.P("Run optimization to view revenue.", className="text-muted")
            ])
        ])
    ]
)

expenseCard = dbc.Card(
    className="custom-card shadow-sm border-2 h-100",
    children=[
        dbc.CardBody([
            html.H5([html.I(className="fa-solid fa-money-bill-transfer me-2 text-primary"), "System Expenses"], 
                    className="card-title border-bottom pb-2 mb-2 fw-bold"),
            dcc.Graph(id="expense-chart", style={"height": "30vh"}),
            html.Div(id="expense-content", className="mt-2", children=[
                html.P("Run optimization to view expenses.", className="text-muted")
            ])
        ])
    ]
)

### MAP ###
# Approximate bounding box for Georgia
GA_BOUNDS = [[30.35, -85.6], [35.0, -80.8]]

mapTab = html.Div([
    dl.Map(
        children=hf.generate_map(None, None, None, render_token="init"), 
        center=[32.8, -83.4],
        zoom=7,
        minZoom=6,
        maxZoom=10,
        maxBounds=GA_BOUNDS,
        maxBoundsViscosity=1.0,
        style={
            "width": "100%",
            "aspectRatio": "1",
            "minHeight": "400px",
            "maxHeight": "50vh", 
            "borderRadius": "8px"
        },
        id="dl_map",
    ),
    
    # Legend
    html.Div(
        className="d-flex flex-wrap justify-content-center gap-3 mt-3 pt-3 border-top",
        children=[
            # Production Markers
            html.Span([html.I(className="fa-solid fa-trash me-1", style={"color": "#28a745"}), "Landfill (w/ BCS)"], className="small fw-semibold text-muted"),
            html.Span([html.I(className="fa-solid fa-trash me-1", style={"color": "#dc3545"}), "Landfill (No BCS)"], className="small fw-semibold text-muted"),
            html.Span([html.I(className="fa-solid fa-bolt me-1", style={"color": "#6f42c1"}), "Plug Power"], className="small fw-semibold text-muted"),
            html.Span([html.I(className="fa-solid fa-industry me-1", style={"color": "#6f42c1"}), "Savannah"], className="small fw-semibold text-muted"),
            html.Span([html.I(className="fa-solid fa-droplet me-1", style={"color": "#fd7e14"}), "Hydrofleet"], className="small fw-semibold text-muted"),
            
            # Demand Markers
            html.Span([html.I(className="fa-solid fa-truck me-1", style={"color": "#007bff"}), "Truck Stop"], className="small fw-semibold text-muted"),
            html.Span([html.I(className="fa-solid fa-box me-1", style={"color": "#ffc107"}), "Amazon"], className="small fw-semibold text-muted"),
            html.Span([html.I(className="fa-solid fa-cart-shopping me-1", style={"color": "#6c757d"}), "Walmart"], className="small fw-semibold text-muted"),
            html.Span([html.I(className="fa-solid fa-warehouse me-1", style={"color": "#ffd700"}), "Warehouse"], className="small fw-semibold text-muted"),
            
            # Routes
            html.Span([html.I(className="fa-solid fa-minus me-1", style={"color": "#2C3E50"}), "Shipping Route"], className="small fw-semibold text-muted"),
        ]
    )
])

### TABLES ###

grid_prod = hf.create_default_grid("grid-prod")
grid_demand = hf.create_default_grid("grid-demand")
grid_ship = hf.create_default_grid("grid-ship")

tabsCard = dbc.Card(
    className="custom-card shadow-sm border-2 h-100",
    children=[
        dbc.CardBody([
            html.H5([html.I(className="fa-solid fa-map-location-dot me-2 text-primary"), "Optimization Results"], 
                    className="card-title border-bottom pb-2 mb-3 fw-bold"),
            dbc.Tabs([
                dbc.Tab(mapTab, label="Optimization Map", tab_id="tab-map", className="pt-3"),
                dbc.Tab(hf.build_grid_tab(grid_prod, "prod", "Production Sites"), label="Production Sites", className="pt-3"),
                dbc.Tab(hf.build_grid_tab(grid_demand, "demand", "Demand Points"), label="Demand Points", className="pt-3"),
                dbc.Tab(hf.build_grid_tab(grid_ship, "ship", "Shipping Routes"), label="Shipping Routes", className="pt-3")
            ], id="master-tabs", active_tab="tab-map")
        ]),
    ],
)

# grid callbacks to download CSV
@callback(
    Output("download-prod", "data"),
    Input("btn-export-prod", "n_clicks"),
    State("grid-prod", "rowData"),
    prevent_initial_call=True
)
def export_prod_csv(n_clicks, row_data):
    if row_data:
        df = pd.DataFrame(row_data)
        return dcc.send_data_frame(df.to_csv, "LOOP_H2_Production_Sites.csv", index=False)

@callback(
    Output("download-demand", "data"),
    Input("btn-export-demand", "n_clicks"),
    State("grid-demand", "rowData"),
    prevent_initial_call=True
)
def export_demand_csv(n_clicks, row_data):
    if row_data:
        df = pd.DataFrame(row_data)
        return dcc.send_data_frame(df.to_csv, "LOOP_H2_Demand_Points.csv", index=False)

@callback(
    Output("download-ship", "data"),
    Input("btn-export-ship", "n_clicks"),
    State("grid-ship", "rowData"),
    prevent_initial_call=True
)
def export_ship_csv(n_clicks, row_data):
    if row_data:
        df = pd.DataFrame(row_data)
        return dcc.send_data_frame(df.to_csv, "LOOP_H2_Shipping_Routes.csv", index=False)
    

### MAIN CALLBACK FUNCTION - GENERATE RESULTS ###
@callback(
    # Map and Alert Outputs
    Output("dl_map", "children"),
    Output("error-alert", "children"),
    Output("error-alert", "style"),
    # Table Outputs
    Output("grid-prod", "rowData"),
    Output("grid-prod", "columnDefs"),
    Output("grid-demand", "rowData"),
    Output("grid-demand", "columnDefs"),
    Output("grid-ship", "rowData"),
    Output("grid-ship", "columnDefs"),
    # Economics Outputs
    Output("roi-projection-content", "children"),
    Output("supply-demand-content", "children"),
    Output("expense-content", "children"),
    Output("revenue-content", "children"),
    Output("fuel-imports-content", "children"),
    Output("roi-projection-math", "children"),
    Output("fuel-imports-math", "children"),
    Output("roi-projection-chart", "figure"),
    Output("supply-demand-chart", "figure"),
    Output("expense-chart", "figure"),
    Output("revenue-chart", "figure"),
    Output("fuel-imports-chart", "figure"),
    # Data Cache
    Output("latest-results-store", "data"),
    # -------------------------
    Input("map_btn", "n_clicks"),
    # -------------------------
    State("demand-segment-select", "value"),
    State("slider-fleetconv", "value"),
    State("slider-distcenter-az", "value"),
    State("slider-distcenter-wm", "value"),
    State("slider-distcenter-hd", "value"),
    State("slider-oversize", "value"),
    State("checklist-prodoptions", "value"),
    State("slider-max-hydrofleet", "value"),
    State("k_transport", "value"),
    State("k_water", "value"),
    State("k_techpen", "value"),
    State("routeselect", "value"),
    State("h2_sales", "value"),
    State("graphene_sales", "value"),
    State("graphene_percent", "value"),
    State("slider-forecast-years", "value"),
    # -------------------------
    running=[
        (Output("map_btn", "disabled"), True, False), # Disables button while running, re-enables when done
        (
            Output("map_btn", "children"), 
            [dbc.Spinner(size="sm", spinnerClassName="me-2"), " Running Optimization..."],
            "Generate Optimization Results"
        ),
    ],
    prevent_initial_call=True
)
def generate_dashboard_results(n, demand_sheet, fleetconv, dist_az, dist_wm, dist_hd, oversize_idx, prod_opts, n_hydro,
                               k_trans, k_water, k_tech, route, h2_sale, graph_sale, graph_pct, forecast_years):
    print(f"Button clicked! n_clicks={n}")
    
    if prod_opts is None:
        prod_opts = []

    # default if user hasn't changed inputs 
    user_params = {
        "demand_sheet_num": 0 if demand_sheet is None else demand_sheet,
        "fleetconv": 3.5 if fleetconv is None else fleetconv,
        "distcenter_az": 10 if dist_az is None else dist_az,
        "distcenter_wm": 10 if dist_wm is None else dist_wm,
        "distcenter_hd": 10 if dist_hd is None else dist_hd,
        "oversize_index": 0 if oversize_idx is None else oversize_idx,
        "prodoptions": prod_opts,
        "n_hydrofleet": 5 if n_hydro is None else n_hydro,
        "k_transport": 0.0 if k_trans is None else k_trans,
        "k_water": 0.0 if k_water is None else k_water,
        "k_techpen": 5.0 if k_tech is None else k_tech,
        "routes": ['I-16', 'I-20', 'I-75', 'I-85', 'I-95'] if route is None else route,
        "h2_sale": 32.0 if h2_sale is None else h2_sale,
        "graphene_sale": 2500.0 if graph_sale is None else graph_sale,
        "graphene_percent": 20.0 if graph_pct is None else graph_pct,
        "forecast_years": 15 if forecast_years is None else forecast_years,
        "time_limit": 60.0,     # MILP Compute time (seconds)
        "mip_rel_gap": 0.05,    # Accept a solution within 5% of theoretical perfection
    }
    
    print("Running model with parameters:", user_params)

    try:
        # Pass the params to the engine
        df_prod, df_demand, df_ship2, summary = opt_model.get_optimal_soln(user_params)
        
        # If it returns successfully, the model is feasible
        print("Model feasible.")
        print(summary)
        
    except Exception as e:
        # If the optimizer fails, catch the error and return the failure UI
        error_message = str(e)
        empty_html = html.P("Model failed. Check parameters.", className="text-danger")
        empty_fig = go.Figure().update_layout(template="plotly_white", margin=dict(t=10, b=10, l=10, r=10))
        empty_df = pd.DataFrame()
        empty_math = "Waiting for valid parameters..."
        
        return [
            # Map and alerts
            hf.generate_map(empty_df, empty_df, empty_df, render_token=f"error-{n}"),
            html.Strong("Error: Optimization failed. " + error_message),
            {"display": "block"},
            # tables
            [], [], [], [], [], [],
            # economics
            empty_html, empty_html, empty_html, empty_html, empty_html,
            empty_math, empty_math, 
            empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, 
            # cache
            {}
        ]
    
    ## Handle Model Success
    print("Optimization successful, updating UI.")
        
    ## Tables
    # Filter production sites with capacity > 0
    df_prod_filtered = df_prod[df_prod["H2 Production Capacity (kg/day)"] > 0]
    prod_data, prod_cols = hf.df_to_ag_grid(df_prod_filtered)
    demand_data, demand_cols = hf.df_to_ag_grid(df_demand)
    ship_data, ship_cols = hf.df_to_ag_grid(df_ship2)
    
    ## Update cards and populate results
    # get safe user params
    tech_pen = user_params.get("k_techpen")
    fleet_conv = user_params.get("fleetconv")
    forecast_yrs = user_params.get("forecast_years")
    h2_p = user_params.get("h2_sale")
    graph_p = user_params.get("graphene_sale")
    graph_perct = user_params.get("graphene_percent") / 100.0

    ### SUPPLY-DEMAND OUTLOOK ###
    fig_sd, sd_html = hf.build_supply_demand_card(df_prod, df_demand, summary)

    ### FUEL TRANSITION FORECAST ###
    fig_forecast, forecast_html, math_fuel = hf.build_fuel_forecast_card(
        df_prod, df_demand, tech_pen, fleet_conv, dist_az, dist_wm, dist_hd, forecast_yrs)

    ### ROI CASH FLOW ###
    fig_roi, roi_html, math_roi = hf.build_roi_card(summary, forecast_yrs)

    ### COST ANALYSIS ###
    fig_rev, revenue_html = hf.build_revenue_card(df_prod, df_demand, df_ship2, summary, h2_p, graph_p, graph_perct)
    fig_expense, expense_html = hf.build_expense_card(df_prod, df_demand, df_ship2, summary, h2_p, graph_p, graph_perct)
    
    # ---------------------------------------------------------------------------

    results_payload = {
        "prod": df_prod.to_dict('records'),
        "demand": df_demand.to_dict('records'),
        "ship": df_ship2.to_dict('records'),
        "summary": summary
    }

    return [
        hf.generate_map(df_prod, df_demand, df_ship2, render_token=f"run-{n}"),
        "",
        {"display": "none"},
        prod_data, prod_cols, demand_data, demand_cols, ship_data, ship_cols,
        roi_html, sd_html, expense_html, revenue_html, forecast_html, 
        math_roi, math_fuel,
        fig_roi, fig_sd, fig_expense, fig_rev, fig_forecast,
        results_payload
    ]


### APP LAYOUT ###
layout = dbc.Container([
    dcc.Store(id="latest-results-store", data=None),
    dcc.Store(id="scenario-store", storage_type="local"),
    # --- Page Header ---
    dbc.Row([
        html.Div([
            html.H2("Hydrogen Infrastructure Dashboard", className="text-dark fw-bold"),
            html.P("Configure parameters to generate an optimized solution for localized hydrogen infrastructure across the State of Georgia.", className="text-muted"),
        ], className="mb-4 mt-3 border-bottom pb-2")
    ]),
    # User Inputs Row
    dbc.Row(
        id="inputs-row",
        className="mb-2 g-2",
        children=[
            dbc.Col(hydrogenDemand, xs=12, md=6, lg=3, ),
            dbc.Col(prodOptions, xs=12, md=6, lg=3, ),
            dbc.Col(tradeOff, xs=12, md=6, lg=3, ),
            dbc.Col(econOptions, xs=12, md=6, lg=3, ),
        ],
    ),
    dbc.Row(
        id="scenario-row",
        className="mb-4 g-4",
        children=[
            dbc.Col(scenarioCard, width=12),
        ],
    ),
    dbc.Row([
        dbc.Col(
            html.Div(
                className="d-grid gap-2 col-6 mx-auto mb-2",
                children=[
                    dbc.Button("Generate Optimization Results", id="map_btn", size="lg", 
                               className="btn-success shadow rounded-pill")
                ]
            )
        )
    ]),
    # Error Alert Row
    dbc.Row(errorAlert, id="error-row", className="mb-3"),
    
    # Graphical Results Row
    dbc.Row(
        id="graph-row",
        className="mb-2 g-2",
        children=[
            dbc.Col(fuelImportsCard, xs=12, md=6, lg=3),
            dbc.Col(roiProjectionCard, xs=12, md=6, lg=3),
            dbc.Col(tabsCard, xs=12, md=12, lg=6),
        ],
    ),
    # Economic Analysis Row
    dbc.Row(
        id="economics-row",
        className="mb-2 g-2",
        children=[
            dbc.Col(supplyDemandCard, xs=12, md=4, lg=4),
            dbc.Col(revenueCard, xs=12, md=4, lg=4),
            dbc.Col(expenseCard, xs=12, md=4, lg=4),
        ],
    ),

    ],
    fluid=True,
    className="dbc custom-bg min-vh-100"
)