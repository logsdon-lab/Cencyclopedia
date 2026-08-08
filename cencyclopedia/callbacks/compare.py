import os
import dash
import pybigtools

import polars as pl
import dash_bootstrap_components as dbc

from typing import Any
from loguru import logger
from dash import html, dcc, Input, Output, State, callback, dash_table
from dash.exceptions import PreventUpdate


from cencyclopedia.components.dataview import dataview_tab
from cencyclopedia.io.data import Data, DataType
from cencyclopedia.io.config import DEFAULT_BED_OPTIONS, DEFAULT_BEDGRAPH_OPTIONS
from cencyclopedia.plot.cen import draw_cenplot
from cencyclopedia.plot.common import BedTrackSettings, DEFAULT_SETTINGS


@callback(
    Output("data-label-tabs", "active_tab"),
    Output("data-label-tabs", "children"),
    Output("bed-track-settings", "data"),
    Input("data-label-tabs", "active_tab"),
    State("data-label-tabs", "children"),
    State("bed-track-settings", "data"),
    prevent_initial_call=True,
)
def add_new_data_tab(
    active_tab: str,
    curr_tabs: list[dict[str, Any] | dbc.Tab],  # pyright: ignore
    expand_tracks: dict[str, BedTrackSettings],
) -> tuple[str, list, dict[str, BedTrackSettings]]:
    if active_tab != "+":
        raise PreventUpdate
    # Remove to add back at end
    add_tab = curr_tabs.pop()

    # Get length of tabs and add 1
    tab_n = len(curr_tabs) + 1
    new_tab_name = f"Datatype {tab_n}"
    # New data tab
    curr_tabs.append(dbc.Tab(label=new_tab_name, tab_id=new_tab_name))
    curr_tabs.append(add_tab)
    expand_tracks[new_tab_name] = DEFAULT_SETTINGS
    return (new_tab_name, curr_tabs, expand_tracks)


def delete_data_tab():
    pass


@callback(
    Output("cfg", "data"),
    Input("upload-data", "isCompleted"),
    Input("upload-data", "upload_id"),
    Input("upload-data", "fileNames"),
    State("cfg", "data"),
    State("data-label-tabs", "active_tab"),
    prevent_initial_call=True,
)
def add_uploaded_data_to_cfg(
    is_done: bool,
    upload_id: str,
    files: list[str],
    cfg: dict[str, Any],
    active_tab: str,
):
    if not is_done:
        return dash.no_update

    file = os.path.join(cfg["general"]["compare"]["tmp_dir"], upload_id, files[0])
    # Check if bigwig or bigbed
    b = pybigtools.open(file)
    if b.is_bigbed:
        opts = DEFAULT_BED_OPTIONS
        opts["type"] = DataType.BIGBED
        opts["path"] = file
    else:
        opts = DEFAULT_BEDGRAPH_OPTIONS
        opts["type"] = DataType.BIGWIG
        opts["path"] = file

    cfg["data"][active_tab] = opts
    return cfg


@callback(
    Output("data-table-container", "children"),
    Output("regions_file", "data"),
    Output("upload-data", "disabled"),
    Input("upload-regions", "isCompleted"),
    Input("upload-regions", "upload_id"),
    Input("upload-regions", "fileNames"),
    State("cfg", "data"),
    prevent_initial_call=True,
)
def draw_regions_datatable(
    is_done: bool, upload_id: str, files: list[str], cfg: dict[str, Any]
):
    if not is_done:
        return dash.no_update

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
        row_deletable=True,
        row_selectable="multi",
        column_selectable="single",
        selected_rows=[0],
        sort_action="native",
        filter_action="native",
        style_cell={"textAlign": "left"},
        style_data={"whiteSpace": "normal", "height": "auto", "lineHeight": "15px"},
    )
    return data_table, file, False


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
):
    if not cfg["data"]:
        return dash.no_update

    elements = []
    for row in selected_rows:
        rgn_info = regions[row]
        itv = (rgn_info["Chrom"], rgn_info["Start"], rgn_info["End"])
        itv_str = f"{itv[0]}:{itv[1]}-{itv[2]}"
        itv_str_plot = f"{itv[0]}<br>{itv[1]}-{itv[2]}"
        fig_res = draw_cenplot(
            itv_selected_cen=itv,
            bed_track_settings=bed_track_settings,
            cfg=cfg,
            add_yaxis_kwargs={"title_text": itv_str_plot},
        )
        if not fig_res:
            logger.debug(f"No plot for {rgn_info}")
            continue

        fig, style = fig_res
        final_fig = dcc.Graph(
            figure=fig,
            id=f"fig-{itv_str}",
            responsive=True,
            config={"displaylogo": False},
            style={**style, **{"height": 200}},
        )
        elements.append(final_fig)

    return elements


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
):
    if not is_data_uploaded:
        return dash.no_update

    data_fhs = Data(cfg["data"])

    # New tab with no uploaded data
    if active_tab not in data_fhs.cfg:
        return html.Div()
    # Display fname
    fname = os.path.basename(cfg["data"][active_tab]["path"])
    dfs: list[pl.DataFrame] = []
    for row in regions_rows:
        rgn_info = data_regions[row]
        df = data_fhs.query(
            label=active_tab,
            chrom=rgn_info["Chrom"],
            st=rgn_info["Start"],
            end=rgn_info["End"],
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
            html.Hr(),
            dataview_tab(
                data_table=data_table,
                track_settings=track_settings,
                all_disabled=disabled,
            ),
        ]
    )
