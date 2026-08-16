import polars as pl

from enum import StrEnum
from typing import Any, TypedDict, Callable
from dataclasses import dataclass

from .bed import (
    read_bigbed_row,
    read_bigwig_row,
    to_relative_coords_bed,
    read_bedn_row,
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
    original_data_fn: Callable[[Any], Any] = lambda rec: list(rec)


class DataType(StrEnum):
    NULL = "null"  # or spacer
    BED9 = "bed"
    BEDGRAPH = "bedgraph"
    BIGWIG = "bigwig"
    BIGBED = "bigbed"
    BEDSTRAND = "bedstrand"
    BEDPE_SELFIDENT = "bedpe_selfident"
    BED_LOCALSELFIDENT = "bed_localselfident"

    def is_expandable(self) -> bool:
        return self.value in EXPANDABLE_DATA_TYPES

    def is_bedgraph_like(self) -> bool:
        return self == DataType.BEDGRAPH or self == DataType.BIGWIG

    def get_extension(self) -> str | None:
        if self == DataType.NULL:
            return None
        elif self == DataType.BEDGRAPH:
            return ".bg.gz"
        elif (
            self == DataType.BED9
            or self == DataType.BED_LOCALSELFIDENT
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

    def get_io_fns(
        self, options: dict[str, Any], chrom: str, st: int | None, end: int | None
    ) -> DataOpFunctions | None:
        # Convert to relative coordinates
        to_relative_fn = lambda df: to_relative_coords_bed(df, st)

        if self == DataType.NULL:
            return None
        elif self == DataType.BIGBED:
            return DataOpFunctions(
                read_fn=lambda rec: read_bigbed_row(rec, chrom),
                to_relative_fn=to_relative_fn,
                finalizer_fn=None,
                # bigtools doesn't return chrom
                original_data_fn=lambda rec: (chrom, *list(rec)),
            )
        elif self == DataType.BIGWIG:
            return DataOpFunctions(
                read_fn=lambda rec: read_bigwig_row(rec, chrom),
                to_relative_fn=to_relative_fn,
                finalizer_fn=None,
                original_data_fn=lambda rec: (chrom, *list(rec)),
            )
        elif self == DataType.BED9:
            return DataOpFunctions(
                read_fn=read_bedn_row, to_relative_fn=to_relative_fn, finalizer_fn=None
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
                options.get("ident_breakpoints")
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
                options.get("ident_breakpoints")
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


class Position(StrEnum):
    RELATIVE = "relative"
    OVERLAP = "overlap"


class Config(TypedDict):
    position: Position
    path: str
    type: DataType
    prop: float
    options: dict[str, Any]


DEFAULT_BED_OPTIONS: Config = {
    "position": Position.RELATIVE,
    "type": DataType.BED9,
    "path": "",
    "prop": 0.05,
    "options": {
        "rle": False,
        "xaxis_kwargs": {"ticks": "", "showline": False},
        "yaxis_kwargs": {
            "showticklabels": False,
            "ticks": "",
            "showline": False,
        },
    },
}


DEFAULT_SPACER_OPTIONS: Config = {
    "position": Position.RELATIVE,
    "type": DataType.NULL,
    "path": "",
    "prop": 0.02,
    "options": {
        "rle": False,
        "xaxis_kwargs": {"showticklabels": False, "ticks": "", "showline": False},
        "yaxis_kwargs": {"showticklabels": False, "ticks": "", "showline": False},
    },
}

DEFAULT_BEDGRAPH_OPTIONS: Config = {
    "position": Position.RELATIVE,
    "type": DataType.BEDGRAPH,
    "path": "",
    "prop": 0.1,
    "options": {
        "rle": False,
        "xaxis_kwargs": {"ticks": "", "showline": False},
        "yaxis_kwargs": {
            "showticklabels": True,
            "showline": True,
        },
    },
}

DEFAULT_LOCALBEDSELFIDENT_OPTIONS: Config = {
    "position": Position.RELATIVE,
    "type": DataType.BED_LOCALSELFIDENT,
    "path": "",
    "prop": 0.02,
    "options": {
        "rle": True,
        "xaxis_kwargs": {"ticks": "", "showline": False},
        "yaxis_kwargs": {"showticklabels": False, "ticks": "", "showline": False},
    },
}

DEFAULT_BEDSTRAND_OPTIONS: Config = {
    "position": Position.RELATIVE,
    "type": DataType.BEDSTRAND,
    "path": "",
    "prop": 0.02,
    "options": {
        "rle": True,
        "xaxis_kwargs": {"ticks": "", "showline": False},
        "yaxis_kwargs": {"showticklabels": False, "ticks": "", "showline": False},
    },
}

DEFAULT_SELFIDENT_OPTIONS: Config = {
    "position": Position.RELATIVE,
    "type": DataType.BEDPE_SELFIDENT,
    "path": "",
    "prop": 0.5,
    "options": {
        "rle": False,
        "xaxis_kwargs": {"title_text": "Genomic position", "showline": True},
        "yaxis_kwargs": {
            "showticklabels": False,
            "ticks": "",
            "showline": False,
            "title_text": "Self-identity",
        },
    },
}
