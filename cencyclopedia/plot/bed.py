from typing import Literal
import polars as pl
import plotly.graph_objs as go


def add_bedgraph_track(df_bg: pl.DataFrame, fig: go._figure.Figure, **kwargs):
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
            line=dict(color="#000000", width=2),
            hovertemplate=f"Interval: ({st}, {end})<br>Value: {value}<br>Length: {length}",
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
        name, color = grp
        for row in df.iter_rows(named=True):
            slop_st = row["chrom_st"] - bp_slop
            st = row["chrom_st"]
            slop_end = row["chrom_end"] + bp_slop
            end = row["chrom_end"]
            length = end - st
            slop_length = slop_end - slop_st
            if shape == "tri":
                midpt = slop_st + (slop_length / 2)
                x = [slop_st, midpt, slop_end, slop_st]
                y = [0, 1 * invert, 0, 0]
            else:
                x = [slop_st, slop_end, slop_end, slop_st, slop_st]
                y = [0, 0, 1, 1, 0]

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
                hovertemplate=f"Interval: ({st}, {end})<br>Length: {length}",
                fillcolor=color,
                showlegend=False,
                **kwargs,
            )


def add_bedstrand_track(df_bedstrand: pl.DataFrame, fig: go._figure.Figure, **kwargs):
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
                size=15, symbol="arrow-bar-up", angleref="previous", color=row["color"]
            ),
            showlegend=False,
            **kwargs,
        )
