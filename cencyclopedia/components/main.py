import dash_bootstrap_components as dbc

from typing import Any
from dash import html, dcc
from cencyclopedia.io.data import Data
from cencyclopedia.plot.tree import create_tree_legend_figure


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


def data_summary(labels: list[str]) -> html.Div:
    return html.Div(
        [
            dbc.Tabs(
                [dbc.Tab(label=label, tab_id=label) for label in labels],
                id="data-label-tabs",
                active_tab=labels[0],
            ),
            html.Br(),
            html.Div(id="data-labels-output"),
        ]
    )


def main_content(
    fig_clade: dcc.Graph,
    fig_clade_legend: dcc.Graph,
    dropdown: dcc.Dropdown,
    dataview: html.Div,
):
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            fig_clade,
                            dbc.Popover(
                                [fig_clade_legend],
                                id="popup-fig-cens-clade-ordered-legend",
                                target="fig-cens-clade-ordered",
                                body=True,
                                hide_arrow=True,
                                trigger="click",
                            ),
                        ],
                        style={"height": "200vh", "width": "50%"},
                    ),
                    dbc.Col(
                        [
                            html.H3("Contig"),
                            html.Hr(),
                            dropdown,
                            html.Br(),
                            dcc.Graph(id="fig-selected-cen", responsive=True),
                            html.Br(),
                            dataview,
                        ],
                        style={"height": "50vh", "width": "50%"},
                    ),
                ],
            )
        ],
    )


def main_page(regions: str, chrom_names: list[str], cfg: dict[str, Any]):
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
    data = Data.new(cfg["data"])
    datatypes = list(data.labels)
    content = main_content(
        fig_clade=dcc.Graph(id="fig-cens-clade-ordered", responsive=True),
        fig_clade_legend=create_tree_legend_figure(cfg),
        dropdown=dcc.Dropdown(
            [],
            value=None,
            searchable=True,
            id="dropdown-selected-cen",
        ),
        dataview=data_summary(datatypes),
    )
    return html.Div(
        [
            dcc.Store(id="regions", data=regions),
            dcc.Store(id="cfg", data=cfg),
            dcc.Store(id="datatypes", data=datatypes),
            dcc.Store(id="selected-cen", data=None),
            dcc.Store(id="expand-tracks", data={}),
            dcc.Location(id="url", refresh=False),
            dbc.Row(
                [
                    dbc.Col(sidebar, width=2),
                    dbc.Col(content, width=10, id="main-content"),
                ],
                style=CONTENT_STYLE,
            ),
        ]
    )
