import dash_bootstrap_components as dbc

from dash import dcc, html


def home_page():
    left_jumbotron = dbc.Col(
        html.Div(
            [
                html.H3(
                    "Centromeres vary in size, sequence, structure, and epigenetic landscapes",
                ),
                html.Hr(),
                dcc.Markdown(
                    "We discover **226 novel centromere haplotypes and 1,870 new α-satellite higher-order repeat (HOR) variants** "
                    "not represented by current reference genomes."
                ),
                dcc.Link(
                    dbc.Button(
                        "See how they compare to CHM13",
                        color="light",
                        outline=True,
                    ),
                    href="overview",
                    refresh=True,
                ),
            ],
            className="h-100 p-5 text-white bg-primary rounded-3",
        ),
        md=6,
    )

    right_jumbotron = dbc.Col(
        html.Div(
            [
                html.H3(
                    "Ancient and modern evolutionary events have shaped human centromere architecture",
                ),
                html.Hr(),
                dcc.Markdown(
                    "Using maximum-likelihood phylogenetic trees, we identify centromere haplotypes "
                    "from **chromosomes 10, 12, and 21 separated by >1 million years of evolution**. "
                    "Minor haplotypes from **chromosomes 10 and 21 have a significant enrichment of archaic hominin-specific k-mers** "
                    "suggesting the presence of introgressed DNA from Neanderthals and Denisovans in these sets of centromeres."
                ),
                dcc.Link(
                    dbc.Button(
                        "See Chromosome 10",
                        color="secondary",
                        outline=True,
                    ),
                    href="chr10",
                    refresh=True,
                ),
            ],
            className="h-100 p-5 text-dark bg-light rounded-3",
        ),
        md=6,
    )
    return html.Div(
        [
            # Home selected cen
            html.H2("Welcome to Cencyclopedia!"),
            html.Hr(),
            dcc.Markdown("""
                This website serves as a comprehensive and interactive catalog of human centromere genetic and epigenetic diversity in
                the 65 samples sequenced by the [Human Genome Structural Variation Consortium](https://www.hgsvc.org/).
            """),
            dbc.Row([left_jumbotron, right_jumbotron]),
            html.Br(),
            html.H4("Acknowledgements"),
            html.Hr(),
            dcc.Markdown("""
                We thank an anonymous reviewer for suggesting we build this interactive centromere visualization tool.
            """),
            html.H4("Cite"),
            html.Hr(),
            dcc.Markdown("""
                If you use this tool in your work, please cite:

                * *Gao S, Oshima KK, Chuang SC, Loftus M, Montanari A, Gordon DS, Human Genome Structural Variation Consortium, Human Pangenome Reference Consortium, Hsieh P, Konkel MK, Ventura M, Logsdon GA. A global view of human centromere variation and evolution. bioRxiv. 2025. p. 2025.12.09.693231. [doi:10.64898/2025.12.09.693231](https://doi.org/10.64898/2025.12.09.693231)*
            """),
        ]
    )
