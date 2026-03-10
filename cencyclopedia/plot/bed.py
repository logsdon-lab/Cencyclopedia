from typing import Literal
import polars as pl
import plotly.graph_objs as go


def add_bedgraph_track(df_bg: pl.DataFrame, fig: go._figure.Figure, **kwargs):
    for row in df_bg.iter_rows(named=True):
        fig.add_scatter(
            fill="toself",
            x=[
                row["chrom_st"],
                row["chrom_end"],
                row["chrom_end"],
                row["chrom_st"],
                row["chrom_st"],
            ],
            y=[0, 0, row["name"], row["name"], 0],
            line=dict(color="#000000", width=2),
            mode="text",
            fillcolor="#000000",
            showlegend=False,
            **kwargs,
        )


def add_bed_track(
    df_bed: pl.DataFrame,
    fig: go._figure.Figure,
    shape: Literal["tri", "rect"] = "rect",
    invert: bool = True,
    bp_slop: int = 0,
    **kwargs,
):
    invert = -1 if invert else 1
    for grp, df in (
        df_bed.with_columns(length=pl.col("chrom_end") - pl.col("chrom_st"))
        .sort(by="length", descending=True)
        .group_by(["name", "color"], maintain_order=True)
    ):
        x, y = [], []
        name, color = grp
        for row in df.iter_rows(named=True):
            st = row["chrom_st"] - bp_slop
            end = row["chrom_end"] + bp_slop
            length = end - st
            if shape == "tri":
                midpt = st + (length / 2)
                x.extend([st, midpt, end, st, None])
                y.extend([0, 1 * invert, 0, 0, None])
            else:
                x.extend([st, end, end, st, st, None])
                y.extend([0, 0, 1, 1, 0, None])

        fig.add_scatter(
            fill="toself",
            x=x,
            y=y,
            line=dict(
                color=color,
                width=2,
            ),
            name=name,
            mode="text",
            fillcolor=color,
            showlegend=False,
            **kwargs,
        )


def add_bedstrand_track(df_bedstrand: pl.DataFrame, fig: go._figure.Figure, **kwargs):
    for row in df_bedstrand.iter_rows(named=True):
        length = row["chrom_end"] - row["chrom_st"]
        if row["name"] == "-":
            x = [row["chrom_end"], row["chrom_st"]]
        else:
            x = [row["chrom_st"], row["chrom_end"]]
        # https://community.plotly.com/t/arrow-lines-between-points-scatter-plot-using-graph-objects/70004/5
        fig.add_scatter(
            x=x,
            y=[1, 1],
            name=f"{length}",
            marker=dict(
                size=15, symbol="arrow-bar-up", angleref="previous", color=row["color"]
            ),
            showlegend=False,
            **kwargs,
        )
