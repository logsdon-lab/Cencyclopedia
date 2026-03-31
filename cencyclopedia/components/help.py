import dash_bootstrap_components as dbc

from dash import html


def row_title_with_help(title: str, button_id: str, button_width: int = 1):
    title_width = 12 - button_width
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(html.H3(title), width=title_width),
                    dbc.Col(
                        dbc.Button(
                            "Help",
                            id=button_id,
                            size="sm",
                            color="secondary",
                            n_clicks=0,
                        ),
                        width=button_width,
                    ),
                ]
            ),
            html.Hr(),
        ]
    )


def popover(header: str, body, target: str):
    return dbc.Popover(
        [
            dbc.PopoverHeader(header),
            dbc.PopoverBody(body),
        ],
        target=target,
        placement="auto",
        trigger="click",
        style={"max-width": "400px"},
    )
