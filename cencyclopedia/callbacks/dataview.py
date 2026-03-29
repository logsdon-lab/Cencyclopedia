import dash

from typing import Any
from loguru import logger
from dash import dcc, Input, Output, callback, dash_table, State, html

from cencyclopedia.io.data import Data
from cencyclopedia.plot.common import (
    BedTrackSettings,
    DEFAULT_SETTINGS,
    TrackMode,
    TrackLimit,
)
from cencyclopedia.components.dataview import dataview_tab


EXPANDABLE_DTYPES = set(("bed", "bedstrand"))


@callback(
    Output("btn-bed-update-tracks", "disabled"),
    Input("rd-bed-expand-tracks-mode", "value"),
)
def disable_update_while_original(mode: str) -> bool:
    return mode == "Original"


@callback(
    Output("data-labels-output", "children"),
    Input("data-label-tabs", "active_tab"),
    Input("itv-selected-cen", "data"),
    State("cfg", "data"),
    State("bed-track-settings", "data"),
)
def draw_dataview_tab(
    data_label: str,
    itv_selected_cen: tuple[str, int, int] | None,
    cfg: dict[str, Any],
    expand_tracks: dict[str, BedTrackSettings],
) -> html.Div:
    if not itv_selected_cen:
        return dash.no_update

    chrom, st, end = itv_selected_cen
    data_fhs = Data.new(cfg["data"])
    df = data_fhs.query(data_label, chrom, st, end, to_relative=False)
    data_table = dash_table.DataTable(
        id=f"data-{data_label}",
        data=list(df.iter_rows(named=True)),
        columns=[{"name": i, "id": i, "selectable": True} for i in df.columns],
        page_size=5,
        column_selectable="single",
        sort_action="native",
        filter_action="native",
        style_cell={"textAlign": "left"},
        style_data={"whiteSpace": "normal", "height": "auto", "lineHeight": "15px"},
    )
    # Use defaults.
    track_settings = expand_tracks[data_label]
    disabled = data_fhs.datatype(data_label) not in EXPANDABLE_DTYPES
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
    data_label: str,
    mode: str,
    limit: int,
    bed_tracks_settings: dict[str, BedTrackSettings],
) -> dash._callback.NoUpdate | dict[str, BedTrackSettings]:
    # Don't update tracks to avoid rerender if not stale.
    if not n_clicks:
        return dash.no_update

    bed_tracks_settings[data_label] = {"mode": mode, "limit": limit}
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
    data_label: str,
    bed_tracks_settings: dict[str, BedTrackSettings],
) -> (
    tuple[dash._callback.NoUpdate, dash._callback.NoUpdate, dash._callback.NoUpdate]
    | tuple[
        dict[str, BedTrackSettings],
        TrackMode,
        TrackLimit,
    ]
):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update

    default_settings = DEFAULT_SETTINGS
    bed_tracks_settings[data_label] = default_settings
    logger.debug("Reset expand tracks.")
    return (
        bed_tracks_settings,
        default_settings["mode"],
        default_settings["limit"],
    )


@callback(
    Output("download-data", "data"),
    Input("btn-download-data", "n_clicks"),
    Input("data-label-tabs", "active_tab"),
    Input("itv-selected-cen", "data"),
    State("cfg", "data"),
    prevent_initial_call=True,
)
def download_data(
    _n_clicks: int, data_label: str, itv_selected_cen: tuple[str, int, int], cfg: str
):
    chrom, st, end = itv_selected_cen
    data_fhs = Data.new(cfg["data"])
    df = data_fhs.query(data_label, chrom, st, end, to_relative=False)
    return dcc.send_string(df.write_csv, f"{data_label}.csv")
