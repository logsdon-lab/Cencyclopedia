import polars as pl

from PIL import Image
from typing import Any
from loguru import logger
from dash import Input, Output, callback, dcc
from dash.exceptions import PreventUpdate

from cencyclopedia.plot.tree import create_tree_figure
from cencyclopedia.components.main import main_content
from cencyclopedia.components.home import home_page


@callback(
    Output("col-chrom-content", "children"),
    Input("url", "pathname"),
    Input("regions", "data"),
    Input("cfg", "data"),
)
def draw_main_content_page(pathname: str, regions: str, cfg: dict[str, Any]):
    chrom_name = pathname.strip("/")
    if not chrom_name:
        return home_page()
    else:
        logger.debug(f"On {chrom_name}")
        if not chrom_name:
            return []

        df_regions_chrom = (
            pl.scan_csv(regions)
            .filter(pl.col("chrom_name").eq(chrom_name) & pl.col("arm").eq(pl.lit("p")))
            .sort(by=["clade"])
            .collect()
        )

        chroms = df_regions_chrom["chrom"]
        try:
            image_tree = cfg.get("trees", {})[f"{chrom_name}_p"]
            img = Image.open(image_tree)
        except (OSError, KeyError) as err:
            logger.error(f"Cannot open image for {chrom_name} p tree")
            raise PreventUpdate

        fig = create_tree_figure(img, chroms, cfg)
        return main_content(
            fig_clade=dcc.Graph(
                figure=fig,
                id="fig-cens-clade-ordered",
                responsive=True,
            ),
            dropdown=dcc.Dropdown(
                chroms.to_list(),
                value=chroms[0],
                searchable=True,
                id="dropdown-selected-cen",
            ),
            selected_cen=chroms[0],
        )
