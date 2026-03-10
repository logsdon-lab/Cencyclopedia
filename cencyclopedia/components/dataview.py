import dash_bootstrap_components as dbc

from dash import html, dash_table
from cencyclopedia.plot.common import BedTrackSettings


def dataview_tab(
    data_table: dash_table.DataTable,
    track_settings: BedTrackSettings,
    *,
    disabled: bool = False,
):
    div_expand = html.Div(
        [
            html.H3("Modify track"),
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
                                    disabled=disabled,
                                )
                            ),
                            dbc.Row(
                                dbc.Button(
                                    "Reset",
                                    id="btn-bed-reset-tracks",
                                    color="danger",
                                    disabled=disabled,
                                )
                            ),
                        ],
                        width=2,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Expand Tracks"),
                            dbc.RadioItems(
                                ["Original", "Length", "Frequency", "Coverage"],
                                value=track_settings["mode"],
                                inline=True,
                                id="rd-bed-expand-tracks-mode",
                            ),
                        ],
                        width=2,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Track Limit"),
                            dbc.Input(
                                type="number",
                                min=1,
                                max=20,
                                value=track_settings["limit"],
                                step=1,
                                id="input-bed-expand-tracks-limit",
                                placeholder="Enter a limit to the number of tracks",
                                disabled=disabled,
                            ),
                        ]
                    ),
                ],
            ),
        ]
    )
    return [div_expand, html.Br(), html.H3("Data"), html.Hr(), data_table]
