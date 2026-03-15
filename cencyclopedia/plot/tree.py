import polars as pl
import numpy as np
import plotly.graph_objs as go

from PIL import Image
from typing import Any
from dash import dcc, get_asset_url
from collections import deque
from itertools import islice

from .image import add_image_to_figure


def sliding_window(iterable, n):
    "Collect data into overlapping fixed-length chunks or blocks."
    # sliding_window('ABCDEFG', 3) → ABC BCD CDE DEF EFG
    iterator = iter(iterable)
    window = deque(islice(iterator, n - 1), maxlen=n)
    for x in iterator:
        window.append(x)
        yield tuple(window)


def create_tree_figure(
    img: Image,
    dfs_regions_chrom_arm: dict[tuple[Any, ...], pl.DataFrame],
    cfg: dict[str, Any],
) -> go._figure.Figure:
    fig = go._figure.Figure()
    fig = add_image_to_figure(img, fig)

    # Origin in top-left so y-coords are negative.
    yst = -cfg["general"]["tree_ystart"]
    yoffset = cfg["general"]["tree_yoffset"]
    img_midpt = int(img.width // 2)

    for tree_arm, df in dfs_regions_chrom_arm.items():
        tree_arm = tree_arm[0]
        chroms = df["chrom"].to_list()
        colors = df["color"].to_list()
        ypos = np.cumsum([yoffset for i in range(len(chroms) + 1)])
        ypos *= -1
        ypos += yst + yoffset

        # Add rectangle around centromere coordinates based on tree_arm
        if tree_arm == "p":
            x = [(0, img_midpt)] * len(chroms)
        else:
            x = [(img_midpt, int(img.width))] * len(chroms)

        y = list(sliding_window(ypos, 2))
        for (x0, x1), (y0, y1), chrom, color in zip(x, y, chroms, colors, strict=True):
            # Color by population
            # Add rect [x_left_bottom, x_left_top, x_right_bottom, x_right_top, x_left_bottom]
            #          [y_left_bottom, y_left_top, y_right_top, y_right_bottom, y_left_bottom]
            fig.add_scatter(
                x=[x0, x0, x1, x1, x0],
                y=[y0, y1, y1, y0, y0],
                fill="toself",
                fillcolor=color,
                opacity=0.1,
                customdata=[chrom],
                # opacity
                name=chrom,
                mode="lines",
            )

    fig.update_layout(
        showlegend=False,
        template="simple_white",
        xaxis={"showgrid": False},
        yaxis={"showgrid": False},
        margin=dict(l=0, r=0, b=0, t=0),
        modebar_remove=["select2d", "lasso2d"],
    )
    return fig


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
