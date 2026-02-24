import yaml
import pysam
import polars as pl
import plotly.graph_objs as go

# from .bed_ident import read_bed_identity

from typing import Self, Any, Literal, Iterator, NamedTuple
from plotly.subplots import make_subplots

RGX_SM_CHROM = r"^(?<sample>.*?)_(?<chrom_name>chr[0-9XY]+)[_:]*"
MARK_ALL = 101

from dash import Dash, html, dcc, Input, Output, callback


def add_ident_track(
    infile: str, chrom: str, fig: go._figure.Figure, row: int, col: int
) -> None:
    df_bedpe = None
    df_ident = None
    for grp, df_grp in df_ident.group_by(
        ["group", "color", "percent_identity_by_events"]
    ):
        group, color, percent_identity_by_events = grp

        fig.add_scatter(
            x=df_grp["x"],
            y=df_grp["y"],
            fill="toself",
            line=dict(
                color=color,
                width=2,
            ),
            hovertemplate=f"%{{x}}, %{{y}}, {percent_identity_by_events}",
            # https://stackoverflow.com/a/71222010
            mode="text",
            fillcolor=color,
            row=row,
            col=col,
            showlegend=False,
        )


def add_bedgraph_track(df_bg: pl.DataFrame, fig: go._figure.Figure, row_n: int, col_n: int):
    for row in df_bg.iter_rows(named=True):
        fig.add_scatter(
            fill="toself",
            x=[
                    row["chrom_st"],
                    row["chrom_end"],
                    row["chrom_end"],
                    row["chrom_st"],
                    row["chrom_st"],
                ],
            y=[0, 0, row["name"], row["name"], 0],
            line=dict(color="#000000", width=2),
            mode="text",
            fillcolor="#000000",
            row=row_n,
            col=col_n,
            showlegend=False,
        )

def add_bed_track(df_bed: pl.DataFrame, fig: go._figure.Figure, row_n: int, col_n: int):
    for grp, df in df_bed.group_by(["name", "color", "zorder"]):
        x, y = [], []
        name, color, zorder = grp
        for row in df.iter_rows(named=True):
            x.extend(
                [
                    row["chrom_st"],
                    row["chrom_end"],
                    row["chrom_end"],
                    row["chrom_st"],
                    row["chrom_st"],
                    None,
                ]
            )
            y.extend([0, 0, 1, 1, 0, None])

        fig.add_scatter(
            fill="toself",
            x=x,
            y=y,
            line=dict(
                color=color,
                width=2,
            ),
            name=name,
            mode="text",
            fillcolor=color,
            row=row_n,
            col=col_n,
            showlegend=False,
            zorder=zorder
        )

def read_bedgraph_row(rec: Any):
    return (rec.contig, rec.start, rec.end, rec.name)

def read_bedstrand_row(rec: Any):
    return (rec.contig, rec.start, rec.end, rec.strand)

def read_bed9_row(rec: Any):
    try:
        name = rec.name
    except KeyError:
        name = "."
    try:
        item_rgb = rec.itemRGB
    except KeyError:
        item_rgb = "#000000"
    return (rec.contig, rec.start, rec.end, name, item_rgb)


# This is unsafe if shared.
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


    def datatype(self, label: str) -> Literal["bed", "bedgraph", "bedstrand", "bedpe_selfident"]:
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

    def query(self, label: str, chrom: str, st: int, end: int, *, to_relative: bool = True) -> pl.DataFrame:
        qry = self.fhs[label].fetch(chrom, st, end, parser=pysam.asBed())
        if self.cfg[label]["type"] == "bed9":
            read_fn = read_bed9_row
            cols = ["chrom", "chrom_st", "chrom_end", "name", "color"]
            # Plot larger first.
            expr_add_zorder = (pl.col("chrom_end") - pl.col("chrom_st")).sort()
        elif self.cfg[label]["type"] == "bedstrand":
            read_fn = read_bedstrand_row
            cols = ["chrom", "chrom_st", "chrom_end", "name"]
            expr_add_zorder = pl.lit(1)
        elif self.cfg[label]["type"] == "bedgraph":
            read_fn = read_bedgraph_row
            cols = ["chrom", "chrom_st", "chrom_end", "name"]
            expr_add_zorder = pl.lit(1)
        else:
            read_fn = read_bed9_row
            cols = ["chrom", "chrom_st", "chrom_end", "name", "color"]
            # Plot larger first.
            expr_add_zorder = (pl.col("chrom_end") - pl.col("chrom_st")).sort()

        df = pl.DataFrame(
            data=[read_fn(rec) for rec in qry],
            orient="row",
            schema=cols,
        )
        
        df = df.with_columns(
            zorder=expr_add_zorder
        )
        if not to_relative:
            return df
        else:
            return df.with_columns(
                pl.col("chrom_st") - pl.col("chrom_st").min().over("chrom"),
                pl.col("chrom_end") - pl.col("chrom_st").min().over("chrom"),
            )

