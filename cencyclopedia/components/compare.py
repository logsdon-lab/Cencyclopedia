import dash_uploader as du
import dash_bootstrap_components as dbc

from copy import deepcopy
from dash import dcc, html

from cencyclopedia.io.data import ALLOWED_FILETYPES
from cencyclopedia.components.err_msg import modal_error_message
from cencyclopedia.components.help import (
    popover,
    row_title_with_help,
    row_title_with_side_components,
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
            row_title_with_side_components(
                "Regions",
                [
                    (
                        dbc.ButtonGroup(
                            [
                                dbc.DropdownMenu(
                                    label="Presets",
                                    children=[
                                        dbc.DropdownMenuItem(
                                            "HGSVC", id="btn-preset-hgsvc", n_clicks=0
                                        ),
                                        dbc.DropdownMenuItem(
                                            "T2T-Primates",
                                            id="btn-preset-t2t-primates",
                                            n_clicks=0,
                                        ),
                                    ],
                                    id="dropdown-compare-preset",
                                    size="sm",
                                ),
                                dbc.Button(
                                    "Help",
                                    id="btn-help-regions",
                                    size="sm",
                                    color="secondary",
                                    n_clicks=0,
                                ),
                                popover(
                                    header="Help",
                                    body=dcc.Markdown(
                                        """
                                        ### Regions
                                        Click or drag a BED3+ file to the upload button to start.
                                        * All files are stored server-side and are deleted on session exit.
                                        * The maximum file size is 100 Mb

                                        A data table of regions will render if successful.
                                        * This is used to filter files uploaded.
                                        * All values are editable and will rerender the plot on change
                                        * Clicking the 1st column's **"x"** will remove the region.
                                        * Clicking the 2nd column's checkbox will add it to the plot.

                                        ### Presets
                                        Click a preset to load a dataset. This disables additional file uploads.
                                        * HGSVC: Human genome structural variation consortium
                                        * T2T-Primates: Telomere-to-telomere primates
                                        """
                                    ),
                                    target="btn-help-regions",
                                ),
                            ],
                        ),
                        2,
                    ),
                ],
            ),
            du.Upload(
                id="upload-regions",
                filetypes=["bed"],
                text="Upload a BED file",
                cancel_button=True,
                max_file_size=100,
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
    extensions = [
        ext.strip(".")
        for exts in ALLOWED_FILETYPES.values()
        for ext in exts  # pyright: ignore
    ]
    filetypes = ""
    filetypes_str_list = ""

    for i, (name, exts) in enumerate(ALLOWED_FILETYPES.items()):
        if i + 1 != len(ALLOWED_FILETYPES):
            filetypes_str_list += f"{name} {tuple(exts)}, "  # pyright: ignore
            filetypes += f"{name}, "
        else:
            filetypes_str_list += f"or {name} {tuple(exts)}"  # pyright: ignore
            filetypes += f"or {name}"

    return html.Div(
        [
            row_title_with_help("Files", button_id="btn-help-files"),
            popover(
                header="Help",
                target="btn-help-files",
                body=dcc.Markdown(
                    f"""
                    ### Files
                    Files can only be uploaded after a BED file is uploaded.
                    * All files are stored server-side and are deleted on session exit.
                    * The maximum file size is 100 Mb
                    * The following extensions are supported: **{filetypes_str_list}**

                    Once uploaded, additionally tabs can be added (**"Add"**) or removed (**"Remove"**).
                    * If a preset is used, only tabs can be removed.

                    ### Track layout
                    Use the arrow buttons (**"<"** or **">"**) to shift the relative position of a given file within the plot.

                    To modify BED track layout, use the "Mode" section. The following modes are possible:
                    * Condensed
                        * Default.
                    * Length
                        * Show the largest annotation at the top.
                    * Frequency
                        * Show the most frequent annotation at the top.
                    * Proportion
                        * Show the annotation covering the largest proportion of the region at the top.

                    ### Update
                    Once set, click **"Update"** to replot.
                    * *"All"* or a set number up to 50 can be drawn at a time.

                    ### Reset
                    To reset the tracks for a give data type to its default. Click the **"Reset"** button.
                    * This is only done for that data type.

                    ### Data
                    Click **"Download"** to download the data locally as a `bed.gz` file.
                    """
                ),
            ),
            du.Upload(
                id="upload-data",
                max_files=1,
                text_disabled="Upload a BED file to enable",
                text=f"Upload a {filetypes} file",
                filetypes=extensions,
                max_file_size=100,
                default_style={
                    "minHeight": "20",
                    "lineHeight": "20px",
                },
                cancel_button=True,
                disabled=True,
            ),
            dbc.ButtonGroup(
                [
                    dbc.Button(
                        "◄",
                        color="secondary",
                        id="btn-shift-data-tab-left",
                        className="d-grid col-1",
                    ),
                    dbc.Button(
                        "Add",
                        color="success",
                        id="btn-add-data-tab",
                        className="d-grid col-5",
                    ),
                    dbc.Button(
                        "Remove",
                        color="danger",
                        id="btn-delete-data-tab",
                        className="d-grid col-5",
                    ),
                    dbc.Button(
                        "►",
                        color="secondary",
                        id="btn-shift-data-tab-right",
                        className="d-grid col-1",
                    ),
                ],
                size="md",
                style={"margin-top": "15px", "width": "100%"},
            ),
            html.Br(),
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


def popout_fig_opts_components(
    fig_height: int, fig_vertical_spacing: float
) -> tuple[dbc.Button, dbc.Popover]:  # pyright:ignore
    return (
        dbc.Button(
            "Layout",
            id="btn-popup-opts-compare-fig",
            size="sm",
            n_clicks=0,
        ),
        popover(
            header="Layout",
            body=[
                dbc.Label("Height"),
                dbc.Input(
                    id="input-height-compare-fig",
                    value=fig_height,
                ),
                html.Br(),
                dbc.Label("Vertical spacing"),
                dbc.Input(
                    id="input-vertical-spacing-compare-fig",
                    min=0.0,
                    placeholder="Set 0.0 to autosize.",
                    value=fig_vertical_spacing if fig_vertical_spacing else 0.0,
                ),
                html.Br(),
                dbc.Button(
                    "Update",
                    id="btn-update-opts-compare-fig",
                    size="sm",
                    n_clicks=0,
                ),
            ],
            target="btn-popup-opts-compare-fig",
        ),
    )


def layout_compare(
    labels: list[str],
    active_tab: str | None,
    fig_height: int,
    fig_vertical_spacing: float,
):
    # https://community.plotly.com/t/scrollable-navigation-bar-in-multi-column-layout/61865/2
    return dbc.Row(
        [
            dbc.Col(
                [
                    row_title_with_side_components(
                        "Plot",
                        [
                            (
                                dbc.ButtonGroup(
                                    [
                                        *popout_fig_opts_components(
                                            fig_height=fig_height,
                                            fig_vertical_spacing=fig_vertical_spacing,
                                        ),
                                        dbc.Button(
                                            "Help",
                                            id="btn-help-plot",
                                            size="sm",
                                            color="secondary",
                                            n_clicks=0,
                                        ),
                                        popover(
                                            header="Help",
                                            body=dcc.Markdown(
                                                """
                                                1. Each track on this figure is interactive.
                                                    * Hovering over each datatype displays associated values/names.
                                                2. To zoom in, use the **"Zoom"** icon in Plotly's modal bar.
                                                3. To move around the figure, use the **"Pan"** option.
                                                4. To reset each figure, click the **"Reset axes"** icon.
                                                5. Use the **"Layout"** button on the left to resize the figure height and vertical track spacing.
                                                """
                                            ),
                                            target="btn-help-plot",
                                        ),
                                    ]
                                ),
                                2,
                            )
                        ],
                    ),
                    dbc.Spinner(html.Div(id="figures-container")),
                ],
                className="h-100 overflow-scroll",
                style={"padding-right": "1rem", "scrollbar-width": "none"},
            ),
            dbc.Col(
                [
                    layout_regions(),
                    html.Br(),
                    layout_upload(labels, active_tab),
                ],
                className="h-100 overflow-scroll",
                style={"padding-left": "1rem", "scrollbar-width": "none"},
            ),
        ],
        className="vh-100",
        style={"scrollbar-width": "none"},
    )


def tab_name(n: int) -> str:
    return f"File {n}"


def get_tab_n(name: str) -> int:
    _, n = name.split(" ")
    return int(n)


def compare_page(cfg):
    tabs = []
    # Blank config
    uploaded_cfg = deepcopy(cfg)
    uploaded_cfg["data"] = {}

    fig_height = cfg["general"]["selected_cen"]["height"]
    fig_vertical_spacing = cfg["general"]["selected_cen"]["vertical_spacing"]

    return dbc.Container(
        [
            # Config
            dcc.Store(id="cfg", data=uploaded_cfg),
            # Individual track settings
            dcc.Store(id="bed-track-settings", data={}),
            # Height
            dcc.Store(id="fig-height", data=fig_height),
            # Vertical spacing
            dcc.Store(id="fig-vertical-spacing", data=fig_vertical_spacing),
            dcc.Store(id="preset-loaded", data=False),
            modal_error_message(),
            layout_compare(
                tabs,
                active_tab=None,
                fig_height=fig_height,
                fig_vertical_spacing=fig_vertical_spacing,
            ),
        ],
        style=COMPARE_PAGE_STYLE,
    )
