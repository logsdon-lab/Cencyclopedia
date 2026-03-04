import PIL
import polars as pl
import matplotlib.pyplot as plt
import plotly.graph_objs as go

from cenplot import Track, TrackType, TrackPosition, draw_self_ident, read_bed_identity
from tempfile import NamedTemporaryFile

from .image import add_image_to_figure


def add_ident_image_track(df_ident: pl.DataFrame) -> PIL.ImageFile:
    fig = go._figure.Figure()
    with NamedTemporaryFile("wt") as fh:
        df_ident.write_csv(fh.name, separator="\t", include_header=False)
        df_ident, colorscale = read_bed_identity(fh.name)

    track = Track(
        title=None,
        pos=TrackPosition.Relative,
        opt=TrackType.SelfIdent,
        prop=1.0,
        data=df_ident,
        options=TrackType.settings(TrackType.SelfIdent),
    )
    mpl_fig, mpl_ax = plt.subplots(layout="constrained", figsize=(16, 8))
    draw_self_ident(mpl_ax, track)
    mpl_ax.set_xlim(df_ident["x"].min(), df_ident["x"].max())
    mpl_ax.margins(x=0, y=0)
    img = "/tmp/mdp.png"
    mpl_fig.savefig(img, bbox_inches="tight", dpi=600)

    pil_image = PIL.Image.open(img)
    return add_image_to_figure(pil_image, fig)   


def add_ident_track(df_ident: pl.DataFrame, fig: go._figure.Figure, **kwargs):
    # https://plotly.github.io/plotly.py-docs/generated/plotly.graph_objects.Heatmap.html
    # https://github.com/marbl/ModDotPlot/blob/a2268ee0a92f4bc2a06851ccb817bb170a7af7d9/src/moddotplot/interactive.py#L124
    for row in df_ident.iter_rows(named=True):
        """
        ref_end  *        *

        ref_st   *        *
                 qry_st   qry_end
        """
        # "qry", "qry_st", "qry_end", "ref", "ref_st", "ref_end", "percent_identity_by_events", "color", "desc"
        fig.add_scattergl(
            x=[
                row["qry_st"],
                row["qry_end"],
                row["qry_end"],
                row["qry_st"],
                row["qry_st"],
            ],
            y=[
                # 0, 0, 1, 1, 0
                row["ref_st"],
                row["ref_end"],
                row["ref_end"],
                row["ref_st"],
                row["ref_st"],
            ],
            fill="toself",
            line=dict(
                color=row["color"],
                width=2,
            ),
            # # https://stackoverflow.com/a/71222010
            mode="lines",
            fillcolor=row["color"],
            name=f"{row['percent_identity_by_events']}, ({row['desc']})",
            showlegend=False,
            **kwargs,
        )
