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


def get_selected_cen(regions: str, chrom_name: str) -> tuple[str, int, int]:
    df_regions_chrom = get_regions(regions, chrom_name)
    all_chroms = df_regions_chrom["chrom"].unique(maintain_order=True).to_list()
    return (
        df_regions_chrom.filter(pl.col("chrom").eq(pl.lit(all_chroms[0])))
        .select("chrom", "chrom_st", "chrom_end")
        .row(0)
    )
