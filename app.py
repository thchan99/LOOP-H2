import dash
from dash import Dash, html, Input, Output, State, callback
import dash_bootstrap_components as dbc

### APP INITIALIZE ###
# bootstrap css formatting
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
external_stylesheets = [
    dbc.themes.FLATLY,
    dbc_css,
    dbc.icons.BOOTSTRAP,
    dbc.icons.FONT_AWESOME,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
]

app = Dash(
    __name__,
    # requests_pathname_prefix='/SGC04_LOOPH2/',
    use_pages=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1.0"}],
    external_stylesheets = external_stylesheets,
)

app.title = "LOOP H2"
app.description = "An interactive dashboard for decision-making tools on Hydrogen Transportation Infrastructure for the State of Georgia."

### APP LAYOUT ###

# Main Navigation Bar
navbar = dbc.Navbar(
    dbc.Container([
        dbc.NavbarBrand(
             "LOOP H2", 
             className="fw-bold fs-3 ms-3", 
             style={"letterSpacing": "2px"}
        ),
        
        dbc.NavbarToggler(id="navbar-toggler", n_clicks=0, className="me-3"),
        
        dbc.Collapse(
            dbc.Nav(
                [
                    dbc.NavItem(dbc.NavLink("User Guide", href="/", className="fw-semibold ms-3")),
                    dbc.NavItem(dbc.NavLink("Dashboard", href="/dashboard", className="fw-semibold ms-3")),
                    dbc.NavItem(dbc.NavLink("Trade Studies", href="/trade-studies", className="fw-semibold ms-3")),
                    dbc.NavItem(dbc.NavLink("Model Constants", href="/constants", className="fw-semibold ms-3")),
                ],
                className="ms-auto me-4",
                navbar=True,
            ),
            id="navbar-collapse",
            is_open=False,
            navbar=True,
        ),
    ], fluid=True),
    color="primary",
    dark=True,
    expand="lg",
    className="mb-4 shadow custom-header py-3"
)
# Callback to toggle the collapse on small screens
@callback(
    Output("navbar-collapse", "is_open"),
    Input("navbar-toggler", "n_clicks"),
    State("navbar-collapse", "is_open"),
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

# Application Shell
app.layout = dbc.Container([
    navbar,
    dash.page_container, # active page layout
    # Footer
    dbc.Row(
        id="footer-row",
        className="mt-auto",
        children=[
            html.Div(
                className="p-4 text-center text-muted",
                children=[
                    html.Small([
                        "Developed by the Aerospace Systems Design Laboratory 2025-26 System of Systems Grand Challenge Team.",
                        html.Br(),
                        "In association with Georgia Institute of Technology & Georgia Department of Economic Development, Center of Innovation."
                    ]),
                ]
            )
        ],
    ),
], 
fluid=True,
className="dbc custom-bg min-vh-100 d-flex flex-column"
)

# Run the app
if __name__ == '__main__':
    app.run(debug=False)
