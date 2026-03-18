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
