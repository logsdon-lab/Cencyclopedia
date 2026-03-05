import numpy as np
import plotly.graph_objs as go

from PIL import Image
from typing import Any, Iterable
from dash import dcc

from .image import add_image_to_figure


def create_tree_figure(
    img: Image, chroms: Iterable[str], cfg: dict[str, Any]
) -> go._figure.Figure:
    fig = go._figure.Figure()
    fig = add_image_to_figure(img, fig)

    # Origin in top-left so y-coords are negative.
    yst = -cfg["tree_ystart"]
    yoffset = cfg["tree_yoffset"]
    ypos = np.cumsum([yoffset for i in range(len(chroms))])
    ypos *= -1
    ypos += yst
    # Add scatter points on right side of centromeres
    fig.add_scatter(
        x=[img.width - 100.0] * len(ypos),
        y=[yst, *ypos],
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
    )
    return fig


def create_tree_legend_figure(cfg: dict[str, Any]):
    fig = add_image_to_figure(
        Image.open(cfg.get("trees", {})["legend"]), go._figure.Figure()
    )
    fig.update_layout(
        showlegend=False,
        template="simple_white",
        xaxis={"showgrid": False, "fixedrange": True},
        yaxis={"showgrid": False, "fixedrange": True},
        margin=dict(l=0, r=0, b=0, t=0),
    )
    return dcc.Graph(figure=fig, id="fig-cens-clade-ordered-legend", responsive=True)
