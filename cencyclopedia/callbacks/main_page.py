import dash
import polars as pl

from PIL import Image
from typing import Any
from loguru import logger
from dash import Input, Output, callback, dcc, dash_table, State, get_asset_url
from dash.exceptions import PreventUpdate

from cencyclopedia.io.data import Data
from cencyclopedia.plot.common import BedTrackSettings
from cencyclopedia.plot.tree import create_tree_figure, create_tree_legend_figure
from cencyclopedia.components.main import main_content, data_summary
from cencyclopedia.components.cite import cite_page
from cencyclopedia.components.home import home_page
from cencyclopedia.components.dataview import dataview_tab


EXPANDABLE_DTYPES = set(("bed", "bedstrand"))


@callback(
    Output("main-content", "children"),
    Output("selected-cen", "data", allow_duplicate=True),
    Input("url", "pathname"),
    State("regions", "data"),
    State("cfg", "data"),
    State("datatypes", "data"),
    prevent_initial_call="initial_duplicate",
)
def draw_main_content_page(
    pathname: str, regions: str, cfg: dict[str, Any], dtypes: list[str]
):
    page = pathname.strip("/")
    if not page:
        return home_page(), None
    elif page == "cite":
        return cite_page(), None
    else:
        chrom_name = page
        logger.debug(f"On {chrom_name}")
        if not chrom_name:
            return []

        df_regions_chrom = (
            pl.scan_csv(regions)
            .filter(pl.col("chrom_name").eq(chrom_name) & pl.col("arm").eq(pl.lit("p")))
            .sort(by=["clade"])
            .collect()
        )

        chroms = df_regions_chrom["chrom"]
        try:
            path = get_asset_url(f"{chrom_name}_PhylogeneticTree.png")
            img = Image.open(path)
        except (OSError, KeyError) as err:
            logger.error(f"Cannot open image for {chrom_name} p tree")
            raise PreventUpdate

        fig = create_tree_figure(img, chroms, cfg)
        selected_cen = chroms[0]

        content = main_content(
            fig_clade=dcc.Graph(
                figure=fig,
                id="fig-cens-clade-ordered",
                responsive=True,
            ),
            fig_clade_legend=create_tree_legend_figure(cfg),
            dropdown=dcc.Dropdown(
                chroms.to_list(),
                value=selected_cen,
                searchable=True,
                id="dropdown-selected-cen",
            ),
            dataview=data_summary(dtypes),
        )
        return content, selected_cen


@callback(
    Output("data-labels-output", "children"),
    Input("data-label-tabs", "active_tab"),
    State("regions", "data"),
    State("selected-cen", "data"),
    State("cfg", "data"),
    State("bed-track-settings", "data"),
)
def draw_dataview_tab(
    data_label: str,
    regions: str,
    selected_cen: str | None,
    cfg: dict[str, Any],
    expand_tracks: dict[str, BedTrackSettings],
):
    if not selected_cen:
        raise PreventUpdate

    data_fhs = Data.new(cfg["data"])
    df_region = (
        pl.scan_csv(regions)
        .filter(pl.col("chrom").eq(selected_cen) & pl.col("arm").eq(pl.lit("q")))
        .collect()
    )
    # TODO: This could probably be updated to also interact with the user selected range.
    if df_region.is_empty():
        raise ValueError(f"Invalid selected_cen: {selected_cen}")

    region = df_region.row(0, named=True)
    chrom, st, end = region["chrom"], region["chrom_st"], region["chrom_end"]
    df = data_fhs.query(data_label, chrom, st, end, to_relative=False)
    data_table = dash_table.DataTable(
        id=f"data-{data_label}",
        data=list(df.iter_rows(named=True)),
        columns=[{"name": i, "id": i, "selectable": True} for i in df.columns],
        page_size=5,
        column_selectable="single",
        sort_action="native",
        filter_action="native",
    )
    # Use defaults.
    track_settings = expand_tracks[data_label]
    disabled = data_fhs.datatype(data_label) not in EXPANDABLE_DTYPES
    return dataview_tab(
        data_table=data_table, track_settings=track_settings, disabled=disabled
    )


@callback(
    Output("bed-track-settings", "data"),
    Output("selected-cen-stale", "data", allow_duplicate=True),
    Input("btn-bed-update-tracks", "n_clicks", allow_optional=True),
    State("data-label-tabs", "active_tab"),
    State("rd-bed-expand-tracks-mode", "value"),
    State("input-bed-expand-tracks-limit", "value"),
    State("bed-track-settings", "data"),
    State("selected-cen-stale", "data"),
    prevent_initial_call=True,
)
def update_bed_tracks_settings(
    n_clicks: int | None,
    data_label: str,
    mode: str,
    limit: int,
    bed_tracks_settings: dict[str, BedTrackSettings],
    stale: bool,
):
    # Don't update tracks to avoid rerender if not stale.
    if not stale and not n_clicks:
        return dash.no_update, False

    bed_tracks_settings[data_label] = {"mode": mode, "limit": limit}
    logger.debug(f"New expand tracks: {bed_tracks_settings}")
    return bed_tracks_settings, True
