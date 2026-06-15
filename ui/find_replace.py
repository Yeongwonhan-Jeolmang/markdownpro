"""
ui/find_replace.py
Floating Find & Replace panel that operates on a QPlainTextEdit.
"""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QCheckBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextDocument, QTextCursor
from themes import AppTheme


class FindReplaceBar(QWidget):
    def __init__(self, parent: QWidget, theme: AppTheme) -> None:
        super().__init__(parent)
        self._editor = None
        self.setWindowFlags(Qt.WindowType.Widget)
        self.hide()

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 6, 10, 6)
        root.setSpacing(4)

        # Find row
        find_row = QHBoxLayout()
        self._find_input = QLineEdit()
        self._find_input.setPlaceholderText("Find…")
        self._find_input.returnPressed.connect(self.find_next)
        self._btn_prev = QPushButton("↑")
        self._btn_next = QPushButton("↓")
        self._btn_prev.setFixedSize(26, 26)
        self._btn_next.setFixedSize(26, 26)
        self._match_label = QLabel("")
        self._case_cb = QCheckBox("Aa")
        self._case_cb.setToolTip("Match case")
        self._regex_cb = QCheckBox(".*")
        self._regex_cb.setToolTip("Regular expression")
        self._btn_close = QPushButton("✕")
        self._btn_close.setFixedSize(22, 22)
        self._btn_close.setFlat(True)
        find_row.addWidget(QLabel("Find"))
        find_row.addWidget(self._find_input, 1)
        find_row.addWidget(self._btn_prev)
        find_row.addWidget(self._btn_next)
        find_row.addWidget(self._match_label)
        find_row.addWidget(self._case_cb)
        find_row.addWidget(self._regex_cb)
        find_row.addStretch()
        find_row.addWidget(self._btn_close)

        # Replace row
        rep_row = QHBoxLayout()
        self._rep_input = QLineEdit()
        self._rep_input.setPlaceholderText("Replace…")
        self._btn_replace = QPushButton("Replace")
        self._btn_replace_all = QPushButton("All")
        rep_row.addWidget(QLabel("Replace"))
        rep_row.addWidget(self._rep_input, 1)
        rep_row.addWidget(self._btn_replace)
        rep_row.addWidget(self._btn_replace_all)

        root.addLayout(find_row)
        root.addLayout(rep_row)

        self._btn_prev.clicked.connect(self.find_prev)
        self._btn_next.clicked.connect(self.find_next)
        self._btn_replace.clicked.connect(self.replace_one)
        self._btn_replace_all.clicked.connect(self.replace_all)
        self._btn_close.clicked.connect(self.hide)
        self._find_input.textChanged.connect(self._update_match_count)

        self.apply_theme(theme)

    def set_editor(self, editor) -> None:
        self._editor = editor

    def show_bar(self) -> None:
        self.show()
        self._find_input.setFocus()
        self._find_input.selectAll()

    # ── Search helpers ──────────────────────────────────────────────────────
    def _flags(self) -> QTextDocument.FindFlag:
        flags = QTextDocument.FindFlag(0)
        if self._case_cb.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        return flags

    def _get_expr(self) -> str:
        return self._find_input.text()

    def find_next(self) -> None:
        if not self._editor or not self._get_expr():
            return
        found = self._editor.find(self._get_expr(), self._flags())
        if not found:
            cur = self._editor.textCursor()
            cur.movePosition(QTextCursor.MoveOperation.Start)
            self._editor.setTextCursor(cur)
            self._editor.find(self._get_expr(), self._flags())

    def find_prev(self) -> None:
        if not self._editor or not self._get_expr():
            return
        flags = self._flags() | QTextDocument.FindFlag.FindBackward
        found = self._editor.find(self._get_expr(), flags)
        if not found:
            cur = self._editor.textCursor()
            cur.movePosition(QTextCursor.MoveOperation.End)
            self._editor.setTextCursor(cur)
            self._editor.find(self._get_expr(), flags)

    def replace_one(self) -> None:
        if not self._editor:
            return
        cur = self._editor.textCursor()
        if cur.hasSelection() and cur.selectedText() == self._get_expr():
            cur.insertText(self._rep_input.text())
        self.find_next()

    def replace_all(self) -> None:
        if not self._editor or not self._get_expr():
            return
        text = self._editor.toPlainText()
        if self._case_cb.isChecked():
            new = text.replace(self._get_expr(), self._rep_input.text())
        else:
            import re

            new = re.sub(
                re.escape(self._get_expr()),
                self._rep_input.text(),
                text,
                flags=re.IGNORECASE,
            )
        self._editor.setPlainText(new)

    def _update_match_count(self) -> None:
        if not self._editor or not self._get_expr():
            self._match_label.setText("")
            return
        text = self._editor.toPlainText()
        import re

        flags = 0 if self._case_cb.isChecked() else re.IGNORECASE
        try:
            count = len(re.findall(re.escape(self._get_expr()), text, flags))
        except Exception:
            count = 0
        self._match_label.setText(f"{count} match{'es' if count != 1 else ''}")

    def apply_theme(self, theme: AppTheme) -> None:
        self.setStyleSheet(f"""
            QWidget {{
                background: {theme.surface};
                border-top: 1px solid {theme.border};
                color: {theme.fg};
                font-family: 'Inter', system-ui, sans-serif;
                font-size: 12px;
            }}
            QLineEdit {{
                background: {theme.editor_bg};
                color: {theme.editor_fg};
                border: 1px solid {theme.border};
                border-radius: 4px;
                padding: 3px 7px;
            }}
            QLineEdit:focus {{ border-color: {theme.accent}; }}
            QPushButton {{
                background: {theme.bg};
                color: {theme.fg};
                border: 1px solid {theme.border};
                border-radius: 4px;
                padding: 2px 8px;
            }}
            QPushButton:hover {{ background: {theme.accent}; color: {theme.accent_fg}; border-color: {theme.accent}; }}
            QLabel {{ color: {theme.fg_dim}; }}
            QCheckBox {{ color: {theme.fg_dim}; spacing: 4px; }}
        """)
