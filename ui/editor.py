"""
ui/editor.py
A plain-text editor widget with Markdown-aware line-highlighting,
live word/char counter, and optional line numbers.
"""

from __future__ import annotations
from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt6.QtGui import (
    QColor, QPainter, QTextFormat, QFont, QFontMetrics,
    QTextCharFormat, QSyntaxHighlighter, QTextDocument,
)
from themes import AppTheme
import re

# ── Markdown syntax highlighter ────────────────────────────────────────────

class MarkdownHighlighter(QSyntaxHighlighter):

    def __init__(self, document: QTextDocument, theme: AppTheme) -> None:
        super().__init__(document)
        self._rules: list[tuple[re.Pattern, QTextCharFormat]] = []
        accent = QColor(theme.accent)
        dim = QColor(theme.fg_dim)
        fg = QColor(theme.editor_fg)

        def fmt(color=None, bold=False, italic=False, size_delta=0) -> QTextCharFormat:
            f = QTextCharFormat()
            if color:
                f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(700)
            if italic:
                f.setFontItalic(True)
            return f

        self._rules = [
            # ATX headings
            (re.compile(r"^#{1,6} .+$"), fmt(accent.name(), bold=True)),
            # Bold
            (re.compile(r"\*\*[^*]+\*\*|__[^_]+__"), fmt(fg.name(), bold=True)),
            # Italic
            (re.compile(r"\*[^*]+\*|_[^_]+_"), fmt(fg.name(), italic=True)),
            # Inline code
            (re.compile(r"`[^`]+`"), fmt("#7EC8B5")),
            # Code fences
            (re.compile(r"^```.*$"), fmt("#7EC8B5", bold=True)),
            # Links
            (re.compile(r"\[([^\]]+)\]\([^\)]+\)"), fmt(accent.name())),
            # Images
            (re.compile(r"!\[[^\]]*\]\([^\)]+\)"), fmt("#A78BFA")),
            # Blockquotes
            (re.compile(r"^>.*$"), fmt(dim.name(), italic=True)),
            # HR
            (re.compile(r"^[-*_]{3,}$"), fmt(dim.name())),
            # Lists
            (re.compile(r"^[\s]*[-*+] "), fmt(accent.name())),
            (re.compile(r"^[\s]*\d+\. "), fmt(accent.name())),
            # HTML tags
            (re.compile(r"<[^>]+>"), fmt(dim.name())),
        ]

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            for m in pattern.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)

# ── Line number gutter ─────────────────────────────────────────────────────

class LineNumberGutter(QWidget):
    def __init__(self, editor: "MarkdownEditor") -> None:
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.gutter_width(), 0)

    def paintEvent(self, event) -> None:
        self._editor.paint_gutter(event)

# ── Main editor ────────────────────────────────────────────────────────────

class MarkdownEditor(QPlainTextEdit):
    stats_changed = pyqtSignal(int, int, int)  # words, chars, lines

    def __init__(self, theme: AppTheme) -> None:
        super().__init__()
        self._theme = theme
        self._show_numbers = True
        self._gutter = LineNumberGutter(self)
        self._highlighter: MarkdownHighlighter | None = None

        self.apply_theme(theme)

        self.blockCountChanged.connect(self._update_gutter_width)
        self.updateRequest.connect(self._update_gutter)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        self.textChanged.connect(self._emit_stats)

        self._update_gutter_width(0)
        self._highlight_current_line()

    # ── Theme ──────────────────────────────────────────────────────────────
    def apply_theme(self, theme: AppTheme) -> None:
        self._theme = theme
        font = QFont()
        font.setFamily("JetBrains Mono")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setPointSize(13)
        self.setFont(font)
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {theme.editor_bg};
                color: {theme.editor_fg};
                border: none;
                selection-background-color: {theme.editor_sel};
                padding: 12px 0 12px 8px;
            }}
        """)
        if self._highlighter:
            self._highlighter.setDocument(None)
        self._highlighter = MarkdownHighlighter(self.document(), theme)