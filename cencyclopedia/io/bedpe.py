import polars as pl

from .constants import IDENT_BREAKPOINTS, IDENT_COLORS


def read_identity_breakpoints(
    infile: str | None,
) -> tuple[tuple[float, ...], tuple[str, ...]]:
    if not infile:
        return IDENT_BREAKPOINTS, IDENT_COLORS

    pair_idents_colors: list[tuple[float, str]] = []
    with open(infile, "rt") as fh:
        for line in fh:
            ident, hexcode_color = line.strip().split("\t")
            pair_idents_colors.append((float(ident), hexcode_color))

    assert len(pair_idents_colors) > 0, "Need at least one identity breakpoint"
    pair_idents_colors.sort(key=lambda x: x[0])

    idents, colors = zip(*pair_idents_colors)
    assert len(idents) == len(colors), (
        "Identity breakpoints and colors must be equal length. "
        "This is different from ModDotPlot in that the each breakpoint is the ending identity. "
        "ex. 80, 90, 100 -> (0-80), (80-90), (90-100)"
    )
    return idents, colors


def read_bedpe_selfident_row(
    rec: tuple[str, str, str, str, str, str, str],
    breakpoints: list[float],
    colors: list[str],
) -> tuple[str, int, int, str, int, int, float, str, str]:
    qry, qry_st, qry_end, ref, ref_st, ref_end, ident = rec
    qry_st = int(qry_st)
    qry_end = int(qry_end)
    ref_st = int(ref_st)
    ref_end = int(ref_end)
    ident = float(ident)
    if ident == 0.0:
        color = colors[0]
        desc = str(ident_end)
        # return (qry, qry_st, qry_end, ref, ref_st, ref_end, ident)
        return (qry, qry_st, qry_end, ref, ref_st, ref_end, ident, color, desc)
    try:
        idx_end = bisect.bisect(breakpoints, ident)
        ident_end = breakpoints[idx_end]
        if idx_end == 0:
            ident_st = 0.0
            color = colors[0]
        else:
            ident_st = breakpoints[idx_end - 1]
            color = colors[idx_end - 1]
        desc = f"{ident_st}%-{ident_end}%"
    except IndexError:
        ident_end = breakpoints[-1]
        color = colors[-1]
        desc = str(ident_end)

    # return (qry, qry_st, qry_end, ref, ref_st, ref_end, ident)
    return (qry, qry_st, qry_end, ref, ref_st, ref_end, ident, color, desc)


def to_relative_coords_bedpe_selfident(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.col("qry_st") - pl.col("qry_st").min().over("qry"),
        pl.col("qry_end") - pl.col("qry_st").min().over("qry"),
        pl.col("ref_st") - pl.col("ref_st").min().over("ref"),
        pl.col("ref_end") - pl.col("ref_st").min().over("ref"),
    )
