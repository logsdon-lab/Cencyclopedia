from collections import defaultdict
import polars as pl
import numpy as np
import plotly.graph_objs as go

from PIL import Image
from typing import Any
from dash import dcc, get_asset_url

from .image import add_image_to_figure


def create_tree_figure(
    img: Image,
    dfs_regions_chrom_arm: dict[tuple[Any, ...], pl.DataFrame],
    cfg: dict[str, Any],
) -> tuple[go._figure.Figure, dict[int, dict[int, str]]]:
    fig = go._figure.Figure()
    fig = add_image_to_figure(img, fig)

    # Origin in top-left so y-coords are negative.
    yst = -cfg["tree_ystart"]
    yoffset = cfg["tree_yoffset"]
    img_midpt = img.width // 2

    coords = defaultdict(dict)
    for tree_arm, df in dfs_regions_chrom_arm.items():
        tree_arm = tree_arm[0]
        chroms = df["chrom"].to_list()
        colors = df["color"].to_list()
        ypos = np.cumsum([yoffset for i in range(len(chroms) - 1)])
        ypos *= -1
        ypos += yst

        # Add scatter points on left or right side of centromeres based on tree_arm
        if tree_arm == "p":
            x = [img_midpt - 100.0] * len(chroms)
        else:
            x = [img_midpt] * len(chroms)
        y = [yst, *ypos]

        for _x, _y, chrom in zip(x, y, chroms, strict=True):
            coords[int(_x)][int(_y)] = chrom

        # Color by population
        fig.add_scatter(
            x=x,
            y=y,
            marker=dict(color=colors),
            customdata=chroms,
            hovertemplate="<b>%{customdata}</b>",
            mode="markers",
        )

    fig.update_layout(
        showlegend=False,
        template="simple_white",
        xaxis={"showgrid": False, "fixedrange": True},
        yaxis={"showgrid": False, "fixedrange": True},
        margin=dict(l=0, r=0, b=0, t=0),
        modebar_remove=["select2d", "lasso2d"],
    )
    return fig, coords


def create_tree_legend_figure():
    fig = add_image_to_figure(
        Image.open(get_asset_url("VerticalLegend.png")), go._figure.Figure()
    )
    fig.update_layout(
        showlegend=False,
        template="simple_white",
        xaxis={"showgrid": False, "fixedrange": True},
        yaxis={"showgrid": False, "fixedrange": True},
        margin=dict(l=0, r=0, b=0, t=0),
        modebar_remove=["select2d", "lasso2d"],
    )
    return dcc.Graph(
        figure=fig,
        id="fig-cens-tree-legend",
        responsive=True,
        config={"displaylogo": False},
    )
