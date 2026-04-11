from dash import dcc, html
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import dash_ag_grid as dag

import plotly.express as px

import pandas as pd
from datetime import datetime
import textwrap

from model.economics import summarize_solution_economics
from model.economics_mixed import summarize_mixed_solution_economics
import config.constants as constants

COLOR_DISCRETE_MAP={
            "Landfill With Bcs": "#28a745", 
            "Landfill Without Bcs": "#dc3545",
            "Plug": "#6f42c1", 
            "Savannah": "#6f42c1", 
            "Hydrofleet": "#FF69B4",
            "Truck": "#007bff", 
            "Amazon": "#ffc107", 
            "Walmart": "#6c757d",
            "Warehouse": "#964B00"
        }
demand_icon_map = {
        "truck": {"icon": "fa-truck", "color": "#007bff"},
        "amazon": {"icon": "fa-box", "color": "#FF9900"},
        "walmart": {"icon": "fa-cart-shopping", "color": "#6c757d"},
        "warehouse": {"icon": "fa-warehouse", "color": "#964B00"},
    }
prod_icon_map = {
        "landfill with bcs": {"icon": "fa-trash", "color": "#28a745"},
        "landfill without bcs": {"icon": "fa-trash", "color": "#dc3545"},
        "plug": {"icon": "fa-bolt", "color": "#6f42c1"},
        "savannah": {"icon": "fa-industry", "color": "#6f42c1"},
        "hydrofleet": {"icon": "fa-droplet", "color": "#FF69B4"},
    }


def format_currency_compact(value, decimals=1):
    """Formats large numbers into $1.2M, $500K, etc."""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return "$0"
    
    sign = "-" if num < 0 else ""
    abs_num = abs(num)
    
    for scale, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs_num >= scale:
            compact = abs_num / scale
            text = f"{compact:,.{decimals}f}".rstrip("0").rstrip(".")
            return f"{sign}${text}{suffix}"
    return f"{sign}${abs_num:,.0f}"

def dict_to_html(title, data_dict, is_currency=False):
        items = []
        for key, val in data_dict.items():
            if isinstance(val, dict):
                # If the value is a nested dictionary, create a sub-list
                sub_items = []
                for sub_key, sub_val in val.items():
                    val_str = format_currency_compact(sub_val) if is_currency else f"{sub_val:,.0f} kg/day"
                    sub_items.append(html.Li(f"{sub_key.title()}: {val_str}"))
                
                # Append the parent category name and its nested sub-list
                items.append(html.Li([
                    html.Span(f"{key.title()}:", className="fw-semibold"),
                    html.Ul(sub_items, className="list-unstyled ms-4 border-start ps-2 border-2 text-muted") 
                ], className="mb-2"))
            else:
                # If it's a standard number, format it normally
                val_str = format_currency_compact(val) if is_currency else f"{val:,.0f} kg/day"
                items.append(html.Li(f"{key.title()}: {val_str}", className="mb-1"))
                
        return html.Div([
            html.H6(title, className="fw-bold mt-2 text-primary"),
            html.Ul(items, className="list-unstyled ms-2")
        ])

def create_default_grid(grid_id):
    return dag.AgGrid(
        id=grid_id,
        rowData=[],
        columnDefs=[],
        defaultColDef={"resizable": True, "sortable": True, "filter": True},
        dashGridOptions={
            "pagination": True, 
            "paginationPageSize": 25,
            "animateRows": True,
            "rowSelection": "single"
        },
        className="ag-theme-alpine custom-grid",
        style={"height": "50vh", "width": "100%"}
    )

# Helper function to wrap grids with an export button
def build_grid_tab(grid_component, tab_id, label):
    return html.Div([
        grid_component,
        html.Div([
            dbc.Button([html.I(className="fa-solid fa-download me-2"), f"Export {label}"], 
                       id=f"btn-export-{tab_id}", size="sm", color="secondary", outline=True, className="mt-2 shadow-sm"),
            dcc.Download(id=f"download-{tab_id}")
        ], className="d-flex justify-content-end")
    ])


def df_to_ag_grid(df):
    formatted_data = [{k: round(v, 4) if isinstance(v, (int, float)) and not isinstance(v, bool) else v 
                        for k, v in record.items()} for record in df.to_dict('records')]
    columns = [{"field": col} for col in df.columns]
    return formatted_data, columns


