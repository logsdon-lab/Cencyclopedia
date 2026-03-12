import polars as pl

from PIL import Image
from typing import Any
from loguru import logger
from dash import Input, Output, callback, dcc, State, get_asset_url

from cencyclopedia.plot.tree import create_tree_figure, create_tree_legend_figure
from cencyclopedia.components.main import main_content, data_summary
from cencyclopedia.components.cite import cite_page
from cencyclopedia.components.home import home_page


@callback(
    Output("main-content", "children"),
    Output("selected-cen", "data", allow_duplicate=True),
    Output("tree-chrom-coords", "data"),
    Input("url", "pathname"),
    State("regions", "data"),
    State("cfg", "data"),
    State("datatypes", "data"),
    prevent_initial_call="initial_duplicate",
)
def draw_main_content_page(
    pathname: str,
    regions: str,
    cfg: dict[str, Any],
    dtypes: list[str],
):
    page = pathname.strip("/")
    if not page:
        return home_page(), None, None
    elif page == "cite":
        return cite_page(), None, None
    else:
        chrom_name = page
        logger.debug(f"On {chrom_name}")
        if not chrom_name:
            return []

        df_regions_chrom = (
            pl.scan_csv(regions)
            .filter(pl.col("chrom_name").eq(chrom_name))
            .sort(by=["arm", "clade"])
            .collect()
        )
        dfs_regions_chrom_arm: dict[tuple[Any, ...], pl.DataFrame] = df_regions_chrom.partition_by(["arm"], maintain_order=True, as_dict=True)
        all_chroms = df_regions_chrom["chrom"].unique(maintain_order=True).to_list()
        selected_cen = all_chroms[0]

        try:
            path = get_asset_url(f"{chrom_name}_PhylogeneticTree_p_q-arm.png")
            img = Image.open(path)
            fig, coords = create_tree_figure(img, dfs_regions_chrom_arm, cfg)
        except (OSError, KeyError) as err:
            logger.error(f"Cannot open image for {chrom_name} tree")
            fig = None
            coords = None

        content = main_content(
            fig_tree=dcc.Graph(
                figure=fig,
                id="fig-cens-tree",
                responsive=True,
                config={"displaylogo": False},
            ),
            fig_tree_legend=create_tree_legend_figure(),
            dropdown=dcc.Dropdown(
                all_chroms,
                value=selected_cen,
                searchable=True,
                id="dropdown-selected-cen",
            ),
            dataview=data_summary(dtypes),
        )
        return content, selected_cen, coords
