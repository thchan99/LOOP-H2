import dash
from dash import html, Input, Output, State, callback, ctx
import dash_bootstrap_components as dbc
import re
import importlib
import shutil
import os

import config.constants as constants

dash.register_page(__name__, path='/constants', name="Model Constants", order=3)

CONSTANT_GROUPS = {
    "Economic & Optimization Tuning": [
        {"id": "GA_DAILY_DIESEL_CONSUMPTION_KG", "label": "GA Daily Diesel Imports (kg/day)", "val": getattr(constants, "GA_DAILY_DIESEL_CONSUMPTION_KG", 11495307.0), "step": 10000},
        {"id": "H2_TO_DIESEL_MASS_RATIO", "label": "H2:Diesel Mass Displacement Ratio", "val": getattr(constants, "H2_TO_DIESEL_MASS_RATIO", 5.0), "step": 0.1},
        {"id": "PRICE_ELECTRICITY_PER_KWH_DEFAULT", "label": "Electricity Price ($/kWh)", "val": getattr(constants, "PRICE_ELECTRICITY_PER_KWH_DEFAULT", 0.1), "step": 0.01},
        {"id": "CAPACITY_FACTOR_DEFAULT", "label": "Capacity Factor", "val": getattr(constants, "CAPACITY_FACTOR_DEFAULT", 0.9), "step": 0.05},
        {"id": "TRANSPORT_COST_PER_KG_KM_DEFAULT", "label": "Transport Cost ($ per kg/km)", "val": getattr(constants, "TRANSPORT_COST_PER_KG_KM_DEFAULT", 0.02), "step": 0.01},
        {"id": "TRANSPORT_BOOST", "label": "Transport Boost Multiplier", "val": getattr(constants, "TRANSPORT_BOOST", 75.0), "step": 1},
        {"id": "WATER_BOOST", "label": "Water Boost Multiplier", "val": getattr(constants, "WATER_BOOST", 10.0), "step": 1},
    ],
    "LFG Generation Model": [
        {"id": "DECAY_CONST_K", "label": "Decay Constant (k)", "val": getattr(constants, "DECAY_CONST_K", 0.017329), "step": 0.0001},
        {"id": "L0_CONSTANT", "label": "Methane Gen Potential (L0)", "val": getattr(constants, "L0_CONSTANT", 3855.406), "step": 1},
        {"id": "DEFAULT_METHANE_PERCENT", "label": "Default Methane (%)", "val": getattr(constants, "DEFAULT_METHANE_PERCENT", 50), "step": 1},
    ],
    "BCS & Well Cost Defaults": [
        {"id": "AVG_WASTE_DEPTH_FT", "label": "Avg Waste Depth (ft)", "val": getattr(constants, "AVG_WASTE_DEPTH_FT", 65), "step": 1},
        {"id": "NUM_WELLS_PER_MMSCFD", "label": "Wells per MMscfd", "val": getattr(constants, "NUM_WELLS_PER_MMSCFD", 47.913), "step": 0.1},
        {"id": "DRILL_CAPEX_PER_FT", "label": "Drilling CapEx ($/ft)", "val": getattr(constants, "DRILL_CAPEX_PER_FT", 85), "step": 1},
        {"id": "GATHERING_CAPEX_PER_WELL", "label": "Gathering CapEx ($/well)", "val": getattr(constants, "GATHERING_CAPEX_PER_WELL", 17000), "step": 100},
        {"id": "SURVEYING_CAPEX_PER_WELL", "label": "Surveying CapEx ($/well)", "val": getattr(constants, "SURVEYING_CAPEX_PER_WELL", 700), "step": 10},
        {"id": "DRILLING_COST_TOTAL_DEFAULT", "label": "Total Drilling Fixed Cost ($)", "val": getattr(constants, "DRILLING_COST_TOTAL_DEFAULT", 20000), "step": 1000},
    ],
    "Flare & Operating Defaults": [
        {"id": "FLARE_CAPEX_CONST", "label": "Flare Fixed CapEx ($)", "val": getattr(constants, "FLARE_CAPEX_CONST", 13700), "step": 100},
        {"id": "FLARE_CAPEX_PROP_PER_KG_DAY", "label": "Flare Prop CapEx ($ per kg/day)", "val": getattr(constants, "FLARE_CAPEX_PROP_PER_KG_DAY", 112), "step": 1},
        {"id": "OPEX_COST_CONST_DEFAULT", "label": "Fixed O&M per Year ($)", "val": getattr(constants, "OPEX_COST_CONST_DEFAULT", 5100), "step": 100},
        {"id": "OPEX_COST_PER_WELL_PER_YEAR", "label": "OpEx per Well/Year ($)", "val": getattr(constants, "OPEX_COST_PER_WELL_PER_YEAR", 2600), "step": 100},
        {"id": "BCS_ELECTRICITY_RATE_KWH_PER_FT3", "label": "BCS Elec. Rate (kWh/ft3)", "val": getattr(constants, "BCS_ELECTRICITY_RATE_KWH_PER_FT3", 0.002), "step": 0.001},
    ],    
    "Levidian Empirical Defaults": [
        {"id": "INPUT_FLOW_M3_PER_HR", "label": "Input Flow (m3/hr)", "val": getattr(constants, "INPUT_FLOW_M3_PER_HR", 10.0), "step": 0.1},
        {"id": "OUTPUT_FLOW_KG_PER_HR", "label": "Output Flow H2 (kg/hr)", "val": getattr(constants, "OUTPUT_FLOW_KG_PER_HR", 2.0), "step": 0.1},
        {"id": "GRAPHENE_PROP_DEFAULT", "label": "Graphene per H2 (kg/kg)", "val": getattr(constants, "GRAPHENE_PROP_DEFAULT", 1.0), "step": 0.1},
        {"id": "LEV_H2_PROD_RATE_PER_HR_DEFAULT", "label": "H2 Prod Rate per Unit (kg/hr)", "val": getattr(constants, "LEV_H2_PROD_RATE_PER_HR_DEFAULT", 2), "step": 1},
        {"id": "LEV_ELECTRICITY_RATE_KWH_PER_HR_DEFAULT", "label": "Electricity Rate (kWh/hr)", "val": getattr(constants, "LEV_ELECTRICITY_RATE_KWH_PER_HR_DEFAULT", 90), "step": 1},
        {"id": "LEVIDIAN_PURCHASE_COST", "label": "Purchase Cost ($)", "val": getattr(constants, "LEVIDIAN_PURCHASE_COST", 5000000), "step": 10000},
        {"id": "LEVIDIAN_LEASE_COST_PER_MONTH", "label": "Lease Cost ($/month)", "val": getattr(constants, "LEVIDIAN_LEASE_COST_PER_MONTH", 10000), "step": 1000},
    ],
    "Hydrofleet Defaults": [
        {"id": "HYDROFLEET_H2_PROD_CAPACITY_KG_DAY", "label": "Max Prod Capacity (kg/day)", "val": getattr(constants, "HYDROFLEET_H2_PROD_CAPACITY_KG_DAY", 60000), "step": 1000},
        {"id": "HYDROFLEET_CAPITAL_COST_PROP", "label": "Prop CapEx ($ per kg/day)", "val": getattr(constants, "HYDROFLEET_CAPITAL_COST_PROP", 27500), "step": 100},
        {"id": "HYDROFLEET_CAPITAL_COST_CONST", "label": "Fixed CapEx ($)", "val": getattr(constants, "HYDROFLEET_CAPITAL_COST_CONST", 275000000), "step": 100000},
        {"id": "HYDROFLEET_OPEX_COST_PROP", "label": "Prop OpEx ($ per kg/day)", "val": getattr(constants, "HYDROFLEET_OPEX_COST_PROP", 0.0), "step": 1},
        {"id": "HYDROFLEET_OPEX_COST_CONST", "label": "Fixed OpEx ($/year)", "val": getattr(constants, "HYDROFLEET_OPEX_COST_CONST", 0.0), "step": 1000},
    ],
    "Plug Power Site Constraints": [
        {"id": "EXIST_PROD_PLUG_LAT", "label": "Latitude", "val": getattr(constants, "EXIST_PROD_PLUG_LAT", 30.8418), "step": 0.0001},
        {"id": "EXIST_PROD_PLUG_LON", "label": "Longitude", "val": getattr(constants, "EXIST_PROD_PLUG_LON", -81.6789), "step": 0.0001},
        {"id": "EXIST_PROD_PLUG_CAPACITY_KG_DAY", "label": "Capacity (kg/day)", "val": getattr(constants, "EXIST_PROD_PLUG_CAPACITY_KG_DAY", 15000), "step": 100},
        {"id": "EXIST_PROD_PLUG_CAPITAL_COST_CONST", "label": "Fixed CapEx ($)", "val": getattr(constants, "EXIST_PROD_PLUG_CAPITAL_COST_CONST", 0.0), "step": 1000},
        {"id": "EXIST_PROD_PLUG_OPEX_COST_CONST", "label": "Fixed OpEx ($)", "val": getattr(constants, "EXIST_PROD_PLUG_OPEX_COST_CONST", 0.0), "step": 1000},
        {"id": "EXIST_PROD_PLUG_CAPITAL_COST_PROP", "label": "Prop CapEx ($ per kg/day)", "val": getattr(constants, "EXIST_PROD_PLUG_CAPITAL_COST_PROP", 0.0), "step": 1},
        {"id": "EXIST_PROD_PLUG_OPEX_COST_PROP", "label": "Prop OpEx ($ per kg)", "val": getattr(constants, "EXIST_PROD_PLUG_OPEX_COST_PROP", 15.0), "step": 0.1},
    ],
    "Savannah Site Constraints": [
        {"id": "EXIST_PROD_SAVANNAH_LAT", "label": "Latitude", "val": getattr(constants, "EXIST_PROD_SAVANNAH_LAT", 32.1133), "step": 0.0001},
        {"id": "EXIST_PROD_SAVANNAH_LON", "label": "Longitude", "val": getattr(constants, "EXIST_PROD_SAVANNAH_LON", -81.2771), "step": 0.0001},
        {"id": "EXIST_PROD_SAVANNAH_CAPACITY_KG_DAY", "label": "Capacity (kg/day)", "val": getattr(constants, "EXIST_PROD_SAVANNAH_CAPACITY_KG_DAY", 4200), "step": 100},
        {"id": "EXIST_PROD_SAVANNAH_CAPITAL_COST_CONST", "label": "Fixed CapEx ($)", "val": getattr(constants, "EXIST_PROD_SAVANNAH_CAPITAL_COST_CONST", 0.0), "step": 1000},
        {"id": "EXIST_PROD_SAVANNAH_OPEX_COST_CONST", "label": "Fixed OpEx ($)", "val": getattr(constants, "EXIST_PROD_SAVANNAH_OPEX_COST_CONST", 15.0), "step": 0.1},
        {"id": "EXIST_PROD_SAVANNAH_CAPITAL_COST_PROP", "label": "Prop CapEx ($ per kg/day)", "val": getattr(constants, "EXIST_PROD_SAVANNAH_CAPITAL_COST_PROP", 0.0), "step": 1},
        {"id": "EXIST_PROD_SAVANNAH_OPEX_COST_PROP", "label": "Prop OpEx ($ per kg)", "val": getattr(constants, "EXIST_PROD_SAVANNAH_OPEX_COST_PROP", 15.0), "step": 0.1},
    ],
}

