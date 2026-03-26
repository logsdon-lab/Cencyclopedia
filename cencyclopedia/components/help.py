import dash_bootstrap_components as dbc

from dash import html, dcc


def row_title_with_help(title: str, button_id: str, button_width: int = 1):
    title_width = 12 - button_width
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(html.H3(title), width=title_width),
                    dbc.Col(
                        dbc.Button(
                            "?",
                            id=button_id,
                            size="sm",
                            n_clicks=0,
                        ),
                        width=button_width,
                    ),
                ]
            ),
            html.Hr(),
        ]
    )


def collapse_help(markdown: str, collapse_id: str):
    return dbc.Collapse(
        dbc.Card(dbc.CardBody(dcc.Markdown(markdown))),
        id=collapse_id,
        is_open=False,
    )
