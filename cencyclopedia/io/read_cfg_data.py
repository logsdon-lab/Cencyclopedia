import os
import gzip
import pysam
import bisect
import polars as pl

from typing import Self, Any, Literal, Iterator, NamedTuple

from .read_ident import read_identity_breakpoints

RGX_SM_CHROM = r"^(?<sample>.*?)_(?<chrom_name>chr[0-9XY]+)[_:]*"
CHROM_NAMES = [f"chr{i}" for i in (*range(1, 23), "X", "Y")]


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


def read_bedpe_selfident_row(
    rec: tuple[str, str, str, str, str, str, str],
    breakpoints: list[float],
    colors: list[str],
) -> tuple[str, int, int, str, int, int, float, str, str]:
    qry, qry_st, qry_end, ref, ref_st, ref_end, ident = rec
    qry_st = int(qry_st)
    qry_end = int(qry_end)
    ref_st = int(ref_st)
    ref_end = int(ref_end)
    ident = float(ident)
    if ident == 0.0:
        color = colors[0]
        desc = str(ident_end)
        # return (qry, qry_st, qry_end, ref, ref_st, ref_end, ident)
        return (qry, qry_st, qry_end, ref, ref_st, ref_end, ident, color, desc)
    try:
        idx_end = bisect.bisect(breakpoints, ident)
        ident_end = breakpoints[idx_end]
        if idx_end == 0:
            ident_st = 0.0
            color = colors[0]
        else:
            ident_st = breakpoints[idx_end - 1]
            color = colors[idx_end - 1]
        desc = f"{ident_st}%-{ident_end}%"
    except IndexError:
        ident_end = breakpoints[-1]
        color = colors[-1]
        desc = str(ident_end)

    # return (qry, qry_st, qry_end, ref, ref_st, ref_end, ident)
    return (qry, qry_st, qry_end, ref, ref_st, ref_end, ident, color, desc)


def to_relative_coords_bed(df: pl.DataFrame):
    return df.with_columns(
        pl.col("chrom_st") - pl.col("chrom_st").min().over("chrom"),
        pl.col("chrom_end") - pl.col("chrom_st").min().over("chrom"),
    )


def to_relative_coords_bedpe_selfident(df: pl.DataFrame):
    return df.with_columns(
        pl.col("qry_st") - pl.col("qry_st").min().over("qry"),
        pl.col("qry_end") - pl.col("qry_st").min().over("qry"),
        pl.col("ref_st") - pl.col("ref_st").min().over("ref"),
        pl.col("ref_end") - pl.col("ref_st").min().over("ref"),
    )


class Data(NamedTuple):
    fhs: dict[str, pysam.TabixFile]
    cfg: dict[str, Any]

    def new(cfg: dict[str, Any]) -> Self:
        fhs = {}
        cfgs = {}
        for label, trk_info in cfg.items():
            fhs[label] = pysam.TabixFile(trk_info["path"])
            cfgs[label] = trk_info

        return Data(fhs=fhs, cfg=cfgs)

    def options(self, label: str) -> dict[str, Any]:
        return self.cfg[label].get("options", {})

    def datatype(
        self, label: str
    ) -> Literal["bed", "bedgraph", "bedstrand", "bedpe_selfident"]:
        return self.cfg[label]["type"]

    @property
    def labels(self) -> Iterator[str]:
        return self.fhs.keys()

    @property
    def track_params(self) -> Iterator[tuple[str, int, float | None]]:
        idx = 0
        for label, cfg in self.cfg.items():
            if cfg["position"] == "relative":
                idx += 1
            yield label, idx, cfg.get("prop")

    def query(
        self, label: str, chrom: str, st: int, end: int, *, to_relative: bool = True
    ) -> pl.DataFrame:
        """
        # Arguments
        * `label`
        * `chrom`
        * `st`
        * `end`

        ## Note
        * Currently to_relative not applicable with bedpe_selfident
        """
        parser: pysam.asBed | pysam.asTuple = pysam.asBed()
        to_relative_fn = to_relative_coords_bed
        if self.cfg[label]["type"] == "bed9":
            read_fn = read_bed9_row
            cols = ["chrom", "chrom_st", "chrom_end", "name", "color"]
        elif self.cfg[label]["type"] == "bedstrand":
            read_fn = read_bedstrand_row
            cols = ["chrom", "chrom_st", "chrom_end", "name", "color"]
        elif self.cfg[label]["type"] == "bedgraph":
            read_fn = read_bedgraph_row
            cols = ["chrom", "chrom_st", "chrom_end", "name"]
        elif self.cfg[label]["type"] == "bedpe_selfident":
            parser = pysam.asTuple()
            breakpoints, colors = read_identity_breakpoints(
                self.cfg[label].get("ident_breakpoints")
            )
            read_fn = lambda rec: read_bedpe_selfident_row(
                rec, breakpoints=breakpoints, colors=colors
            )
            to_relative_fn = to_relative_coords_bedpe_selfident
            cols = [
                "qry",
                "qry_st",
                "qry_end",
                "ref",
                "ref_st",
                "ref_end",
                "percent_identity_by_events",
                "color",
                "desc",
            ]
        else:
            read_fn = read_bed9_row
            cols = ["chrom", "chrom_st", "chrom_end", "name", "color"]

        qry = self.fhs[label].fetch(chrom, st, end, parser=parser)
        df = pl.DataFrame(
            data=[read_fn(rec) for rec in qry],
            orient="row",
            schema=cols,
        )

        if not to_relative:
            return df
        else:
            return to_relative_fn(df)


def read_or_write_regions(
    cfg: dict[str, Any], regions: str = "assets/regions.csv.gz"
) -> pl.DataFrame:
    if not os.path.exists(regions):
        df_regions = read_regions_from_data(
            cfg["regions"], cfg["clades"], cfg["sample_metadata"]
        )
        with gzip.open(regions, "wb") as fh:
            df_regions.write_csv(fh)
    else:
        df_regions = pl.read_csv(regions)

    return df_regions.cast({"chrom_name": pl.Enum(CHROM_NAMES)})


def read_regions_from_data(
    regions: str, clades: str, sample_metadata: str
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
    df_metadata = pl.read_csv(
        sample_metadata,
        separator="\t",
        has_header=False,
        new_columns=["sample", "population", "gender"],
    )
    df_final_regions = (
        df_regions.join(df_clades, on=["chrom", "sample", "chrom_name"])
        .join(df_metadata, on=["sample"])
        .cast({"chrom_name": pl.Enum(CHROM_NAMES)})
    )

    return df_final_regions
