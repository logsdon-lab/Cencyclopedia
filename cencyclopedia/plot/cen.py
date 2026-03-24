import polars as pl
import plotly.graph_objs as go

from typing import Any
from loguru import logger
from plotly.subplots import make_subplots

from cencyclopedia.io.data import Data
from cencyclopedia.plot.common import (
    BedTrackSettings,
    add_empty_track,
    default_bed_track_settings,
)
from cencyclopedia.plot.ident import add_heatmap_track
from cencyclopedia.plot.bed import (
    add_bed_track,
    add_bedgraph_track,
    add_bedstrand_track,
)


def draw_cenplot(
    itv_selected_cen: tuple[str, int, int] | None,
    bed_track_settings: dict[str, BedTrackSettings] | None,
    cfg: dict[str, Any],
    *,
    to_relative: bool = False,
) -> tuple[go._figure.Figure, dict[str, Any]] | None:
    if not itv_selected_cen:
        return None
    if not bed_track_settings:
        bed_track_settings = {}

    chrom, st, end = itv_selected_cen
    # Open tabix file handles
    data_fhs = Data.new(cfg["data"])

    props = []
    total_original_prop = 0.0
    indices: dict[str, tuple[list[int], pl.DataFrame]] = {}

    # Add additional rows if expand. If overlap, must ignore.
    track_params = list(data_fhs.track_params)
    # Update index based on if want to expand
    idx_offset = 0
    for i, (label, idx, prop) in enumerate(track_params):
        track_settings = bed_track_settings.get(label, default_bed_track_settings())
        mode = track_settings["mode"]
        # Whether to run-length encode
        rle = data_fhs.options(label).get("rle", True)
        dtype = data_fhs.datatype(label)
        if dtype == "bedpe_selfident":
            df = data_fhs.query(
                label, chrom, st, end, to_relative=to_relative
            ).with_columns(group=pl.lit(0))
        else:
            df = data_fhs.split(
                label,
                chrom,
                st,
                end,
                by=mode,
                to_relative=to_relative,
                rle=rle,
                clip=True,
            ).sort(by="group")

        if prop:
            total_original_prop += prop

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
    )

    # Adjust height
    style = {"height": cfg["general"]["selected_cen"]["height"]}
    if isinstance(cfg["general"]["selected_cen"]["height"], int):
        ht_adj_ratio = sum(props) / total_original_prop
        style["height"] = cfg["general"]["selected_cen"]["height"] * ht_adj_ratio

    idx_yaxis_titles = {}
    for label, (indices, df) in indices.items():
        dtype = data_fhs.datatype(label)
        options = data_fhs.options(label)
        dfs_groups = list(df.group_by(["group"], maintain_order=True))
        # https://plotly.com/python/reference/layout/xaxis/
        update_xaxis_kwargs = options.get("xaxis_kwargs", {})
        update_yaxis_kwargs = options.get("yaxis_kwargs", {})

        for i, track_idx in enumerate(indices):
            # Remove title text before updating axes args
            try:
                yaxis_title = update_yaxis_kwargs.pop("title_text")
            except KeyError:
                yaxis_title = None

            # Only plot first.
            if yaxis_title and not idx_yaxis_titles.get(track_idx):
                fig.add_annotation(
                    x=0,
                    y=0.5,
                    valign="middle",
                    xref="x domain",
                    axref="x domain",
                    yref="y domain",
                    ayref="y domain",
                    xanchor="right",
                    yanchor="middle",
                    borderpad=20,
                    text=yaxis_title,
                    showarrow=False,
                    row=track_idx,
                    col=1,
                )
                idx_yaxis_titles[track_idx] = yaxis_title

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
                add_heatmap_track(df_grp, fig, row=track_idx, col=1)
            else:
                logger.debug(
                    f"Ignoring {label} (Group {grp}) of type {dtype} at index of {track_idx}"
                )

            # Set range to start and end so legend axis ticks reach plot.
            fig.update_xaxes(
                **update_xaxis_kwargs, range=(st, end), row=track_idx, col=1
            )
            fig.update_yaxes(
                **update_yaxis_kwargs, row=track_idx, col=1, fixedrange=True
            )

            logger.debug(f"Finished adding {label} (Group {grp}) on track {track_idx}")

    fig.update_layout(
        template="simple_white",
        xaxis={"showgrid": False},
        yaxis={"showgrid": False},
        margin=dict(
            l=cfg["general"]["selected_cen"]["lmargin"],
            r=cfg["general"]["selected_cen"]["rmargin"],
            b=cfg["general"]["selected_cen"]["bmargin"],
            t=cfg["general"]["selected_cen"]["tmargin"],
        ),
        modebar_remove=["select2d", "lasso2d"],
    )

    return fig, style
