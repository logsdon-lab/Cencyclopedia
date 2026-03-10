import polars as pl

from PIL import Image
from typing import Any, Literal
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
    Output("selected-cen-stale", "data", allow_duplicate=True),
    Input("url", "pathname"),
    Input("tree-arm", "data"),
    State("regions", "data"),
    State("cfg", "data"),
    State("datatypes", "data"),
    prevent_initial_call="initial_duplicate",
)
def draw_main_content_page(
    pathname: str,
    tree_arm: Literal["p-arm", "q-arm"],
    regions: str,
    cfg: dict[str, Any],
    dtypes: list[str],
):
    page = pathname.strip("/")
    if not page:
        return home_page(), None, False
    elif page == "cite":
        return cite_page(), None, False
    else:
        chrom_name = page
        logger.debug(f"On {chrom_name}")
        if not chrom_name:
            return []

        df_regions_chrom = (
            pl.scan_csv(regions)
            .filter(
                pl.col("chrom_name").eq(chrom_name)
                & pl.col("arm").eq(pl.lit(tree_arm.replace("-arm", "")))
            )
            .sort(by=["clade"])
            .collect()
        )

        chroms = df_regions_chrom["chrom"]
        try:
            path = get_asset_url(f"{chrom_name}_PhylogeneticTree_{tree_arm}.png")
            img = Image.open(path)
        except (OSError, KeyError) as err:
            logger.error(f"Cannot open image for {chrom_name} p tree")
            raise PreventUpdate

        fig = create_tree_figure(img, chroms, cfg, tree_arm=tree_arm)
        selected_cen = chroms[0]

        content = main_content(
            fig_tree=dcc.Graph(
                figure=fig,
                id="fig-cens-tree",
                responsive=True,
            ),
            fig_tree_legend=create_tree_legend_figure(cfg),
            tree_arm=tree_arm,
            dropdown=dcc.Dropdown(
                chroms.to_list(),
                value=selected_cen,
                searchable=True,
                id="dropdown-selected-cen",
            ),
            dataview=data_summary(dtypes),
        )
        return content, selected_cen, True


@callback(
    Output("tree-arm", "data"),
    Input("dropdown-tree-arm", "value"),
)
def update_clade_arm(tree_arm: Literal["p-arm", "q-arm"]) -> Literal["p-arm", "q-arm"]:
    return tree_arm
