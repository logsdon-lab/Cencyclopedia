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


def to_relative_coords_bed(df: pl.DataFrame):
    return df.with_columns(
        pl.col("chrom_st") - pl.col("chrom_st").min().over("chrom"),
        pl.col("chrom_end") - pl.col("chrom_st").min().over("chrom"),
    )
