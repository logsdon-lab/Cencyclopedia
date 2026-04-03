import polars as pl
import plotly.graph_objs as go
import dash_bootstrap_components as dbc

from PIL import Image
from typing import Any
from dash import dcc, html, get_asset_url

from cencyclopedia.plot.image import add_image_to_figure

HOME_PAGE_STYLE = {
    "padding": "4rem",
    "overflow": "scroll",
    # Hide scrollbar
    "scrollbar-width": "none",
}


def create_chromosome_navlink(cfg: dict[str, Any]) -> go._figure.Figure:
    fig = add_image_to_figure(
        Image.open(get_asset_url("Chromosomes.png")), fig=go._figure.Figure()
    )
    df_bboxes = pl.read_csv(cfg["general"]["chrom_navlink"]["bboxes"])

    for row in df_bboxes.iter_rows(named=True):
        chrom_name = row["chrom_name"]
        x0, x1 = row["xpos_st"], row["xpos_end"]
        y0, y1 = -row["ypos_st"], -row["ypos_end"]
        # Add rect [x_left_bottom, x_left_top, x_right_bottom, x_right_top, x_left_bottom]
        #          [y_left_bottom, y_left_top, y_right_top, y_right_bottom, y_left_bottom]
        fig.add_scatter(
            x=[x0, x0, x1, x1, x0],
            y=[y0, y1, y1, y0, y0],
            fillcolor="#FFFFFF",
            fill="toself",
            opacity=0.0,
            customdata=[chrom_name],
            name=chrom_name,
            mode="lines+text",
        )

    fig.update_layout(
        showlegend=False,
        template="simple_white",
        xaxis={"showgrid": False, "fixedrange": True},
        yaxis={"showgrid": False, "fixedrange": True},
        margin=dict(l=0, r=0, b=0, t=0),
    )
    return fig


def create_logo(width: str = "8rem"):
    img = Image.open(get_asset_url("logo.png"))
    return html.Img(
        src=img,
        style={
            "width": width,
            "display": "block",
            "margin-left": "auto",
            "margin-right": "auto",
        },
    )


def home_page(cfg: dict[str, Any]):
    return html.Div(
        [
            # Home selected cen
            create_logo(width="30%"),
            html.Br(),
            dcc.Markdown(
                """
                ### Cencyclopedia is an interactive visualization tool that allows you to investigate
                ### the sequence, structure, and epigenetic landscape, and evolutionary relationships among human centromeres
                """,
                style={"text-align": "center"},
            ),
            html.Hr(),
            html.Br(),
            html.H1("Start by picking a chromosome", style={"text-align": "center"}),
            html.Br(),
            dbc.Row(
                dcc.Graph(
                    figure=create_chromosome_navlink(cfg),
                    id="fig-chrom-navlink",
                    style={"height": "30vh"},
                    config={"displayModeBar": False},
                )
            ),
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H3("Developed by"),
                            html.Hr(),
                            dcc.Markdown("""
                                * [Keisuke K. Oshima](https://github.com/koisland) ([Logsdon Lab](https://www.logsdonlab.com/))
                                * [Zikun Yang](https://github.com/Zikun-Yang) ([Mao Lab](https://www.yafmao.org/))

                                We thank an anonymous reviewer for suggesting we build this interactive centromere visualization tool.
                            """),
                        ]
                    ),
                    dbc.Col(
                        [
                            html.H3("Citation"),
                            html.Hr(),
                            dcc.Markdown("""
                                *Gao S, Oshima KK, Chuang SC, Loftus M, Montanari A, Gordon DS, Human Genome Structural Variation Consortium, Human Pangenome Reference Consortium, Hsieh P, Konkel MK, Ventura M, Logsdon GA. A global view of human centromere variation and evolution. bioRxiv. 2025. p. 2025.12.09.693231. [doi:10.64898/2025.12.09.693231](https://doi.org/10.64898/2025.12.09.693231)*
                            """),
                        ]
                    ),
                ]
            ),
        ],
        style=HOME_PAGE_STYLE,
    )
