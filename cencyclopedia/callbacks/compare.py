import os
import pysam
import traceback
import pybigtools
import polars as pl
import dash_bootstrap_components as dbc

from typing import Any
from loguru import logger
from functools import lru_cache
from plotly.graph_objs import Figure
from frozendict import frozendict, cool
from dash.exceptions import PreventUpdate
from dash import ctx, html, dcc, Input, Output, State, callback, dash_table

from cencyclopedia.components.compare import get_tab_n, tab_name
from cencyclopedia.components.dataview import dataview_tab
from cencyclopedia.io.data import Data, DataType
from cencyclopedia.io.config import DEFAULT_BED_OPTIONS, DEFAULT_BEDGRAPH_OPTIONS
from cencyclopedia.plot.cen import draw_cenplot
from cencyclopedia.plot.common import BedTrackSettings, DEFAULT_SETTINGS


Tabs = list[dict[str, Any] | dbc.Tab]  # pyright:ignore


@callback(
    Output("btn-add-data-tab", "disabled"),
    Output("btn-delete-data-tab", "disabled"),
    Input("cfg", "data"),
    Input("data-label-tabs", "active_tab"),
)
def enable_add_del_btn(cfg: dict[str, Any], active_tab: str) -> tuple[bool, bool]:
    is_enabled = active_tab not in cfg["data"]
    return is_enabled, is_enabled


def get_new_tab_info(
    curr_tabs: Tabs,
    expand_tracks: dict[str, BedTrackSettings],
) -> tuple[str, list, dict[str, BedTrackSettings]]:
    # Get max n of tabs and add 1
    if curr_tabs:
        tab_n = max([get_tab_n(tab["props"]["tab_id"]) for tab in curr_tabs]) + 1
    else:
        tab_n = 1

    new_tab_name = tab_name(tab_n)
    # New data tab
    curr_tabs.append(dbc.Tab(label=new_tab_name, tab_id=new_tab_name))
    expand_tracks[new_tab_name] = DEFAULT_SETTINGS
    return (new_tab_name, curr_tabs, expand_tracks)


@callback(
    Output("data-label-tabs", "active_tab"),
    Output("data-label-tabs", "children"),
    Output("bed-track-settings", "data"),
    Input("btn-add-data-tab", "n_clicks"),
    State("data-label-tabs", "children"),
    State("bed-track-settings", "data"),
    prevent_initial_call=True,
)
def add_new_data_tab_manual(
    n_clicks: int | None,
    curr_tabs: Tabs,
    expand_tracks: dict[str, BedTrackSettings],
) -> tuple[str, list, dict[str, BedTrackSettings]]:
    """
    Adds a new data tab when add button is manula pressed.
    """
    if not n_clicks or not ctx.triggered_id == "btn-add-data-tab":
        raise PreventUpdate
    new_tab_id, curr_tabs, expand_tracks = get_new_tab_info(curr_tabs, expand_tracks)
    return (new_tab_id, curr_tabs, expand_tracks)


@callback(
    Output("data-label-tabs", "active_tab", allow_duplicate=True),
    Output("data-label-tabs", "children", allow_duplicate=True),
    Output("cfg", "data", allow_duplicate=True),
    Input("btn-delete-data-tab", "n_clicks"),
    Input("data-label-tabs", "active_tab"),
    State("data-label-tabs", "children"),
    State("cfg", "data"),
    prevent_initial_call=True,
)
def delete_data_tab(
    n_clicks: int | None,
    active_tab: str,
    curr_tabs: Tabs,
    cfg: dict[str, Any],
) -> tuple[str | None, Tabs, dict[str, Any]]:
    if not n_clicks or not ctx.triggered_id == "btn-delete-data-tab":
        raise PreventUpdate

    # Find tab to delete and get next tab
    delete_tab_idx = None
    for i, tab in enumerate(curr_tabs):
        if tab["props"]["tab_id"] == active_tab:
            delete_tab_idx = i
            break

    if not isinstance(delete_tab_idx, int):
        raise RuntimeError(
            f"Active tab ({active_tab}) must exist in tabs ({curr_tabs})"
        )

    # Remove tab
    try:
        curr_tabs.pop(delete_tab_idx)
    except IndexError:
        raise RuntimeError("Invalid idx to delete.")

    try:
        next_tab_id = next(iter(curr_tabs))["props"]["tab_id"]
    except (StopIteration, KeyError):
        next_tab_id = None

    # Cleanup file
    try:
        opts = cfg["data"].pop(active_tab)
    except KeyError:
        raise PreventUpdate

    try:
        os.remove(opts["path"])
    except FileNotFoundError:
        pass

    logger.info(f"Deleted tab, {active_tab}. New active tab: {next_tab_id}")
    return next_tab_id, curr_tabs, cfg


