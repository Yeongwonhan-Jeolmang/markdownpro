"""
ui/statusbar.py
Custom status bar with word/char/line counts and theme/mode indicators.
"""

from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from themes import AppTheme


class StatusBar(QWidget):
    def __init__(self, theme: AppTheme) -> None:
        super().__init__()
        self._theme = theme
        self.setFixedHeight(28)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(0)

        self._file_label = QLabel("Untitled")
        self._spacer = QLabel()
        self._stats_label = QLabel("0 words · 0 chars · 1 line")
        self._mode_label = QLabel("Split")

        for lbl in (
            self._file_label,
            self._spacer,
            self._stats_label,
            self._mode_label,
        ):
            lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self._file_label)
        layout.addWidget(self._spacer, 1)
        layout.addWidget(self._stats_label)
        layout.addSpacing(20)
        layout.addWidget(self._mode_label)

        self.apply_theme(theme)

    def apply_theme(self, theme: AppTheme) -> None:
        self._theme = theme
        self.setStyleSheet(f"""
            QWidget {{
                background: {theme.bg};
                border-top: 1px solid {theme.border};
            }}
            QLabel {{
                color: {theme.fg_dim};
                font-family: 'Inter', 'Helvetica Neue', system-ui, sans-serif;
                font-size: 11px;
                letter-spacing: 0.03em;
            }}
        """)

    def set_file(self, name: str) -> None:
        self._file_label.setText(name)

    def set_stats(self, words: int, chars: int, lines: int) -> None:
        self._stats_label.setText(
            f"{words:,} words · {chars:,} chars · {lines:,} lines"
        )

    def set_mode(self, mode: str) -> None:
        self._mode_label.setText(mode)
