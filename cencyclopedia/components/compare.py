import dash_uploader as du
import dash_bootstrap_components as dbc

from copy import deepcopy
from dash import dcc, html

from cencyclopedia.components.err_msg import modal_error_message
from cencyclopedia.plot.common import DEFAULT_SETTINGS


ALLOWED_FILETYPES = (
    "bb",
    "bw",
    "bed.gz",
)


def layout_regions() -> html.Div:
    return html.Div(
        [
            html.H2("Regions"),
            html.Hr(),
            du.Upload(
                id="upload-regions",
                filetypes=["bed"],
                cancel_button=True,
                default_style={
                    "minHeight": "20",
                    "lineHeight": "20px",
                },
            ),
            html.Br(),
            html.Div(id="data-table-container"),
        ]
    )


def layout_upload(labels: list[str], active_tab: str | None = None) -> html.Div:
    return html.Div(
        [
            html.H2("Upload"),
            html.Hr(),
            du.Upload(
                id="upload-data",
                max_files=1,
                filetypes=ALLOWED_FILETYPES,
                default_style={
                    "minHeight": "20",
                    "lineHeight": "20px",
                },
                cancel_button=True,
                disabled=True,
            ),
            html.Br(),
            dbc.Tabs(
                [dbc.Tab(label=label, tab_id=label) for label in labels],
                id="data-label-tabs",
                active_tab=active_tab,
            ),
            html.Br(),
            dbc.Spinner(html.Div(id="data-settings-content")),
        ]
    )


def layout_compare(labels: list[str], active_tab: str | None = None):
    if not active_tab:
        active_tab = labels[0]
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.H2("Plot"),
                    html.Hr(),
                    dbc.Spinner(html.Div(id="figures-container")),
                ],
                width=6,
            ),
            dbc.Col(
                [
                    layout_regions(),
                    html.Br(),
                    layout_upload(labels, active_tab),
                ],
                width=6,
            ),
        ]
    )


def compare_page(cfg):
    tabs = ["Datatype 1", "+"]
    # Blank config
    uploaded_cfg = deepcopy(cfg)
    uploaded_cfg["data"] = {}

    # TODO: Should also allow filtering by descriptors like maternal/paternal or species
    # TODO: Click new to add new tab and auto load new tab.
    # TODO: Parse data based on extension. Display error message otherwise.
    return html.Div(
        [
            # Config
            dcc.Store(id="cfg", data=uploaded_cfg),
            # Regions
            dcc.Store(id="selected_regions", data=[]),
            # Path to uploaded file.
            dcc.Store(id="regions_file", data=None),
            # Individual track settings
            dcc.Store(
                id="bed-track-settings",
                data={tabs[0]: DEFAULT_SETTINGS},
            ),
            modal_error_message(),
            layout_compare(tabs, active_tab=tabs[0]),
        ],
        style={
            "padding": "4rem",
        },
    )
