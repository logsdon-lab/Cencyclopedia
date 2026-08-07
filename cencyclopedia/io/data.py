import os
import enum
import pysam
import pathlib
import pybigtools
import polars as pl

from dataclasses import dataclass
from loguru import logger
from typing import Callable, Any, Iterator

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

EXPANDABLE_DATA_TYPES = set(("bed", "bigbed", "bedstrand", "bed_localselfident"))


@dataclass
class DataOpFunctions:
    read_fn: Callable[[Any], Any]
    to_relative_fn: Callable[[pl.DataFrame], pl.DataFrame]
    finalizer_fn: Callable[[pl.DataFrame], pl.DataFrame] | None


class DataType(enum.Enum):
    NULL = "null"  # or spacer
    BED9 = "bed"
    BEDGRAPH = "bedgraph"
    BIGWIG = "bigwig"
    BIGBED = "bigbed"
    BEDSTRAND = "bedstrand"
    BEDPE_SELFIDENT = "bedpe_selfident"
    BED_LOCALSELFIDENT = "bed_localselfident"

    def get_extension(self) -> str | None:
        if self == DataType.NULL:
            return None
        elif (
            self == DataType.BED9
            or self == DataType.BED_LOCALSELFIDENT
            or self == DataType.BEDGRAPH
            or self == DataType.BEDSTRAND
        ):
            return ".bed.gz"
        elif self == DataType.BIGWIG:
            return ".bw"
        elif self == DataType.BIGBED:
            return ".bb"
        elif self == DataType.BEDPE_SELFIDENT:
            # TODO: Should rename HGSVC data at some point and change this.
            return ".bed.gz"
        else:
            raise ValueError(f"Invalid name. {self}")

    def get_schema(self) -> dict[str, Any]:
        if (
            self == DataType.BED9
            or self == DataType.BEDSTRAND
            or self == DataType.BED_LOCALSELFIDENT
            or self == DataType.BIGBED
        ):
            return BED_SCHEMA
        elif self == DataType.BEDGRAPH or self == DataType.BIGWIG:
            return BEDGRAPH_SCHEMA
        elif self == DataType.NULL:
            return {}
        elif self == DataType.BEDPE_SELFIDENT:
            return BEDPE_SCHEMA
        else:
            raise ValueError(f"Invalid name. {self}")

    def get_pysam_parser(self) -> pysam.asBed | pysam.asTuple:
        if self == DataType.BEDPE_SELFIDENT:
            return pysam.asTuple()
        else:
            return pysam.asBed()

    def get_read_fns(
        self, cfg: dict[str, Any], st: int | None, end: int | None
    ) -> DataOpFunctions | None:
        # Convert to relative coordinates
        to_relative_fn = lambda df: to_relative_coords_bed(df, st)

        if self == DataType.NULL:
            return None
        elif self == DataType.BIGBED:
            pass
        elif self == DataType.BIGWIG:
            pass
        elif self == DataType.BED9:
            return DataOpFunctions(
                read_fn=read_bed9_row, to_relative_fn=to_relative_fn, finalizer_fn=None
            )
        elif self == DataType.BEDSTRAND:
            return DataOpFunctions(
                read_fn=read_bedstrand_row,
                to_relative_fn=to_relative_fn,
                finalizer_fn=None,
            )
        elif self == DataType.BEDGRAPH:
            return DataOpFunctions(
                read_fn=read_bedgraph_row,
                to_relative_fn=to_relative_fn,
                finalizer_fn=None,
            )
        elif self == DataType.BED_LOCALSELFIDENT:
            breakpoints, colors = read_identity_breakpoints(
                cfg.get("ident_breakpoints")
            )
            return DataOpFunctions(
                read_fn=lambda rec: read_bed_local_selfident_row(
                    rec, breakpoints=list(breakpoints), colors=list(colors)
                ),
                to_relative_fn=to_relative_fn,
                finalizer_fn=None,
            )
        elif self == DataType.BEDPE_SELFIDENT:
            breakpoints, colors = read_identity_breakpoints(
                cfg.get("ident_breakpoints")
            )
            return DataOpFunctions(
                read_fn=lambda rec: read_bedpe_selfident_row(
                    rec,
                ),
                to_relative_fn=lambda df: to_relative_coords_bedpe_selfident(df, st),
                finalizer_fn=lambda df: df.filter(
                    pl.col("ref_st").is_between(st, end)
                    & pl.col("ref_end").is_between(st, end)
                ),
            )
        else:
            raise ValueError(f"Invalid name. {self}")


class Data:
    def __init__(self, cfg: dict[str, Any]):
        self.fhs = {}
        self.cfg = {}
        for label, trk_info in cfg.items():
            self.cfg[label] = trk_info
            typ = trk_info["type"]
            is_bigfile = typ == "bigwig" or typ == "bigbed"
            path = trk_info.get("path")
            if not path:
                self.fhs[label] = None
            elif os.path.isfile(path):
                if is_bigfile:
                    self.fhs[label] = pybigtools.open(trk_info["path"])
                else:
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
        try:
            dtype = DataType(self.cfg[label]["type"])
        except Exception:
            logger.info(f"Skipped {self.cfg[label]['type']}")
            dtype = DataType.NULL

        parser = dtype.get_pysam_parser()
        schema = dtype.get_schema()
        read_fns = dtype.get_read_fns(cfg=self.cfg[label], st=st, end=end)
        # Spacer or invalid datatype
        if not read_fns:
            return None

        fh = self.fhs[label]
        if isinstance(fh, pysam.TabixFile):
            fh = fh
        elif isinstance(fh, pybigtools.BBIReader):
            fh = fh
        elif isinstance(fh, pathlib.Path):
            try:
                ext = dtype.get_extension()
                path = fh.joinpath(f"{chrom}{ext}").as_posix()
                if dtype == DataType.BIGWIG or dtype == DataType.BIGBED:
                    fh = pybigtools.open(path)
                else:
                    fh = pysam.TabixFile(path)
            except Exception as err:
                raise RuntimeError(
                    f"Error reading {fh} for {label} and {chrom}:{st}-{end}: {err}"
                )
        else:
            raise TypeError(
                f"Invalid file handle type for {label} and {chrom}:{st}-{end}: {fh}"
            )

        try:
            logger.debug(f"Query {label} for {chrom}:{st}-{end}")
            if isinstance(fh, pysam.TabixFile):
                qry = fh.fetch(chrom, st, end, parser=parser)
            else:
                qry = fh.values(chrom, st, end)
                breakpoint()

            df = pl.DataFrame(
                data=[read_fns.read_fn(rec) for rec in qry],
                orient="row",
                schema=schema,
            )
            if read_fns.finalizer_fn:
                df = read_fns.finalizer_fn(df)
        except Exception as err:
            logger.debug(f"Unable to query {label} for {chrom}:{st}-{end} ({err})")
            return pl.DataFrame(schema=schema)

        if not to_relative:
            return df
        else:
            return read_fns.to_relative_fn(df)

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
