import dash_bootstrap_components as dbc

from typing import Any
from dash import html, dcc
from cencyclopedia.io.data import Data
from cencyclopedia.components.help import row_title_with_help, collapse_help
from cencyclopedia.components.err_msg import modal_error_message
from cencyclopedia.plot.common import DEFAULT_SETTINGS


SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
    "overflow": "scroll",
    # Hide scrollbar
    "scrollbar-width": "none",
}
CONTENT_STYLE = {
    "padding": "2rem 10rem",
    "overflow": "scroll",
    # Hide scrollbar
    "scrollbar-width": "none",
}
CHROMS = {
    "chr1": "Chromosome 1",
    "chr2": "Chromosome 2",
    "chr3": "Chromosome 3",
    "chr4": "Chromosome 4",
    "chr5": "Chromosome 5",
    "chr6": "Chromosome 6",
    "chr7": "Chromosome 7",
    "chr8": "Chromosome 8",
    "chr9": "Chromosome 9",
    "chr10": "Chromosome 10",
    "chr11": "Chromosome 11",
    "chr12": "Chromosome 12",
    "chr13": "Chromosome 13",
    "chr14": "Chromosome 14",
    "chr15": "Chromosome 15",
    "chr16": "Chromosome 16",
    "chr17": "Chromosome 17",
    "chr18": "Chromosome 18",
    "chr19": "Chromosome 19",
    "chr20": "Chromosome 20",
    "chr21": "Chromosome 21",
    "chr22": "Chromosome 22",
    "chrX": "Chromosome X",
    "chrY": "Chromosome Y",
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


def main_content(
    fig_tree: dcc.Graph,
    dropdown: dcc.Dropdown,
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
                            row_title_with_help(
                                "Phylogenetic Tree", "btn-collapse-howto-tree"
                            ),
                            collapse_help(
                                """
                                1. Each centromere haplotype on this figure is clickable.
                                    * Hovering over each centromere displays the contig name, superpopulation, and sex.
                                2. To zoom in, use the **"Zoom"** icon in Plotly's modal bar.
                                3. To move around the image, use the **"Pan"** option.
                                4. To reset the image, click the **"Reset axes"** icon.
                                """,
                                "collapse-howto-tree",
                            ),
                            fig_tree,
                        ],
                        width=cfg["general"]["tree"]["width"],
                        style={"height": cfg["general"]["tree"]["height"]},
                    ),
                    dbc.Col(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(dropdown, width=11),
                                    dbc.Col(
                                        dbc.Button(
                                            "Help",
                                            id="btn-collapse-howto-selected-cen",
                                            size="sm",
                                            color="secondary",
                                            n_clicks=0,
                                        ),
                                        width=1,
                                    ),
                                ]
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

                                ### View
                                To view BED tracks, use the "View By" section. The following modes are possible:
                                * Condensed
                                    * Default.
                                * Length
                                    * Show the largest annotation at the top.
                                * Frequency
                                    * Show the most frequent annotation at the top.
                                * Proportion
                                    * Show the annotation covering the largest proportion of the region.

                                Once set, click **"Update"** to replot.
                                * *"All"* or a set number up to 50 can be drawn at a time.

                                To reset the tracks for a give data type to its default. Click the **"Reset"** button.
                                * This is only done for that data type.
                                """,
                                "collapse-howto-selected-cen",
                            ),
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
                        dbc.NavLink(CHROMS[chrom], href=f"/{chrom}", active="exact")
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
                data={dtype: DEFAULT_SETTINGS for dtype in datatypes},
            ),
            dcc.Location(id="url", refresh=False),
            dbc.Row(
                [
                    dbc.Col(sidebar, width=1),
                    dbc.Col(
                        width=11,
                        id="main-content",
                        style=CONTENT_STYLE,
                    ),
                ],
            ),
        ],
        style={
            "overflow": "scroll",
            # Hide scrollbar
            "scrollbar-width": "none",
        },
    )
