from typing import Any
from PIL.Image import Image
import plotly.graph_objs as go


def add_image_to_figure(
    img: Image,
    fig: go._figure.Figure,
    xaxis_kwargs: dict[str, Any] | None = None,
    yaxis_kwargs: dict[str, Any] | None = None,
    **kwargs,
) -> go._figure.Figure:
    if not xaxis_kwargs:
        xaxis_kwargs = {}
    if not yaxis_kwargs:
        yaxis_kwargs = {}

    # Constants
    img_width = img.width
    img_height = img.height

    # Add invisible scatter trace.
    # This trace is added to help the autoresize logic work.
    # Needs to be in negative coordinates such that the top offset that makes sense.
    fig.add_trace(
        go.Scatter(
            x=[0, img_width], y=[-img_height, 0], mode="markers", marker_opacity=0
        ),
        **kwargs,
    )

    # Configure axes
    xaxis_kwargs = {"visible": False} | xaxis_kwargs
    yaxis_kwargs = {"visible": False} | yaxis_kwargs
    fig.update_xaxes(range=[0, img_width], **xaxis_kwargs)
    fig.update_yaxes(
        scaleanchor="x",
        range=[-img_height, 0],
        constrain="domain",
        constraintoward="top",
        **yaxis_kwargs,
    )

    # Add image
    fig.add_layout_image(
        dict(
            # x-coord of image
            x=0,
            # Width of image
            sizex=img_width,
            # y-coord of image
            y=0,
            # Height of image
            sizey=img_height,
            xref="x",
            yref="y",
            opacity=1.0,
            layer="below",
            sizing="stretch",
            source=img,
        ),
        **kwargs,
    )

    return fig
