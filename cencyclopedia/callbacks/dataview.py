import sys
import dash

from typing import Any, Literal
from loguru import logger
from dash import Input, Output, callback, dash_table, State, html

from cencyclopedia.io.data import Data
from cencyclopedia.plot.common import BedTrackSettings, default_bed_track_settings
from cencyclopedia.components.dataview import dataview_tab


EXPANDABLE_DTYPES = set(("bed", "bedstrand"))


@callback(
    Output("itv-selected-cen", "data"),
    Input("fig-selected-cen", "relayoutData"),
    State("itv-selected-cen", "data"),
)
def update_selected_cen_coords_from_zoom_info(
    zoom_info: dict[str, Any] | None, selected_cen: tuple[str, int, int] | None
) -> dash._callback.NoUpdate | tuple[str, int, int]:
    if not selected_cen or not zoom_info or not "xaxis.range[0]" in zoom_info:
        return dash.no_update

    # Get coordinates from zoom level.
    logger.debug(f"Zoom info: {zoom_info}")
    st, end = sys.maxsize, 0
    for val in zoom_info.values():
        val = round(val)
        st = min(st, val)
        end = max(end, val)

    prev_chrom, prev_st, prev_end = selected_cen
    logger.debug(
        f"Updated start and end coordinates from {prev_chrom}:{prev_st}-{prev_end} to {prev_chrom}:{st}-{end}."
    )
    return prev_chrom, st, end


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
) -> list[html.Br | dash_table.DataTable | html.Div | html.H3 | html.Hr]:
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
    )
    # Use defaults.
    track_settings = expand_tracks[data_label]
    disabled = data_fhs.datatype(data_label) not in EXPANDABLE_DTYPES
    return dataview_tab(
        data_table=data_table, track_settings=track_settings, disabled=disabled
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
        Literal["Coverage", "Frequency", "Length", "Original"],
        Literal["All"] | int,
    ]
):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update

    default_settings = default_bed_track_settings()
    bed_tracks_settings[data_label] = default_settings
    logger.debug("Reset expand tracks.")
    return (
        bed_tracks_settings,
        default_settings["mode"],
        default_settings["limit"],
    )
