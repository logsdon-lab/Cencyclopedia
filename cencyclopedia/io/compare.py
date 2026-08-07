DEFAULT_BED_OPTIONS = {
    "position": "relative",
    "type": "bed",
    "prop": 0.05,
    "options": {
        "rle": False,
        "xaxis_kwargs": {"ticks": "", "showline": False},
        "yaxis_kwargs": {
            # TODO: Add title,  in settings
            "showticklabels": False,
            "ticks": "",
            "showline": False,
        },
    },
}


DEFAULT_SPACER_OPTIONS = {
    "position": "relative",
    "type": "spacer",
    "prop": 0.02,
    "options": {
        "rle": False,
        "xaxis_kwargs": {"showticklabels": False, "ticks": "", "showline": False},
        "yaxis_kwargs": {"showticklabels": False, "ticks": "", "showline": False},
    },
}

DEFAULT_BEDGRAPH_OPTIONS = {
    "position": "relative",
    "type": "bedgraph",
    "prop": 0.1,
    "options": {
        "rle": False,
        "xaxis_kwargs": {"ticks": "", "showline": False},
        "yaxis_kwargs": {
            "range": [0.0, 1.0],
            "showticklabels": False,
            "ticks": "",
            "showline": False,
        },
    },
}

DEFAULT_LOCALBEDSELFIDENT_OPTIONS = {
    "position": "relative",
    "type": "bed_localselfident",
    "prop": 0.02,
    "options": {
        "rle": False,
        "xaxis_kwargs": {"ticks": "", "showline": False},
        "yaxis_kwargs": {"showticklabels": False, "ticks": "", "showline": False},
    },
}

DEFAULT_BEDSTRAND_OPTIONS = {
    "position": "relative",
    "type": "bedstrand",
    "prop": 0.02,
    "options": {
        "rle": False,
        "xaxis_kwargs": {"ticks": "", "showline": False},
        "yaxis_kwargs": {"showticklabels": False, "ticks": "", "showline": False},
    },
}

DEFAULT_SELFIDENT_OPTIONS = {
    "position": "relative",
    "type": "bedpe_selfident",
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
