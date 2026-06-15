#!/usr/bin/env python3
"""
main.py
Entry point for MarkdownPro.

Usage:
    python main.py [file.md]
"""

import sys
import os

# Ensure local packages resolve correctly
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from ui.main_window import MainWindow
from pathlib import Path


def main() -> None:
    # HiDPI
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("MarkdownPro")
    app.setOrganizationName("MarkdownPro")

    # Default font
    font = QFont("Inter", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    window = MainWindow()

    # Open file passed as argument
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if path.exists() and path.suffix in (".md", ".markdown", ".txt"):
            from core.document import Document

            window._document = Document.open(path)
            window._editor.setPlainText(window._document.text)
            window._status.set_file(window._document.display_name)
            if window._document.path is not None:
                window.setWindowTitle(f"MarkdownPro – {window._document.path.name}")

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
