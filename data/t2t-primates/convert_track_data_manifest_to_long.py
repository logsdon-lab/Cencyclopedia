import sys
import polars as pl

SCHEMA = {
    "track": pl.String,
    "shortLabel": pl.String,
    "longLabel": pl.String,
    "group": pl.String,
    "type": pl.String,
    "visibility": pl.String,
    "itemRgb": pl.String,
    "bigDataUrl": pl.String,
    "priority": pl.String,
    "html": pl.String,
    "txt description": pl.String,
    "who": pl.String,
    "file received": pl.String,
    "on-hub": pl.String,
    "comment": pl.String,
}
RGXS_SM = {
    "mGorGor1": r"mGorGor1|mGorGor|gorgor",
    "mPanPan1": r"mPanPan1|mPanPan|panpan",
    "mPanTro3": r"mPanTro3|mPanTro|pantro",
    "mPonAbe1": r"mPonAbe1|mPonAbe|ponabe",
    "mPonPyg2": r"mPonPyg2|mPonPyg|ponpyg",
}


def main():
    path_track_db = sys.argv[1]
    order = sys.argv[2]
    df_order = pl.read_csv(
        order, separator="\t", has_header=False, new_columns=["name", "track"]
    )
    df = (
        pl.read_csv(
            path_track_db,
            separator="\t",
            has_header=True,
            schema=SCHEMA,
        )
        .with_columns(pl.col("bigDataUrl").str.split(" "))
        .explode(["bigDataUrl"], empty_as_null=True)
        .filter(pl.col("track").is_in(df_order["track"].implode()))
    )
    df_sm_name = (
        df.select("bigDataUrl")
        .with_columns(
            **{
                sm: pl.col("bigDataUrl").str.contains(rgx)
                for sm, rgx in RGXS_SM.items()
            }
        )
        .unpivot(
            index="bigDataUrl", on=None, variable_name="sample", value_name="is_sample"
        )
        .filter(pl.col("is_sample").eq(True))
        .drop("is_sample")
    )

    df = df.join(df_sm_name, on="bigDataUrl", how="left")

    df.write_csv(sys.stdout, separator="\t", include_header=True)


if __name__ == "__main__":
    raise SystemExit(main())
