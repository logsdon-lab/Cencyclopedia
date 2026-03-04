import yaml
import numpy as np
import polars as pl
import plotly.graph_objs as go
import dash_bootstrap_components as dbc

from PIL import Image
from typing import Any
from loguru import logger
from plotly.subplots import make_subplots
from dash import Dash, Input, Output, callback, dcc, html
from dash.exceptions import PreventUpdate

from cencyclopedia.io.read_cfg_data import read_regions, Data
from cencyclopedia.plot.ident import add_ident_track
from cencyclopedia.plot.image import add_image_to_figure
from cencyclopedia.plot.bed import (
    add_bed_track,
    add_bedgraph_track,
    add_bedstrand_track,
)
from cencyclopedia.components.layout import layout, create_content_layout


with open("config.yaml", "rb") as fh:
    cfg = yaml.safe_load(fh)

df_regions = read_regions(cfg)

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Cencyclopedia",
)
app.layout = layout(
    chrom_names=df_regions["chrom_name"].unique().sort().to_list(),
)


@callback(
    Output("fig-selected-cen", "figure"),
    Output("fig-selected-cen-mdp", "src"),
    Input("selected-cen", "data"),
)
def draw_selected_cen(selected_cen: str | None):
    if not selected_cen:
        raise PreventUpdate

    df_region = df_regions.filter(
        pl.col("chrom").eq(selected_cen) & pl.col("arm").eq(pl.lit("q"))
    )
    if df_region.is_empty():
        raise ValueError(f"Invalid selected_cen: {selected_cen}")

    # Open tabix file handles
    data_fhs = Data.new(cfg["data"])

    region = df_region.row(0, named=True)
    props = []
    nrows = 0
    indices = {}
    for dtype, idx, prop in data_fhs.track_params:
        indices[dtype] = idx
        if not prop:
            continue
        nrows += 1
        props.append(prop)

    fig: go._figure.Figure = make_subplots(
        rows=nrows, cols=1, shared_xaxes=True, row_heights=props
    )

    img_mdp = None
    for label, idx in indices.items():
        df = data_fhs.query(
            label,
            region["chrom"],
            region["chrom_st"],
            region["chrom_end"],
            to_relative=False,
        )
        dtype = data_fhs.datatype(label)
        if dtype == "bed":
            add_bed_track(df, fig, row=idx, col=1)
        elif dtype == "bedgraph":
            add_bedgraph_track(df, fig, row=idx, col=1)
        elif dtype == "bedstrand":
            add_bedstrand_track(df, fig, row=idx, col=1)
        elif dtype == "bedpe_selfident":
            # https://plotly.com/python/heatmaps/#display-an-xarray-image-with-pximshow
            img_mdp = add_ident_track(df)
        else:
            logger.debug(f"Ignoring {label} of type {dtype} at index of {idx}")

        logger.debug(f"Finished adding {label} on track {idx}")

    fig.update_layout(
        template="simple_white",
        xaxis={"showgrid": False},
        yaxis={"showgrid": False},
        margin=dict(l=0, r=0, b=0, t=0),
    )
    # https://plotly.com/python/reference/layout/xaxis/
    fig.update_xaxes(showline=False)
    fig.update_yaxes(showticklabels=False, ticks="", showline=False)
    return fig, img_mdp


@callback(
    Output("col-chrom-content", "children"),
    Input("url", "pathname"),
)
def select_chrom_page(pathname: str):
    page = pathname.strip("/")
    if not page:
        return dcc.Markdown("""
            Welcome to **Cencyclopedia**!

            This website serves as a comprehensive and interactive catelog of human centromere genetic and epigenetic diversity in
            the 65 samples sequenced by the [Human Genome Structural Variation Consortium](https://www.hgsvc.org/).

            If you use this tool in your work, please cite:

            * *Gao S, Oshima KK, Chuang SC, Loftus M, Montanari A, Gordon DS, Human Genome Structural Variation Consortium, Human Pangenome Reference Consortium, Hsieh P, Konkel MK, Ventura M, Logsdon GA. A global view of human centromere variation and evolution. bioRxiv. 2025. p. 2025.12.09.693231. [doi:10.64898/2025.12.09.693231](https://doi.org/10.64898/2025.12.09.693231)*
        """)
    else:
        return get_fig_cens_components(chrom=page)


@callback(
    Output("selected-cen", "data"),
    Output("dropdown-selected-cen", "value"),
    Input("url", "pathname"),
    Input("fig-cens-clade-ordered", "clickData", allow_optional=True),
    prevent_initial_call=True,
)
def update_selected_cen_by_click(pathname: str, data: dict[str, Any] | None):
    if not data:
        raise PreventUpdate

    chrom = pathname.strip("/")
    click_data = data["points"][0]
    y = click_data["y"]
    df_regions_chrom = df_regions.filter(
        pl.col("chrom_name").eq(chrom) & pl.col("arm").eq(pl.lit("p"))
    ).sort(by=["clade"])
    chroms = df_regions_chrom["chrom"]
    y = abs(y)
    yst = cfg["tree_ystart"]
    yoffset = cfg["tree_yoffset"]

    idx = round((y - yst) / yoffset)
    logger.debug(f"Clicked y-pos, {y}, corresponding to {idx}")
    try:
        chrom = chroms[idx]
    except IndexError:
        logger.debug(f"Invalid chrom index {idx}/{len(chroms)}")
        raise PreventUpdate
    return chrom, chrom


def get_fig_cens_components(chrom: str) -> html.Div:
    logger.debug(f"On {chrom}")
    if not chrom:
        return []

    df_regions_chrom = df_regions.filter(
        pl.col("chrom_name").eq(chrom) & pl.col("arm").eq(pl.lit("p"))
    ).sort(by=["clade"])

    chroms = df_regions_chrom["chrom"]
    try:
        image_tree = cfg.get("trees", {})[f"{chrom}_p"]
        img = Image.open(image_tree)
    except (OSError, KeyError) as err:
        logger.error(f"Cannot open image for {chrom} p tree")
        raise PreventUpdate

    fig = go._figure.Figure()
    fig = add_image_to_figure(img, fig)

    # Origin in top-left so y-coords are negative.
    yst = -cfg["tree_ystart"]
    yoffset = cfg["tree_yoffset"]
    ypos = np.cumsum([yoffset for i in range(len(chroms))])
    ypos *= -1
    ypos += yst
    fig.add_scatter(
        x=[img.width - 100.0] * len(ypos),
        y=[yst, *ypos],
        customdata=chroms,
        hovertemplate="<b>%{customdata}</b>",
        mode="markers",
    )
    fig.update_layout(
        showlegend=False,
        template="simple_white",
        xaxis={"showgrid": False, "fixedrange": True},
        yaxis={"showgrid": False, "fixedrange": True},
        margin=dict(l=0, r=0, b=0, t=0),
    )

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


if __name__ == "__main__":
    app.run(debug=True)
