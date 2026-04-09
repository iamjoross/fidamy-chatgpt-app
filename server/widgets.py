"""Widget definitions and static asset loading for the quotation server."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class QuoteWidget:
    identifier: str
    title: str
    template_uri: str
    invoking: str
    invoked: str
    html: str
    response_text: str


ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
MIME_TYPE = "text/html+skybridge"


@lru_cache(maxsize=None)
def load_widget_html(component_name: str) -> str:
    html_path = ASSETS_DIR / f"{component_name}.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf8")

    fallback_candidates = sorted(ASSETS_DIR.glob(f"{component_name}-*.html"))
    if fallback_candidates:
        return fallback_candidates[-1].read_text(encoding="utf8")

    raise FileNotFoundError(
        f'Widget HTML for "{component_name}" not found in {ASSETS_DIR}. '
        "Run `pnpm run build` to generate the assets before starting the server."
    )


WIDGETS = [
    QuoteWidget(
        identifier="quote",
        title="Generate quotation",
        template_uri="ui://widget/quote.html",
        invoking="Preparing your quotation",
        invoked="Served a fresh quotation",
        html=load_widget_html("quote"),
        response_text="Rendered quotation details!",
    ),
]

WIDGETS_BY_ID = {widget.identifier: widget for widget in WIDGETS}
WIDGETS_BY_URI = {widget.template_uri: widget for widget in WIDGETS}


def resource_description(widget: QuoteWidget) -> str:
    return f"{widget.title} widget markup"


def tool_meta(widget: QuoteWidget) -> dict[str, str | bool]:
    return {
        "openai/outputTemplate": widget.template_uri,
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
        "openai/widgetAccessible": True,
    }


def tool_invocation_meta(widget: QuoteWidget) -> dict[str, str]:
    return {
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
    }
