import plotly.graph_objs as go
from typing import Literal, TypedDict
from dash import dcc

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


PLOTLY_CONFIG_SETTINGS: dcc.Graph.Config = {
    "displaylogo": False,
    "toImageButtonOptions": {"format": "svg", "scale": 1},
}


def plotly_config_settings(filename: str | None = None) -> dcc.Graph.Config:
    settings = PLOTLY_CONFIG_SETTINGS
    settings["toImageButtonOptions"]["filename"] = filename  # pyright: ignore
    return settings
