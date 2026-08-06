import polars as pl
import dash_bootstrap_components as dbc

from dash import dcc, html
from typing import Any

from cencyclopedia.io.data import Data
from cencyclopedia.components.tree import dataview_selected_cen
from cencyclopedia.components.err_msg import modal_error_message
from cencyclopedia.components.help import popover, row_title_with_help
from cencyclopedia.plot.common import DEFAULT_SETTINGS

CEN_PAGE_STYLE = {
    "padding": "4rem",
}


def layout_cen(cfg, dropdown, dataview_selected_cen) -> html.Div:
    selected_cen_height = cfg["general"]["selected_cen"]["height"]
    selected_cen_vspacing = cfg["general"]["selected_cen"]["vertical_spacing"]
    return html.Div(
        [
            row_title_with_help(
                "Centromere",
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
                        "height": cfg["general"]["selected_cen"]["height"],
                    },
                )
            ),
            dataview_selected_cen,
        ],
    )


def cen_page(
    regions: str,
    cfg: dict[str, Any],
):
    data = Data(cfg["data"])
    datatypes = list(data.labels)
    df_regions = pl.scan_csv(regions).collect()
    all_chroms = df_regions["chrom"].to_list()
    itv_selected_cen = (
        df_regions.filter(pl.col("chrom").eq(pl.lit(all_chroms[0])))
        .select("chrom", "chrom_st", "chrom_end")
        .row(0)
    )
    dropdown = dcc.Dropdown(
        all_chroms,
        value=itv_selected_cen[0],
        searchable=True,
        id="dropdown-selected-cen",
    )
    dataview = dataview_selected_cen(
        datatypes,
        active_tab=cfg["general"]["selected_cen"].get("default_data_tab"),
    )
    selected_cen_height = cfg["general"]["selected_cen"]["height"]
    selected_cen_vspacing = cfg["general"]["selected_cen"]["vertical_spacing"]

    return html.Div(
        [
            # Selected cen.
            dcc.Store(id="itv-selected-cen", data=itv_selected_cen),
            # Regions string
            dcc.Store(id="regions", data=regions),
            # Configuration dictionary (yaml file)
            dcc.Store(id="cfg", data=cfg),
            # Datatypes provided
            dcc.Store(id="datatypes", data=datatypes),
            # Store selected cen layout params. We need these to persist if user clicks to different chromosome.
            # Height
            dcc.Store(id="selected-cen-height", data=selected_cen_height),
            # Vertical spacing
            dcc.Store(id="selected-cen-vspacing", data=selected_cen_vspacing),
            # Individual track settings
            dcc.Store(
                id="bed-track-settings",
                data={
                    dtype: DEFAULT_SETTINGS
                    for dtype, dcfg in cfg["data"].items()
                    if dcfg["type"] != "spacer"
                },
            ),
            modal_error_message(),
            layout_cen(cfg, dropdown, dataview),
        ],
        style=CEN_PAGE_STYLE,
    )
