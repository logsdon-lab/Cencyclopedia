import sys
import polars as pl
from cenplot.lib.io.bed_hor import read_bed_hor  # pyright: ignore

(
    read_bed_hor(sys.argv[1], live_only=False)
    .select(
        pl.col("chrom"),
        pl.col("chrom_st"),
        pl.col("chrom_end"),
        pl.col("name"),
        ((pl.col("chrom_end") - pl.col("chrom_st")) / pl.lit(171))
        .clip(lower_bound=1)
        .round(mode="half_away_from_zero")
        .alias("score"),
        pl.col("strand"),
        pl.col("chrom_st").alias("thick_st"),
        pl.col("chrom_end").alias("thick_end"),
        pl.col("color"),
    )
    .sort(by=["chrom", "chrom_st"])
    .write_csv(sys.stdout, separator="\t", include_header=False)
)