def generate_map(df_prod, df_demand, df_ship2, render_token="init"):
    """Create a set of map layers from model output tables."""
    
    if df_prod is None or df_prod.empty:
        df_prod = pd.DataFrame(columns=["Latitude", "Longitude", "Type", "H2 Production Capacity (kg/day)", "Total H2 Shipped (kg/day)"])
    if df_demand is None or df_demand.empty:
        df_demand = pd.DataFrame(columns=["Latitude", "Longitude", "Type", "Name", "Demand (kg/day)"])
    if df_ship2 is None or df_ship2.empty:
        df_ship2 = pd.DataFrame(columns=["supply_idx", "supply_lon", "supply_lat", "demand_lon", "demand_lat", "ship_kg_day"])
    
    # --- Markers: Demand (With Clustering) ---
    demand_markers = []
    
    
    for idx, r in df_demand.iterrows():
        name = r.get("Name", "Unknown Facility")
        demand_type = r.get("Type", "truck")
        demand_amt = r.get("Demand (kg/day)", 0)
        icon_info = demand_icon_map.get(demand_type.lower(), {"icon": "fa-map-marker", "color": "#007bff"})
        
        # Determine opacity based on demand volume
        opacity = 0.9 if demand_amt > 0 else 0.2
        
        popup_html = [
            html.B(name),
            html.Br(),
            f"Type: {demand_type.title()}",
            html.Br(),
            f"Demand: {demand_amt:,.0f} kg/day",
        ]

        # Badge CSS Styling for Demand Markers
        badge_html = f"""
        <div style="
            background-color: {icon_info['color']};
            color: white;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 3px 6px rgba(0,0,0,0.4);
            border: 2px solid white;
        ">
            <i class="fa-solid {icon_info['icon']}" style="font-size: 14px;"></i>
        </div>
        """

        demand_markers.append(
            dl.DivMarker(
                id=f"demand-marker-{render_token}-{idx}",
                position=(r.get("Latitude", 0), r.get("Longitude", 0)),
                opacity=opacity,
                iconOptions={ 
                    "className": "custom-div-icon", 
                    "html": badge_html,
                    "iconSize": [24, 24],
                    "iconAnchor": [15, 15],
                },
                children=dl.Popup(popup_html)
            )
        )
        
    # --- Markers: Production ---
    prod_markers = []
    

    for idx, r in df_prod.iterrows():
        prod_type = r.get("Type", "prod")
        cap = r.get("H2 Production Capacity (kg/day)", 0)
        site_name = r.get("Name", prod_type.title())
        shipped_amt = r.get("Total H2 Shipped (kg/day)", 0)

        is_hydrofleet = str(prod_type).lower() == "hydrofleet"
        is_plug = str(prod_type).lower() == "plug"
        is_savannah = str(prod_type).lower() == "savannah"
        
        if is_hydrofleet and cap <= 0:
            continue
        
        icon_info = prod_icon_map.get(prod_type.lower(), {"icon": "fa-industry", "color": "#000000"})
        icon_size = 42 if (is_hydrofleet or is_plug or is_savannah) else 30
        icon_font_size = 24 if (is_hydrofleet or is_plug or is_savannah) else 18
        icon_anchor = icon_size // 2
        opacity = 1.0 if cap > 0 else 0.4

        # Update the popup to show the specific Name with the Type underneath
        popup_html = [
            html.B(site_name),
            html.Br(),
            html.Span(f"Facility Type: {prod_type.title()}", style={"fontSize": "0.85em", "color": "#6c757d"}),
            html.Br(),
            f"Capacity: {cap:,.0f} kg/day",
            html.Br(),
            f"Shipped: {shipped_amt:,.0f} kg/day",
        ]

        # Badge CSS Styling for Production Markers
        prod_badge_html = f"""
        <div style="
            background-color: {icon_info['color']};
            color: white;
            border-radius: 50%;
            width: {icon_size}px;
            height: {icon_size}px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 8px rgba(0,0,0,0.5);
            border: 2px solid white;
        ">
            <i class="fa-solid {icon_info['icon']}" style="font-size: {icon_font_size}px;"></i>
        </div>
        """

        prod_markers.append(
            dl.DivMarker(
                id=f"prod-marker-{render_token}-{idx}",
                position=(r.get("Latitude", 0), r.get("Longitude", 0)),
                opacity=opacity,
                iconOptions={
                    "className": "custom-div-icon",
                    "html": prod_badge_html,
                    "iconSize": [icon_size, icon_size],
                    "iconAnchor": [icon_anchor, icon_anchor],
                },
                children=dl.Popup(popup_html)
            )
        )

    # --- Lines: Shipments ---
    line_features = []
    for _, r in df_ship2.iterrows():
        ship_amt = r.get('ship_kg_day', 0)
        line_features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[r.get("supply_lon", 0), r.get("supply_lat", 0)],
                                [r.get("demand_lon", 0), r.get("demand_lat", 0)]],
            },
            "properties": {
                "popup": f"<b>Route Load:</b> {ship_amt:,.0f} kg/day"
            }
        })
        
    lines_geojson = {"type": "FeatureCollection", "features": line_features}

    return [
        dl.TileLayer(id=f"tile-{render_token}", maxZoom=10, maxNativeZoom=9),
        dl.GeoJSON(
            id=f"routes-{render_token}",
            data=lines_geojson,
            style={"color": "#2C3E50", "weight": 2, "opacity": 0.5}, 
        ),
        dl.LayerGroup(
            demand_markers, 
            id=f"demand-layer-{render_token}"
        ),
        dl.LayerGroup(
            prod_markers, 
            id=f"prod-layer-{render_token}"
        ),
    ]


