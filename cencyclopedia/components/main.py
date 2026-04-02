import dash_bootstrap_components as dbc

from typing import Any
from dash import html, dcc
from cencyclopedia.io.data import Data
from cencyclopedia.components.home import home_page
from cencyclopedia.plot.common import DEFAULT_SETTINGS


def main_page(
    regions: str,
    cfg: dict[str, Any],
):
    # Data
    data = Data.new(cfg["data"])
    datatypes = list(data.labels)
    selected_cen_height = cfg["general"]["selected_cen"]["height"]
    selected_cen_vspacing = cfg["general"]["selected_cen"]["vertical_spacing"]
    return html.Div(
        [
            # Regions
            dcc.Store(id="regions", data=regions),
            # Configuration dictionary (yaml file)
            dcc.Store(id="cfg", data=cfg),
            # Datatypes provided
            dcc.Store(id="datatypes", data=datatypes),
            # Store selected cen layout params. We need these to persist if user clicks to different chromosome.
            # Height
            dcc.Store(id="selected-cen-height", data=selected_cen_height),
            # Vertical spacing
            dcc.Store(id="selected-cen-vspacing", data=selected_cen_vspacing),
            # Individual track settings
            dcc.Store(
                id="bed-track-settings",
                data={dtype: DEFAULT_SETTINGS for dtype in cfg["data"].keys()},
            ),
            # URL (/, all, chr?)
            dcc.Location(id="url", refresh=False),
            dbc.Row(home_page(cfg), id="main-content"),
        ],
        style={
            "overflow": "scroll",
            # Hide scrollbar
            "scrollbar-width": "none",
        },
    )
