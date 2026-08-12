import sys
import re
import polars as pl

RGX_SM = re.compile(r"(m[^\s]*)")


def main():
    infile = sys.argv[1]
    df = pl.read_csv(infile, separator="\t", has_header=True)
    cols = [c for c in df.columns if "HOR" not in c]
    df = df.select(cols)
    new_cols = {}
    for c in df.columns:
        mtch = RGX_SM.search(c)
        if mtch:
            new_cols[c] = mtch.group()
    df = (
        df.rename(new_cols)
        .drop_nulls()
        .unpivot(on=None, variable_name="sample", value_name="itv")
        .with_columns(
            pl.col("itv").str.extract_groups(r"^(?<chrom>.*?):(?<st>.*?)-(?<end>.*?)$")
        )
        .unnest("itv")
        .with_columns(sm_chrom=pl.col("sample") + "_" + pl.col("chrom"))
        .select("sm_chrom", "st", "end")
    )
    df.write_csv(sys.stdout, separator="\t", include_header=False)


if __name__ == "__main__":
    raise SystemExit(main())