def build_supply_demand_card(df_prod, df_demand, summary):
    """
    Modular builder for the Supply-Demand Card. 
    Returns: (Figure, HTML_Content)
    """

    supply_dict = df_prod.groupby("Type")["H2 Production Capacity (kg/day)"].sum().to_dict()
    demand_dict = df_demand.groupby("Type")["Demand (kg/day)"].sum().to_dict()
    
    records = []
    for type_name, val in supply_dict.items():
        if val > 0:
            records.append({"Category": "Supply", "Facility Type": type_name.title(), "Amount (kg/day)": val})
    for type_name, val in demand_dict.items():
        if val > 0:
            records.append({"Category": "Demand", "Facility Type": type_name.title(), "Amount (kg/day)": val})
    
    df_plot = pd.DataFrame(records)

    fig_sd = px.bar(
        df_plot, x="Category", y="Amount (kg/day)", color="Facility Type", 
        barmode="stack", template="plotly_white",
        color_discrete_map=COLOR_DISCRETE_MAP
    )
    fig_sd.update_layout(margin=dict(t=30, b=0, l=0, r=0), legend_title_text="")

    total_supply = sum(supply_dict.values())
    total_demand = sum(demand_dict.values())
    graphene_produced = summary.get("total_graphene_kg_day", summary.get("graphene_produced", 0))

    utilization = (total_demand / total_supply * 100) if total_supply > 0 else 0

    sd_html = html.Div([
        html.Div([
            html.H6(f"Total H2 Supply: {total_supply:,.0f} kg/day", className="fw-bold text-success mb-1"),
            html.H6(f"Total H2 Demand: {total_demand:,.0f} kg/day", className="fw-bold text-primary mb-1"),
            html.H6(f"Graphene Produced: {graphene_produced:,.0f} kg/day", className="fw-bold text-primary mb-1"),
            html.H6(f"Network Utilization: {utilization:,.1f}%", className="fw-bold text-primary mb-3"),
        ], className="border-bottom pb-2 mb-2"),
        dict_to_html("Supply Breakdown", supply_dict),
        dict_to_html("Demand Breakdown", demand_dict)
    ])

    return fig_sd, sd_html