def build_constants_tables():
    layout_elements = []
    for group_name, params in CONSTANT_GROUPS.items():
        layout_elements.append(html.H5(group_name, className="mt-4 mb-2 text-primary fw-bold border-bottom pb-2"))
        
        table_header = [html.Thead(html.Tr([
            html.Th("Parameter Definition", style={"width": "35%"}),
            html.Th("Python Variable Name", style={"width": "25%"}),
            html.Th("Current Value", style={"width": "15%"}),
            html.Th("New Value", style={"width": "25%"})
        ]))]
        
        rows = []
        for p in params:
            rows.append(html.Tr([
                html.Td(p["label"], className="align-middle fw-semibold text-secondary"),
                html.Td(html.Code(p["id"], className="small text-muted bg-light px-2 py-1 rounded"), className="align-middle"),
                html.Td(
                    dbc.Input(id=f"current-{p['id']}", type="number", value=p["val"], disabled=True, size="sm", className="bg-light text-muted border-light"), 
                    className="align-middle"
                ),
                html.Td(dbc.Input(id=f"input-{p['id']}", type="number", value=p["val"], step="any", size="sm", className="shadow-sm border-secondary"), className="align-middle")
            ]))
            
        table_body = [html.Tbody(rows)]
        table = dbc.Table(table_header + table_body, bordered=True, hover=True, striped=True, responsive=True, className="bg-white shadow-sm mb-4 align-middle")
        layout_elements.append(table)
        
    return html.Div(layout_elements)

