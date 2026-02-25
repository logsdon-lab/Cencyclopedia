import math
import polars as pl

IDENT_BREAKPOINTS = (
    85.0,
    90.0,
    95.0,
    97.5,
    98.0,
    98.5,
    98.75,
    99.0,
    99.25,
    99.5,
    99.75,
    100.0,
)
IDENT_COLORS = (
    "#4b3991",
    "#2974af",
    "#4a9da8",
    "#57b894",
    "#9dd893",
    "#e1f686",
    "#ffffb2",
    "#fdda79",
    "#fb9e4f",
    "#ee5634",
    "#c9273e",
    "#8a0033",
)


def read_identity_breakpoints(
    infile: str | None,
) -> tuple[tuple[float, ...], tuple[str, ...]]:
    if not infile:
        return IDENT_BREAKPOINTS, IDENT_COLORS

    pair_idents_colors: list[tuple[float, Str]] = []
    with open(infile, "rt") as fh:
        for line in fh:
            ident, hexcode_color = line.strip().split("\t")
            pair_idents_colors.append((float(ident), hexcode_color))

    assert len(pair_idents_colors) > 0, "Need at least one identity breakpoint"
    pair_idents_colors.sort(key=lambda x: x[0])

    idents, colors = zip(*pair_idents_colors)
    assert len(idents) == len(colors), (
        "Identity breakpoints and colors must be equal length. "
        "This is different from ModDotPlot in that the each breakpoint is the ending identity. "
        "ex. 80, 90, 100 -> (0-80), (80-90), (90-100)"
    )
    return idents, colors
