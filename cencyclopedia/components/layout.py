from dash import html, dcc
import dash_bootstrap_components as dbc


SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "overflow": "scroll",
    # Hide scrollbar
    "scrollbar-width": "none",
    "background-color": "#f8f9fa",
}
CONTENT_STYLE = {
    "padding": "2rem 1rem",
}


def create_content_layout(
    fig_clade: dcc.Graph, dropdown: dcc.Dropdown, selected_cen: str | None
):
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [fig_clade],
                        style={"height": "200vh", "width": "50%"},
                    ),
                    dbc.Col(
                        [
                            # There's probably a better way to organize this.
                            dropdown,
                            html.Hr(),
                            dcc.Store(id="selected-cen", data=selected_cen),
                            dcc.Graph(id="fig-selected-cen", responsive=False),
                            html.Img(id="fig-selected-cen-mdp"),
                        ],
                        style={"width": "50%"},
                    ),
                ],
            )
        ],
    )


def layout(chrom_names: list[str]):
    sidebar = html.Div(
        [
            html.H2("Cencyclopedia", className="display-7"),
            html.Hr(),
            dbc.Nav(
                [
                    dbc.NavLink("Home", href="/", active="exact"),
                    html.Hr(),
                    *[
                        dbc.NavLink(chrom, href=f"/{chrom}", active="exact")
                        for chrom in chrom_names
                    ],
                ],
                vertical=True,
                pills=True,
            ),
        ],
        style=SIDEBAR_STYLE,
    )
    content = create_content_layout(
        fig_clade=dcc.Graph(id="fig-cens-clade-ordered", responsive=True),
        dropdown=dcc.Dropdown(
            [],
            value=None,
            searchable=True,
            id="dropdown-selected-cen",
        ),
        selected_cen=None,
    )
    return html.Div(
        [
            dcc.Location(id="url", refresh=False),
            dbc.Row(
                [
                    dbc.Col(sidebar, width=2),
                    dbc.Col(content, width=10, id="col-chrom-content"),
                ],
                style=CONTENT_STYLE,
            ),
        ]
    )
