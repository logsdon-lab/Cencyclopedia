import polars as pl
import dash_bootstrap_components as dbc

from PIL import Image
from typing import Any
from loguru import logger
from dash import dcc, html, get_asset_url

from cencyclopedia.plot.tree import create_tree_figure
from cencyclopedia.components.home import create_logo
from cencyclopedia.components.err_msg import modal_error_message
from cencyclopedia.components.help import row_title_with_help, popover


SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "12rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
    "overflow": "scroll",
    # Hide scrollbar
    "scrollbar-width": "none",
}
CONTENT_STYLE = {
    "padding-top": "2rem",
    "padding-bottom": "2rem",
    "padding-left": "7rem",
    "padding-right": "8rem",
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


def tree_layout(
    selected_cen: tuple[str, int, int],
    fig_tree: dcc.Graph,
    dropdown: dcc.Dropdown,
    dataview_selected_cen: html.Div,
    cfg: dict[str, Any],
):
    selected_cen_height = cfg["general"]["selected_cen"]["height"]
    selected_cen_vspacing = cfg["general"]["selected_cen"]["vertical_spacing"]
    return html.Div(
        [
            modal_error_message(),
            # Interval for selected centromere
            dcc.Store(id="itv-selected-cen", data=selected_cen),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            row_title_with_help(
                                "Phylogenetic Tree", "btn-collapse-howto-tree"
                            ),
                            popover(
                                header="Help",
                                body=dcc.Markdown(
                                    """
                                    1. Each centromere haplotype on this figure is clickable.
                                        * Hovering over each centromere displays the contig name, superpopulation, and sex.
                                    2. To zoom in, use the **"Zoom"** icon in Plotly's modal bar.
                                    3. To move around the image, use the **"Pan"** option.
                                    4. To reset the image, click the **"Reset axes"** icon.
                                    """
                                ),
                                target="btn-collapse-howto-tree",
                            ),
                            fig_tree,
                        ],
                        width=cfg["general"]["tree"]["width"],
                        style={"height": cfg["general"]["tree"]["height"]},
                    ),
                    dbc.Col(
                        [
                            row_title_with_help(
                                "Individual centromere",
                                "btn-collapse-howto-selected-cen",
                            ),
                            popover(
                                header="Help",
                                target="btn-collapse-howto-selected-cen",
                                body=dcc.Markdown(
                                    """
                                    ### General
                                    1. Select a contig from the dropdown. Contigs are ordered in the same order as the tree.
                                    2. There are multiple ways to adjust position in the displayed plot:
                                        1. Adjust the slider. Click the **"Reset"** button to reset to the original coordinates.
                                        2. Zoom in using the **"Zoom"** icon.
                                        3. Drag along the track with **"Pan"** to move to a new position.
                                    3. Hover over individual annotations to get a short description.

                                    ### Mode
                                    To view BED tracks, use the "Mode" section. The following modes are possible:
                                    * Condensed
                                        * Default.
                                    * Length
                                        * Show the largest annotation at the top.
                                    * Frequency
                                        * Show the most frequent annotation at the top.
                                    * Proportion
                                        * Show the annotation covering the largest proportion of the region at the top.

                                    ### Update
                                    Once set, click **"Update"** to replot.
                                    * *"All"* or a set number up to 50 can be drawn at a time.

                                    ### Reset
                                    To reset the tracks for a give data type to its default. Click the **"Reset"** button.
                                    * This is only done for that data type.
                                    """
                                ),
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(dropdown, width=11),
                                    dbc.Col(
                                        [
                                            dbc.Button(
                                                "Layout",
                                                id="btn-popup-layout-selected-cen",
                                                size="sm",
                                                n_clicks=0,
                                            ),
                                            popover(
                                                header="Layout",
                                                body=[
                                                    dbc.Label("Height"),
                                                    dbc.Input(
                                                        id="input-selected-cen-height",
                                                        value=selected_cen_height,
                                                    ),
                                                    html.Br(),
                                                    dbc.Label("Vertical spacing"),
                                                    dbc.Input(
                                                        id="input-selected-cen-vertical-spacing",
                                                        min=0.0,
                                                        placeholder="Set 0.0 to autosize.",
                                                        value=selected_cen_vspacing
                                                        if selected_cen_vspacing
                                                        else 0.0,
                                                    ),
                                                    html.Br(),
                                                    dbc.Button(
                                                        "Update",
                                                        id="btn-update-selected-cen-layout",
                                                        size="sm",
                                                        n_clicks=0,
                                                    ),
                                                ],
                                                target="btn-popup-layout-selected-cen",
                                            ),
                                        ],
                                        width=1,
                                    ),
                                ]
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


def tree_page(
    page: str,
    dtypes: list[str],
    regions: str,
    cfg: dict[str, Any],
):
    chrom_name = page
    logger.debug(f"On {chrom_name}")
    if not chrom_name:
        return []

    df_regions = pl.scan_csv(regions).collect()
    df_regions_chrom = df_regions.filter(pl.col("chrom_name").eq(chrom_name))
    dfs_regions_chrom_arm: dict[tuple[Any, ...], pl.DataFrame] = (
        df_regions_chrom.partition_by(["arm"], maintain_order=True, as_dict=True)
    )
    all_chroms = df_regions_chrom["chrom"].unique(maintain_order=True).to_list()
    itv_selected_cen = (
        df_regions_chrom.filter(pl.col("chrom").eq(pl.lit(all_chroms[0])))
        .select("chrom", "chrom_st", "chrom_end")
        .row(0)
    )
    fname = f"{chrom_name}_PhylogeneticTree_p_q-arm_withLegend.png"
    try:
        path = get_asset_url(fname)
        fig = create_tree_figure(Image.open(path), dfs_regions_chrom_arm, cfg)
    except (OSError, KeyError):
        logger.error(f"Cannot open image ({fname}) for {chrom_name} tree")
        fig = None

    layout = split_layout(
        content=tree_layout(
            selected_cen=itv_selected_cen,
            fig_tree=dcc.Graph(
                id="fig-cens-tree",
                figure=fig,
                responsive=True,
                config={"displaylogo": False, "displayModeBar": True},
            ),
            dropdown=dcc.Dropdown(
                all_chroms,
                value=itv_selected_cen[0],
                searchable=True,
                id="dropdown-selected-cen",
            ),
            dataview_selected_cen=dataview_selected_cen(
                dtypes,
                active_tab=cfg["general"]["selected_cen"].get("default_data_tab"),
            ),
            cfg=cfg,
        ),
        chrom_names=CHROMS.keys(),
    )
    return layout


def split_layout(content: html.Div, chrom_names: list[str]) -> dbc.Row:
    sidebar = html.Div(
        [
            dbc.NavLink(create_logo(width="8rem"), href="/", active="exact"),
            html.Hr(),
            dbc.Nav(
                [
                    dbc.NavLink("All", href="/all", active="exact"),
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
    return dbc.Row(
        [
            dbc.Col(sidebar, width=1),
            dbc.Col(content, width=11, style=CONTENT_STYLE),
        ]
    )
