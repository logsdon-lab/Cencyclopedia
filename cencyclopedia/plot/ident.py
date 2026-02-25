import polars as pl
import plotly.graph_objs as go


def add_ident_track(
    df_ident: pl.DataFrame,
    fig: go._figure.Figure,
    row_n: int,
    col_n: int,
) -> None:
    for row in df_ident.iter_rows(named=True):
        """
        ref_end  *        *

        ref_st   *        *
                 qry_st   qry_end
        """
        # "qry", "qry_st", "qry_end", "ref", "ref_st", "ref_end", "percent_identity_by_events", "color", "desc"
        fig.add_scatter(
            x=[
                row["qry_st"],
                row["qry_end"],
                row["qry_end"],
                row["qry_st"],
                row["qry_st"],
            ],
            y=[
                # 0, 0, 1, 1, 0
                row["ref_st"],
                row["ref_end"],
                row["ref_end"],
                row["ref_st"],
                row["ref_st"],
            ],
            fill="toself",
            line=dict(
                color=row["color"],
                width=2,
            ),
            # # https://stackoverflow.com/a/71222010
            mode="lines",
            fillcolor=row["color"],
            name=f"{row['percent_identity_by_events']}, ({row['desc']})",
            row=row_n,
            col=col_n,
            showlegend=False,
        )
