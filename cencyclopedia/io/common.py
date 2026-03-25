import polars as pl


def get_chrom(regions: str, chrom: str) -> pl.DataFrame:
    return (
        pl.scan_csv(regions)
        .filter(pl.col("chrom").eq(chrom))
        .sort(by=["arm", "clade"], maintain_order=True)
        .collect()
    )


def get_regions(regions: str, chrom_name: str) -> pl.DataFrame:
    return (
        pl.scan_csv(regions)
        .filter(pl.col("chrom_name").eq(chrom_name))
        .sort(by=["arm", "clade"], maintain_order=True)
        .collect()
    )


def clip_df(df: pl.DataFrame, st: int, end: int):
    return (
        df.with_columns(
            pl.col("chrom_st").clip(st, end),
            pl.col("chrom_end").clip(st, end),
        )
        # To clip, we only take intervals that are non-null,
        #   Before:
        #   ||
        #      | | # (st, end)
        #   After:
        #      |    <- Remove this
        #      | | # (st, end)
        .filter(
            ~(
                pl.col("chrom_st").eq(pl.lit(st)) & pl.col("chrom_end").eq(pl.lit(st))
                | pl.col("chrom_st").eq(pl.lit(end))
                & pl.col("chrom_end").eq(pl.lit(end))
            )
        )
    )
