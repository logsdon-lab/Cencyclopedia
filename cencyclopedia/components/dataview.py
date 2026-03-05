import dash_bootstrap_components as dbc

from dash import html, dash_table
from cencyclopedia.plot.common import ExpandTracksSettings


def dataview_tab(
    data_table: dash_table.DataTable,
    expand_tracks: ExpandTracksSettings,
    *,
    disabled: bool = False,
):
    div_expand = html.Div(
        [
            html.H5("Expand or compress track"),
            dbc.Alert("Only applicable to BED tracks.", color="primary"),
            # We don't store by data label
            # The callback looks at the active tab to determine where to store the state.
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Button(
                            "Expand" if expand_tracks["expand"] else "Compress",
                            id="btn-expand-tracks",
                            disabled=disabled,
                        ),
                        width=2,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Mode"),
                            dbc.RadioItems(
                                ["Name", "Length", "Frequency"],
                                value=expand_tracks["mode"],
                                inline=True,
                                id="rd-expand-tracks-mode",
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
                                max=10,
                                value=expand_tracks["limit"],
                                step=1,
                                id="input-expand-tracks-limit",
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
