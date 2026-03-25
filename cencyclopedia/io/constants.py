RGX_SM_CHROM = r"^(?<sample>.*?)_(rc-)*(?<chrom_name>chr[0-9XY]+)[_:]*"
CHROM_NAMES = [f"chr{i}" for i in (*range(1, 23), "X", "Y")]
IDENT_BREAKPOINTS = (
    90.0,
    97.5,
    97.75,
    98.0,
    98.25,
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
