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
    return html.Div(
        [
            # Regions
            dcc.Store(id="regions", data=regions),
            # Configuration dictionary (yaml file)
            dcc.Store(id="cfg", data=cfg),
            # Datatypes provided
            dcc.Store(id="datatypes", data=datatypes),
            # Interval for selected centromere
            dcc.Store(id="itv-selected-cen", data=None),
            # Individual track settings
            dcc.Store(
                id="bed-track-settings",
                data={dtype: DEFAULT_SETTINGS for dtype in datatypes},
            ),
            dcc.Location(id="url", refresh=False),
            dbc.Row(home_page(cfg), id="main-content"),
        ],
        style={
            "overflow": "scroll",
            # Hide scrollbar
            "scrollbar-width": "none",
        },
    )
