import dash
import polars as pl
import plotly.graph_objs as go

from typing import Any
from loguru import logger
from copy import deepcopy
from dash import Input, Output, callback, ctx, State, dcc
from dash.exceptions import PreventUpdate

from cencyclopedia.plot.common import BedTrackSettings
from cencyclopedia.plot.cen import draw_cenplot
from cencyclopedia.components.err_msg import modal_body_content


@callback(
    Output("selected-cen-height", "data"),
    Output("selected-cen-vspacing", "data"),
    Input("btn-update-selected-cen-layout", "n_clicks"),
    State("input-selected-cen-height", "value"),
    State("input-selected-cen-vertical-spacing", "value"),
)
def update_selected_cen_layout_params(
    n_clicks: int | None,
    new_height: str,
    new_vspace: float | str,  # idk
):
    if not n_clicks or not new_vspace or not new_height:
        return dash.no_update, dash.no_update
    try:
        ht = float(new_height)
    except Exception:
        ht = new_height

    if new_vspace == 0.0:
        vspace = None
    else:
        vspace = float(new_vspace)
    return ht, vspace


@callback(
    Output("fig-selected-cen", "figure"),
    Output("fig-selected-cen", "style"),
    Output("body-err-msg", "children"),
    Output("modal-err-msg", "is_open"),
    Input("itv-selected-cen", "data"),
    Input("selected-cen-height", "data"),
    Input("selected-cen-vspacing", "data"),
    Input("bed-track-settings", "data"),
    State("cfg", "data"),
)
def draw_selected_cen_figure(
    itv_selected_cen: tuple[str, int, int] | None,
    selected_cen_height: str,
    selected_cen_vspacing: str,
    bed_track_settings: dict[str, BedTrackSettings],
    cfg: dict[str, Any],
) -> tuple[
    go._figure.Figure | dash.NoUpdate,
    dict[str, Any] | dash.NoUpdate,
    dcc.Markdown | dash.NoUpdate,
    bool | dash.NoUpdate,
]:
    logger.debug(f"Draw update context: {ctx.triggered}")
    if not itv_selected_cen:
        raise PreventUpdate
    try:
        cfg = deepcopy(cfg)
        # Set user/default height.
        cfg["general"]["selected_cen"]["height"] = selected_cen_height
        cfg["general"]["selected_cen"]["vertical_spacing"] = selected_cen_vspacing
        # Draw plot and update height if expanded.
        fig_res = draw_cenplot(itv_selected_cen, bed_track_settings, cfg)
        if not fig_res:
            raise PreventUpdate
        fig, style = fig_res
    except Exception as err:
        return dash.no_update, dash.no_update, modal_body_content(str(err)), True
    return fig, style, dash.no_update, dash.no_update


@callback(
    Output("itv-selected-cen", "data", allow_duplicate=True),
    Output("dropdown-selected-cen", "value"),
    Input("fig-cens-tree", "clickData", allow_optional=True),
    Input("dropdown-selected-cen", "value"),
    State("itv-selected-cen", "data"),
    State("regions", "data"),
    prevent_initial_call=True,
)
def update_selected_cen(
    click_data: dict[str, Any] | None,
    dropdown_selected_cen: str,
    itv_selected_cen: tuple[str, int, int],
    regions: str,
) -> tuple[tuple[str, int, int], str] | tuple[dash.NoUpdate, dash.NoUpdate]:
    logger.debug(f"Click update context: {ctx.triggered}")
    if dropdown_selected_cen != itv_selected_cen[0]:
        itv_selected_cen = (
            pl.scan_csv(regions)
            .filter(pl.col("chrom").eq(dropdown_selected_cen))
            .select("chrom", "chrom_st", "chrom_end")
            .collect()
            .row(0)
        )
        return itv_selected_cen, dropdown_selected_cen

    if not click_data:
        return dash.no_update, dash.no_update

    try:
        selected_cen = click_data["points"][0]["customdata"][0]
        itv_selected_cen = (
            pl.scan_csv(regions)
            .filter(pl.col("chrom").eq(selected_cen))
            .select("chrom", "chrom_st", "chrom_end")
            .collect()
            .row(0)
        )
    except KeyError as err:
        logger.debug(f"Error when accessing fields in {click_data}: {err}")
        return dash.no_update, dash.no_update

    return itv_selected_cen, selected_cen
