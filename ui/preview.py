"""
ui/preview.py
QWebEngineView wrapper that displays the rendered HTML preview.
"""

from __future__ import annotations
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QColor
from themes import AppTheme
from core.renderer import MarkdownRenderer
from core.page_builder import build_page


class PreviewPane(QWebEngineView):
    def __init__(self, theme: AppTheme) -> None:
        super().__init__()
        self._theme = theme
        self._renderer = MarkdownRenderer()

        s = self.settings()
        if s is not None:
            s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            s.setAttribute(
                QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True
            )

        page = self.page()
        if page is not None:
            page.setBackgroundColor(QColor(theme.preview_bg))

    def update_content(self, markdown_text: str) -> None:
        fragment = self._renderer.render(markdown_text)
        code_css = MarkdownRenderer.pygments_css(self._theme.code_style)
        page_html = build_page(fragment, self._theme, code_css)
        # Preserve scroll position
        page = self.page()
        if page is not None:
            page.runJavaScript(
                "window.scrollY",
                lambda y: self._set_html_preserve_scroll(page_html, int(y) if y else 0),
            )

    def _set_html_preserve_scroll(self, html: str, scroll_y: int) -> None:
        if scroll_y > 0:
            # Connect before setHtml so the signal fires after the new page loads.
            # The handler disconnects itself after the first call to avoid stacking.
            def _on_load(_ok: bool) -> None:
                self.loadFinished.disconnect(_on_load)
                page = self.page()
                if page is not None:
                    page.runJavaScript(f"window.scrollTo(0, {scroll_y})")

            self.loadFinished.connect(_on_load)
        self.setHtml(html, QUrl("about:blank"))

    def apply_theme(self, theme: AppTheme) -> None:
        self._theme = theme
        page = self.page()
        if page is not None:
            page.setBackgroundColor(QColor(theme.preview_bg))
