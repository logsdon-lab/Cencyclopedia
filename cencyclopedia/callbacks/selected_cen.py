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
    Input("itv-selected-cen", "data"),
    Input("bed-track-settings", "data"),
    State("cfg", "data"),
    prevent_initial_call="initial_duplicate",
)
def draw_selected_cen_figure(
    itv_selected_cen: tuple[str, int, int] | None,
    bed_track_settings: dict[str, BedTrackSettings],
    cfg: dict[str, Any],
) -> go._figure.Figure:
    logger.debug(f"Draw update context: {ctx.triggered}")
    if not itv_selected_cen:
        raise PreventUpdate

    chrom, st, end = itv_selected_cen
    # Open tabix file handles
    data_fhs = Data.new(cfg["data"])

    props = []
    indices: dict[str, tuple[list[int], pl.DataFrame]] = {}

    # Add additional rows if expand. If overlap, must ignore.
    track_params = list(data_fhs.track_params)
    # Update index based on if want to expand
    idx_offset = 0
    for i, (label, idx, prop) in enumerate(track_params):
        track_settings = bed_track_settings[label]
        mode = track_settings["mode"]
        # Whether to run-length encode
        rle = data_fhs.options(label).get("rle", True)
        df = data_fhs.split(
            label,
            chrom,
            st,
            end,
            by=mode,
            to_relative=False,
            rle=rle,
            clip=True,
        ).sort(by="group")

        if mode == "Original":
            indices[label] = ([idx + idx_offset], df)
            if not prop:
                continue
            props.append(prop)
        else:
            # Overlap ignored if expanded. Force to take space.
            if not prop:
                prev_label, prev_idx, prev_prop = track_params[i - 1]
                prop = prev_prop
                idx = idx + 1

            # Split by all or a set limit.
            if track_settings["limit"] == "All":
                limit = df["group"].n_unique()
            else:
                limit = min(track_settings["limit"], df["group"].n_unique())

            split_indices = []
            for split_idx in range(limit + 1):
                props.append(prop)
                split_indices.append(idx + split_idx + idx_offset)

            idx_offset += limit
            indices[label] = (split_indices, df)

    logger.debug(f"Generating subplot with {len(props)} rows. Indices are: {indices}")

    fig: go._figure.Figure = make_subplots(
        rows=len(props),
        cols=1,
        shared_xaxes=True,
        row_heights=props,
        horizontal_spacing=0,
        vertical_spacing=cfg["general"]["hspace"],
    )

    for label, (indices, df) in indices.items():
        dtype = data_fhs.datatype(label)
        options = data_fhs.options(label)
        dfs_groups = list(df.group_by(["group"], maintain_order=True))
        # https://plotly.com/python/reference/layout/xaxis/
        update_xaxis_kwargs = options.get("xaxis_kwargs")
        update_yaxis_kwargs = options.get("yaxis_kwargs")

        for i, track_idx in enumerate(indices):
            # Remove title text before updating axes args
            try:
                yaxis_title = update_yaxis_kwargs.pop("title_text")
            except KeyError:
                yaxis_title = None

            if yaxis_title:
                fig.add_annotation(
                    x=cfg["general"]["ytitle_offset"],
                    y=0.5,
                    xref="x domain",
                    yref="y domain",
                    yanchor="middle",
                    text=yaxis_title,
                    showarrow=False,
                    row=track_idx,
                    col=1,
                )

            # Set range to start and end so legend axis ticks reach plot.
            fig.update_xaxes(
                **update_xaxis_kwargs, range=(st, end), row=track_idx, col=1
            )
            fig.update_yaxes(
                **update_yaxis_kwargs, row=track_idx, col=1, fixedrange=True
            )

            try:
                grp, df_grp = dfs_groups[i]
                grp = grp[0]
            except IndexError:
                add_empty_track(
                    fig,
                    xlim=(st, end),
                    row=track_idx,
                    col=1,
                )
                logger.debug(
                    f"Finished adding empty track for {label} on track {track_idx}"
                )
                continue

            if dtype == "bed" or dtype == "bed_localselfident":
                add_bed_track(
                    df_grp,
                    fig,
                    row=track_idx,
                    col=1,
                    shape=options.get("shape", "rect"),
                    invert=options.get("invert", True),
                    bp_slop=options.get("bp_slop", 0),
                )
            elif dtype == "bedgraph":
                add_bedgraph_track(df_grp, fig, row=track_idx, col=1)
            elif dtype == "bedstrand":
                add_bedstrand_track(df_grp, fig, row=track_idx, col=1)
            elif dtype == "bedpe_selfident":
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
        margin=dict(
            l=cfg["general"]["lmargin"],
            r=cfg["general"]["rmargin"],
            b=cfg["general"]["bmargin"],
            t=cfg["general"]["tmargin"],
        ),
        modebar_remove=["select2d", "lasso2d"],
    )

    return fig


@callback(
    Output("itv-selected-cen", "data", allow_duplicate=True),
    Output("dropdown-selected-cen", "value"),
    Input("fig-cens-tree", "clickData", allow_optional=True),
    Input("dropdown-selected-cen", "value"),
    State("itv-selected-cen", "data"),
    State("regions", "data"),
    prevent_initial_call=True,
)
def update_selected_cen(
    click_data: dict[str, Any] | None,
    dropdown_selected_cen: str,
    itv_selected_cen: tuple[str, int, int] | None,
    regions: str,
) -> (
    tuple[tuple[str, int, int], str]
    | tuple[dash._callback.NoUpdate, dash._callback.NoUpdate]
):
    logger.debug(f"Click update context: {ctx.triggered}")
    if dropdown_selected_cen != itv_selected_cen[0]:
        itv_selected_cen = (
            pl.scan_csv(regions)
            .filter(pl.col("chrom").eq(dropdown_selected_cen))
            .select("chrom", "chrom_st", "chrom_end")
            .collect()
            .row(0)
        )
        return itv_selected_cen, dropdown_selected_cen

    if not click_data:
        return dash.no_update, dash.no_update

    try:
        selected_cen = click_data["points"][0]["customdata"][0]
        itv_selected_cen = (
            pl.scan_csv(regions)
            .filter(pl.col("chrom").eq(selected_cen))
            .select("chrom", "chrom_st", "chrom_end")
            .collect()
            .row(0)
        )
    except KeyError as err:
        logger.debug(f"Error when accessing fields in {click_data}: {err}")
        return dash.no_update, dash.no_update

    return itv_selected_cen, selected_cen
