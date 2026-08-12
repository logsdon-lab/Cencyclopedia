import bisect
import polars as pl
import numpy as np
import plotly.graph_objs as go

from loguru import logger

from cencyclopedia.io.constants import IDENT_BREAKPOINTS, IDENT_COLORS


def assign_color_ident(ident: float, colorscale: list[list[float | str]]):
    breakpoints, colors = zip(*colorscale)
    try:
        idx_end = bisect.bisect(breakpoints, ident)
        if idx_end == 0:
            color = colors[0]
        else:
            color = colors[idx_end - 1]
    except IndexError:
        _, color = colorscale[-1]

    return color


def format_colorscale(
    breakpoints: list[float],
    colors: list[str],
) -> list[tuple[float, str]]:
    assert len(breakpoints) == len(colors)
    brkpts = list(zip(breakpoints, colors))
    final_brkpts = []
    for i, (brk, color) in enumerate(brkpts):
        idx = i - 1
        if idx == -1:
            prev = 0.0
        else:
            prev, _ = brkpts[i - 1]
        final_brkpts.append(tuple([prev / 100.0, color]))
        final_brkpts.append(tuple([brk / 100.0, color]))

    # Add final
    _, final_color = brkpts[-1]
    final_brkpts.append(tuple([1.0, final_color]))
    return final_brkpts


# Adapted from https://github.com/Zikun-Yang/VAMPIRE/blob/dev/src/vampire/pl/_plot.py
def add_heatmap_track(
    data: pl.DataFrame,
    fig: go._figure.Figure,
    row: int,
    col: int,
    zmin: float = 0.0,
    zmax: float = 100.0,
    colorscale: list[tuple[float, str]] | None = None,
    flip_y: bool = True,
) -> None:
    """
    Plot a triangular heatmap track on the figure.

    Parameters
    ----------
    fig : go.Figure
        The Plotly figure object to add the heatmap to.
    data : pl.DataFrame
        Polars DataFrame containing heatmap data with columns: qry, qry_st, qry_end,
        ref, ref_st, ref_end, and percent_identity_by_events.
    row : int
        Subplot row number (1-indexed) where the heatmap should be added.
    col : int
        Subplot col number (1-indexed) where the heatmap should be added.
    min_value : float
        Min identity. Must match first value in colorscale.
    max_value : float
        Max identity.
    colorscale : list[tuple[float, str]]
        Colorscale identity breakpoints
    flip_y : bool
        Flip triangle.

    Returns
    -------
    None
        The function modifies the figure in-place.
    """
    data = data.filter(
        (data["percent_identity_by_events"] >= zmin)
        & (data["percent_identity_by_events"] <= zmax)
    )
    if data.height == 0:
        return

    # prepare colorscale
    if not colorscale:
        colorscale = format_colorscale(list(IDENT_BREAKPOINTS), list(IDENT_COLORS))

    logger.debug(f"Using colorscale: {colorscale}")

    # build bins
    bins = (
        pl.concat(
            [
                data.select(
                    [pl.col("qry_st").alias("start"), pl.col("qry_end").alias("end")]
                ),
                data.select(
                    [pl.col("ref_st").alias("start"), pl.col("ref_end").alias("end")]
                ),
            ]
        )
        .unique()
        .sort("start")
        .with_row_index("idx")
    )

    bin_starts = bins["start"].to_numpy()
    bin_ends = bins["end"].to_numpy()
    bin_centers = (bin_starts + bin_ends) / 2

    # join i/j
    data = data.join(
        bins.rename({"start": "qry_st", "idx": "i"}), on="qry_st", how="left"
    ).join(bins.rename({"start": "ref_st", "idx": "j"}), on="ref_st", how="left")

    i = data["i"].to_numpy()
    j = data["j"].to_numpy()
    v = data["percent_identity_by_events"].to_numpy()

    x1 = bin_centers[i]
    x2 = bin_centers[j]

    # compute rotated triangle coordinates
    xp = (x1 + x2) / 2
    yp = (x2 - x1) / 2

    mask = yp >= 0
    xp = xp[mask]
    yp = yp[mask]
    v = v[mask]

    if len(xp) == 0:
        return

    # compute resolution
    resolution = int(np.median(np.diff(np.sort(bin_centers))))
    if resolution <= 0:
        resolution = 1

    # build grid
    x_min, x_max = xp.min(), xp.max()
    y_min, y_max = 0, yp.max()
    x_bins = np.arange(x_min, x_max + resolution, resolution)
    y_bins = np.arange(y_min, y_max + resolution, resolution)

    z_vals = np.zeros((len(y_bins), len(x_bins)), dtype=np.float32)
    counts = np.zeros_like(z_vals, dtype=np.int32)

    # compute floor index
    x_idx = np.floor((xp - x_min) / resolution).astype(int)
    y_idx = np.floor((yp - y_min) / resolution).astype(int)

    valid = (x_idx >= 0) & (x_idx < len(x_bins)) & (y_idx >= 0) & (y_idx < len(y_bins))

    # accumulate and count
    np.add.at(z_vals, (y_idx[valid], x_idx[valid]), v[valid])
    np.add.at(counts, (y_idx[valid], x_idx[valid]), 1)

    # compute average value and NaN
    mask_nonzero = counts > 0
    z_vals[mask_nonzero] /= counts[mask_nonzero]

    # output frequency of values with 2 or more counts (normal situation)
    if np.any(counts[mask_nonzero] > 1):
        frequency = np.sum(counts[mask_nonzero] > 1) / len(counts[mask_nonzero])
        logger.debug(f"Some cells have 2 or more values: {frequency:.3%}")

    z_vals[~mask_nonzero] = np.nan

    # add trace
    invert = -1 if flip_y else 1
    fig.add_trace(
        go.Heatmap(
            x=x_bins,
            y=y_bins * invert,
            z=z_vals,
            colorscale=colorscale,
            zmin=zmin,
            zmax=zmax,
            showscale=False,
            hovertemplate="Position: %{x}<br>Y: %{y}<br>Identity: %{z}%<extra></extra>",
            colorbar=dict(
                orientation="h",  # horizontal
                x=0.5,
                xanchor="center",
                y=-0.1 - 0.1 * row,
                len=1,
            ),
        ),
        row=row,
        col=col,
    )
    fig.update_yaxes(
        # Maintains aspect ratio when scaling figure.
        scaleanchor=f"x{row}",
        constrain="domain",
        ## If need to adjust, move up rather than to middle.
        constraintoward="top",
        row=row,
        col=col,
    )
