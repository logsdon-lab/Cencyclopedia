# TODO: Lots of duplicate code. Difficult to separate with inputs. Need to

import dash
import polars as pl
import plotly.graph_objs as go

from PIL import Image
from copy import deepcopy
from typing import Any
from loguru import logger
from dash import Input, Output, callback, ctx, State, get_asset_url
from cencyclopedia.plot.cen import draw_cenplot
from cencyclopedia.plot.common import add_empty_figure
from cencyclopedia.plot.figure_1 import draw_fig1
from cencyclopedia.io.figure_1 import read_figure_1_bbox_data


@callback(
    Output("fig-1-home", "figure"),
    # Not actually updating. Will load once.
    Input("cfg", "data"),
    State("regions", "data"),
)
def draw_figure_1(cfg: dict[str, Any], regions: str):
    df_fig1_data = read_figure_1_bbox_data(cfg)
    df_regions = pl.scan_csv(regions).collect()

    # Add continental group and sex
    df_fig1_data = df_fig1_data.join(
        df_regions.select("chrom", "continental_group", "sex", "color"),
        on="chrom",
        how="left",
    )
    return draw_fig1(Image.open(get_asset_url("Figure1.png")), df_fig1_data)


# Return chm13 and other.
@callback(
    Output("fig-selected-cen-home", "figure"),
    Output("fig-selected-cen-home-chm13", "figure"),
    Output("lbl-selected-cen-home-chm13", "children"),
    Input("itv-selected-cen-home", "data"),
    State("cfg", "data"),
    State("regions", "data"),
    prevent_initial_call="initial_duplicate",
)
def draw_selected_cen_home_figure(
    itv_selected_cen: tuple[str, int, int],
    cfg: dict[str, Any],
    regions: str,
):
    logger.debug(f"Draw (home) update context: {ctx.triggered}")
    chrom_name = (
        pl.scan_csv(regions)
        .filter(pl.col("chrom").eq(pl.lit(itv_selected_cen[0])))
        .collect()["chrom_name"][0]
    )
    if chrom_name != "chrY":
        itv_chm13 = (
            pl.scan_csv(regions)
            .filter(
                pl.col("sample").eq(pl.lit("chm13"))
                & pl.col("chrom_name").eq(pl.lit(chrom_name))
            )
            .select("chrom", "chrom_st", "chrom_end")
            .collect()
            .row(0)
        )
        label_chm13_chrom = itv_chm13[0]
    else:
        itv_chm13, label_chm13_chrom = None, "None"

    # Subset data.
    cfg["data"] = {
        k: v for k, v in cfg["data"].items() if k in cfg["general"]["fig_1"]["use_data"]
    }

    # Then set both to largest xlim and relative coordinates
    fig_cfg = deepcopy(cfg)
    fig_cfg["general"]["selected_cen"]["vertical_spacing"] = 0.01

    fig_chm13_cfg = deepcopy(cfg)
    fig_chm13_cfg["general"]["selected_cen"]["vertical_spacing"] = 0.01

    fig_res = draw_cenplot(itv_selected_cen, None, fig_cfg, to_relative=True)
    if not fig_res:
        return dash.no_update

    fig, _ = fig_res

    if itv_chm13:
        fig_chm13_res = draw_cenplot(itv_chm13, None, fig_chm13_cfg, to_relative=True)
        if not fig_chm13_res:
            return dash.no_update
        fig_chm13, _ = fig_chm13_res
    else:
        fig_chm13 = go._figure.Figure()
        add_empty_figure(fig_chm13, xlim=(0, 1))

    return fig, fig_chm13, label_chm13_chrom


@callback(
    Output("itv-selected-cen-home", "data"),
    Output("lbl-selected-cen-home", "children"),
    Input("fig-1-home", "clickData", allow_optional=True),
    State("regions", "data"),
    prevent_initial_call=True,
)
def update_selected_cen_home(
    click_data: dict[str, Any] | None,
    regions: str,
) -> tuple[tuple[str, int, int], str] | tuple[dash.NoUpdate, dash.NoUpdate]:
    logger.debug(f"Click (home) update context: {ctx.triggered}")
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
