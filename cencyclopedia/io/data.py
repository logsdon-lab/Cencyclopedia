import os
import pysam
import pathlib
import polars as pl

from loguru import logger
from typing import Callable, Any, Literal, Iterator

from cencyclopedia.plot.common import TrackMode

from .bed import (
    to_relative_coords_bed,
    read_bed9_row,
    read_bedgraph_row,
    read_bedstrand_row,
    read_bed_local_selfident_row,
    BED_SCHEMA,
    BEDGRAPH_SCHEMA,
    BEDPE_SCHEMA,
)
from .bedpe import (
    read_bedpe_selfident_row,
    read_identity_breakpoints,
    to_relative_coords_bedpe_selfident,
)

EXPANDABLE_DATA_TYPES = set(("bed", "bedstrand", "bed_localselfident"))

DataType = Literal[
    "bed", "bedgraph", "bedstrand", "bedpe_selfident", "bed_localselfident"
]


class Data:
    def __init__(self, cfg: dict[str, Any]):
        self.fhs = {}
        self.cfg = {}
        for label, trk_info in cfg.items():
            self.cfg[label] = trk_info
            path = trk_info.get("path")
            if not path:
                self.fhs[label] = None
            elif os.path.isfile(path):
                self.fhs[label] = pysam.TabixFile(trk_info["path"])
            elif os.path.isdir(path):
                self.fhs[label] = pathlib.Path(path)
            else:
                logger.debug(f"Invalid file type for {path}")
                continue

    def options(self, label: str) -> dict[str, Any]:
        return self.cfg[label].get("options", {})

    def datatype(self, label: str) -> DataType | None:
        dtype = self.cfg[label]["type"]
        return self.cfg[label]["type"] if dtype != "spacer" else None

    @property
    def labels(self) -> Iterator[str]:
        for lbl in self.fhs.keys():
            if self.cfg[lbl]["type"] == "spacer":
                continue
            yield lbl

    @property
    def track_params(self) -> Iterator[tuple[str, int, float | None]]:
        idx = 0
        for label, cfg in self.cfg.items():
            if cfg["position"] == "relative":
                idx += 1
            yield label, idx, cfg.get("prop")

    def query(
        self,
        label: str,
        chrom: str,
        st: int | None = None,
        end: int | None = None,
        *,
        to_relative: bool = True,
    ) -> pl.DataFrame | None:
        """
        # Arguments
        * `label`
        * `chrom`
        * `st`
        * `end`
        """
        parser: pysam.asBed | pysam.asTuple = pysam.asBed()
        to_relative_fn = lambda df: to_relative_coords_bed(df, st)
        finalizer_fn: Callable[[pl.DataFrame], pl.DataFrame] | None = None
        if self.cfg[label]["type"] == "spacer":
            return None
        elif self.cfg[label]["type"] == "bed9":
            read_fn = read_bed9_row
            schema = BED_SCHEMA
        elif self.cfg[label]["type"] == "bedstrand":
            read_fn = read_bedstrand_row
            schema = BED_SCHEMA
        elif self.cfg[label]["type"] == "bedgraph":
            read_fn = read_bedgraph_row
            schema = BEDGRAPH_SCHEMA
        elif self.cfg[label]["type"] == "bed_localselfident":
            breakpoints, colors = read_identity_breakpoints(
                self.cfg[label].get("ident_breakpoints")
            )
            read_fn = lambda rec: read_bed_local_selfident_row(
                rec, breakpoints=list(breakpoints), colors=list(colors)
            )
            schema = BED_SCHEMA
        elif self.cfg[label]["type"] == "bedpe_selfident":
            parser = pysam.asTuple()
            breakpoints, colors = read_identity_breakpoints(
                self.cfg[label].get("ident_breakpoints")
            )
            read_fn = lambda rec: read_bedpe_selfident_row(
                rec,
            )
            to_relative_fn = lambda df: to_relative_coords_bedpe_selfident(df, st)
            finalizer_fn = lambda df: df.filter(
                pl.col("ref_st").is_between(st, end)
                & pl.col("ref_end").is_between(st, end)
            )
            schema = BEDPE_SCHEMA
        else:
            read_fn = read_bed9_row
            schema = BED_SCHEMA

        fh = self.fhs[label]
        if isinstance(fh, pysam.TabixFile):
            fh = fh
        elif isinstance(fh, pathlib.Path):
            try:
                fname = fh.joinpath(f"{chrom}.bed.gz").as_posix()
                fh = pysam.TabixFile(fname)
            except Exception as err:
                raise RuntimeError(
                    f"Error reading {fh} for {label} and {chrom}:{st}-{end}: {err}."
                )
        else:
            raise TypeError(
                f"Invalid file handle type for {label} and {chrom}:{st}-{end}: {fh}"
            )

        try:
            logger.debug(f"Query {label} for {chrom}:{st}-{end}")
            qry = fh.fetch(chrom, st, end, parser=parser)
            df = pl.DataFrame(
                data=[read_fn(rec) for rec in qry],
                orient="row",
                schema=schema,
            )
            if finalizer_fn:
                df = finalizer_fn(df)
        except ValueError as err:
            logger.debug(f"Unable to query {label} for {chrom}:{st}-{end} ({err})")
            return pl.DataFrame(schema=BED_SCHEMA)

        if not to_relative:
            return df
        else:
            return to_relative_fn(df)

    def split(
        self,
        label: str,
        chrom: str,
        chrom_st: int | None,
        chrom_end: int | None,
        *,
        by: TrackMode,
        rle: bool = True,
        to_relative: bool = True,
    ) -> pl.DataFrame | None:
        df = self.query(
            label,
            chrom,
            chrom_st,
            chrom_end,
            to_relative=to_relative,
        )
        if not isinstance(df, pl.DataFrame):
            return None

        if by == "Length":
            df_name_order = (
                df.group_by(["name"])
                # In case that BED is run-length encoded to reduce number of rows.
                .agg(length=(pl.col("chrom_end") - pl.col("chrom_st")).min())
                .sort("length", descending=True)
                .with_columns(group=pl.col("name").rle_id())
                .drop("length")
            )
            df_final = df.join(df_name_order, on="name", how="left")
        elif by == "Frequency":
            df_name_order = (
                df["name"]
                .value_counts(sort=True)
                .with_columns(group=pl.col("name").rle_id())
                .drop("count")
            )
            df_final = df.join(df_name_order, on="name", how="left")
        elif by == "Proportion":
            df_name_order = (
                df.group_by(["name"])
                .agg(length=(pl.col("chrom_end") - pl.col("chrom_st")).sum())
                .sort("length", descending=True)
                .with_columns(group=pl.col("name").rle_id())
                .drop("length")
            )
            df_final = df.join(df_name_order, on="name", how="left")
        else:
            df_final = df.with_columns(group=pl.lit(None))

        if rle:
            df_final = (
                df_final.sort(by=["chrom", "chrom_st"])
                .with_columns(
                    group_rle=pl.col("name").rle_id().over(["chrom"]),
                    # Ensure exists
                    strand=pl.coalesce(pl.col("^strand$"), pl.lit(".")),
                    color=pl.coalesce(pl.col("^color$"), pl.lit("black")),
                )
                .group_by(["chrom", "group_rle"])
                .agg(
                    pl.col("chrom_st").min(),
                    pl.col("chrom_end").max(),
                    pl.col("name").first(),
                    pl.col("score").median(),
                    pl.col("strand").first(),
                    pl.col("color").first(),
                    pl.col("group").first(),
                )
                .drop("group_rle")
            )

        return df_final
