from dash import html, dcc

MARK_ALL = 101


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
                            html.Div("Render:"),
                            dcc.Slider(
                                step=None,
                                marks={
                                    1: "1",
                                    25: "25",
                                    50: "50",
                                    75: "75",
                                    100: "100",
                                    MARK_ALL: "All",
                                },
                                value=25,
                                id="filter-render-n",
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
                                # config={"staticPlot": True}
                            )
                        ],
                        style={
                            "width": "49%",
                            "float": "left",
                            "display": "inline-block",
                        },
                    ),
                    html.Div(
                        [
                            dcc.Dropdown([], searchable=True, id="lbl-selected-cen"),
                            dcc.Graph(
                                id="fig-selected-cen",
                            ),
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
