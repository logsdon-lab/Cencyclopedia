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
) -> tuple[str, int, int, str, int, int, float]:
    qry, qry_st, qry_end, ref, ref_st, ref_end, ident = rec
    qry_st = int(qry_st)
    qry_end = int(qry_end)
    ref_st = int(ref_st)
    ref_end = int(ref_end)
    ident = float(ident)
    return (qry, qry_st, qry_end, ref, ref_st, ref_end, ident)


def to_relative_coords_bedpe_selfident(
    df: pl.DataFrame, min_st: int | None
) -> pl.DataFrame:
    if min_st:
        min_st_ref = pl.lit(min_st)
        min_st_qry = pl.lit(min_st)
    else:
        min_st_ref = pl.col("ref_st").min().over("ref")
        min_st_qry = pl.col("qry_st").min().over("qry")

    return df.with_columns(
        pl.col("qry_st") - min_st_qry,
        pl.col("qry_end") - min_st_qry,
        pl.col("ref_st") - min_st_ref,
        pl.col("ref_end") - min_st_ref,
    )
