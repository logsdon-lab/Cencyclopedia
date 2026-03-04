import polars as pl

from PIL import Image
from typing import Any
from loguru import logger
from dash import Input, Output, callback, dcc
from dash.exceptions import PreventUpdate

from cencyclopedia.plot.tree import create_tree_figure
from cencyclopedia.components.layout import create_content_layout


@callback(
    Output("col-chrom-content", "children"),
    Input("url", "pathname"),
    Input("regions", "data"),
    Input("cfg", "data"),
)
def draw_main_content_page(pathname: str, regions: str, cfg: dict[str, Any]):
    chrom_name = pathname.strip("/")
    if not chrom_name:
        return dcc.Markdown("""
            Welcome to **Cencyclopedia**!

            This website serves as a comprehensive and interactive catalog of human centromere genetic and epigenetic diversity in
            the 65 samples sequenced by the [Human Genome Structural Variation Consortium](https://www.hgsvc.org/).

            If you use this tool in your work, please cite:

            * *Gao S, Oshima KK, Chuang SC, Loftus M, Montanari A, Gordon DS, Human Genome Structural Variation Consortium, Human Pangenome Reference Consortium, Hsieh P, Konkel MK, Ventura M, Logsdon GA. A global view of human centromere variation and evolution. bioRxiv. 2025. p. 2025.12.09.693231. [doi:10.64898/2025.12.09.693231](https://doi.org/10.64898/2025.12.09.693231)*
        """)
    else:
        logger.debug(f"On {chrom_name}")
        if not chrom_name:
            return []

        df_regions_chrom = pl.scan_csv(regions).filter(
            pl.col("chrom_name").eq(chrom_name) & pl.col("arm").eq(pl.lit("p"))
        ).sort(by=["clade"]).collect()

        chroms = df_regions_chrom["chrom"]
        try:
            image_tree = cfg.get("trees", {})[f"{chrom_name}_p"]
            img = Image.open(image_tree)
        except (OSError, KeyError) as err:
            logger.error(f"Cannot open image for {chrom_name} p tree")
            raise PreventUpdate

        fig = create_tree_figure(img, chroms, cfg)
        return create_content_layout(
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
