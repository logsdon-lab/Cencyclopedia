import sys
import polars as pl
from cenplot.lib.io.bed_hor import read_bed_hor

# TODO: Store original data and
(
    read_bed_hor(sys.argv[1], live_only=False)
    .sort(by=["chrom", "chrom_st"])
    .with_columns(grp=pl.col("name").rle_id().over(["chrom"]))
    .group_by(["chrom", "grp"])
    .agg(
        pl.col("chrom_st").min(),
        pl.col("chrom_end").max(),
        pl.col("name").first(),
        pl.col("strand").first(),
        pl.col("color").first(),
    )
    .select(
        pl.col("chrom"),
        pl.col("chrom_st"),
        pl.col("chrom_end"),
        pl.col("name"),
        pl.lit(0),
        pl.col("strand"),
        pl.col("chrom_st").alias("thick_st"),
        pl.col("chrom_end").alias("thick_end"),
        pl.col("color"),
    )
    .sort(by=["chrom", "chrom_st"])
    .write_csv(sys.stdout, separator="\t", include_header=False)
)