@callback(
    Output("data-label-tabs", "active_tab", allow_duplicate=True),
    Output("data-label-tabs", "children", allow_duplicate=True),
    Output("bed-track-settings", "data", allow_duplicate=True),
    Output("cfg", "data"),
    Input("upload-data", "isCompleted"),
    Input("upload-data", "upload_id"),
    Input("upload-data", "fileNames"),
    State("cfg", "data"),
    State("data-label-tabs", "active_tab"),
    State("data-label-tabs", "children"),
    State("bed-track-settings", "data"),
    prevent_initial_call=True,
)
def add_uploaded_data_to_cfg(
    is_done: bool,
    upload_id: str,
    files: list[str],
    cfg: dict[str, Any],
    active_tab: str,
    curr_tabs: Tabs,
    expand_tracks: dict[str, BedTrackSettings],
) -> tuple[
    str,
    Tabs,
    dict[str, BedTrackSettings],
    dict[str, Any],
]:
    if not is_done:
        raise PreventUpdate

    fname = files[0]
    _, ext = os.path.splitext(fname)
    fpath = os.path.join(cfg["general"]["compare"]["tmp_dir"], upload_id, fname)

    # Check if bigwig or bigbed
    # TODO: Message
    if ext == ".bb" or ext == ".bw":
        try:
            # Check valid bigwig/bigbed
            b = pybigtools.open(fpath)
        except Exception as err:
            raise RuntimeError(f"Cannot read file with bigtools: {err}")

        if b.is_bigbed:
            opts = DEFAULT_BED_OPTIONS
            opts["type"] = DataType.BIGBED
        else:
            opts = DEFAULT_BEDGRAPH_OPTIONS
            opts["type"] = DataType.BIGWIG
    elif ext == ".bed.gz":
        try:
            # Check valid bgzipped file
            pysam.tabix_index(fpath)
        except Exception as err:
            raise RuntimeError(f"Cannot index tabix bgzipped file: {err}")

        opts = DEFAULT_BED_OPTIONS
        opts["type"] = DataType.BED9
    else:
        raise ValueError("Invalid datatype extension")

    # Add new tab in case none exist
    if not active_tab:
        new_tab_id, curr_tabs, expand_tracks = get_new_tab_info(
            curr_tabs, expand_tracks
        )
        logger.info(f"Added new tab, {new_tab_id}.")
    else:
        new_tab_id = active_tab

    opts["path"] = fpath
    cfg["data"][new_tab_id] = opts
    return new_tab_id, curr_tabs, expand_tracks, cfg


@callback(
    Output("data-table-container", "children"),
    Output("upload-data", "disabled"),
    Input("upload-regions", "isCompleted"),
    Input("upload-regions", "upload_id"),
    Input("upload-regions", "fileNames"),
    State("cfg", "data"),
    prevent_initial_call=True,
)
def draw_regions_datatable(
    is_done: bool, upload_id: str, files: list[str], cfg: dict[str, Any]
) -> tuple[dash_table.DataTable, bool]:
    if not is_done:
        raise PreventUpdate

    file = os.path.join(cfg["general"]["compare"]["tmp_dir"], upload_id, files[0])

    df = pl.read_csv(
        file,
        separator="\t",
        has_header=False,
        comment_prefix="#",
        # Anything after the first three are treated as metadata
        new_columns=["Chrom", "Start", "End"],
    )

    data_table = dash_table.DataTable(
        id="datatable-regions",
        data=list(df.iter_rows(named=True)),  # pyright: ignore
        columns=[
            {
                "name": col,
                "id": col,
                "selectable": True,
            }
            for col in df.columns
        ],
        page_size=5,
        editable=True,
        row_deletable=True,
        row_selectable="multi",
        column_selectable="single",
        selected_rows=[0],
        sort_action="native",
        filter_action="native",
        style_cell={"textAlign": "left"},
        style_data={"whiteSpace": "normal", "height": "auto", "lineHeight": "15px"},
    )
    return data_table, False


@lru_cache(maxsize=20)
def draw_cenplot_cached(
    itv: tuple[str, int, int] | None,
    bed_track_settings: frozendict[str, BedTrackSettings] | None,
    cfg: frozendict[str, Any],
    add_yaxis_kwargs: frozendict[str, Any],
) -> tuple[Figure, dict[str, Any]] | None:
    return draw_cenplot(
        itv_selected_cen=itv,
        bed_track_settings=bed_track_settings,
        cfg=cfg,
        add_yaxis_kwargs=add_yaxis_kwargs,
    )


