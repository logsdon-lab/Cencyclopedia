from typing import Any
from dash import Input, Output, callback, State

from cencyclopedia.components.overview import overview_page
from cencyclopedia.components.home import home_page
from cencyclopedia.components.tree import tree_page


@callback(
    Output("main-content", "children"),
    Input("url", "pathname"),
    State("regions", "data"),
    State("cfg", "data"),
    State("datatypes", "data"),
)
def draw_main_content_page(
    pathname: str,
    regions: str,
    cfg: dict[str, Any],
    dtypes: list[str],
):
    page = pathname.strip("/")
    if not page:
        return home_page(cfg)
    elif page == "overview":
        return overview_page(regions, cfg)
    else:
        return tree_page(page, dtypes, regions, cfg)
