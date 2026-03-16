import os
import yaml
import polars as pl
import dash_bootstrap_components as dbc

from dash import Dash
from cencyclopedia.io.regions import read_or_write_regions
from cencyclopedia.components.main import main_page
from cencyclopedia.callbacks.main_page import *
from cencyclopedia.callbacks.selected_cen import *
from cencyclopedia.callbacks.dataview import *
from cencyclopedia.callbacks.figure_1 import *

with open("config.yaml", "rb") as fh:
    cfg = yaml.safe_load(fh)
    regions = "data/samples.csv.gz"
    df_regions = read_or_write_regions(cfg, regions=regions)
    chrom_names = df_regions["chrom_name"].unique().sort().to_list()

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Cencyclopedia",
    assets_external_path=".",
    suppress_callback_exceptions=True,
)
app.layout = main_page(
    regions=regions,
    chrom_names=df_regions["chrom_name"].unique().sort().to_list(),
    cfg=cfg,
)
server = app.server

if __name__ == "__main__":
    # https://github.com/yaojiach/docker-dash/blob/main/app/app.py
    app.run(
        port=8050,
        host="0.0.0.0",
        debug=os.environ["DASH_DEBUG_MODE"] == "True"
    )
