import dash
from typing import Any
from dash import Input, Output, callback


@callback(
    Output("url", "pathname"),
    Input("fig-chrom-navlink", "clickData", allow_optional=True),
    prevent_initial_call=True,
)
def navigate_to_page_from_chrom(click_data: dict[str, Any] | None):
    if not click_data:
        return dash.no_update
    chrom_name = click_data["points"][0]["customdata"][0]
    return chrom_name
