import dash_bootstrap_components as dbc
from dash import html, dcc


def modal_body_content(
    msg: str,
    ctx: str = "plotting",
    likely_issue: str = "This is likely due to track spacing. Please try again with different settings.",
) -> dcc.Markdown:
    return dcc.Markdown(
        f"""
        Encountered an issue during {ctx}.
        ```
        {msg.replace("\n", " ")}
        ```

        {likely_issue}

        If unable to fix, please report this text on the GitHub [issue tracker](https://github.com/logsdon-lab/Cencyclopedia/issues).
        """
    )


def modal_error_message():
    return html.Div(
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Error")),
                dbc.ModalBody(id="body-err-msg"),
            ],
            id="modal-err-msg",
            is_open=False,
        )
    )
