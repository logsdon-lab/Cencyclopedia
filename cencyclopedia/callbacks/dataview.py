import dash
import polars as pl

from typing import Any
from loguru import logger
from dash.dcc.express import send_bytes
from dash.exceptions import PreventUpdate
from dash import Input, Output, callback, dash_table, State, html, ctx

from cencyclopedia.io.data import Data
from cencyclopedia.plot.common import (
    BedTrackSettings,
    DEFAULT_SETTINGS,
    DEFAULT_MODE,
    TrackMode,
    TrackLimit,
)
from cencyclopedia.components.dataview import dataview_tab


@callback(
    Output("btn-bed-update-tracks", "disabled"),
    Input("data-label-tabs", "active_tab"),
    Input("rd-bed-expand-tracks-mode", "value"),
    State("bed-track-settings", "data"),
)
def disable_update_while_original(
    active_tab: str | None, mode: str, expand_tracks: dict[str, BedTrackSettings]
) -> bool:
    if not active_tab:
        raise PreventUpdate

    track_settings = expand_tracks[active_tab]
    return mode == DEFAULT_MODE and track_settings.get("mode") == DEFAULT_MODE


@callback(
    Output("data-labels-output", "children"),
    Input("data-label-tabs", "active_tab"),
    Input("itv-selected-cen", "data"),
    State("cfg", "data"),
    State("bed-track-settings", "data"),
)
def draw_dataview_tab(
    active_tab: str | None,
    itv_selected_cen: tuple[str, int, int] | None,
    cfg: dict[str, Any],
    expand_tracks: dict[str, BedTrackSettings],
) -> html.Div:
    if not itv_selected_cen or not active_tab:
        raise PreventUpdate

    chrom, st, end = itv_selected_cen
    data_fhs = Data(cfg["data"])
    df = data_fhs.query(active_tab, chrom, st, end, to_relative=False)
    if not isinstance(df, pl.DataFrame):
        raise PreventUpdate

    replace_colnames: dict[str, str] = data_fhs.options(active_tab).get(
        "replace_colnames", {}
    )
    data_table = dash_table.DataTable(
        id=f"data-{active_tab}",
        data=list(df.iter_rows(named=True)),  # pyright: ignore
        columns=[
            {
                # Get replacement name, otherwise keep same.
                "name": replace_colnames.get(i, i),
                "id": i,
                "selectable": True,
            }
            for i in df.columns
        ],
        page_size=5,
        column_selectable="single",
        sort_action="native",
        filter_action="native",
        style_cell={"textAlign": "left"},
        style_data={"whiteSpace": "normal", "height": "auto", "lineHeight": "15px"},
    )
    # Use defaults.
    track_settings = expand_tracks[active_tab]
    dtype = data_fhs.datatype(active_tab)
    disabled = not dtype.is_expandable() if dtype else True
    return dataview_tab(
        data_table=data_table, track_settings=track_settings, all_disabled=disabled
    )


@callback(
    Output("bed-track-settings", "data", allow_duplicate=True),
    Input("btn-bed-update-tracks", "n_clicks", allow_optional=True),
    State("data-label-tabs", "active_tab"),
    State("rd-bed-expand-tracks-mode", "value"),
    State("dropdown-bed-expand-tracks-limit", "value"),
    State("bed-track-settings", "data"),
    prevent_initial_call=True,
)
def update_bed_tracks_settings(
    n_clicks: int | None,
    active_tab: str | None,
    mode: TrackMode,
    limit: TrackLimit,
    bed_tracks_settings: dict[str, BedTrackSettings],
) -> dash.NoUpdate | dict[str, BedTrackSettings]:
    # Don't update tracks to avoid rerender if not stale.
    if not n_clicks or not active_tab:
        raise PreventUpdate

    bed_tracks_settings[active_tab] = {"mode": mode, "limit": limit}
    logger.debug(f"New expand tracks: {bed_tracks_settings}")
    return bed_tracks_settings


@callback(
    Output("bed-track-settings", "data", allow_duplicate=True),
    Output("rd-bed-expand-tracks-mode", "value"),
    Output("dropdown-bed-expand-tracks-limit", "value"),
    Input("btn-bed-reset-tracks", "n_clicks", allow_optional=True),
    State("data-label-tabs", "active_tab"),
    State("bed-track-settings", "data"),
    prevent_initial_call=True,
)
def reset_bed_tracks_settings(
    n_clicks: int | None,
    active_tab: str | None,
    bed_tracks_settings: dict[str, BedTrackSettings],
) -> tuple[dict[str, BedTrackSettings], TrackMode, TrackLimit]:
    if not n_clicks or not active_tab:
        raise PreventUpdate

    default_settings = DEFAULT_SETTINGS
    bed_tracks_settings[active_tab] = default_settings
    logger.debug("Reset expand tracks.")
    return (
        bed_tracks_settings,
        default_settings["mode"],
        default_settings["limit"],
    )


@callback(
    Output("download-data", "data"),
    Input("btn-download-data", "n_clicks"),
    State("data-label-tabs", "active_tab"),
    State("itv-selected-cen", "data"),
    State("cfg", "data"),
    prevent_initial_call=True,
)
def download_data(
    n_clicks: int | None,
    active_tab: str | None,
    itv_selected_cen: tuple[str, int, int],
    cfg: dict[str, Any],
) -> dash.NoUpdate | dict[str, Any]:
    logger.debug(f"Download triggered: {ctx.triggered}")
    if not n_clicks or not active_tab:
        raise PreventUpdate

    chrom, st, end = itv_selected_cen
    data_fhs = Data(cfg["data"])
    df = data_fhs.query(active_tab, chrom, st, end, to_relative=False)
    if not isinstance(df, pl.DataFrame):
        return dash.no_update

    # Rename if replacement colnames provided.
    replace_colnames: dict[str, str] | None = data_fhs.options(active_tab).get(
        "replace_colnames"
    )
    if replace_colnames:
        df = df.rename(replace_colnames, strict=False)

    first_col = df.columns[0]
    # Assume bed-like and is chrom. Add # to start so works in IGV
    if not first_col.startswith("#"):
        df = df.rename({first_col: f"#{first_col}"})

    outfname = f"{chrom}_{st}_{end}_{active_tab.replace(' ', '_')}.bed.gz"
    return send_bytes(
        lambda x: df.write_csv(x, separator="\t", compression="gzip"), outfname
    )
