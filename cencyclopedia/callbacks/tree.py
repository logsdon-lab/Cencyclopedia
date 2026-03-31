import dash
import polars as pl

from typing import Any
from loguru import logger
from dash import Input, Output, callback, State, ctx


@callback(
    Output("itv-selected-cen", "data", allow_duplicate=True),
    # Need to reset to None or will trigger in future invocations.
    Output("btn-reset-itv-selected-cen", "n_clicks"),
    Input("btn-reset-itv-selected-cen", "n_clicks"),
    Input("rng-itv-selected_cens", "value"),
    State("itv-selected-cen", "data"),
    State("regions", "data"),
    prevent_initial_call=True,
)
def update_itv_selected_cen_from_ui(
    reset_clicks: int | None,
    rng_itv_selected_cen: list[int],
    itv_selected_cen: tuple[str, int, int],
    regions: str,
) -> dash._callback.NoUpdate | tuple[str, int, int] | tuple[Any, ...]:
    logger.debug(f"Update context from selection UI: {ctx.triggered}")
    try:
        rng_st, rng_end = rng_itv_selected_cen
        rng_st, rng_end = int(rng_st), int(rng_end)
    except Exception:
        return dash.no_update, dash.no_update

    # Doesn't matter if p or q
    if reset_clicks:
        itv = (
            pl.scan_csv(regions)
            .filter(pl.col("chrom").eq(itv_selected_cen[0]))
            .select("chrom", "chrom_st", "chrom_end")
            .collect()
            .row(0)
        )
        return itv, None

    if rng_st == itv_selected_cen[1] and rng_end == itv_selected_cen[2]:
        return dash.no_update

    itv = (itv_selected_cen[0], rng_st, rng_end)
    return itv, None
