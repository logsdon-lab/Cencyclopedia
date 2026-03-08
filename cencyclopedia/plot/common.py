from typing import Literal, TypedDict


class BedTrackSettings(TypedDict):
    mode: Literal["Name", "Length", "Frequency"]
    limit: int


def default_bed_track_settings() -> BedTrackSettings:
    return {"mode": "Name", "limit": 1}
