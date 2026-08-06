import polars as pl
import plotly.graph_objs as go

from PIL.Image import Image
from cencyclopedia.plot.image import add_image_to_figure


def draw_fig1(img: Image, df_fig1_bboxes: pl.DataFrame) -> go._figure.Figure:
    fig = go._figure.Figure()
    fig = add_image_to_figure(img, fig)

    # Figure 1 bboxes around centromeres
    for row in df_fig1_bboxes.iter_rows(named=True):
        chrom = row["chrom"]
        desc = f"Contig: {chrom}<br>Continental Group: {row['continental_group']}<br>Sex: {row['sex']}"
        # ChrY CHM1 has none so skip
        if not row["ypos_st"]:
            continue

        x0, x1 = row["xpos_st"], row["xpos_end"]
        y0, y1 = -row["ypos_st"], -row["ypos_end"]
        # Add rect [x_left_bottom, x_left_top, x_right_bottom, x_right_top, x_left_bottom]
        #          [y_left_bottom, y_left_top, y_right_top, y_right_bottom, y_left_bottom]
        fig.add_scatter(
            x=[x0, x0, x1, x1, x0],
            y=[y0, y1, y1, y0, y0],
            fill="toself",
            fillcolor=row["color"],
            opacity=0,
            customdata=[chrom],
            hoverlabel=dict(bgcolor=row["color"], font_color="white"),
            line=dict(color=row["color"]),
            marker=dict(color=row["color"]),
            hovertemplate=desc,
            name=desc,
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
