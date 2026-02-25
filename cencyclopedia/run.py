import yaml
import polars as pl
import plotly.graph_objs as go

from loguru import logger
from plotly.subplots import make_subplots
from dash import Dash, Input, Output, callback

from cencyclopedia.io.read_cfg_data import read_regions, Data
from cencyclopedia.plot.ident import add_ident_track
from cencyclopedia.plot.bed import (
    add_bed_track,
    add_bedgraph_track,
    add_bedstrand_track,
)
from cencyclopedia.components.layout import layout, MARK_ALL


with open("config.yaml", "rb") as fh:
    cfg = yaml.safe_load(fh)

df_regions = read_regions(cfg)

app = Dash(
    __name__, external_stylesheets=cfg["app"]["stylesheets"], title="Cencyclopedia"
)
app.layout = layout(chrom_names=df_regions["chrom_name"].unique().sort().to_list())


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
            add_bed_track(df, fig, idx, 1)
        elif dtype == "bedgraph":
            add_bedgraph_track(df, fig, idx, 1)
        elif dtype == "bedstrand":
            add_bedstrand_track(df, fig, idx, 1)
        elif dtype == "bedpe_selfident":
            # options = data_fhs.options(label)
            # https://plotly.com/python/heatmaps/#display-an-xarray-image-with-pximshow
            add_ident_track(df, fig, idx, 1)
        else:
            logger.debug(f"Ignoring {label} of type {dtype} at index of {idx}")

        logger.debug(f"Finished adding {label} on track {idx}")

    fig.update_layout(
        template="simple_white",
        xaxis={"showgrid": False},
        yaxis={"showgrid": False},
        height=600.0,
    )
    # https://plotly.com/python/reference/layout/xaxis/
    fig.update_xaxes(showline=False)
    fig.update_yaxes(showticklabels=False, ticks="", showline=False)
    return fig


@callback(
    Output("fig-cens-clade-ordered", "figure"),
    Output("lbl-selected-cen", "options"),
    Output("lbl-selected-cen", "value"),
    Input("filter-chrom", "value"),
    Input("filter-render-n", "value"),
)
def update_fig_cens(chrom: str, render_n: int):
    df_regions_chrom = df_regions.filter(
        pl.col("chrom_name").eq(chrom) & pl.col("arm").eq(pl.lit("q"))
    ).sort(by=["clade"])
    rows = list(df_regions_chrom.iter_rows(named=True))
    if render_n == MARK_ALL:
        nrows = len(rows)
    else:
        nrows = render_n
    data_fhs = Data.new(cfg["data"])

    # https://dash.plotly.com/holoviews
    fig: go._figure.Figure = make_subplots(
        rows=nrows, cols=2, shared_xaxes=True, column_widths=[0.1, 0.9]
    )
    rendered_cens = []
    for i in range(1, nrows + 1):
        try:
            row = rows[i]
        except IndexError:
            break
        df_hor = data_fhs.query(
            "as_hor_stv",
            row["chrom"],
            row["chrom_st"],
            row["chrom_end"],
            to_relative=True,
        )
        logger.debug(f"On {i}, {row}")
        # Add label
        # https://community.plotly.com/t/can-axis-title-position-be-changed/72794/3
        # captureevents
        fig.add_annotation(row=i, col=1, text=row["chrom"], showarrow=False)
        # Disable interaction with label annotation.
        fig.update_xaxes(
            fixedrange=True,
            showticklabels=False,
            ticks="",
            showline=False,
            row=i,
            col=1,
        )
        fig.update_yaxes(fixedrange=True, row=i, col=1)
        add_bed_track(df_bed=df_hor, fig=fig, row_n=i, col_n=2)
        rendered_cens.append(row["chrom"])

    fig.update_layout(
        template="simple_white",
        xaxis={"showgrid": False},
        yaxis={"showgrid": False},
        height=max(50.0 * nrows, 700.0),
    )
    # https://plotly.com/python/reference/layout/xaxis/
    fig.update_xaxes(showline=False)
    fig.update_yaxes(showticklabels=False, ticks="", showline=False)

    return fig, rendered_cens, rendered_cens[0]


if __name__ == "__main__":
    app.run(debug=True, port=8080)
