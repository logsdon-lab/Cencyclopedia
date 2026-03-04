import yaml
import polars as pl
import dash_bootstrap_components as dbc

from dash import Dash
from cencyclopedia.io.read_cfg_data import read_or_write_regions
from cencyclopedia.components.layout import layout

with open("config.yaml", "rb") as fh:
    cfg = yaml.safe_load(fh)
    regions = "assets/regions.csv.gz"
    df_regions = read_or_write_regions(cfg, regions=regions)
    chrom_names = df_regions["chrom_name"].unique().sort().to_list()

from cencyclopedia.callbacks.main_page import *
from cencyclopedia.callbacks.selected_cen import *

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Cencyclopedia",
)
app.layout = layout(
    regions=regions,
    chrom_names=df_regions["chrom_name"].unique().sort().to_list(),
    cfg=cfg
)

if __name__ == "__main__":
    app.run(debug=True)
