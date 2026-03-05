from copy import deepcopy
import polars as pl

from PIL import Image
from typing import Any
from loguru import logger
from dash import Input, Output, callback, dcc, dash_table, State
from dash.exceptions import PreventUpdate

from cencyclopedia.io.data import Data
from cencyclopedia.plot.common import (
    ExpandTracksSettings,
    default_expand_track_settings,
)
from cencyclopedia.plot.tree import create_tree_figure, create_tree_legend_figure
from cencyclopedia.components.main import main_content, data_summary
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
    chrom_name = pathname.strip("/")
    if not chrom_name:
        return home_page(), None
    else:
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
            image_tree = cfg.get("trees", {})[f"{chrom_name}_p"]
            img = Image.open(image_tree)
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
    State("expand-tracks", "data"),
)
def draw_dataview_tab(
    data_label: str,
    regions: str,
    selected_cen: str | None,
    cfg: dict[str, Any],
    expand_tracks: dict[str, ExpandTracksSettings],
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
    expand_tracks_dtype = expand_tracks.get(data_label, default_expand_track_settings())
    disabled = data_fhs.datatype(data_label) not in EXPANDABLE_DTYPES
    return dataview_tab(
        data_table=data_table, expand_tracks=expand_tracks_dtype, disabled=disabled
    )


@callback(
    Output("expand-tracks", "data"),
    Output("btn-expand-tracks", "children"),
    Input("btn-expand-tracks", "n_clicks"),
    State("data-label-tabs", "active_tab"),
    State("rd-expand-tracks-mode", "value"),
    State("input-expand-tracks-limit", "value"),
    State("expand-tracks", "data"),
    prevent_initial_call=True,
)
def update_expand_tracks_data(
    n_clicks: int | None,
    data_label: str,
    mode: str,
    limit: int,
    expand_tracks: dict[str, ExpandTracksSettings],
):
    default_settings = default_expand_track_settings()
    settings = expand_tracks.get(data_label, default_settings)

    # Settings change from default.
    different_settings = settings != default_settings
    # Same tab but clicked
    if n_clicks:
        expand = not settings["expand"]
    # Switched tabs causing n_clicks to reset to None
    elif not n_clicks and different_settings:
        expand = settings["expand"]
        n_clicks = settings["n_clicks"]
    # Just loaded
    elif not n_clicks:
        expand = settings["expand"]
        n_clicks = 1

    expand_tracks[data_label] = {"mode": mode, "expand": expand, "limit": limit, "n_clicks": n_clicks}
    button_label = "Expand" if expand else "Compress"
    logger.debug(f"New expand tracks: {expand_tracks}")
    return expand_tracks, button_label
