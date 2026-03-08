import bisect
import polars as pl

from typing import Any


def read_bedgraph_row(rec: Any):
    return (rec.contig, rec.start, rec.end, rec.name)


def read_bedstrand_row(rec: Any):
    try:
        item_rgb = rec.itemRGB
    except KeyError:
        item_rgb = "#000000"
    return (rec.contig, rec.start, rec.end, rec.strand, item_rgb)


def read_bed9_row(rec: Any):
    try:
        name = rec.name
    except KeyError:
        name = "."
    try:
        item_rgb = rec.itemRGB
    except KeyError:
        item_rgb = "#000000"
    return (rec.contig, rec.start, rec.end, name, item_rgb)


def read_bed_local_selfident_row(
    rec: tuple[str, str, str, str],
    breakpoints: list[float],
    colors: list[str],
) -> tuple[str, int, int, float, str]:
    chrom, chrom_st, chrom_end, ident = rec
    chrom_st = int(chrom_st)
    chrom_end = int(chrom_end)
    ident = float(ident)
    if ident == 0.0:
        color = colors[0]
        return (chrom, chrom_st, chrom_end, ident, color)
    try:
        idx_end = bisect.bisect(breakpoints, ident)
        if idx_end == 0:
            color = colors[0]
        else:
            color = colors[idx_end - 1]
    except IndexError:
        color = colors[-1]

    return (chrom, chrom_st, chrom_end, ident, color)


def to_relative_coords_bed(df: pl.DataFrame):
    return df.with_columns(
        pl.col("chrom_st") - pl.col("chrom_st").min().over("chrom"),
        pl.col("chrom_end") - pl.col("chrom_st").min().over("chrom"),
    )
