import pysam
import polars as pl

from loguru import logger
from typing import Self, Any, Literal, Iterator, NamedTuple

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
    ) -> Literal[
        "bed", "bedgraph", "bedstrand", "bedpe_selfident", "bed_localselfident"
    ]:
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
        self,
        label: str,
        chrom: str,
        st: int | None = None,
        end: int | None = None,
        *,
        to_relative: bool = True,
    ) -> pl.DataFrame:
        """
        # Arguments
        * `label`
        * `chrom`
        * `st`
        * `end`
        """
        parser: pysam.asBed | pysam.asTuple = pysam.asBed()
        to_relative_fn = to_relative_coords_bed
        if self.cfg[label]["type"] == "bed9":
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
                rec, breakpoints=breakpoints, colors=colors
            )
            schema = BED_SCHEMA
        elif self.cfg[label]["type"] == "bedpe_selfident":
            parser = pysam.asTuple()
            breakpoints, colors = read_identity_breakpoints(
                self.cfg[label].get("ident_breakpoints")
            )
            read_fn = lambda rec: read_bedpe_selfident_row(
                rec,
                # breakpoints=breakpoints, colors=colors
            )
            to_relative_fn = to_relative_coords_bedpe_selfident
            schema = BEDPE_SCHEMA
        else:
            read_fn = read_bed9_row
            schema = BED_SCHEMA

        try:
            qry = self.fhs[label].fetch(chrom, st, end, parser=parser)
            df = pl.DataFrame(
                data=[read_fn(rec) for rec in qry],
                orient="row",
                schema=schema,
            )
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
        by: Literal["Original", "Length", "Frequency", "Coverage"],
        rle: bool = True,
        clip: bool = True,
        to_relative: bool = True,
    ):
        df = self.query(
            label,
            chrom,
            chrom_st,
            chrom_end,
            to_relative=to_relative,
        )
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
        elif by == "Coverage":
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
        if clip and chrom_st and chrom_end:
            df_final = (
                df_final.with_columns(
                    pl.col("chrom_st").clip(chrom_st, chrom_end),
                    pl.col("chrom_end").clip(chrom_st, chrom_end),
                )
                # To clip, we only take intervals that are non-null,
                #   Before:
                #   ||
                #      | | # (st, end)
                #   After:
                #      |    <- Remove this
                #      | | # (st, end)
                .filter(
                    ~(
                        pl.col("chrom_st").eq(pl.lit(chrom_st))
                        & pl.col("chrom_end").eq(pl.lit(chrom_st))
                        | pl.col("chrom_st").eq(pl.lit(chrom_end))
                        & pl.col("chrom_end").eq(pl.lit(chrom_end))
                    )
                )
            )
        return df_final