@callback(
    Output("figures-container", "children"),
    Input("datatable-regions", "data"),
    Input("datatable-regions", "selected_rows"),
    Input("cfg", "data"),
    Input("bed-track-settings", "data"),
    prevent_initial_call=True,
)
def draw_selected_region_plots(
    regions: list[dict[str, Any]],
    selected_rows: list[int],
    cfg: dict[str, Any],
    bed_track_settings: dict[str, BedTrackSettings],
) -> list[dcc.Graph]:
    # If no data (just init)
    if not cfg["data"]:
        return []

    # Convert to immutable frozendict to hash
    fcfg = cool.deepfreeze(cfg)
    fbed_track_settings = cool.deepfreeze(bed_track_settings)

    # https://stackoverflow.com/a/5884123
    figures = []
    for row in sorted(selected_rows):
        rgn_info = regions[row]
        try:
            st, end = int(rgn_info["Start"]), int(rgn_info["End"])
        except ValueError:
            logger.error(f"Invalid st and end: {rgn_info}")
            continue

        itv = (rgn_info["Chrom"], st, end)
        itv_str = f"{itv[0]}:{itv[1]}-{itv[2]}"
        itv_str_plot = f"{itv[0]}<br>{itv[1]}-{itv[2]}"

        # Cache existing plots
        try:
            fig_res = draw_cenplot_cached(
                itv=itv,
                bed_track_settings=fbed_track_settings,
                cfg=fcfg,
                add_yaxis_kwargs=frozendict({"title_text": itv_str_plot}),
            )
        except Exception as err:
            tbk = traceback.format_exc()
            logger.error(
                f"Failed to draw compare plot for {rgn_info}: {err}\ntrace: {tbk}"
            )
            continue

        if not fig_res:
            logger.error(f"No plot for {rgn_info}")
            continue

        fig, style = fig_res
        final_fig = dcc.Graph(
            figure=fig,
            id=f"fig-{itv_str}",
            responsive=True,
            config={"displaylogo": False},
            style={**style, **{"height": 200}},
        )
        figures.append(final_fig)

    return figures


@callback(
    Output("data-settings-content", "children"),
    Input("cfg", "data"),
    Input("upload-data", "isCompleted"),
    Input("data-label-tabs", "active_tab"),
    Input("datatable-regions", "data"),
    Input("datatable-regions", "selected_rows"),
    State("bed-track-settings", "data"),
    prevent_initial_call=True,
)
def draw_settings_and_dataview_table(
    cfg: dict[str, Any],
    is_data_uploaded: bool,
    active_tab: str,
    data_regions: list[dict[str, Any]],
    regions_rows: list[int],
    expand_tracks: dict[str, BedTrackSettings],
) -> html.Div:
    if not is_data_uploaded:
        raise PreventUpdate

    data_fhs = Data(cfg["data"])

    # New tab with no uploaded data
    if active_tab not in data_fhs.cfg:
        return html.Div()

    # Display fname
    fname = os.path.basename(cfg["data"][active_tab]["path"])
    dfs: list[pl.DataFrame] = []
    for row in regions_rows:
        rgn_info = data_regions[row]
        try:
            st, end = int(rgn_info["Start"]), int(rgn_info["End"])
        except ValueError:
            logger.error(f"Invalid st and end: {rgn_info}")
            continue

        df = data_fhs.query(
            label=active_tab, chrom=rgn_info["Chrom"], st=st, end=end, to_relative=False
        )
        if not isinstance(df, pl.DataFrame):
            logger.debug(f"No data found for {active_tab} and {rgn_info}")
            continue
        dfs.append(df)

    if dfs:
        df_all = pl.concat(dfs)
    else:
        df_all = pl.DataFrame()

    data_table = dash_table.DataTable(
        id="datatable-active-tab",
        data=list(df_all.iter_rows(named=True)),  # pyright: ignore
        columns=[
            {
                "name": col,
                "id": col,
                "selectable": True,
            }
            for col in df_all.columns
        ],
        page_size=5,
        column_selectable="single",
        selected_rows=[0],
        sort_action="native",
        filter_action="native",
        style_cell={"textAlign": "left"},
        style_data={"whiteSpace": "normal", "height": "auto", "lineHeight": "15px"},
    )
    track_settings = expand_tracks[active_tab]
    dtype = data_fhs.datatype(active_tab)
    disabled = not dtype.is_expandable() if dtype else True
    return html.Div(
        [
            html.H3(fname),
            html.Br(),
            dataview_tab(
                data_table=data_table,
                track_settings=track_settings,
                all_disabled=disabled,
            ),
        ]
    )
