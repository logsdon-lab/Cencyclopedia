import polars as pl
import plotly.graph_objs as go
import dash_bootstrap_components as dbc

from typing import Any
from PIL import Image
from dash import dcc, html, get_asset_url
from cencyclopedia.plot.image import add_image_to_figure
from cencyclopedia.io.figure_1 import read_figure_1_bbox_data


def draw_fig1(img: Image, df_fig1_bboxes: pl.DataFrame) -> go._figure.Figure:
    fig = go._figure.Figure()
    fig = add_image_to_figure(img, fig)

    # Figure 1 bboxes around centromeres
    for row in df_fig1_bboxes.iter_rows(named=True):
        desc = f"Population: {row['population']}<br>Gender: {row['gender']}"
        # ChrY CHM1 has none so skip
        if not row["ypos_st"]:
            continue

        x0, x1 = row["xpos_st"], row["xpos_end"]
        y0, y1 = -row["ypos_st"], -row["ypos_end"]
        chrom = row["chrom"]
        # Add rect [x_left_bottom, x_left_top, x_right_bottom, x_right_top, x_left_bottom]
        #          [y_left_bottom, y_left_top, y_right_top, y_right_bottom, y_left_bottom]
        fig.add_scatter(
            x=[x0, x0, x1, x1, x0],
            y=[y0, y1, y1, y0, y0],
            fill="toself",
            fillcolor=row["color"],
            opacity=0,
            # opacity=0.1,
            customdata=[chrom],
            hoverlabel=dict(bgcolor=row["color"], font_color="white"),
            line=dict(color=row["color"]),
            marker=dict(color=row["color"]),
            hovertemplate=desc,
            name=chrom,
            mode="lines+markers+text",
        )

    fig.update_layout(
        showlegend=False,
        template="simple_white",
        # xaxis={"fixedrange": True},
        # yaxis={"fixedrange": True},
        margin=dict(l=0, r=0, b=0, t=0),
        modebar_remove=["select2d", "lasso2d"],
    )
    return fig


def home_page(regions: str, cfg: dict[str, Any], default_chrom_name: str = "chr8"):
    df_fig1_data = read_figure_1_bbox_data(cfg)
    df_regions = pl.scan_csv(regions).collect()

    # Add population and gender
    df_fig1_data = df_fig1_data.join(
        df_regions.select("chrom", "population", "gender", "color"),
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

    fig = draw_fig1(Image.open(get_asset_url("Figure1.png")), df_fig1_data)
    return html.Div(
        [
            # Home selected cen
            dcc.Store(id="itv-selected-cen-home", data=selected_cen),
            dcc.Markdown("""
                Welcome to **Cencyclopedia**!

                This website serves as a comprehensive and interactive catalog of human centromere genetic and epigenetic diversity in
                the 65 samples sequenced by the [Human Genome Structural Variation Consortium](https://www.hgsvc.org/).
            """),
            html.Hr(),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Spinner(
                                dcc.Graph(
                                    id="fig-1-home",
                                    figure=fig,
                                    style={"height": "120vh"},
                                )
                            )
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.Br(),
                            dbc.Alert(
                                "No two centromeres are identical! Click a centromere on the left and see how it compare to CHM13.",
                                color="primary",
                            ),
                            html.Br(),
                            dbc.Spinner(
                                [
                                    dbc.Label(
                                        f"chm13_{default_chrom_name}",
                                        id="lbl-selected-cen-home-chm13",
                                    ),
                                    html.Br(),
                                    dcc.Graph(
                                        id="fig-selected-cen-home-chm13",
                                        responsive=True,
                                        config={"displaylogo": False},
                                        style={"height": "25vh"},
                                    ),
                                ]
                            ),
                            html.Br(),
                            dbc.Spinner(
                                [
                                    dbc.Label(
                                        selected_cen[0],
                                        id="lbl-selected-cen-home",
                                    ),
                                    html.Br(),
                                    dcc.Graph(
                                        id="fig-selected-cen-home",
                                        responsive=True,
                                        config={"displaylogo": False},
                                        style={"height": "25vh"},
                                    ),
                                ]
                            ),
                        ],
                        width=6,
                    ),
                ]
            ),
        ]
    )
