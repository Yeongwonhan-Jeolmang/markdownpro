"""
core/exporter.py
Exports a rendered HTML document to HTML or PDF.
"""

from __future__ import annotations
from pathlib import Path


def export_html(html_page: str, dest: Path) -> None:
    """Write a complete HTML page to *dest*."""
    dest.write_text(html_page, encoding="utf-8")


def export_pdf(web_view, dest: Path) -> None:
    """
    Print the QWebEngineView page to PDF.
    *web_view* must be a QWebEngineView instance.
    """
    from PyQt6.QtCore import QMarginsF
    from PyQt6.QtGui import QPageLayout, QPageSize

    layout = QPageLayout(
        QPageSize(QPageSize.PageSizeId.A4),
        QPageLayout.Orientation.Portrait,
        QMarginsF(15, 15, 15, 15),
    )
    web_view.page().printToPdf(str(dest), layout)
