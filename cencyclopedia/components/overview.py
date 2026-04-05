import polars as pl
import dash_bootstrap_components as dbc

from typing import Any
from dash import dcc, html
from cencyclopedia.components.tree import CHROMS
from cencyclopedia.components.tree import split_layout
from cencyclopedia.io.figure_1 import read_figure_1_bbox_data
from cencyclopedia.components.help import row_title_with_help, popover


def overview_page(regions: str, cfg: dict[str, Any], default_chrom_name: str = "chr8"):
    df_fig1_data = read_figure_1_bbox_data(cfg)
    df_regions = pl.scan_csv(regions).collect()

    # Add population and sex
    df_fig1_data = df_fig1_data.join(
        df_regions.select("chrom", "population", "sex", "color"),
        on="chrom",
        how="left",
    )

    # Get interval
    df_regions_subset = df_regions.filter(pl.col("chrom_name").eq(default_chrom_name))
    all_chroms = df_regions_subset["chrom"].unique(maintain_order=True).to_list()
    selected_cen = (
        df_regions_subset.filter(pl.col("chrom").eq(pl.lit(all_chroms[0])))
        .select("chrom", "chrom_st", "chrom_end")
        .row(0)
    )
    layout_overview = html.Div(
        [
            # Home selected cen
            dcc.Store(id="itv-selected-cen-home", data=selected_cen),
            dbc.Col(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    row_title_with_help(
                                        "Centromere Haplotypes",
                                        "btn-collapse-howto-fig1",
                                        button_width=1,
                                    ),
                                    dcc.Markdown(
                                        """
                                        Sequence, structure, methylation pattern, local sequence identity, and haplotype frequency of 2,156 completely assembled centromeres from CHM13, CHM1, and 65 diverse human genomes.
                                        """
                                    ),
                                    popover(
                                        header="Help",
                                        body=dcc.Markdown(
                                            """
                                            1. Each centromere haplotype on this figure is clickable.
                                                * Hovering over each centromere displays the contig, superpopulation and sex.
                                            2. To zoom in, use the **"Zoom"** icon in Plotly's modal bar.
                                            3. To move around the image, use the **"Pan"** option.
                                            4. To reset the image, click the **"Reset axes"**.
                                            """
                                        ),
                                        target="btn-collapse-howto-fig1",
                                    ),
                                    dbc.Spinner(
                                        dcc.Graph(
                                            id="fig-1-home",
                                            config={
                                                "displaylogo": False,
                                                "displayModeBar": True,
                                            },
                                            style={
                                                "height": cfg["general"]["fig_1"][
                                                    "height_figure"
                                                ]
                                            },
                                        )
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    # Nest divs so same level as above header.
                                    html.Div(
                                        [
                                            dbc.Row(
                                                dbc.Col(
                                                    [
                                                        html.H3(
                                                            "Centromere Comparison"
                                                        ),
                                                    ]
                                                )
                                            ),
                                            html.Hr(),
                                        ]
                                    ),
                                    dcc.Markdown(
                                        "While reference genomes like CHM13 and CHM1 provide useful insight into centromere variation, "
                                        "they only represent a fraction of human centromere variation. "
                                        "Click the figure on the left to see how centromeres vary genetically and epigenetically in the human population."
                                    ),
                                    dbc.Spinner(
                                        [
                                            html.H5(
                                                f"chm13_{default_chrom_name}",
                                                id="lbl-selected-cen-home-chm13",
                                            ),
                                            html.Br(),
                                            dcc.Graph(
                                                id="fig-selected-cen-home-chm13",
                                                responsive=True,
                                                config={"displaylogo": False},
                                                style={
                                                    "height": cfg["general"]["fig_1"][
                                                        "height_cens"
                                                    ]
                                                },
                                            ),
                                        ],
                                    ),
                                    html.Br(),
                                    dbc.Spinner(
                                        [
                                            html.H5(
                                                selected_cen[0],
                                                id="lbl-selected-cen-home",
                                            ),
                                            html.Br(),
                                            dcc.Graph(
                                                id="fig-selected-cen-home",
                                                responsive=True,
                                                config={"displaylogo": False},
                                                style={
                                                    "height": cfg["general"]["fig_1"][
                                                        "height_cens"
                                                    ]
                                                },
                                            ),
                                        ]
                                    ),
                                ],
                                width=6,
                            ),
                        ],
                    ),
                ]
            ),
        ]
    )
    return split_layout(
        content=layout_overview,
        chrom_names=CHROMS.keys(),
    )
