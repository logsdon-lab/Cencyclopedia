import dash
import polars as pl
import plotly.graph_objs as go

from typing import Any
from loguru import logger
from plotly.subplots import make_subplots
from dash import Input, Output, callback, ctx, State
from dash.exceptions import PreventUpdate

from cencyclopedia.io.data import Data
from cencyclopedia.plot.common import BedTrackSettings, add_empty_track
from cencyclopedia.plot.ident import add_ident_track
from cencyclopedia.plot.bed import (
    add_bed_track,
    add_bedgraph_track,
    add_bedstrand_track,
)


@callback(
    Output("fig-selected-cen", "figure"),
    Output("dropdown-selected-cen", "value"),
    Output("selected-cen-stale", "data", allow_duplicate=True),
    Input("selected-cen", "data"),
    Input("selected-cen-stale", "data"),
    State("regions", "data"),
    State("cfg", "data"),
    State("bed-track-settings", "data"),
    prevent_initial_call="initial_duplicate",
)
def draw_selected_cen_figure(
    selected_cen: str | None,
    stale: bool,
    regions: str,
    cfg: dict[str, Any],
    bed_track_settings: dict[str, BedTrackSettings],
):
    logger.debug(f"{ctx.triggered}, {stale}")
    if not selected_cen or not stale:
        raise PreventUpdate

    df_region = (
        pl.scan_csv(regions)
        .filter(pl.col("chrom").eq(selected_cen) & pl.col("arm").eq(pl.lit("q")))
        .collect()
    )
    if df_region.is_empty():
        raise ValueError(f"Invalid selected_cen: {selected_cen}")

    # Open tabix file handles
    data_fhs = Data.new(cfg["data"])

    region = df_region.row(0, named=True)
    props = []
    indices = {}

    # Add additional rows if expand. If overlap, must ignore.
    track_params = list(data_fhs.track_params)
    # Update index based on if want to expand
    idx_offset = 0
    for i, (label, idx, prop) in enumerate(track_params):
        track_settings = bed_track_settings[label]
        mode = track_settings["mode"]
        if mode == "Original":
            indices[label] = [idx + idx_offset]
            if not prop:
                continue
            props.append(prop)
        else:
            # Overlap ignored if expanded. Force to take space.
            if not prop:
                prev_label, prev_idx, prev_prop = track_params[i - 1]
                prop = prev_prop

            split_indices = []
            for split_idx in range(track_settings["limit"]):
                props.append(prop)
                split_indices.append(idx + split_idx + idx_offset)

            idx_offset += track_settings["limit"] - 1
            indices[label] = split_indices

    logger.debug(f"Generating subplot with {len(props)} rows. Indices are: {indices}")

    fig: go._figure.Figure = make_subplots(
        rows=len(props), cols=1, shared_xaxes=True, row_heights=props
    )

    for label, indices in indices.items():
        dtype = data_fhs.datatype(label)
        track_settings = bed_track_settings[label]
        mode = track_settings["mode"]

        df = data_fhs.split(
            label,
            region["chrom"],
            region["chrom_st"],
            region["chrom_end"],
            by=mode,
            to_relative=False,
        ).sort(by="group")

        # TODO: Split if expand
        dfs_groups = list(df.group_by(["group"], maintain_order=True))
        for i, track_idx in enumerate(indices):
            try:
                grp, df_grp = dfs_groups[i]
                grp = grp[0]
            except IndexError:
                add_empty_track(
                    fig,
                    xlim=(region["chrom_st"], region["chrom_end"]),
                    row=track_idx,
                    col=1,
                )
                logger.debug(
                    f"Finished adding empty track for {label} (Group {grp}) on track {track_idx}"
                )
                continue

            if dtype == "bed" or dtype == "bed_localselfident":
                add_bed_track(df_grp, fig, row=track_idx, col=1)
            elif dtype == "bedgraph":
                add_bedgraph_track(df_grp, fig, row=track_idx, col=1)
            elif dtype == "bedstrand":
                add_bedstrand_track(df_grp, fig, row=track_idx, col=1)
            elif dtype == "bedpe_selfident":
                # https://plotly.com/python/heatmaps/#display-an-xarray-image-with-pximshow
                # img_mdp = add_ident_track(df)
                add_ident_track(df_grp, fig, row=track_idx, col=1)
            else:
                logger.debug(
                    f"Ignoring {label} (Group {grp}) of type {dtype} at index of {track_idx}"
                )

            logger.debug(f"Finished adding {label} (Group {grp}) on track {track_idx}")

    fig.update_layout(
        template="simple_white",
        xaxis={"showgrid": False},
        yaxis={"showgrid": False},
        margin=dict(l=0, r=0, b=0, t=0),
    )
    # https://plotly.com/python/reference/layout/xaxis/
    fig.update_xaxes(showline=False)
    fig.update_yaxes(showticklabels=False, ticks="", showline=False)
    # No longer stale.
    return fig, selected_cen, False


@callback(
    Output("selected-cen", "data", allow_duplicate=True),
    Output("selected-cen-stale", "data", allow_duplicate=True),
    Input("url", "pathname"),
    Input("fig-cens-clade-ordered", "clickData", allow_optional=True),
    Input("dropdown-selected-cen", "value"),
    State("selected-cen", "data"),
    State("regions", "data"),
    State("cfg", "data"),
    prevent_initial_call=True,
)
def update_selected_cen_by_click(
    pathname: str,
    data: dict[str, Any] | None,
    dropdown_selected_cen: str,
    selected_cen: str,
    regions: str,
    cfg: dict[str, Any],
):
    selected_cen_different = dropdown_selected_cen != selected_cen
    # Select via dropdown
    if selected_cen_different:
        return dropdown_selected_cen, True
    if not data and not selected_cen_different:
        raise PreventUpdate

    chrom = pathname.strip("/")
    click_data = data["points"][0]
    y = click_data["y"]

    df_regions_chrom = (
        pl.scan_csv(regions)
        .filter(pl.col("chrom_name").eq(chrom) & pl.col("arm").eq(pl.lit("p")))
        .sort(by=["clade"])
        .collect()
    )
    chroms = df_regions_chrom["chrom"]
    y = abs(y)
    yst = cfg["tree_ystart"]
    yoffset = cfg["tree_yoffset"]

    idx = round((y - yst) / yoffset)
    logger.debug(f"Clicked y-pos, {y}, corresponding to index {idx}")
    try:
        chrom = chroms[idx]
    except IndexError:
        logger.debug(f"Invalid chrom index {idx}/{len(chroms)}")
        raise PreventUpdate
    return chrom, True