# Main Layout
layout = dbc.Container([
    # --- FULL SCREEN LOADING OVERLAY ---
    html.Div(
        id="full-screen-loader",
        className="d-none",
        style={
            "position": "fixed", "top": 0, "left": 0, "width": "100vw", "height": "100vh",
            "backgroundColor": "rgba(33, 37, 41, 0.85)",
            "zIndex": 9999, "flexDirection": "column", "justifyContent": "center", "alignItems": "center"
        },
        children=[
            dbc.Spinner(color="light", spinner_style={"width": "4rem", "height": "4rem"}),
            html.H3("Recompiling Engine Configuration...", className="mt-4 text-light fw-bold"),
            html.P("Do not refresh. The page will reload automatically.", className="text-light mt-2")
        ]
    ),
    # -----------------------------------
    dbc.Row([
        html.Div([
            html.H2("Global Constants Manager", className="text-dark fw-bold"),
            html.P("Changes saved here will be immediately reloaded into the optimization engine for the next run.", className="text-muted"),
        ], className="mb-4 mt-3 border-bottom pb-2")
    ]),
    # Warning Banner
    dbc.Row([
        dbc.Col([
            dbc.Alert([
                html.I(className="fa-solid fa-triangle-exclamation me-2 fs-5"),
                html.Strong("WARNING: ", className="p-2"),
                "Modifying these global constants will rewrite the underlying Python configuration files. ",
                "Only adjust these parameters if you fully understand their impact on the MILP solver bounds and the system economics. ",
                "You may restore the default configuration at any time by clicking the button at the bottom of the page."
            ], color="danger", className="shadow-sm mb-4 mt-3 border-2 border-danger d-flex align-items-center")
        ], width=12)
    ]),
    
    dbc.Row([
        dbc.Col(build_constants_tables(), width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Button([html.I(className="fa-solid fa-rotate-left me-2"), "Restore Defaults"], 
                       id="btn-restore-defaults", color="warning", size="lg", className="shadow mt-4 px-4 rounded-pill fw-bold mb-5 me-3"),
            dbc.Button([html.I(className="fa-solid fa-floppy-disk me-2"), "Save and Overwrite"], 
                       id="btn-save-constants", color="danger", size="lg", className="shadow mt-4 px-4 rounded-pill fw-bold mb-5"),
            html.Div(id="constants-alert-container", className="mt-3 mb-5")
        ], width=12, className="text-center")
    ])
], fluid=True)

