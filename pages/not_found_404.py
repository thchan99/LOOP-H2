import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__)

layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H1("404", className="display-1 fw-bold text-primary mb-3"),
                html.H3("Page Not Found", className="text-dark fw-bold mb-4"),
                
                html.P(
                    "The infrastructure scenario or dashboard path you are looking for does not exist or has been moved.", 
                    className="text-muted mb-5 fs-5"
                ),
                
                dbc.Button(
                    [html.I(className="fa-solid fa-house me-2"), "Return to Home"], 
                    href="/",
                    color="primary", 
                    size="lg", 
                    className="shadow-sm rounded-pill px-4"
                )
            ], className="text-center p-5 bg-white shadow rounded-3 border")
        ], md=8, lg=6, className="mx-auto mt-5")
    ], className="align-items-center min-vh-75")
], fluid=True, className="mb-5")