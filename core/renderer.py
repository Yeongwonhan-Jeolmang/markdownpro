"""
core/renderer.py
Converts Markdown text to styled HTML using python-markdown + Pygments.
"""

from __future__ import annotations
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.toc import TocExtension
from markdown.extensions.admonition import AdmonitionExtension
from markdown.extensions.footnotes import FootnoteExtension
from markdown.extensions.attr_list import AttrListExtension
from markdown.extensions.def_list import DefListExtension
from markdown.extensions.abbr import AbbrExtension
from pygments.formatters import HtmlFormatter

_EXTENSIONS = [
    FencedCodeExtension(),
    CodeHiliteExtension(linenums=False, guess_lang=True, css_class="highlight"),
    TableExtension(),
    TocExtension(permalink=True, toc_depth="2-4"),
    AdmonitionExtension(),
    FootnoteExtension(),
    AttrListExtension(),
    DefListExtension(),
    AbbrExtension(),
    "nl2br",
    "sane_lists",
    "smarty",
    "meta",
]


class MarkdownRenderer:
    """Stateless converter: Markdown text → HTML fragment."""

    def __init__(self) -> None:
        self._md = markdown.Markdown(extensions=_EXTENSIONS)

    def render(self, text: str) -> str:
        self._md.reset()
        return self._md.convert(text)

    @staticmethod
    def pygments_css(style: str = "monokai") -> str:
        """Return Pygments CSS for the given style name.
        Falls back to 'monokai' if the requested style is not installed."""
        try:
            formatter = HtmlFormatter(style=style)
        except Exception:
            formatter = HtmlFormatter(style="monokai")
        return formatter.get_style_defs(".highlight")
