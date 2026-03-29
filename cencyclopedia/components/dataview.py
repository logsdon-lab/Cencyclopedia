import dash_bootstrap_components as dbc

from dash import html, dash_table, dcc
from cencyclopedia.plot.common import BedTrackSettings, ALL_MODES


DEFAULT_TRACK_LIMIT = 50


def dataview_tab(
    data_table: dash_table.DataTable,
    track_settings: BedTrackSettings,
    *,
    all_disabled: bool = False,
):
    div_expand = html.Div(
        [
            # We don't store by data label
            # The callback looks at the active tab to determine where to store the state.
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Row(
                                dbc.Button(
                                    "Update",
                                    id="btn-bed-update-tracks",
                                    disabled=True or all_disabled,
                                )
                            ),
                            dbc.Row(
                                dbc.Button(
                                    "Reset",
                                    id="btn-bed-reset-tracks",
                                    color="danger",
                                    disabled=False or all_disabled,
                                )
                            ),
                        ],
                        width=2,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("View By"),
                            dbc.RadioItems(
                                ALL_MODES,
                                value=track_settings["mode"],
                                inline=True,
                                id="rd-bed-expand-tracks-mode",
                            ),
                        ],
                        width=3,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Track Limit"),
                            dcc.Dropdown(
                                value=track_settings["limit"],
                                options=["All", *range(1, DEFAULT_TRACK_LIMIT + 1)],
                                searchable=True,
                                disabled=False or all_disabled,
                                id="dropdown-bed-expand-tracks-limit",
                                placeholder="Select a limit to the number of tracks",
                            ),
                        ]
                    ),
                ],
            ),
        ]
    )
    return html.Div(
        [
            div_expand,
            html.Br(),
            html.H3("Data"),
            html.Hr(),
            html.Div(
                [
                    data_table,
                    dbc.Button("Download", id="btn-download-data"),
                    dcc.Download(id="download-data"),
                ],
                style={
                    "overflow": "scroll",
                    # Hide scrollbar
                    "scrollbar-width": "none",
                },
            ),
        ]
    )
