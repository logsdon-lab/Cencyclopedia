import bisect
import polars as pl

from typing import Any

BED_SCHEMA = {
    "chrom": pl.String,
    "chrom_st": pl.UInt64,
    "chrom_end": pl.UInt64,
    "name": pl.String,
    "color": pl.String,
    "score": pl.Float64,
}

BEDGRAPH_SCHEMA = {
    "chrom": pl.String,
    "chrom_st": pl.UInt64,
    "chrom_end": pl.UInt64,
    "name": pl.Float32,
}

BEDPE_SCHEMA = {
    "qry": pl.String,
    "qry_st": pl.UInt64,
    "qry_end": pl.UInt64,
    "ref": pl.String,
    "ref_st": pl.UInt64,
    "ref_end": pl.UInt64,
    "percent_identity_by_events": pl.Float32,
}


def into_hexcode(s: Any) -> str:
    if not isinstance(s, str):
        return "#000000"
    # https://stackoverflow.com/a/3380739
    if s.startswith("#"):
        return s
    else:
        channels = s.split(",")
        if len(channels) != 3:
            return "#000000"
        return "#%02x%02x%02x" % tuple(int(v) for v in channels)


def read_bedgraph_row(rec: tuple[Any, ...]) -> tuple[str, int, int, str]:
    return (rec[0], rec[1], rec[2], rec[3])


def read_bigwig_row(rec: Any, chrom: str) -> tuple[str, int, int, int]:
    try:
        value = rec[2]
    except IndexError:
        value = 0
    return (chrom, rec[0], rec[1], value)


def read_bedstrand_row(rec: Any) -> tuple[str, int, int, str, str, int]:
    try:
        item_rgb = rec[8]
    except IndexError:
        item_rgb = "#000000"
    try:
        score = rec[4]
    except IndexError:
        score = 0
    return (rec[0], rec[1], rec[2], rec[5], item_rgb, score)


def read_bedn_row(rec: Any) -> tuple[str, int, int, str, str, int]:
    try:
        name = rec[3]
    except IndexError:
        name = "."

    try:
        item_rgb = into_hexcode(rec[8])
    except IndexError:
        item_rgb = "#000000"
    try:
        score = rec[4]
    except IndexError:
        score = 0

    contig = rec[0]
    start = rec[1]
    end = rec[2]
    return (contig, start, end, name, item_rgb, score)


def read_bigbed_row(rec: Any, chrom: str) -> tuple[str, int, int, str, str, int]:
    try:
        name = rec[2]
    except IndexError:
        name = "."
    try:
        item_rgb = into_hexcode(rec[7])
    except IndexError:
        item_rgb = "#000000"
    try:
        score = rec[3]
    except IndexError:
        score = 0
    return (chrom, rec[0], rec[1], name, item_rgb, score)


def read_bed_local_selfident_row(
    rec: tuple[str, str, str, str],
    breakpoints: list[float],
    colors: list[str],
) -> tuple[str, int, int, str, str, float]:
    chrom, chrom_st, chrom_end, ident = rec
    chrom_st = int(chrom_st)
    chrom_end = int(chrom_end)
    ident = float(ident)
    if ident == 0.0:
        color = colors[0]
        label = f"0.0-{breakpoints[0]}"
        return (chrom, chrom_st, chrom_end, label, color, ident)
    try:
        idx_end = bisect.bisect(breakpoints, ident)
        if idx_end == 0:
            color = colors[0]
            label = f"0.0-{breakpoints[0]}"
        else:
            color = colors[idx_end - 1]
            label = f"{breakpoints[idx_end - 1]}-{breakpoints[idx_end]}"
    except IndexError:
        color = colors[-1]
        label = str(breakpoints[-1])

    return (chrom, chrom_st, chrom_end, label, color, ident)


def to_relative_coords_bed(df: pl.DataFrame, min_st: int | None) -> pl.DataFrame:
    if min_st:
        min_st_expr: pl.Expr = pl.lit(min_st)
    else:
        min_st_expr = pl.col("chrom_st").min().over("chrom")
    return df.with_columns(
        pl.col("chrom_st") - min_st_expr,
        pl.col("chrom_end") - min_st_expr,
    )
