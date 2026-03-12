import dash_bootstrap_components as dbc

from typing import Any
from dash import html, dcc
from cencyclopedia.io.data import Data
from cencyclopedia.plot.tree import create_tree_legend_figure
from cencyclopedia.plot.common import default_bed_track_settings


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


def dataview_selected_cen(labels: list[str]) -> html.Div:
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


def rangeslider_selected_cen(
    dropdown: dcc.Dropdown, min: int, max: int, value: list[int]
) -> html.Div:
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [dbc.Label("Contig"), dropdown],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Position"),
                            dcc.RangeSlider(
                                min=min,
                                max=max,
                                value=value,
                                allowCross=False,
                                id="rng-itv-selected_cens",
                            ),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            html.Br(),
                            dbc.Button(
                                "Reset", id="btn-reset-itv-selected-cen", color="danger"
                            ),
                        ],
                        width=2,
                    ),
                ]
            )
        ]
    )


def main_content(
    fig_tree: dcc.Graph,
    fig_tree_legend: dcc.Graph,
    rangeslider_selected_cen: html.Div,
    dataview_selected_cen: html.Div,
):
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H3("Tree"),
                            html.Hr(),
                            fig_tree,
                            dbc.Popover(
                                [fig_tree_legend],
                                id="popup-fig-cens-tree-legend",
                                target="fig-cens-tree",
                                body=True,
                                hide_arrow=True,
                                trigger="hover",
                            ),
                        ],
                        style={"height": "150vh", "width": "50%"},
                    ),
                    dbc.Col(
                        [
                            html.H3("Tracks"),
                            html.Hr(),
                            rangeslider_selected_cen,
                            html.Br(),
                            dcc.Graph(
                                id="fig-selected-cen",
                                responsive=True,
                                config={"displaylogo": False},
                            ),
                            html.Br(),
                            dataview_selected_cen,
                        ],
                        style={"height": "50vh", "width": "50%"},
                    ),
                ],
            )
        ],
    )


def main_page(
    regions: str,
    chrom_names: list[str],
    cfg: dict[str, Any],
):
    sidebar = html.Div(
        [
            html.H2("Cencyclopedia", className="display-7"),
            html.Hr(),
            dbc.Nav(
                [
                    dbc.NavLink("Home", href="/", active="exact"),
                    dbc.NavLink("Cite", href="/cite", active="exact"),
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
        fig_tree=dcc.Graph(id="fig-cens-tree", responsive=True),
        fig_tree_legend=create_tree_legend_figure(),
        rangeslider_selected_cen=rangeslider_selected_cen(
            min=0,
            max=0,
            value=[0, 0],
            dropdown=dcc.Dropdown(
                [],
                value=None,
                searchable=True,
                id="dropdown-selected-cen",
            ),
        ),
        dataview_selected_cen=dataview_selected_cen(datatypes),
    )
    return html.Div(
        [
            # Regions
            dcc.Store(id="regions", data=regions),
            # Configuration dictionary (yaml file)
            dcc.Store(id="cfg", data=cfg),
            # Datatypes provided
            dcc.Store(id="datatypes", data=datatypes),
            # Interval for selected centromere
            dcc.Store(id="itv-selected-cen", data=None),
            # Individual track settings
            dcc.Store(
                id="bed-track-settings",
                data={dtype: default_bed_track_settings() for dtype in datatypes},
            ),
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
