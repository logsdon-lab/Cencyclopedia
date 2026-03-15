from cencyclopedia.plot.common import add_empty_track
import plotly.graph_objs as go
import dash_bootstrap_components as dbc

from PIL import Image
from dash import dcc, html, get_asset_url
from cencyclopedia.plot.image import add_image_to_figure


def draw_fig1() -> go._figure.Figure:
    path = get_asset_url("Figure1.png")
    img = Image.open(path)
    fig = go._figure.Figure()
    fig = add_image_to_figure(img, fig)

    # for (x0, x1), (y0, y1), chrom in zip(x, y, chroms, strict=True):
    #     # Color by population
    #     # Add rect [x_left_bottom, x_left_top, x_right_bottom, x_right_top, x_left_bottom]
    #     #          [y_left_bottom, y_left_top, y_right_top, y_right_bottom, y_left_bottom]
    #     fig.add_scatter(
    #         x=[x0, x0, x1, x1, x0],
    #         y=[y0, y1, y1, y0, y0],
    #         fill="toself",
    #         fillcolor=color,
    #         opacity=0.1,
    #         customdata=[chrom],
    #         # opacity
    #         name=chrom,
    #         mode="lines",
    #     )

    fig.update_layout(
        showlegend=False,
        template="simple_white",
        xaxis={"fixedrange": True},
        yaxis={"fixedrange": True},
        margin=dict(l=0, r=0, b=0, t=0),
        modebar_remove=["select2d", "lasso2d"],
    )
    return fig


def home_page():
    fig = draw_fig1()
    return html.Div(
        [
            dcc.Markdown("""
                Welcome to **Cencyclopedia**!

                This website serves as a comprehensive and interactive catalog of human centromere genetic and epigenetic diversity in
                the 65 samples sequenced by the [Human Genome Structural Variation Consortium](https://www.hgsvc.org/).
            """),
            html.Hr(),
            dbc.Row(
                [
                    dbc.Col(
                        [dbc.Spinner(dcc.Graph(figure=fig, style={"height": "120vh"}))],
                        width=6,
                    ),
                    dbc.Col(
                        dbc.Spinner(
                            dcc.Graph(
                                figure=add_empty_track(go._figure.Figure(), (0, 1)),
                                id="fig-selected-cen-home",
                                responsive=True,
                                config={"displaylogo": False},
                                style={"height": "50vh"},
                            )
                        ),
                        width=6,
                    ),
                ]
            ),
        ]
    )
