import dash
import polars as pl

from PIL import Image
from typing import Any
from loguru import logger
from dash import Input, Output, callback, dcc, State, get_asset_url, ctx

from cencyclopedia.plot.tree import create_tree_figure
from cencyclopedia.components.main import (
    main_content,
    dataview_selected_cen,
)
from cencyclopedia.components.overview import overview_page
from cencyclopedia.components.home import home_page
from cencyclopedia.io.common import get_regions


@callback(
    Output("collapse-howto-tree", "is_open"),
    [Input("btn-collapse-howto-tree", "n_clicks")],
    [State("collapse-howto-tree", "is_open")],
)
def toggle_howto_tree_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


@callback(
    Output("itv-selected-cen", "data", allow_duplicate=True),
    # Need to reset to None or will trigger in future invocations.
    Output("btn-reset-itv-selected-cen", "n_clicks"),
    Input("btn-reset-itv-selected-cen", "n_clicks"),
    Input("rng-itv-selected_cens", "value"),
    State("itv-selected-cen", "data"),
    State("regions", "data"),
    prevent_initial_call=True,
)
def update_itv_selected_cen_from_ui(
    reset_clicks: int | None,
    rng_itv_selected_cen: list[int],
    itv_selected_cen: tuple[str, int, int],
    regions: str,
) -> dash._callback.NoUpdate | tuple[str, int, int] | tuple[Any, ...]:
    logger.debug(f"Update context from selection UI: {ctx.triggered}")
    try:
        rng_st, rng_end = rng_itv_selected_cen
        rng_st, rng_end = int(rng_st), int(rng_end)
    except Exception:
        return dash.no_update, dash.no_update

    # Doesn't matter if p or q
    if reset_clicks:
        itv = (
            pl.scan_csv(regions)
            .filter(pl.col("chrom").eq(itv_selected_cen[0]))
            .select("chrom", "chrom_st", "chrom_end")
            .collect()
            .row(0)
        )
        return itv, None

    if rng_st == itv_selected_cen[1] and rng_end == itv_selected_cen[2]:
        return dash.no_update

    itv = (itv_selected_cen[0], rng_st, rng_end)
    return itv, None


@callback(
    Output("main-content", "children"),
    Output("itv-selected-cen", "data", allow_duplicate=True),
    Input("url", "pathname"),
    State("regions", "data"),
    State("cfg", "data"),
    State("datatypes", "data"),
    prevent_initial_call="initial_duplicate",
)
def draw_main_content_page(
    pathname: str,
    regions: str,
    cfg: dict[str, Any],
    dtypes: list[str],
):
    page = pathname.strip("/")
    if not page:
        return home_page(), None
    elif page == "overview":
        return overview_page(regions, cfg), None
    else:
        chrom_name = page
        logger.debug(f"On {chrom_name}")
        if not chrom_name:
            return []

        df_regions_chrom = get_regions(regions, chrom_name)
        dfs_regions_chrom_arm: dict[tuple[Any, ...], pl.DataFrame] = (
            df_regions_chrom.partition_by(["arm"], maintain_order=True, as_dict=True)
        )
        all_chroms = df_regions_chrom["chrom"].unique(maintain_order=True).to_list()
        itv_selected_cen = (
            df_regions_chrom.filter(pl.col("chrom").eq(pl.lit(all_chroms[0])))
            .select("chrom", "chrom_st", "chrom_end")
            .row(0)
        )

        fname = f"{chrom_name}_PhylogeneticTree_p_q-arm_withLegend.png"
        try:
            path = get_asset_url(fname)
            fig = create_tree_figure(Image.open(path), dfs_regions_chrom_arm, cfg)
        except (OSError, KeyError):
            logger.error(f"Cannot open image ({fname}) for {chrom_name} tree")
            fig = None

        content = main_content(
            fig_tree=dcc.Graph(
                figure=fig,
                id="fig-cens-tree",
                responsive=True,
                config={"displaylogo": False, "displayModeBar": True},
            ),
            dropdown=dcc.Dropdown(
                all_chroms,
                value=itv_selected_cen[0],
                searchable=True,
                id="dropdown-selected-cen",
            ),
            dataview_selected_cen=dataview_selected_cen(
                dtypes,
                active_tab=cfg["general"]["selected_cen"].get("default_data_tab"),
            ),
            cfg=cfg,
        )
        return content, itv_selected_cen
