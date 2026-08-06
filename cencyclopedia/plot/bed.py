import polars as pl
import plotly.graph_objs as go

from typing import Literal


def add_bedgraph_track(
    df_bg: pl.DataFrame, fig: go._figure.Figure, name_label: str | None = None, **kwargs
):
    if not name_label:
        name_label = "Value"
    for row in df_bg.iter_rows(named=True):
        st, end = row["chrom_st"], row["chrom_end"]
        value = row["name"]
        length = end - st
        fig.add_scatter(
            fill="toself",
            x=[
                st,
                end,
                end,
                st,
                st,
            ],
            y=[0, 0, value, value, 0],
            line=dict(color="#000000"),
            hovertemplate=f"Interval: ({st}, {end})<br>Length: {length}<br>{name_label}: {value}<extra></extra>",
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
    score_label: str | None = None,
    **kwargs,
):
    if not score_label:
        score_label = "score"
    invert_adj = -1 if invert else 1
    for grp, df in (
        df_bed.with_columns(length=pl.col("chrom_end") - pl.col("chrom_st"))
        .sort(by="length", descending=True)
        .group_by(["name", "color"], maintain_order=True)
    ):
        name, color = grp
        x = []
        y = []
        custom_data = []
        for row in df.iter_rows(named=True):
            slop_st = row["chrom_st"] - bp_slop
            slop_end = row["chrom_end"] + bp_slop
            slop_length = slop_end - slop_st
            hoverdata = [
                row["chrom_st"],
                row["chrom_end"],
                row["chrom_end"] - row["chrom_st"],
                row["score"],
            ]
            if shape == "tri":
                midpt = slop_st + (slop_length / 2)
                x.extend([slop_st, midpt, slop_end, slop_st, None])
                y.extend([0, 1 * invert_adj, 0, 0, None])
                custom_data.extend((hoverdata for _ in range(5)))
            else:
                x.extend([slop_st, slop_end, slop_end, slop_st, slop_st, None])
                y.extend([0, 0, 1, 1, 0, None])
                custom_data.extend((hoverdata for _ in range(6)))

        fig.add_scattergl(
            fill="toself",
            x=x,
            y=y,
            line=dict(color=color),
            customdata=custom_data,
            name=name,
            mode="text",
            hovertemplate=f"Interval: (%{{customdata[0]}}, %{{customdata[1]}})<br>Length: %{{customdata[2]}}<br>{score_label}: %{{customdata[3]}}",
            fillcolor=color,
            showlegend=False,
            **kwargs,
        )


def add_bedstrand_track(
    df_bedstrand: pl.DataFrame, fig: go._figure.Figure, arrow_size: int = 10, **kwargs
):
    for row in df_bedstrand.iter_rows(named=True):
        length = row["chrom_end"] - row["chrom_st"]
        if row["name"] == "-":
            x = [row["chrom_end"], row["chrom_st"]]
            name = "Reverse"
        else:
            x = [row["chrom_st"], row["chrom_end"]]
            name = "Forward"

        # https://community.plotly.com/t/arrow-lines-between-points-scatter-plot-using-graph-objects/70004/5
        fig.add_scatter(
            x=x,
            y=[1, 1],
            name=name,
            hovertext=f"Interval: ({x[0]}, {x[1]})<br>Length: {length}",
            marker=dict(
                size=arrow_size,
                symbol="arrow-bar-up",
                angleref="previous",
                color=row["color"],
            ),
            showlegend=False,
            **kwargs,
        )
