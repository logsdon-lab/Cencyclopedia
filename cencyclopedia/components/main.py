import dash_bootstrap_components as dbc

from typing import Any
from dash import html, dcc
from cencyclopedia.io.data import Data
from cencyclopedia.components.err_msg import modal_error_message
from cencyclopedia.plot.common import default_bed_track_settings


SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding-top": "2rem",
    "padding-bottom": "2rem",
    "padding-left": "1rem",
    "padding-right": "1rem",
    # Hide scrollbar
    "overflow": "scroll",
    "scrollbar-width": "none",
    "background-color": "#f8f9fa",
}
CONTENT_STYLE = {
    "overflow": "scroll",
    # Hide scrollbar
    "scrollbar-width": "none",
    "padding-top": "2rem",
    "padding-bottom": "2rem",
    "padding-left": "1rem",
    "padding-right": "1rem",
}


def dataview_selected_cen(labels: list[str], active_tab: str | None = None) -> html.Div:
    if not active_tab:
        active_tab = labels[0]
    return html.Div(
        [
            dbc.Tabs(
                [dbc.Tab(label=label, tab_id=label) for label in labels],
                id="data-label-tabs",
                active_tab=active_tab,
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
    cfg: dict[str, Any],
):
    return html.Div(
        [
            modal_error_message(),
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
                                placement="left",
                                trigger="legacy",
                            ),
                        ],
                        width=cfg["general"]["tree"]["width"],
                        style={"height": cfg["general"]["tree"]["height"]},
                    ),
                    dbc.Col(
                        [
                            html.H3("Tracks"),
                            html.Hr(),
                            rangeslider_selected_cen,
                            html.Br(),
                            dbc.Spinner(
                                dcc.Graph(
                                    id="fig-selected-cen",
                                    responsive=True,
                                    config={"displaylogo": False},
                                    style={
                                        "height": cfg["general"]["selected_cen"][
                                            "height"
                                        ],
                                    },
                                )
                            ),
                            html.Br(),
                            dataview_selected_cen,
                        ],
                        width=cfg["general"]["selected_cen"]["width"],
                    ),
                ],
            ),
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
                    dbc.NavLink("Overview", href="/overview", active="exact"),
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
    # Data
    data = Data.new(cfg["data"])
    datatypes = list(data.labels)
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
                    dbc.Col(
                        width=10,
                        id="main-content",
                        style={"padding-left": "8rem", "padding-right": "2rem"},
                    ),
                ],
                style=CONTENT_STYLE,
            ),
        ],
        style={
            "overflow": "scroll",
            # Hide scrollbar
            "scrollbar-width": "none",
        },
    )
