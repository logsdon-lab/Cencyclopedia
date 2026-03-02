from typing import Any
import yaml
import numpy as np
import polars as pl
import plotly.graph_objs as go
import plotly.express as px

from PIL import Image
from loguru import logger
from plotly.subplots import make_subplots
from dash import Dash, Input, Output, callback
from dash.exceptions import PreventUpdate

from cencyclopedia.io.read_cfg_data import read_regions, Data
from cencyclopedia.plot.ident import add_ident_track
from cencyclopedia.plot.bed import (
    add_bed_track,
    add_bedgraph_track,
    add_bedstrand_track,
)
from cencyclopedia.components.layout import layout


with open("config.yaml", "rb") as fh:
    cfg = yaml.safe_load(fh)

df_regions = read_regions(cfg)

app = Dash(
    __name__, external_stylesheets=cfg["app"]["stylesheets"], title="Cencyclopedia"
)
app.layout = layout(
    chrom_names=df_regions["chrom_name"].unique().sort().to_list(),
)


@callback(
    Output("fig-selected-cen", "figure"),
    Input("lbl-selected-cen", "value"),
)
def draw_selected_cen(ctg: str):
    df_region = df_regions.filter(
        pl.col("chrom").eq(ctg) & pl.col("arm").eq(pl.lit("q"))
    )
    if df_region.is_empty():
        raise ValueError(f"Invalid ctg: {ctg}")

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
            # options = data_fhs.options(label)
            # https://plotly.com/python/heatmaps/#display-an-xarray-image-with-pximshow
            add_ident_track(df, fig, row=idx, col=1)
        else:
            logger.debug(f"Ignoring {label} of type {dtype} at index of {idx}")

        logger.debug(f"Finished adding {label} on track {idx}")

    fig.update_layout(
        template="simple_white",
        xaxis={"showgrid": False},
        yaxis={"showgrid": False},
    )
    # https://plotly.com/python/reference/layout/xaxis/
    fig.update_xaxes(showline=False)
    fig.update_yaxes(showticklabels=False, ticks="", showline=False)
    return fig


@callback(
    Output("lbl-selected-cen", "value", allow_duplicate=True),
    Input("filter-chrom", "value"),
    Input("fig-cens-clade-ordered", "clickData"),
    prevent_initial_call=True,
)
def update_selected_cen_by_click(chrom: str, data: dict[str, Any]):
    click_data = data["points"][0]
    y = click_data["y"]
    df_regions_chrom = df_regions.filter(
        pl.col("chrom_name").eq(chrom) & pl.col("arm").eq(pl.lit("p"))
    ).sort(by=["clade"])
    chroms = df_regions_chrom["chrom"]
    yst = cfg["tree_ystart"]
    yoffset = cfg["tree_yoffset"]

    idx = round((y - yst) / yoffset)
    try:
        chrom = chroms[idx]
    except IndexError:
        raise PreventUpdate
    return chrom


@callback(
    Output("fig-cens-clade-ordered", "figure"),
    Output("lbl-selected-cen", "options"),
    Output("lbl-selected-cen", "value"),
    Input("filter-chrom", "value"),
)
def update_fig_cens(chrom: str):
    df_regions_chrom = df_regions.filter(
        pl.col("chrom_name").eq(chrom) & pl.col("arm").eq(pl.lit("p"))
    ).sort(by=["clade"])

    chroms = df_regions_chrom["chrom"]
    chrom_name = df_regions_chrom["chrom_name"][0]
    try:
        image_tree = cfg.get("trees", {})[f"{chrom_name}_p"]
        img = np.array(Image.open(image_tree))
    except (OSError, KeyError) as err:
        raise PreventUpdate

    fig: go._figure.Figure = px.imshow(img)
    fig.update_layout(
        template="simple_white",
        xaxis={"showgrid": False},
        yaxis={"showgrid": False},
        margin={"t": 0, "b": 0, "r": 0, "l": 0, "pad": 0},
    )
    fig.update_xaxes(showticklabels=False, ticks="", showline=False, fixedrange=True)
    fig.update_yaxes(showticklabels=False, ticks="", showline=False, fixedrange=True)

    selected_cen = chroms[0]
    return fig, chroms.to_list(), selected_cen


if __name__ == "__main__":
    app.run(debug=True)
