import polars as pl
import plotly.graph_objs as go

from typing import Any
from loguru import logger
from plotly.subplots import make_subplots
from dash import Input, Output, callback
from dash.exceptions import PreventUpdate

from cencyclopedia.io.data import Data
from cencyclopedia.plot.ident import add_ident_track
from cencyclopedia.plot.bed import (
    add_bed_track,
    add_bedgraph_track,
    add_bedstrand_track,
)


@callback(
    Output("fig-selected-cen", "figure"),
    Input("regions", "data"),
    Input("cfg", "data"),
    Input("selected-cen", "data"),
)
def draw_selected_cen_figure(
    regions: str, cfg: dict[str, Any], selected_cen: str | None
):
    if not selected_cen:
        raise PreventUpdate

    df_region = (
        pl.scan_csv(regions)
        .filter(pl.col("chrom").eq(selected_cen) & pl.col("arm").eq(pl.lit("q")))
        .collect()
    )
    if df_region.is_empty():
        raise ValueError(f"Invalid selected_cen: {selected_cen}")

    # Open tabix file handles
    data_fhs = Data.new(cfg["data"])

    region = df_region.row(0, named=True)
    props = []
    nrows = 0
    indices = {}
    for dtype, idx, prop in data_fhs.track_params:
        indices[dtype] = idx
        if not prop:
            continue
        nrows += 1
        props.append(prop)

    fig: go._figure.Figure = make_subplots(
        rows=nrows, cols=1, shared_xaxes=True, row_heights=props
    )

    for label, idx in indices.items():
        df = data_fhs.query(
            label,
            region["chrom"],
            region["chrom_st"],
            region["chrom_end"],
            to_relative=False,
        )
        dtype = data_fhs.datatype(label)
        if dtype == "bed":
            add_bed_track(df, fig, row=idx, col=1)
        elif dtype == "bedgraph":
            add_bedgraph_track(df, fig, row=idx, col=1)
        elif dtype == "bedstrand":
            add_bedstrand_track(df, fig, row=idx, col=1)
        elif dtype == "bedpe_selfident":
            # https://plotly.com/python/heatmaps/#display-an-xarray-image-with-pximshow
            # img_mdp = add_ident_track(df)
            add_ident_track(df, fig, row=idx, col=1)
        else:
            logger.debug(f"Ignoring {label} of type {dtype} at index of {idx}")

        logger.debug(f"Finished adding {label} on track {idx}")

    fig.update_layout(
        template="simple_white",
        xaxis={"showgrid": False},
        yaxis={"showgrid": False},
        margin=dict(l=0, r=0, b=0, t=0),
    )
    # https://plotly.com/python/reference/layout/xaxis/
    fig.update_xaxes(showline=False)
    fig.update_yaxes(showticklabels=False, ticks="", showline=False)
    return fig


@callback(
    Output("selected-cen", "data", allow_duplicate=True),
    Input("dropdown-selected-cen", "value"),
    prevent_initial_call=True,
)
def update_selected_cen_dropdown(selected_cen: str) -> str:
    return selected_cen


@callback(
    Output("selected-cen", "data", allow_duplicate=True),
    Input("url", "pathname"),
    Input("regions", "data"),
    Input("cfg", "data"),
    Input("fig-cens-clade-ordered", "clickData", allow_optional=True),
    prevent_initial_call=True,
)
def update_selected_cen_by_click(
    pathname: str, regions: str, cfg: dict[str, Any], data: dict[str, Any] | None
):
    if not data:
        raise PreventUpdate

    chrom = pathname.strip("/")
    click_data = data["points"][0]
    y = click_data["y"]

    df_regions_chrom = (
        pl.scan_csv(regions)
        .filter(pl.col("chrom_name").eq(chrom) & pl.col("arm").eq(pl.lit("p")))
        .sort(by=["clade"])
        .collect()
    )
    chroms = df_regions_chrom["chrom"]
    y = abs(y)
    yst = cfg["tree_ystart"]
    yoffset = cfg["tree_yoffset"]

    idx = round((y - yst) / yoffset)
    logger.debug(f"Clicked y-pos, {y}, corresponding to index {idx}")
    try:
        chrom = chroms[idx]
    except IndexError:
        logger.debug(f"Invalid chrom index {idx}/{len(chroms)}")
        raise PreventUpdate
    return chrom
