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
    "color": pl.String,
    "desc": pl.String,
}


def read_bedgraph_row(rec: Any):
    return (rec.contig, rec.start, rec.end, rec.name)


def read_bedstrand_row(rec: Any):
    try:
        item_rgb = rec.itemRGB
    except KeyError:
        item_rgb = "#000000"
    try:
        score = rec.score
    except KeyError:
        score = 0
    return (rec.contig, rec.start, rec.end, rec.strand, item_rgb, score)


def read_bed9_row(rec: Any):
    try:
        name = rec.name
    except KeyError:
        name = "."
    try:
        item_rgb = rec.itemRGB
    except KeyError:
        item_rgb = "#000000"
    try:
        score = rec.score
    except KeyError:
        score = 0
    return (rec.contig, rec.start, rec.end, name, item_rgb, score)


def read_bed_local_selfident_row(
    rec: tuple[str, str, str, str],
    breakpoints: list[float],
    colors: list[str],
) -> tuple[str, int, int, float, str, int]:
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


def to_relative_coords_bed(df: pl.DataFrame):
    return df.with_columns(
        pl.col("chrom_st") - pl.col("chrom_st").min().over("chrom"),
        pl.col("chrom_end") - pl.col("chrom_st").min().over("chrom"),
    )
