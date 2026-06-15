"""
ui/main_window.py
MainWindow: wires together toolbar, editor, preview, find-bar, and status-bar.
"""

from __future__ import annotations
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QSplitter,
    QFileDialog,
    QMessageBox,
    QApplication,
)
from PyQt6.QtCore import Qt, QTimer, QSettings
from PyQt6.QtGui import QKeySequence, QShortcut

from themes import THEMES, DEFAULT_THEME, AppTheme
from core.document import Document
from core.exporter import export_html, export_pdf
from core.page_builder import build_page
from core.renderer import MarkdownRenderer
from ui.editor import MarkdownEditor
from ui.preview import PreviewPane
from ui.toolbar import Toolbar
from ui.statusbar import StatusBar
from ui.find_replace import FindReplaceBar

_SAMPLE_MD = """\
# Welcome to MarkdownPro ✦

> *A clean, distraction-free editor with live preview.*

## Features

- **Live preview** with scroll sync
- Syntax highlighting in the editor
- Multiple themes: Ink, Parchment, Graphite
- Export to **HTML** or **PDF**
- Find & Replace with match count
- Word / char / line counter

## Code blocks

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("world"))
```

## Tables

| Feature        | Status  |
|----------------|---------|
| Live preview   | ✅      |
| PDF export     | ✅      |
| Themes         | ✅      |
| Find & Replace | ✅      |

## Admonitions

!!! note
    Use the toolbar above to switch between **Editor**, **Split**, and **Preview** modes.

!!! tip
    Press **Ctrl+F** to open the Find & Replace bar.

---

Start writing your own Markdown — the preview updates as you type.
"""


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings("MarkdownPro", "MarkdownPro")
        self._document = Document(text=_SAMPLE_MD)
        self._document._saved_text = _SAMPLE_MD  # treat sample as "clean"
        self._current_view = "split"

        theme_name = self._settings.value("theme", DEFAULT_THEME)
        self._theme: AppTheme = THEMES.get(theme_name, THEMES[DEFAULT_THEME])

        self._build_ui()
        self._connect_signals()
        self._setup_shortcuts()
        self._restore_geometry()

        # Trigger initial render
        self._editor.setPlainText(_SAMPLE_MD)

    # ── UI construction ─────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        self.setWindowTitle("MarkdownPro")
        self.setMinimumSize(900, 600)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toolbar
        self._toolbar = Toolbar(self._theme)
        root.addWidget(self._toolbar)

        # Splitter (editor | preview)
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(1)

        self._editor = MarkdownEditor(self._theme)
        self._preview = PreviewPane(self._theme)

        self._splitter.addWidget(self._editor)
        self._splitter.addWidget(self._preview)
        self._splitter.setSizes([500, 500])

        # Find bar (overlay at bottom of editor)
        self._find_bar = FindReplaceBar(self, self._theme)
        self._find_bar.set_editor(self._editor)

        # Content area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self._splitter, 1)
        content_layout.addWidget(self._find_bar)

        root.addWidget(content, 1)

        # Status bar
        self._status = StatusBar(self._theme)
        root.addWidget(self._status)

        self._apply_app_theme(self._theme)

        # Debounce timer
        self._render_timer = QTimer()
        self._render_timer.setSingleShot(True)
        self._render_timer.setInterval(120)
        self._render_timer.timeout.connect(self._render_preview)

    def _connect_signals(self) -> None:
        # Toolbar
        self._toolbar.new_file.connect(self._on_new)
        self._toolbar.open_file.connect(self._on_open)
        self._toolbar.save_file.connect(self._on_save)
        self._toolbar.save_as.connect(self._on_save_as)
        self._toolbar.export_html_sig.connect(self._on_export_html)
        self._toolbar.export_pdf_sig.connect(self._on_export_pdf)
        self._toolbar.view_changed.connect(self._on_view_changed)
        self._toolbar.theme_changed.connect(self._on_theme_changed)
        self._toolbar.find_triggered.connect(self._find_bar.show_bar)
        self._toolbar.toggle_numbers.connect(self._editor.toggle_line_numbers)

        # Editor
        self._editor.textChanged.connect(self._on_text_changed)
        self._editor.stats_changed.connect(self._status.set_stats)

    def _setup_shortcuts(self) -> None:
        shortcuts = {
            "Ctrl+N": self._on_new,
            "Ctrl+O": self._on_open,
            "Ctrl+S": self._on_save,
            "Ctrl+Shift+S": self._on_save_as,
            "Ctrl+F": self._find_bar.show_bar,
            "Escape": self._find_bar.hide,
            "Ctrl+B": lambda: self._insert_snippet("**", "**", "bold text"),
            "Ctrl+I": lambda: self._insert_snippet("*", "*", "italic text"),
            "Ctrl+`": lambda: self._insert_snippet("`", "`", "code"),
        }
        for key, slot in shortcuts.items():
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(slot)

    # ── Text changes ────────────────────────────────────────────────────────
    def _on_text_changed(self) -> None:
        self._document.text = self._editor.toPlainText()
        self._status.set_file(self._document.display_name)
        self._render_timer.start()

    def _render_preview(self) -> None:
        if self._current_view != "editor":
            self._preview.update_content(self._document.text)

    # ── View modes ──────────────────────────────────────────────────────────
    def _on_view_changed(self, mode: str) -> None:
        if mode.startswith("__insert__"):
            self._handle_insert(mode)
            return

        self._current_view = mode
        self._status.set_mode(mode.capitalize())

        if mode == "editor":
            self._editor.show()
            self._preview.hide()
        elif mode == "preview":
            self._editor.hide()
            self._preview.show()
            self._render_preview()
        else:  # split
            self._editor.show()
            self._preview.show()
            self._render_preview()

    def _handle_insert(self, mode: str) -> None:
        inserts = {
            "__insert__bold__": ("**", "**", "bold text"),
            "__insert__italic__": ("*", "*", "italic text"),
            "__insert__code__": ("`", "`", "code"),
            "__insert__link__": ("[", "](url)", "link text"),
            "__insert__image__": ("![", "](url)", "alt text"),
            "__insert__table__": ("", "", None),  # handled below
        }
        if mode == "__insert__table__":
            snippet = (
                "\n| Column 1 | Column 2 | Column 3 |\n"
                "|----------|----------|----------|\n"
                "| Cell     | Cell     | Cell     |\n"
            )
            cur = self._editor.textCursor()
            cur.insertText(snippet)
            return
        prefix, suffix, placeholder = inserts.get(mode, ("", "", ""))
        self._insert_snippet(prefix, suffix, placeholder)

    def _insert_snippet(
        self, prefix: str, suffix: str, placeholder: str | None
    ) -> None:
        cur = self._editor.textCursor()
        had_selection = cur.hasSelection()
        selected = cur.selectedText() or placeholder or ""
        cur.insertText(f"{prefix}{selected}{suffix}")
        if not had_selection and placeholder:
            # Select the placeholder so the user can type over it
            pos = cur.position()
            cur.setPosition(pos - len(suffix) - len(placeholder))
            cur.setPosition(pos - len(suffix), cur.MoveMode.KeepAnchor)
            self._editor.setTextCursor(cur)
        self._editor.setFocus()

    # ── File I/O ─────────────────────────────────────────────────────────────
    def _check_unsaved(self) -> bool:
        if not self._document.is_modified:
            return True
        reply = QMessageBox.question(
            self,
            "Unsaved changes",
            f"'{self._document.display_name.removeprefix('●  ')}' has unsaved changes.\nDiscard them?",
            QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
        )
        return reply == QMessageBox.StandardButton.Discard

    def _on_new(self) -> None:
        if not self._check_unsaved():
            return
        self._document.new()
        self._editor.setPlainText("")
        self._status.set_file("Untitled")
        self.setWindowTitle("MarkdownPro")

    def _on_open(self) -> None:
        if not self._check_unsaved():
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Markdown file",
            "",
            "Markdown files (*.md *.markdown *.txt);;All files (*)",
        )
        if not path:
            return
        self._document = Document.open(Path(path))
        self._editor.setPlainText(self._document.text)
        self._status.set_file(self._document.display_name)
        if self._document.path is not None:
            self.setWindowTitle(f"MarkdownPro – {self._document.path.name}")

    def _on_save(self) -> None:
        if self._document.path is None:
            self._on_save_as()
            return
        self._document.save()
        self._status.set_file(self._document.display_name)

    def _on_save_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save as", "", "Markdown files (*.md);;All files (*)"
        )
        if not path:
            return
        self._document.save(Path(path))
        self._status.set_file(self._document.display_name)
        if self._document.path is not None:
            self.setWindowTitle(f"MarkdownPro – {self._document.path.name}")

    def _on_export_html(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export HTML", "", "HTML files (*.html)"
        )
        if not path:
            return
        renderer = MarkdownRenderer()
        fragment = renderer.render(self._document.text)
        code_css = MarkdownRenderer.pygments_css(self._theme.code_style)
        page = build_page(fragment, self._theme, code_css)
        export_html(page, Path(path))
        QMessageBox.information(self, "Exported", f"HTML saved to:\n{path}")

    def _on_export_pdf(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", "", "PDF files (*.pdf)"
        )
        if not path:
            return
        export_pdf(self._preview, Path(path))
        QMessageBox.information(self, "Exported", f"PDF will be saved to:\n{path}")

    # ── Theming ──────────────────────────────────────────────────────────────
    def _on_theme_changed(self, name: str) -> None:
        theme = THEMES.get(name)
        if not theme:
            return
        self._theme = theme
        self._apply_app_theme(theme)
        self._settings.setValue("theme", name)

    def _apply_app_theme(self, theme: AppTheme) -> None:
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background: {theme.bg}; color: {theme.fg}; }}
            QSplitter::handle {{ background: {theme.border}; }}
        """)
        self._toolbar.apply_theme(theme)
        self._editor.apply_theme(theme)
        self._preview.apply_theme(theme)
        self._status.apply_theme(theme)
        self._find_bar.apply_theme(theme)
        self._render_preview()

    # ── Window lifecycle ─────────────────────────────────────────────────────
    def _restore_geometry(self) -> None:
        geo = self._settings.value("geometry")
        if geo:
            self.restoreGeometry(geo)
        else:
            self.resize(1280, 800)
            primary_screen = QApplication.primaryScreen()
            if primary_screen is not None:
                screen = primary_screen.availableGeometry()
                self.move(
                    (screen.width() - self.width()) // 2,
                    (screen.height() - self.height()) // 2,
                )

    def closeEvent(self, a0) -> None:
        if not self._check_unsaved():
            if a0 is not None:
                a0.ignore()
            return
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("theme", self._theme.name)
        if a0 is not None:
            a0.accept()
