from dash import html, dcc
from cencyclopedia.io.read_cfg_data import Data


def layout(chrom_names: list[str]):
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div("Chromosome:"),
                            dcc.Dropdown(
                                chrom_names,
                                "chrY",
                                id="filter-chrom",
                            ),
                        ],
                    )
                ],
            ),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Graph(
                                id="fig-cens-clade-ordered",
                                responsive=True,
                            )
                        ],
                        style={
                            "width": "49%",
                            "float": "left",
                            "display": "inline-block",
                            # This took way too long to figure out.
                            "height": "300vh",
                        },
                    ),
                    html.Div(
                        [
                            dcc.Dropdown([], searchable=True, id="lbl-selected-cen"),
                            dcc.Graph(id="fig-selected-cen"),
                        ],
                        style={
                            "width": "49%",
                            "float": "right",
                            "display": "inline-block",
                        },
                    ),
                ],
            ),
        ]
    )
