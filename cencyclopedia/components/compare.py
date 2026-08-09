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
COMPARE_PAGE_STYLE = {
    "padding": "2rem 4rem",
    "overflow": "scroll",
    # Hide scrollbar
    "scrollbar-width": "none",
}


def layout_regions() -> html.Div:
    return html.Div(
        [
            html.H2("Regions"),
            html.Hr(),
            du.Upload(
                id="upload-regions",
                filetypes=["bed"],
                text="Upload a BED file",
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
                text_disabled="Upload a BED file to enable",
                text="Upload a BED (bed.gz), bigwig (.bw) or bigBed (.bb) file",
                filetypes=ALLOWED_FILETYPES,
                default_style={
                    "minHeight": "20",
                    "lineHeight": "20px",
                },
                cancel_button=True,
                disabled=True,
            ),
            html.Br(),
            html.H2("Settings"),
            html.Hr(),
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
    # https://community.plotly.com/t/scrollable-navigation-bar-in-multi-column-layout/61865/2
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.H2("Plot"),
                    html.Hr(),
                    dbc.Spinner(html.Div(id="figures-container")),
                ],
                className="h-100 overflow-scroll",
                style={"padding-right": "1rem"},
            ),
            dbc.Col(
                [
                    layout_regions(),
                    html.Br(),
                    layout_upload(labels, active_tab),
                ],
                className="h-100 overflow-scroll",
                style={"padding-left": "1rem"},
            ),
        ],
        className="vh-100",
    )


def compare_page(cfg):
    tabs = ["Datatype 1", "+"]
    # Blank config
    uploaded_cfg = deepcopy(cfg)
    uploaded_cfg["data"] = {}

    # TODO: Parse data based on extension. Display error message otherwise.
    return dbc.Container(
        [
            # Config
            dcc.Store(id="cfg", data=uploaded_cfg),
            # Individual track settings
            dcc.Store(
                id="bed-track-settings",
                data={tabs[0]: DEFAULT_SETTINGS},
            ),
            modal_error_message(),
            layout_compare(tabs, active_tab=tabs[0]),
        ],
        style=COMPARE_PAGE_STYLE,
    )
