import os
import pysam
import pathlib
import pybigtools
import polars as pl

from loguru import logger
from typing import Any, Iterator, Mapping

from cencyclopedia.io.config import Config, Position, DataType
from cencyclopedia.plot.common import TrackMode


FILE_HANDLE = pybigtools.BBIReader | pysam.TabixFile | pathlib.Path | None


class Data:
    def __init__(self, cfg: Mapping[str, Config]):
        self.fhs: dict[str, FILE_HANDLE] = {}
        self.cfg: dict[str, Config] = {}

        for label, og_trk_info in cfg.items():
            # validate datatype and position
            typ = DataType("null" if not og_trk_info["type"] else og_trk_info["type"])
            pos = Position(og_trk_info["position"])
            # Might be immutable so create new dict
            trk_info: Config = {
                "options": og_trk_info["options"],
                "path": og_trk_info.get("path", ""),
                "position": pos,
                "prop": og_trk_info.get("prop", 0.0),
                "type": typ,
            }
            self.cfg[label] = trk_info

            is_bigfile = typ == DataType.BIGWIG or typ == DataType.BIGBED
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
        return self.cfg[label]["type"] if dtype != DataType.NULL else None

    @property
    def labels(self) -> Iterator[str]:
        for lbl in self.fhs.keys():
            if self.cfg[lbl]["type"] == DataType.NULL:
                continue
            yield lbl

    @property
    def track_params(self) -> Iterator[tuple[str, int, float | None]]:
        idx = 0
        for label, cfg in self.cfg.items():
            if cfg["position"] == Position.RELATIVE:
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
        dtype = self.cfg[label]["type"]
        schema = dtype.get_schema()
        read_fns = dtype.get_read_fns(
            options=self.cfg[label]["options"], chrom=chrom, st=st, end=end
        )
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
                qry = fh.fetch(chrom, st, end, parser=pysam.asTuple())
            else:
                qry = fh.records(chrom, st, end)

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
