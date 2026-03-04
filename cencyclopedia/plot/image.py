import PIL
import plotly.graph_objs as go


def add_image_to_figure(
    img: PIL.Image, fig: go._figure.Figure, **kwargs
) -> go._figure.Figure:
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
    fig.update_xaxes(visible=False, range=[0, img_width], **kwargs)
    fig.update_yaxes(visible=False, scaleanchor="x", range=[-img_height, 0], **kwargs)

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
