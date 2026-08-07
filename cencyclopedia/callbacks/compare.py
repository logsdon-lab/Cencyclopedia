import os
import dash
import pybigtools
import polars as pl

import dash_bootstrap_components as dbc

from typing import Any
from dash import dcc, Input, Output, State, callback, dash_table
from dash.exceptions import PreventUpdate

from cencyclopedia.io.compare import DEFAULT_BED_OPTIONS, DEFAULT_BEDGRAPH_OPTIONS
from cencyclopedia.plot.cen import draw_cenplot


@callback(
    Output("data-tabs", "active_tab"),
    Output("data-tabs", "children"),
    Input("data-tabs", "active_tab"),
    State("data-tabs", "children"),
    prevent_initial_call=True,
)
def add_new_data_tab(
    active_tab: str,
    curr_tabs: list[dict[str, Any] | dbc.Tab],  # pyright: ignore
) -> tuple[str, list]:
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
    return (new_tab_name, curr_tabs)


def delete_data_tab():
    pass


@callback(
    Output("cfg", "data"),
    Input("upload-data", "isCompleted"),
    Input("upload-data", "upload_id"),
    Input("upload-data", "fileNames"),
    State("cfg", "data"),
    State("data-tabs", "active_tab"),
    prevent_initial_call=True,
)
def add_uploaded_data_to_cfg(is_done, upload_id, files, cfg, active_tab):
    if not is_done:
        return dash.no_update

    file = os.path.join(cfg["general"]["compare"]["tmp_dir"], upload_id, files[0])
    # Read bigwig or bigbed
    b = pybigtools.open(file)
    if b.is_bigbed:
        opts = DEFAULT_BED_OPTIONS
        opts["type"] = "bigbed"
        opts["path"] = file
    else:
        opts = DEFAULT_BEDGRAPH_OPTIONS
        opts["type"] = "bigwig"
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
def render_regions_datatable(is_done, upload_id, files, cfg):
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
    State("cfg", "data"),
    State("bed-track-settings", "data"),
    prevent_initial_call=True,
)
def render_selected_region_plots(regions, selected_rows, cfg, bed_track_settings):
    elements = []
    for row in selected_rows:
        rgn_info = regions[row]
        itv = (rgn_info["Chrom"], rgn_info["Start"], rgn_info["End"])
        fig_res = draw_cenplot(
            itv_selected_cen=itv, bed_track_settings=bed_track_settings, cfg=cfg
        )
        if not fig_res:
            continue

        fig, style = fig_res
        final_fig = dbc.Spinner(
            dcc.Graph(
                figure=fig,
                id=f"fig-{itv[0]}:{itv[1]}-{itv[2]}",
                responsive=True,
                config={"displaylogo": False},
                style=style,
            )
        )
        elements.append(final_fig)

    return elements


@callback(
    Output("bed-track-settings", "data"),
    Output("data-settings-content", "children"),
    Input("cfg", "data"),
    State("data-tabs", "active_tab"),
    prevent_initial_call=True,
)
def render_settings_and_dataview_table(cfg, active_tab):
    pass
