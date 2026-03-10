import polars as pl

from PIL import Image
from typing import Any
from loguru import logger
from dash import Input, Output, callback, dcc, State, get_asset_url
from dash.exceptions import PreventUpdate

from cencyclopedia.plot.tree import create_tree_figure, create_tree_legend_figure
from cencyclopedia.components.main import main_content, data_summary
from cencyclopedia.components.cite import cite_page
from cencyclopedia.components.home import home_page


@callback(
    Output("main-content", "children"),
    Output("selected-cen", "data", allow_duplicate=True),
    Input("url", "pathname"),
    State("regions", "data"),
    State("cfg", "data"),
    State("datatypes", "data"),
    prevent_initial_call="initial_duplicate",
)
def draw_main_content_page(
    pathname: str, regions: str, cfg: dict[str, Any], dtypes: list[str]
):
    page = pathname.strip("/")
    if not page:
        return home_page(), None
    elif page == "cite":
        return cite_page(), None
    else:
        chrom_name = page
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
            path = get_asset_url(f"{chrom_name}_PhylogeneticTree.png")
            img = Image.open(path)
        except (OSError, KeyError) as err:
            logger.error(f"Cannot open image for {chrom_name} p tree")
            raise PreventUpdate

        fig = create_tree_figure(img, chroms, cfg)
        selected_cen = chroms[0]

        content = main_content(
            fig_clade=dcc.Graph(
                figure=fig,
                id="fig-cens-clade-ordered",
                responsive=True,
            ),
            fig_clade_legend=create_tree_legend_figure(cfg),
            dropdown=dcc.Dropdown(
                chroms.to_list(),
                value=selected_cen,
                searchable=True,
                id="dropdown-selected-cen",
            ),
            dataview=data_summary(dtypes),
        )
        return content, selected_cen
