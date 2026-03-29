import plotly.graph_objs as go
from typing import Literal, TypedDict


DEFAULT_MODE = "Condensed"
ALL_MODES = ["Condensed", "Proportion", "Frequency", "Length"]
DEFAULT_LIMIT = "All"
TrackMode = Literal["Condensed", "Proportion", "Frequency", "Length"]
TrackLimit = int | Literal["All"]


class BedTrackSettings(TypedDict):
    mode: TrackMode
    limit: TrackLimit


DEFAULT_SETTINGS: BedTrackSettings = {"mode": DEFAULT_MODE, "limit": DEFAULT_LIMIT}


def add_empty_figure(fig: go._figure.Figure, xlim: tuple[int, int], **kwargs):
    fig.add_trace(
        go.Scatter(x=xlim, y=[0, 0], mode="markers", marker_opacity=0),
        **kwargs,
    )

    fig.update_layout(
        showlegend=False,
        template="simple_white",
        xaxis_range=xlim,
        margin=dict(l=0, r=0, b=0, t=0),
    )
