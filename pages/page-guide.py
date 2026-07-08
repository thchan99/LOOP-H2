import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/', name="About & Guide", order=4)

# --- GitHub & Resource Links ---
resource_links = dbc.Card([
    dbc.CardBody([
        html.H5([html.I(className="fa-brands fa-github me-2"), "Source Code & Repository"], className="card-title fw-bold text-dark mb-3"),
        html.P("The underlying MILP optimization model, Dash application framework, and documentation are available on GitHub.", className="text-muted small"),
        dbc.Button([html.I(className="fa-brands fa-github me-2"), "View on GitHub"], 
                   href="https://github.com/thchan99/LOOP-H2",
                   target="_blank", 
                   color="dark", 
                   className="w-100 mb-2 shadow-sm"),
        html.Hr(),
        html.P("Developed by the Aerospace Systems Design Laboratory 2025-26 System of Systems Grand Challenge Team.", className="text-muted small text-center mb-0")
    ])
], className="shadow-sm border-0 h-100 custom-card")

# --- Project Abstract ---
project_abstract = dbc.Card([
    dbc.CardBody([
        html.H5([html.I(className="fa-solid fa-rocket me-2"), "Project Abstract"], className="card-title fw-bold text-primary mb-3"),
        dcc.Markdown("""
        Georgia's reliance on imported conventional gasoline and diesel fuels creates a significant economic risk within its logistical and transportation networks. To stay globally competitive and secure regional economic security, a paradigm shift is required towards localized, sustainable energy generation. Supported by the Georgia Department of Economic Development's Center for Innovation, the Localized Optimization Platform for Hydrogen (LOOP-H2) presents a parametric decision-making tool designed to identify the optimal locations and investments required for new hydrogen infrastructure in Georgia.
 
        The LOOP-H2 model evaluates a supply-demand balance, considering multiple technologies as potential hydrogen production drivers, including Levidian Loop technology, Hydrofleet, and Plug Power, against localized demand from industrial truck fleets and warehouse forklifts. An optimization engine drives the model to minimize cost, containing a comprehensive database mapping landfills, distribution centers, Average Annual Daily Traffic (AADT) flows, and major truck stops such as RaceTrac and state-owned fuel centers.
 
        Stakeholders interact with the model through an interactive dashboard, allowing rapid trade studies depending on the user's priorities. This dashboard displays the optimized network of hydrogen production locations for development as well as key economic information, including revenue, capital expenses, O&M expenses, and return on investment. Results show that while localized hydrogen production is economically viable, physical network capacities limit transition speeds. To demonstrate this, a baseline scenario was created with an initial 3.5% truck fleet conversion and a 1% annual growth rate. This scenario achieves financial viability but outpaces local hydrogen supply limits by 2030 without additional network investment. Ultimately, LOOP-H2 provides the necessary framework to make informed decisions on the future of a hydrogen-based infrastructure in Georgia.
        """, className="text-muted")
    ])
], className="shadow-sm border-0 h-100 custom-card")


# --- Comprehensive User Guide (Accordion) ---
user_guide = dbc.Accordion([
    dbc.AccordionItem([
        dcc.Markdown("""
        The **Dashboard** is the primary interface for running the optimization engine (MILP solver). 
        
        1. **Set Parameters:** Adjust the input cards on the top row (Hydrogen Demand, Production Options, Trade-off Weights, and Economic Inputs).
        2. **Run Optimization:** Click the green `Generate Optimization Results` button. The system will compile your constraints and solve for the most cost-effective hydrogen supply chain.
        3. **Analyze Results:** Scroll down to view the capacity breach forecasts, cumulative cash flow, and a map of the finalized network routes.
        4. **Scenario Manager (Optional):** After running, you can save your specific configuration to your local cache using the Scenario Manager. You can also load past scenarios here to instantly repopulate the inputs and visualizations.
        """)
    ], title="1. Dashboard & Running Optimizations", item_id="guide-dash"),
    
    dbc.AccordionItem([
        dcc.Markdown("""
        The **Trade Studies** page allows for rapid, side-by-side comparisons of different infrastructural strategies focusing on Key Performance Indicators.
        
        1. **Ensure Cached Data:** You must first generate and `Save` at least two distinct scenarios on the main Dashboard page.
        2. **Select Scenarios:** Choose a Baseline (Scenario A) and an Experiment (Scenario B) from the dropdown menus.
        3. **Review Deltas:** The page will instantly load the map routing for both networks and calculate the mathematical differences (Deltas) between key performance indicators, such as CapEx, OpEx, and Payback Period.
        """)
    ], title="2. Trade Studies Explorer", item_id="guide-trade"),
    
    dbc.AccordionItem([
        dcc.Markdown("""
        The **Model Constants** page provides deep, system-level access to the variables that govern the physics, thermodynamics, and base economics of the simulation.
        
        * **Editing:** You can modify generation potentials (e.g., LFG Decay Constants), specific energy costs, and fixed site CapEx.
        * **Warning:** Clicking `Save and Overwrite` physically rewrites the underlying Python configuration files. The entire optimization engine will recompile using these new absolute truths. 
        * **Restoring:** If the model becomes unstable or economically unviable, click `Restore Defaults` to revert the system to its original state.
        """)
    ], title="3. Managing Global Constants", item_id="guide-constants"),
    
    dbc.AccordionItem([
        dcc.Markdown("""
        If the dashboard returns an error alert or the map fails to generate lines:
        
        * **Infeasible Solution:** The solver may fail if your constraints contradict each other (e.g., setting demand extremely high while disabling all production facilities). 
        * **Missing Data:** Ensure you haven't entered `0` or left an input completely blank on the Constants page, which can cause division-by-zero errors in the economic calculations.
        * **Refresh Cache:** If Trade Studies act erratically, go to the Dashboard and click `Clear All` in the Scenario Manager to flush your browser's local storage.
        """)
    ], title="4. Troubleshooting & Infeasible Models", item_id="guide-troubleshoot"),
], always_open=True, className="shadow-sm")


# --- Main Layout ---
layout = dbc.Container([
    # Page Header
    dbc.Row([
        html.Div([
            html.H2("About & User Guide", className="text-dark fw-bold"),
            html.P("Documentation, repository links, and instructions for operating the LOOP H2 simulation environment.", className="text-muted"),
        ], className="mb-4 mt-3 border-bottom pb-2")
    ]),
    
    dbc.Row([
        dbc.Col(project_abstract, xs=12, lg=12, className="mb-4"),
        #dbc.Col(resource_links, xs=12, lg=4, className="mb-4"),
    ]),
    
    dbc.Row([
        dbc.Col([
            html.H4([html.I(className="fa-solid fa-book-open-reader me-2"), "Comprehensive User Guide"], className="fw-bold text-dark mb-3"),
            user_guide
        ], width=12)
    ], className="mb-5")

], fluid=True)