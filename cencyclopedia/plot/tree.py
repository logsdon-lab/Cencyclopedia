import numpy as np
import plotly.graph_objs as go

from PIL import Image
from typing import Any, Iterable, Literal
from dash import dcc, get_asset_url

from .image import add_image_to_figure


def create_tree_figure(
    img: Image,
    chroms: Iterable[str],
    colors: Iterable[str],
    cfg: dict[str, Any],
    tree_arm: Literal["p-arm", "q-arm"],
) -> go._figure.Figure:
    fig = go._figure.Figure()
    fig = add_image_to_figure(img, fig)

    # Origin in top-left so y-coords are negative.
    yst = -cfg["tree_ystart"]
    yoffset = cfg["tree_yoffset"]
    ypos = np.cumsum([yoffset for i in range(len(chroms))])
    ypos *= -1
    ypos += yst

    # Add scatter points on left or right side of centromeres based on tree_arm
    if tree_arm == "p-arm":
        x = [img.width - 100.0] * len(ypos)
    else:
        x = [100.0] * len(ypos)

    # TODO: Color by population
    fig.add_scatter(
        x=x,
        y=[yst, *ypos],
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
        modebar_remove=["select2d", "lasso2d"]
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
        modebar_remove=["select2d", "lasso2d"]
    )
    return dcc.Graph(figure=fig, id="fig-cens-tree-legend", responsive=True, config={"displaylogo": False})
