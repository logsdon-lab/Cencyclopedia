import plotly.graph_objs as go
from typing import Literal, TypedDict


class BedTrackSettings(TypedDict):
    mode: Literal["Original", "Interval_Length", "Frequency", "Coverage"]
    limit: int


def default_bed_track_settings() -> BedTrackSettings:
    return {"mode": "Original", "limit": 1}


def add_empty_track(fig: go._figure.Figure, xlim: tuple[int, int], **kwargs):
    fig.add_trace(
        go.Scatter(x=xlim, y=[0, 0], mode="markers", marker_opacity=0),
        **kwargs,
    )

    fig.update_layout(
        showlegend=False,
        template="simple_white",
        xaxis_range=xlim,
        xaxis={"showgrid": False, "fixedrange": True},
        yaxis={"showgrid": False, "fixedrange": True},
        margin=dict(l=0, r=0, b=0, t=0),
    )
