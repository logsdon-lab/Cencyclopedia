import os
import sys
import yaml
import dash_bootstrap_components as dbc

from dash import Dash
from cencyclopedia.io.regions import read_or_write_regions
from cencyclopedia.components.main import main_page
from cencyclopedia.components.cen import cen_page

from cencyclopedia.callbacks.main import *
from cencyclopedia.callbacks.tree import *
from cencyclopedia.callbacks.selected_cen import *
from cencyclopedia.callbacks.dataview import *
from cencyclopedia.callbacks.overview import *
from cencyclopedia.callbacks.home import *


def server():
    configfile = os.environ.get("CENCYCLOPEDIA_CONFIG", "config.yaml")
    with open(configfile, "rb") as fh:
        cfg = yaml.safe_load(fh)
        title = cfg["general"]["title"]
        mode = cfg["general"]["mode"]
        regions = cfg["general"]["output_regions"]
        _ = read_or_write_regions(cfg, mode=mode, regions=regions)

    app = Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        title=title,
        assets_external_path=".",
        suppress_callback_exceptions=True,
    )

    if mode == "all":
        layout = main_page(
            regions=regions,
            cfg=cfg,
        )
    elif mode == "single":
        layout = cen_page(regions=regions, cfg=cfg)
    else:
        raise RuntimeError(f"Invalid mode, {mode}")

    app.layout = layout
    server = app.server
    return server


if __name__ == "__main__":
    server = server()
    server.run(
        port=8050, host="0.0.0.0", debug=os.environ.get("DASH_DEBUG_MODE") == "True"
    )
    sys.exit(0)
