from typing import Literal
import os
import gzip
import polars as pl

from typing import Any

from .constants import RGX_SM_CHROM, CHROM_NAMES


def read_or_write_regions(
    cfg: dict[str, Any], regions: str, mode=Literal["single", "all"]
) -> pl.DataFrame:
    if not os.path.exists(regions):
        if mode == "single":
            df_regions = pl.read_csv(
                cfg["general"]["regions"],
                separator="\t",
                has_header=False,
                columns=[0, 1, 2],
                new_columns=["chrom", "chrom_st", "chrom_end"],
            )
        else:
            df_regions = read_regions_from_data(
                cfg["general"]["regions"],
                cfg["general"]["clades"],
                cfg["general"]["sample_metadata"],
                cfg["general"]["population_colors"],
            )

        with gzip.open(regions, "wb") as fh:
            df_regions.write_csv(fh)
    else:
        df_regions = pl.read_csv(
            regions, schema_overrides={"chrom_name": pl.Enum(CHROM_NAMES)}
        )

    return df_regions


def read_regions_from_data(
    regions: str, clades: str, sample_metadata: str, population_colors: str
) -> pl.DataFrame:
    df_regions = (
        pl.read_csv(
            regions,
            separator="\t",
            has_header=False,
            columns=[0, 1, 2],
            new_columns=["chrom", "chrom_st", "chrom_end"],
        )
        .with_columns(mtch=pl.col("chrom").str.extract_groups(RGX_SM_CHROM))
        .unnest("mtch")
    )
    df_clades = (
        pl.read_csv(
            clades,
            separator="\t",
            has_header=False,
            new_columns=["chrom", "clade", "arm"],
        )
        .with_columns(mtch=pl.col("chrom").str.extract_groups(RGX_SM_CHROM))
        .unnest("mtch")
    )
    df_populations = pl.read_csv(
        population_colors,
        separator="\t",
        has_header=False,
        new_columns=["population", "color"],
    )
    df_metadata = pl.read_csv(
        sample_metadata,
        separator="\t",
        has_header=False,
        new_columns=["sample", "population", "sex"],
    )
    df_final_regions = (
        df_regions.join(df_clades, on=["chrom", "sample", "chrom_name"])
        .join(df_metadata, on="sample")
        .join(df_populations, on="population")
        .cast({"chrom_name": pl.Enum(CHROM_NAMES)})
    )

    return df_final_regions