# Generate Dynamic Output/State Lists
all_param_ids = [p["id"] for group in CONSTANT_GROUPS.values() for p in group]

output_current_boxes = [Output(f"current-{pid}", "value") for pid in all_param_ids]
output_input_boxes = [Output(f"input-{pid}", "value") for pid in all_param_ids]
state_dependencies = [State(f"input-{pid}", "value") for pid in all_param_ids]

@callback(
    Output("constants-alert-container", "children"),
    *output_current_boxes,
    *output_input_boxes,
    Input("btn-save-constants", "n_clicks"),
    Input("btn-restore-defaults", "n_clicks"),
    *state_dependencies,
    running=[
        (
            Output("full-screen-loader", "className"),
            "d-flex flex-column justify-content-center align-items-center", # Active state
            "d-none"                                                        # Inactive state
        )
    ],
    prevent_initial_call=True
)
def manage_constants(save_clicks, restore_clicks, *values):
    triggered_id = ctx.triggered_id
    
    # Calculate the number of NO_UPDATEs needed if an error occurs
    num_params = len(all_param_ids)
    error_fallback = tuple(dash.no_update for _ in range(num_params * 2))

    if triggered_id == "btn-save-constants":
        new_values = dict(zip(all_param_ids, values))
        file_path = "config/constants.py" 
        
        # SAFETY CHECK: Prevent empty fields (None) from corrupting the file
        for key, val in new_values.items():
            if val is None:
                alert = dbc.Alert(f"Error: The field for '{key}' cannot be empty. Please enter a valid number.", color="danger", duration=5000)
                return (alert,) + error_fallback
        
        try:
            with open(file_path, "r") as file:
                file_data = file.read()
                
            for var_name, new_val in new_values.items():
                pattern = rf"^({var_name}\s*=\s*)([0-9]*\.?[0-9]+)"
                file_data = re.sub(pattern, rf"\g<1>{new_val}", file_data, flags=re.MULTILINE)
                
            with open(file_path, "w") as file:
                file.write(file_data)
                
            importlib.reload(constants)
            
            alert = dbc.Alert("Constants successfully overwritten and reloaded into the engine.", color="success", duration=4000)
            
            # Return Alert, then the values for the static boxes, then the values for the input boxes
            vals_list = list(values)
            return (alert,) + tuple(vals_list) + tuple(vals_list)
            
        except Exception as e:
            alert = dbc.Alert(f"Error updating file: {str(e)}", color="danger")
            return (alert,) + error_fallback


    elif triggered_id == "btn-restore-defaults":
        file_path = "config/constants.py"
        default_file_path = "config/constants_default.py"
        
        if not os.path.exists(default_file_path):
            alert = dbc.Alert("Error: 'constants_default.py' file not found in the config directory.", color="danger")
            return (alert,) + error_fallback
            
        try:
            # Physically overwrite the active constants file with the default backup
            shutil.copyfile(default_file_path, file_path)
            
            # Reload the module to update Python's memory
            importlib.reload(constants)
            
            # Fetch the restored values dynamically
            restored_vals = []
            for pid in all_param_ids:
                restored_vals.append(getattr(constants, pid, 0))
                
            alert = dbc.Alert("Constants successfully restored to system defaults.", color="success", duration=4000)
            
            # Push the restored values into both the static boxes and input sliders
            return (alert,) + tuple(restored_vals) + tuple(restored_vals)
            
        except Exception as e:
            alert = dbc.Alert(f"Error restoring defaults: {str(e)}", color="danger")
            return (alert,) + error_fallback

    return (dash.no_update,) + error_fallback