"""
ui/editor.py
A plain-text editor widget with Markdown-aware syntax highlighting,
live word/char counter, optional line numbers, word wrap toggle, and font zoom.
"""

from __future__ import annotations
from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QPainter,
    QPaintEvent,
    QTextFormat,
    QFont,
    QTextCharFormat,
    QSyntaxHighlighter,
    QTextDocument,
)
from themes import AppTheme
import re

# ── Markdown syntax highlighter ────────────────────────────────────────────


class MarkdownHighlighter(QSyntaxHighlighter):

    def __init__(self, document: QTextDocument | None, theme: AppTheme) -> None:
        super().__init__(document)
        self._rules: list[tuple[re.Pattern, QTextCharFormat]] = []
        accent = QColor(theme.accent)
        dim = QColor(theme.fg_dim)
        fg = QColor(theme.editor_fg)
        base_font_size = (
            document.defaultFont().pointSize() if document is not None else 13
        )

        def fmt(
            color=None,
            bold=False,
            italic=False,
            size_delta=0,
            strikeout=False,
        ) -> QTextCharFormat:
            f = QTextCharFormat()
            if color:
                f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(700)
            if italic:
                f.setFontItalic(True)
            if size_delta:
                f.setFontPointSize(base_font_size + size_delta)
            if strikeout:
                f.setFontStrikeOut(True)
            return f

        self._rules = [
            # ATX headings
            (re.compile(r"^#{1,6} .+$"), fmt(accent.name(), bold=True)),
            # Strikethrough  ~~text~~
            (re.compile(r"~~[^~]+~~"), fmt(dim.name(), strikeout=True)),
            # Italic (single * or _, but not part of a ** or __ pair)
            (
                re.compile(
                    r"(?<!\*)\*(?!\*)[^*]+?(?<!\*)\*(?!\*)"
                    r"|(?<!_)_(?!_)[^_]+?(?<!_)_(?!_)"
                ),
                fmt(fg.name(), italic=True),
            ),
            # Bold (applied after italic so it wins on overlapping ranges)
            (re.compile(r"\*\*[^*]+\*\*|__[^_]+__"), fmt(fg.name(), bold=True)),
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
            # Task list checked  - [x]
            (re.compile(r"^[\s]*[-*+] \[x\] .+$", re.IGNORECASE), fmt("#4CAF50")),
            # Task list unchecked  - [ ]
            (re.compile(r"^[\s]*[-*+] \[ \] .+$"), fmt(accent.name())),
            # Regular lists (after task-list rules so they don't override)
            (re.compile(r"^[\s]*[-*+] "), fmt(accent.name())),
            (re.compile(r"^[\s]*\d+\. "), fmt(accent.name())),
            # HTML tags
            (re.compile(r"<[^>]+>"), fmt(dim.name())),
        ]

    def highlightBlock(self, text: str | None) -> None:
        if text is None:
            return
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

    def paintEvent(self, a0) -> None:
        self._editor.paint_gutter(a0)


# ── Main editor ────────────────────────────────────────────────────────────


class MarkdownEditor(QPlainTextEdit):
    stats_changed = pyqtSignal(int, int, int)  # words, chars, lines
    cursor_moved = pyqtSignal(int, int)  # line, column (1-based)

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
        self.cursorPositionChanged.connect(self._emit_cursor_pos)
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

    # ── Gutter ─────────────────────────────────────────────────────────────
    def gutter_width(self) -> int:
        if not self._show_numbers:
            return 0
        digits = max(3, len(str(self.blockCount())))
        return 12 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_gutter_width(self, _: int) -> None:
        self.setViewportMargins(self.gutter_width(), 0, 0, 0)

    def _update_gutter(self, rect: QRect, dy: int) -> None:
        if dy:
            self._gutter.scroll(0, dy)
        else:
            self._gutter.update(0, rect.y(), self._gutter.width(), rect.height())
        vp = self.viewport()
        if vp is not None and rect.contains(vp.rect()):
            self._update_gutter_width(0)

    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        cr = self.contentsRect()
        self._gutter.setGeometry(
            QRect(cr.left(), cr.top(), self.gutter_width(), cr.height())
        )

    def paint_gutter(self, event: QPaintEvent | None) -> None:
        if event is None:
            return
        painter = QPainter(self._gutter)
        painter.fillRect(event.rect(), QColor(self._theme.editor_line))

        block = self.firstVisibleBlock()
        num = block.blockNumber()
        top = int(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + int(self.blockBoundingRect(block).height())

        dim = QColor(self._theme.fg_dim)
        cur_line_color = QColor(self._theme.accent)
        cur = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                color = cur_line_color if num == cur else dim
                painter.setPen(color)
                painter.setFont(self.font())
                painter.drawText(
                    0,
                    top,
                    self._gutter.width() - 6,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(num + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            num += 1

    # ── Current line highlight ──────────────────────────────────────────────
    def _highlight_current_line(self) -> None:
        extras: list[QTextEdit.ExtraSelection] = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            fmt = QTextCharFormat()
            fmt.setBackground(QColor(self._theme.editor_line))
            fmt.setProperty(QTextFormat.Property.FullWidthSelection, True)
            object.__setattr__(sel, "format", fmt)
            cursor = self.textCursor()
            cursor.clearSelection()
            object.__setattr__(sel, "cursor", cursor)
            extras.append(sel)
        self.setExtraSelections(extras)

    # ── Stats ──────────────────────────────────────────────────────────────
    def _emit_stats(self) -> None:
        text = self.toPlainText()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        lines = self.blockCount()
        self.stats_changed.emit(words, chars, lines)

    def _emit_cursor_pos(self) -> None:
        cur = self.textCursor()
        line = cur.blockNumber() + 1
        col = cur.positionInBlock() + 1
        self.cursor_moved.emit(line, col)

    # ── Font zoom ───────────────────────────────────────────────────────────
    def zoom_in_font(self) -> None:
        self.zoomIn(1)

    def zoom_out_font(self) -> None:
        self.zoomOut(1)

    # ── Word wrap ───────────────────────────────────────────────────────────
    def toggle_word_wrap(self, enabled: bool) -> None:
        mode = (
            QPlainTextEdit.LineWrapMode.WidgetWidth
            if enabled
            else QPlainTextEdit.LineWrapMode.NoWrap
        )
        self.setLineWrapMode(mode)

    # ── Public ─────────────────────────────────────────────────────────────
    def toggle_line_numbers(self, visible: bool) -> None:
        self._show_numbers = visible
        self._update_gutter_width(0)
        self._gutter.setVisible(visible)
