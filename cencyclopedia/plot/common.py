from typing import Literal, TypedDict


class ExpandTracksSettings(TypedDict):
    expand: bool
    mode: Literal["Name", "Length", "Frequency"]
    limit: int
    n_clicks: int


def default_expand_track_settings() -> ExpandTracksSettings:
    return {"expand": False, "mode": "Name", "limit": 1, "n_clicks": 0}