def build_fuel_forecast_card(df_prod, df_demand, tech_pen, fleet_conv, az_conv, wm_conv, hd_conv, forecast_yrs):
    """
    Consolidates the Fuel Transition Forecast Card components for a multi-sector system.
    Returns: (Figure, HTML_Banner, Math_Markdown)
    """
    
    if df_demand.empty:
        df_demand = pd.DataFrame(columns=["Type", "Demand (kg/day)"])
    if df_prod.empty:
        df_prod = pd.DataFrame(columns=["H2 Production Capacity (kg/day)"])

    max_supply = df_prod["H2 Production Capacity (kg/day)"].sum()

    demand_by_type = df_demand.groupby("Type")["Demand (kg/day)"].sum().to_dict()
    
    truck_h2 = demand_by_type.get("truck", 0)
    az_h2 = demand_by_type.get("amazon", 0)
    wm_h2 = demand_by_type.get("walmart", 0)
    hd_h2 = demand_by_type.get("warehouse", 0)

    # Dynamically Calculate 100% Theoretical Diesel Baseline
    # Formula: Current H2 Demand / (Current Conversion % / 100)
    truck_max = (truck_h2 / (fleet_conv / 100.0)) if fleet_conv > 0 else 0
    az_max = (az_h2 / (az_conv / 100.0)) if az_conv > 0 else 0
    wm_max = (wm_h2 / (wm_conv / 100.0)) if wm_conv > 0 else 0
    hd_max = (hd_h2 / (hd_conv / 100.0)) if hd_conv > 0 else 0

    max_theoretical_demand = constants.GA_DAILY_DIESEL_CONSUMPTION_KG
    mass_ratio = constants.H2_TO_DIESEL_MASS_RATIO
        
    current_year = datetime.now().year
    records = []

    # Multi-Sector Transition Forecast
    for i in range(forecast_yrs + 1):
        target_year = current_year + i
                
        # Apply the annual technology penetration rate to grow all sectors
        truck_c = min(100.0, fleet_conv + (tech_pen * i))
        az_c = min(100.0, az_conv + (tech_pen * i))
        wm_c = min(100.0, wm_conv + (tech_pen * i))
        hd_c = min(100.0, hd_conv + (tech_pen * i))
        
        # Calculate new H2 demand per sector for the current year
        h2_demand_truck = truck_max * (truck_c / 100.0)
        h2_demand_az = az_max * (az_c / 100.0)
        h2_demand_wm = wm_max * (wm_c / 100.0)
        h2_demand_hd = hd_max * (hd_c / 100.0)
        
        total_h2_demand = h2_demand_truck + h2_demand_az + h2_demand_wm + h2_demand_hd
        
        # Remaining Diesel is the combined theoretical ceiling minus total H2 deployed
        displaced_fossil = total_h2_demand * mass_ratio
        remaining_fossil = max(0, max_theoretical_demand - displaced_fossil)
        
        # Calculate the true weighted average conversion of the entire state network
        total_conversion = (displaced_fossil / max_theoretical_demand * 100.0) if max_theoretical_demand > 0 else 100.0
        
        records.append({
            "Year": target_year,
            "Conversion (%)": min(100.0, total_conversion),
            "Imported Diesel": remaining_fossil,
            "Hydrogen Demand": total_h2_demand,
            "Local H2 Capacity": max_supply
        })

    df_forecast = pd.DataFrame(records)

    # Generate Figure
    fig_forecast = px.area(df_forecast, x="Year", y=["Hydrogen Demand", "Imported Diesel"],
                  color_discrete_map={"Imported Diesel": "#6c757d", "Hydrogen Demand": "#007bff"},
                  template="plotly_white", labels={"variable": ""})
    
    fig_forecast.add_scatter(x=df_forecast["Year"], y=df_forecast["Local H2 Capacity"],
                    mode="lines", line=dict(dash="dash", color="#28a745", width=3),
                    name="Local H2 Capacity")
    
    fig_forecast.update_layout(margin=dict(t=40, b=0, l=0, r=0), yaxis_title="Fuel Mass (kg/day)",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig_forecast.update_xaxes(range=[current_year, current_year + forecast_yrs], tickformat="d")

    # Capacity Breach Detection
    deficit_df = df_forecast[df_forecast["Hydrogen Demand"] > df_forecast["Local H2 Capacity"]]
    limit_text = " Local supply is sufficient for the entire forecast window."
    
    if not deficit_df.empty:
        limit_year = int(deficit_df.iloc[0]["Year"])
        fig_forecast.add_vline(
            x=limit_year, line_dash="solid", line_color="#dc3545", 
            annotation_text="Network Capacity Exceeded", annotation_position="bottom right"
        )
        limit_text = f" Local supply limit will be breached in {limit_year}."

    zero_emission_df = df_forecast[df_forecast["Imported Diesel"] <= 0]
    if not zero_emission_df.empty:
        zero_year = int(zero_emission_df.iloc[0]["Year"])
        fig_forecast.add_vline(
            x=zero_year, 
            line_dash="solid", 
            line_color="#28a745",
            annotation_text="100% Phase-out Reached", 
            annotation_position="top left"
        )

    # Math Equations
    math_fuel = textwrap.dedent(f"""
    **Multi-Sector Transition Model:**
    
    $$F_{{rem}}(t) = D_{{max}} - (H_2(t) \\cdot R_{{eq}})$$
    
    $$Limit: H_2(t) \\le S_{{max}}$$

    * $D_{{max}}$: Base Diesel Demand ({max_theoretical_demand:,.0f} kg)
    * $H_2(t)$: Network Hydrogen Deployed
    * $R_{{eq}}$: Energy/Mass Equivalence Ratio ({mass_ratio}:1)
    * $S_{{max}}$: Local H2 Capacity ({max_supply:,.0f} kg)
    """)

    # Summary Banner
    final_year_rem = df_forecast.iloc[-1]["Imported Diesel"]
    final_conv = df_forecast.iloc[-1]["Conversion (%)"]
    is_breached = not deficit_df.empty

    if final_conv >= 100:
        alert_class = "alert alert-success p-2 mt-2 fs-6"
        status_header = "Zero Imported iesel: "
        status_body = f"100% network conversion reached within the {forecast_yrs}-year window."
    else:
        alert_class = "alert alert-info p-2 mt-2 fs-6"
        status_header = "Partial Reduction: "
        status_body = f"Network conversion reaches {final_conv:.0f}% in {forecast_yrs} years. Diesel drops to {final_year_rem:,.0f} kg/day."

    forecast_html = html.Div([
        html.Span(status_header, className="fw-bold text-light"),
        status_body,
        html.Span(limit_text, className="fw-bold text-warning" if is_breached else "fw-bold text-success")
    ], className=alert_class)

    return fig_forecast, forecast_html, math_fuel

def build_roi_card(summary, forecast_years):
    """Returns (Figure, HTML_Content, Math_Markdown) for Cumulative Cashflow."""
    current_year = datetime.now().year
    total_cap = summary.get("capex_term", 0)
    total_rev = summary.get("total_revenue", 0)
    total_op = summary.get("opex_term", 0) + summary.get("transport_term", 0)
    yearly_net = total_rev - total_op

    roi_records = [{"Year": current_year + i, "Cumulative Cash Flow ($)": -total_cap + (yearly_net * i)} 
                   for i in range(forecast_years + 1)]
    
    df_roi = pd.DataFrame(roi_records)
    fig_roi = px.line(df_roi, x="Year", y="Cumulative Cash Flow ($)", template="plotly_white", markers=True)
    fig_roi.add_hline(y=0, line_dash="dash", line_color="#dc3545", annotation_text="Break-Even")
    fig_roi.update_layout(margin=dict(t=30, b=0, l=0, r=0))
    fig_roi.update_traces(line=dict(color="#28a745", width=3))

    # Break-Even Logic
    be_df = df_roi[df_roi["Cumulative Cash Flow ($)"] >= 0]
    if not be_df.empty and yearly_net > 0:
        status = html.H6(f"Estimated Break-Even: {be_df.iloc[0]['Year']}", className="fw-bold text-success m-0")
    else:
        status = html.H6("No Break-Even in forecast window.", className="fw-bold text-warning m-0")

    roi_html = html.Div([
        html.Div([
            html.H6(f"Initial CapEx: {format_currency_compact(total_cap)}", className="fw-bold text-danger mb-1"),
            html.H6(f"Annual Net: {format_currency_compact(yearly_net)} / yr", className="fw-bold text-primary mb-2"),
        ], className="border-bottom pb-2 mb-2"),
        status
    ])

    math_roi = f"""
    **Cash Flow Model:**
    $$C(t) = -K + t(R - O)$$
    * $K$: Initial CapEx ({format_currency_compact(total_cap)})
    * $R$: Annual Revenue ({format_currency_compact(total_rev)})
    * $O$: Annual OpEx ({format_currency_compact(total_op)})
    """
    
    return fig_roi, roi_html, math_roi

def get_cost_analysis(df_prod, df_demand, df_ship2, h2_price, graphene_price, graphene_percent):
    mixed_cost_columns = {
        "Proportional Capital Cost",
        "Proportional Operating Cost",
        "Constant Capital Cost",
        "Constant Operating Cost",
    }
    use_mixed_economics = mixed_cost_columns.issubset(df_prod.columns)

    if use_mixed_economics:
        economics = summarize_mixed_solution_economics(
            df_prod,
            df_demand,
            df_ship2,
            h2_price,
            graphene_price,
            graphene_percent,
        )
    else:
        economics = summarize_solution_economics(
            df_prod,
            df_demand,
            df_ship2,
            h2_price,
            graphene_price,
            graphene_percent,
        )

    return {
        "revenue": {
            "hydrogen": {
                key: value
                for key, value in economics["revenue"].items()
                if key != "graphene"
            },
            "graphene": economics["revenue"].get("graphene", {}),
        },
        "capital_cost": economics["capital_cost"],
        "operating_cost": economics["operating_cost"],
    }

def build_revenue_card(df_prod, df_demand, df_ship2, summary, h2_p, graph_p, graph_pct):
    """Returns (Figure, HTML_Content) for Revenue Generation."""
    cost_data = get_cost_analysis(df_prod, df_demand, df_ship2, h2_p, graph_p, graph_pct)
    
    total_rev = summary.get("total_revenue", 0)
    total_profit = summary.get("total_profit", 0)

    rev_records = []
    for product in ["hydrogen", "graphene"]:
        for item, amount in cost_data["revenue"].get(product, {}).items():
            if amount > 0:
                rev_records.append({"Product": product.title(), "Component": item.title(), "Amount ($)": amount})

    df_rev = pd.DataFrame(rev_records)
    fig_rev = px.bar(
        df_rev, x="Component", y="Amount ($)", color="Component", 
        template="plotly_white", barmode="stack",
        color_discrete_map=COLOR_DISCRETE_MAP
    )
    fig_rev.update_layout(margin=dict(t=20, b=0, l=0, r=0), xaxis_title=None, showlegend=False)

    revenue_html = html.Div([
        html.Div([
            html.H6(f"Total Revenue: {format_currency_compact(total_rev)} / yr", className="fw-bold text-success mb-2"),
            html.H6(f"First Year Net Profit: {format_currency_compact(total_profit)}", className="fw-bold text-primary mb-2"),
        ], className="border-bottom pb-2 mb-2"),
        dict_to_html("Revenue Breakdown", cost_data["revenue"], is_currency=True)
    ])
    
    return fig_rev, revenue_html

def build_expense_card(df_prod, df_demand, df_ship2, summary, h2_p, graph_p, graph_pct):
    """Returns (Figure, HTML_Content) for System Expenses."""
    cost_data = get_cost_analysis(df_prod, df_demand, df_ship2, h2_p, graph_p, graph_pct)
    
    total_cap = summary.get("capex_term", 0)
    total_op = summary.get("opex_term", 0) + summary.get("transport_term", 0)

    cost_records = []
    for category, values in cost_data.items():
        if category == "revenue": 
            continue
        if isinstance(values, dict):
            for item, amount in values.items():
                if isinstance(amount, dict):
                    for sub_item, sub_amount in amount.items():
                        if sub_amount > 0:
                            cost_records.append({"Component": sub_item.title(), "Amount ($)": sub_amount})
                elif amount > 0:
                    cost_records.append({"Component": item.title(), "Amount ($)": amount})

    df_expenses = pd.DataFrame(cost_records)
    fig_expense = px.bar(
        df_expenses, x="Component", y="Amount ($)", color="Component",
        template="plotly_white", barmode="stack",
        color_discrete_map=COLOR_DISCRETE_MAP
    )
    fig_expense.update_layout(margin=dict(t=20, b=0, l=0, r=0), xaxis_title=None, showlegend=False)

    total_demand = df_demand["Demand (kg/day)"].sum() if not df_demand.empty else 0
    unit_opex = (total_op / (total_demand * 365)) if total_demand > 0 else 0

    expense_html = html.Div([
        html.Div([
            html.H6(f"Total CapEx: {format_currency_compact(total_cap)}", className="fw-bold text-danger mb-1"),
            html.H6(f"Total OpEx: {format_currency_compact(total_op)} / yr", className="fw-bold text-warning mb-2"),
            html.H6(f"Unit OpEx: ${unit_opex:,.2f} / kg", className="fw-bold text-info mb-2"),
        ], className="border-bottom pb-2 mb-2"),
        dict_to_html("Capital Cost Breakdown", cost_data["capital_cost"], is_currency=True),
        dict_to_html("Operating Cost Breakdown", cost_data["operating_cost"], is_currency=True)
    ])
    
    return fig_expense, expense_html

