"""
ui/toolbar.py
Top toolbar with file actions, view modes, and theme switcher.
"""

from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from themes import AppTheme, THEMES


class ToolButton(QPushButton):
    def __init__(self, label: str, tooltip: str = "") -> None:
        super().__init__(label)
        self.setToolTip(tooltip)
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(30)
        font = QFont("Inter", 12)
        self.setFont(font)


class Divider(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setFrameShape(QFrame.Shape.VLine)
        self.setFixedWidth(1)
        self.setFixedHeight(20)


class Toolbar(QWidget):
    new_file = pyqtSignal()
    open_file = pyqtSignal()
    save_file = pyqtSignal()
    save_as = pyqtSignal()
    export_html_sig = pyqtSignal()
    export_pdf_sig = pyqtSignal()
    view_changed = pyqtSignal(str)  # "editor" | "split" | "preview"
    theme_changed = pyqtSignal(str)
    find_triggered = pyqtSignal()
    toggle_numbers = pyqtSignal(bool)

    def __init__(self, theme: AppTheme) -> None:
        super().__init__()
        self._theme = theme
        self._number_on = True

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(4)

        # File actions
        self._btn_new = ToolButton("⊕", "New file  (Ctrl+N)")
        self._btn_open = ToolButton("⊙", "Open file  (Ctrl+O)")
        self._btn_save = ToolButton("⊘", "Save  (Ctrl+S)")

        layout.addWidget(self._btn_new)
        layout.addWidget(self._btn_open)
        layout.addWidget(self._btn_save)
        layout.addWidget(Divider())

        # Insert helpers
        self._btn_bold = ToolButton("B", "Bold  (Ctrl+B)")
        self._btn_bold.setObjectName("bold")
        self._btn_italic = ToolButton("I", "Italic  (Ctrl+I)")
        self._btn_italic.setObjectName("italic")
        self._btn_code = ToolButton("</>", "Inline code")
        self._btn_link = ToolButton("⛓", "Insert link")
        self._btn_img = ToolButton("⊞", "Insert image")
        self._btn_table = ToolButton("⊟", "Insert table")

        for btn in (
            self._btn_bold,
            self._btn_italic,
            self._btn_code,
            self._btn_link,
            self._btn_img,
            self._btn_table,
        ):
            layout.addWidget(btn)
        layout.addWidget(Divider())

        # Find
        self._btn_find = ToolButton("⌕", "Find & Replace  (Ctrl+F)")
        layout.addWidget(self._btn_find)
        layout.addWidget(Divider())

        # Line numbers toggle
        self._btn_lnum = ToolButton("#", "Toggle line numbers")
        self._btn_lnum.setCheckable(True)
        self._btn_lnum.setChecked(True)
        layout.addWidget(self._btn_lnum)
        layout.addWidget(Divider())

        # Export
        self._btn_exp_html = ToolButton("↓ HTML", "Export to HTML")
        self._btn_exp_pdf = ToolButton("↓ PDF", "Export to PDF")
        layout.addWidget(self._btn_exp_html)
        layout.addWidget(self._btn_exp_pdf)

        layout.addStretch()

        # View switcher
        self._view_editor = ToolButton("Editor", "Editor only")
        self._view_split = ToolButton("Split", "Side by side")
        self._view_preview = ToolButton("Preview", "Preview only")
        self._view_split.setProperty("active", True)
        for btn in (self._view_editor, self._view_split, self._view_preview):
            layout.addWidget(btn)
        layout.addWidget(Divider())

        # Theme
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(list(THEMES.keys()))
        self._theme_combo.setCurrentText(theme.name)
        self._theme_combo.setFixedHeight(28)
        self._theme_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._theme_combo)

        self.apply_theme(theme)
        self._connect()

    # ── Connections ────────────────────────────────────────────────────────
    def _connect(self) -> None:
        self._btn_new.clicked.connect(self.new_file)
        self._btn_open.clicked.connect(self.open_file)
        self._btn_save.clicked.connect(self.save_file)
        self._btn_exp_html.clicked.connect(self.export_html_sig)
        self._btn_exp_pdf.clicked.connect(self.export_pdf_sig)
        self._btn_find.clicked.connect(self.find_triggered)
        self._btn_lnum.toggled.connect(self.toggle_numbers)

        self._view_editor.clicked.connect(lambda: self._switch_view("editor"))
        self._view_split.clicked.connect(lambda: self._switch_view("split"))
        self._view_preview.clicked.connect(lambda: self._switch_view("preview"))

        self._theme_combo.currentTextChanged.connect(self.theme_changed)

        # Insert shortcuts
        self._btn_bold.clicked.connect(self._insert_bold)
        self._btn_italic.clicked.connect(self._insert_italic)
        self._btn_code.clicked.connect(self._insert_code)
        self._btn_link.clicked.connect(self._insert_link)
        self._btn_img.clicked.connect(self._insert_image)
        self._btn_table.clicked.connect(self._insert_table)

    def _switch_view(self, mode: str) -> None:
        for btn, m in (
            (self._view_editor, "editor"),
            (self._view_split, "split"),
            (self._view_preview, "preview"),
        ):
            btn.setProperty("active", m == mode)
            style = btn.style()
            if style is not None:
                style.polish(btn)
        self.view_changed.emit(mode)

    # ── Insert helpers (emit signals consumed by MainWindow) ───────────────
    def _insert_bold(self) -> None:
        self.view_changed.emit("__insert__bold__")

    def _insert_italic(self) -> None:
        self.view_changed.emit("__insert__italic__")

    def _insert_code(self) -> None:
        self.view_changed.emit("__insert__code__")

    def _insert_link(self) -> None:
        self.view_changed.emit("__insert__link__")

    def _insert_image(self) -> None:
        self.view_changed.emit("__insert__image__")

    def _insert_table(self) -> None:
        self.view_changed.emit("__insert__table__")

    # ── Theme ──────────────────────────────────────────────────────────────
    def apply_theme(self, theme: AppTheme) -> None:
        self._theme = theme
        self.setFixedHeight(44)
        self.setStyleSheet(f"""
            QWidget {{
                background: {theme.surface};
                border-bottom: 1px solid {theme.border};
            }}
            QPushButton {{
                background: transparent;
                color: {theme.fg_dim};
                border: none;
                border-radius: 5px;
                padding: 4px 10px;
                font-family: 'Inter', 'Helvetica Neue', system-ui, sans-serif;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {theme.border};
                color: {theme.fg};
            }}
            QPushButton[active=true] {{
                background: {theme.accent};
                color: {theme.accent_fg};
            }}
            QPushButton#bold {{ font-weight: 700; }}
            QPushButton#italic {{ font-style: italic; }}
            QFrame {{
                background: {theme.border};
                margin: 12px 4px;
            }}
            QComboBox {{
                background: {theme.bg};
                color: {theme.fg};
                border: 1px solid {theme.border};
                border-radius: 5px;
                padding: 2px 8px;
                font-family: 'Inter', system-ui, sans-serif;
                font-size: 12px;
                min-width: 90px;
            }}
            QComboBox::drop-down {{ border: none; width: 18px; }}
            QComboBox QAbstractItemView {{
                background: {theme.surface};
                color: {theme.fg};
                selection-background-color: {theme.accent};
                border: 1px solid {theme.border};
            }}
        """)
        self._theme_combo.setCurrentText(theme.name)
