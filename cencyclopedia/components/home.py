import dash_bootstrap_components as dbc
from PIL import Image
from dash import dcc, html, get_asset_url


def home_page():
    path = get_asset_url(
        "260302_Fig1_CenOverview_piechartsonright_flipped_boldColors_updated.png"
    )
    return html.Div(
        [
            dbc.Col(
                [
                    dcc.Markdown("""
                Welcome to **Cencyclopedia**!

                This website serves as a comprehensive and interactive catalog of human centromere genetic and epigenetic diversity in
                the 65 samples sequenced by the [Human Genome Structural Variation Consortium](https://www.hgsvc.org/).
            """),
                    html.Img(src=Image.open(path), style={"height": "100vh"}),
                ]
            )
        ]
    )
