import polars as pl
from typing import Any
from .constants import RGX_SM_CHROM


def read_figure_1_bbox_data(cfg: dict[str, Any]):
    df_order = (
        pl.read_csv(cfg["general"]["fig_1"]["order"])
        .with_columns(mtch=pl.col("chrom").str.extract_groups(RGX_SM_CHROM))
        .unnest("mtch")
        .with_columns(idx=pl.col("sample").rle_id().over("chrom_name"))
        .select("chrom", "label", "sample", "chrom_name", "idx")
    )

    df_bboxes = pl.read_csv(cfg["general"]["fig_1"]["bboxes"])
    df_bboxes = (
        df_bboxes.with_columns(
            offset=(pl.col("ypos_end") - pl.col("ypos_st")) / pl.col("rows"),
            idx=pl.Series(list(range(0, nrow + 1)) for nrow in df_bboxes["rows"]),
        )
        .explode("idx")
        .with_columns(
            ypos_st=pl.col("ypos_st") + (pl.col("offset") * pl.col("idx")),
            ypos_end=pl.col("ypos_st")
            + (pl.col("offset") * pl.col("idx"))
            + pl.col("offset"),
        )
    )
    return df_order.join(df_bboxes, on=["chrom_name", "idx"], how="left").select(
        "chrom",
        "label",
        "sample",
        "chrom_name",
        "xpos_st",
        "xpos_end",
        "ypos_st",
        "ypos_end",
    )