def read_regions(cfg: dict[str, Any]) -> pl.DataFrame:
    DF_REGIONS = (
        pl.read_csv(
            cfg["regions"],
            separator="\t",
            has_header=False,
            columns=[0, 1, 2],
            new_columns=["chrom", "chrom_st", "chrom_end"],
        )
        .with_columns(mtch=pl.col("chrom").str.extract_groups(RGX_SM_CHROM))
        .unnest("mtch")
    )
    DF_CLADES = (
        pl.read_csv(
            cfg["clades"],
            separator="\t",
            has_header=False,
            new_columns=["chrom", "clade", "arm"],
        )
        .with_columns(mtch=pl.col("chrom").str.extract_groups(RGX_SM_CHROM))
        .unnest("mtch")
    )
    DF_METADATA = pl.read_csv(
        cfg["sample_metadata"],
        separator="\t",
        has_header=False,
        new_columns=["sample", "population", "gender"],
    )
    DF_REGIONS = DF_REGIONS.join(DF_CLADES, on=["chrom", "sample", "chrom_name"]).join(
        DF_METADATA, on=["sample"]
    )

    return DF_REGIONS


# https://github.com/slowkow/pytabix
with open("config.yaml", "rb") as fh:
    cfg = yaml.safe_load(fh)

app = Dash(__name__, external_stylesheets=cfg["app"]["stylesheets"])

df_regions = read_regions(cfg)

app.layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.Div("Chromosome:"),
                        dcc.Dropdown(
                            list(df_regions["chrom_name"].unique()),
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
                        dcc.Dropdown(
                            [],
                            searchable=True,
                            id="lbl-selected-cen"
                        ),
                        dcc.Graph(
                            id="fig-selected-cen",
                        )
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

@callback(
    Output("fig-selected-cen", "figure"),
    Input("lbl-selected-cen", "value"),
)
def draw_selected_cen(ctg: str):
    df_region = df_regions.filter(pl.col("chrom").eq(ctg) & pl.col("arm").eq(pl.lit("q")))
    if df_region.is_empty():
        raise ValueError(f"Invalid ctg: {ctg}")

    # Open tabix file handles
    data_fhs = Data.new(cfg["data"])

    region = df_region.row(0, named=True)
    props = []
    nrows = 0
    indices = {}
    for dtype, idx, prop in data_fhs.track_params:
        indices[dtype] = idx
        if not prop:
            continue
        nrows += 1
        props.append(prop)

    fig: go._figure.Figure = make_subplots(
        rows=nrows,
        cols=1,
        shared_xaxes=True,
        row_heights=props
    )

    for label, idx in indices.items():
        df = data_fhs.query(label, region["chrom"], region["chrom_st"], region["chrom_end"], to_relative=False)
        dtype = data_fhs.datatype(label)
        if dtype == "bed":
            add_bed_track(df, fig, idx, 1)
        elif dtype == "bedgraph":
            add_bedgraph_track(df, fig, idx, 1)
        else:
            pass

    fig.update_layout(
        template="simple_white",
        xaxis={"showgrid": False},
        yaxis={"showgrid": False},
    )
    # https://plotly.com/python/reference/layout/xaxis/
    fig.update_xaxes(showline=False)
    fig.update_yaxes(showticklabels=False, ticks="", showline=False)
    return fig

@callback(
    Output("fig-cens-clade-ordered", "figure"),
    Output("lbl-selected-cen", "options"),
    Output("lbl-selected-cen", "value"),
    Input("filter-chrom", "value"),
    Input("filter-render-n", "value"),
)
def update_fig_cens(chrom: str, render_n: int):
    df_regions_chrom = df_regions.filter(
        pl.col("chrom_name").eq(chrom) & pl.col("arm").eq(pl.lit("q"))
    ).sort(by=["clade"])
    rows = list(df_regions_chrom.iter_rows(named=True))
    if render_n == MARK_ALL:
        nrows = len(rows)
    else:
        nrows = render_n
    data_fhs = Data.new(cfg["data"])

    fig: go._figure.Figure = make_subplots(
        rows=nrows, cols=2, shared_xaxes=True, column_widths=[0.1, 0.9]
    )
    rendered_cens = []
    for i in range(1, nrows + 1):
        try:
            row = rows[i]
        except IndexError:
            break
        df_hor = data_fhs.query(
            "as_hor_stv", row["chrom"], row["chrom_st"], row["chrom_end"], to_relative=True
        )
        print(f"On {i}, {row}")
        # Add label
        # https://community.plotly.com/t/can-axis-title-position-be-changed/72794/3
        fig.add_annotation(row=i, col=1, text=row["chrom"], showarrow=False)
        # Disable interaction with label annotation.
        fig.update_xaxes(
            fixedrange=True,
            showticklabels=False,
            ticks="",
            showline=False,
            row=i,
            col=1,
        )
        fig.update_yaxes(fixedrange=True, row=i, col=1)
        add_bed_track(df_bed=df_hor, fig=fig, row_n=i, col_n=2)
        rendered_cens.append(row["chrom"])

    fig.update_layout(
        template="simple_white",
        xaxis={"showgrid": False},
        yaxis={"showgrid": False},
        height=max(50.0 * nrows, 700.0),
    )
    # https://plotly.com/python/reference/layout/xaxis/
    fig.update_xaxes(showline=False)
    fig.update_yaxes(showticklabels=False, ticks="", showline=False)

    return fig, rendered_cens, rendered_cens[0]


if __name__ == "__main__":
    app.run(debug=True, port=8080)
