import dash_bootstrap_components as dbc

from typing import Any
from dash import html, dcc
from cencyclopedia.io.data import Data
from cencyclopedia.components.help import row_title_with_help, collapse_help
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
CONTENT_STYLE = {"padding-left": "4rem", "padding-right": "6rem"}
CONTAINER_STYLE = {
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
                            row_title_with_help("Tree", "btn-collapse-howto-tree"),
                            collapse_help(
                                """
                                1. Each centromere haplotype on this figure is clickable.
                                    * Hovering over each centromere displays the contig name, superpopulation, and sex.
                                2. To zoom in, use the **"Zoom"** icon in Plotly's modal bar.
                                3. To move around the image, use the **"Pan"** option.
                                4. To reset the image, click the **"Reset axes"** icon.
                                5. To display the figure legend, click anywhere in the top-most part of the image.
                                """,
                                "collapse-howto-tree",
                            ),
                            html.Br(),
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
                            row_title_with_help(
                                "Tracks", "btn-collapse-howto-selected-cen"
                            ),
                            collapse_help(
                                """
                                ### General
                                1. Select a contig from the dropdown. Contigs are ordered in the same order as the tree.
                                2. There are multiple ways to adjust position in the displayed plot:
                                    1. Adjust the slider. Click the **"Reset"** button to reset to the original coordinates.
                                    2. Zoom in using the **"Zoom"** icon.
                                    3. Drag along the track with **"Pan"** to move to a new position.
                                3. Hover over individual annotations to get a short description.

                                ### Expand
                                To expand BED tracks, use the "Expand Tracks" section. The following modes are possible:
                                * Original
                                    * Default.
                                * Length
                                    * Show the largest annotation at the top.
                                * Frequency
                                    * Show the most frequent annotation at the top.
                                * Coverage
                                    * Show the annotation covering the largest portion of the region.

                                Once set, click **"Update"** to replot.
                                * *"All"* or a set number up to 50 can be drawn at a time.

                                To reset the tracks for a give data type to its default. Click the **"Reset"** button.
                                * This is only done for that data type.
                                """,
                                "collapse-howto-selected-cen",
                            ),
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
                        style=CONTENT_STYLE,
                    ),
                ],
                style=CONTAINER_STYLE,
            ),
        ],
        style={
            "overflow": "scroll",
            # Hide scrollbar
            "scrollbar-width": "none",
        },
    )
