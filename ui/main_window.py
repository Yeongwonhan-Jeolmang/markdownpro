"""
ui/main_window.py
MainWindow: wires together toolbar, editor, preview, find-bar, and status-bar.
"""

from __future__ import annotations
import re
import tempfile
from collections.abc import Callable
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QSplitter,
    QFileDialog,
    QMessageBox,
    QApplication,
    QMenuBar,
    QMenu,
)
from PyQt6.QtCore import Qt, QTimer, QSettings
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QKeySequence, QShortcut, QAction

from themes import THEMES, DEFAULT_THEME, AppTheme, theme_for_color_scheme
from core.document import Document
from core.exporter import export_html
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
- Multiple themes: Ink, Parchment, Graphite, Light
- Export to **HTML** or **PDF**
- Find & Replace with match count
- Word / char / line counter
- Undo/Redo, auto-save, drag & drop

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

## Task list

- [x] Undo/Redo support
- [x] Auto-save
- [ ] Your next great idea

## Admonitions

!!! note
    Use the toolbar above to switch between **Editor**, **Split**, and **Preview** modes.

!!! tip
    Press **Ctrl+F** to open the Find & Replace bar.

---

Start writing your own Markdown — the preview updates as you type.
"""

_MAX_RECENT = 10
_AUTOSAVE_INTERVAL_MS = 60_000


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings("MarkdownPro", "MarkdownPro")
        self._document = Document(text=_SAMPLE_MD)
        self._document._saved_text = _SAMPLE_MD
        self._current_view = "split"
        self._autosave_path = Path(tempfile.gettempdir()) / "markdownpro_autosave.md"

        theme_name = self._settings.value("theme", DEFAULT_THEME)
        self._theme: AppTheme = THEMES.get(theme_name, THEMES[DEFAULT_THEME])

        self._build_ui()
        self._build_menu()
        self._connect_signals()
        self._setup_shortcuts()
        self._restore_geometry()
        self._setup_autosave()
        self._check_autosave_recovery()
        self._sync_os_theme()

        # Trigger initial render
        self._editor.setPlainText(_SAMPLE_MD)

        # Accept drag-and-drop .md files
        self.setAcceptDrops(True)

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

        # Find bar
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

    def _build_menu(self) -> None:
        """Add a minimal menu bar for Recent Files and Print."""
        # menuBar() always returns a valid QMenuBar for a QMainWindow
        mb: QMenuBar = self.menuBar()  # type: ignore[assignment]

        file_menu_raw = mb.addMenu("File")
        assert file_menu_raw is not None, "Failed to create File menu"
        file_menu: QMenu = file_menu_raw

        act_new = QAction("New", self)
        act_new.setShortcut(QKeySequence("Ctrl+N"))
        act_new.triggered.connect(self._on_new)
        file_menu.addAction(act_new)

        act_open = QAction("Open…", self)
        act_open.setShortcut(QKeySequence("Ctrl+O"))
        act_open.triggered.connect(self._on_open)
        file_menu.addAction(act_open)

        recent_menu_raw = file_menu.addMenu("Open Recent")
        assert recent_menu_raw is not None, "Failed to create Open Recent menu"
        self._recent_menu: QMenu = recent_menu_raw
        self._update_recent_menu()

        file_menu.addSeparator()

        act_save = QAction("Save", self)
        act_save.setShortcut(QKeySequence("Ctrl+S"))
        act_save.triggered.connect(self._on_save)
        file_menu.addAction(act_save)

        act_save_as = QAction("Save As…", self)
        act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        act_save_as.triggered.connect(self._on_save_as)
        file_menu.addAction(act_save_as)

        file_menu.addSeparator()

        act_exp_html = QAction("Export HTML…", self)
        act_exp_html.triggered.connect(self._on_export_html)
        file_menu.addAction(act_exp_html)

        act_exp_pdf = QAction("Export PDF…", self)
        act_exp_pdf.triggered.connect(self._on_export_pdf)
        file_menu.addAction(act_exp_pdf)

        act_print = QAction("Print…", self)
        act_print.setShortcut(QKeySequence("Ctrl+P"))
        act_print.triggered.connect(self._on_print)
        file_menu.addAction(act_print)

        file_menu.addSeparator()

        act_quit = QAction("Quit", self)
        act_quit.setShortcut(QKeySequence("Ctrl+Q"))
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        # Apply menu bar styling
        self._apply_menu_theme(self._theme)

    def _apply_menu_theme(self, theme: AppTheme) -> None:
        mb = self.menuBar()
        if mb is None:
            return
        mb.setStyleSheet(f"""
            QMenuBar {{
                background: {theme.surface};
                color: {theme.fg};
                border-bottom: 1px solid {theme.border};
                font-family: 'Inter', system-ui, sans-serif;
                font-size: 12px;
            }}
            QMenuBar::item {{
                background: transparent;
                padding: 4px 10px;
            }}
            QMenuBar::item:selected {{
                background: {theme.border};
                border-radius: 4px;
            }}
            QMenu {{
                background: {theme.surface};
                color: {theme.fg};
                border: 1px solid {theme.border};
                font-family: 'Inter', system-ui, sans-serif;
                font-size: 12px;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 16px;
            }}
            QMenu::item:selected {{
                background: {theme.accent};
                color: {theme.accent_fg};
            }}
            QMenu::separator {{
                height: 1px;
                background: {theme.border};
                margin: 4px 0;
            }}
        """)

    def _connect_signals(self) -> None:
        # Toolbar
        self._toolbar.new_file.connect(self._on_new)
        self._toolbar.open_file.connect(self._on_open)
        self._toolbar.save_file.connect(self._on_save)
        self._toolbar.save_as.connect(self._on_save_as)
        self._toolbar.export_html_sig.connect(self._on_export_html)
        self._toolbar.export_pdf_sig.connect(self._on_export_pdf)
        self._toolbar.print_sig.connect(self._on_print)
        self._toolbar.view_changed.connect(self._on_view_changed)
        self._toolbar.insert_action.connect(self._handle_insert)
        self._toolbar.theme_changed.connect(self._on_theme_changed)
        self._toolbar.find_triggered.connect(self._find_bar.show_bar)
        self._toolbar.toggle_numbers.connect(self._editor.toggle_line_numbers)
        self._toolbar.toggle_wrap.connect(self._editor.toggle_word_wrap)
        self._toolbar.undo_triggered.connect(self._editor.undo)
        self._toolbar.redo_triggered.connect(self._editor.redo)

        # Editor
        self._editor.textChanged.connect(self._on_text_changed)
        self._editor.stats_changed.connect(self._status.set_stats)
        self._editor.cursor_moved.connect(self._status.set_cursor)

        # Scroll sync: editor scroll → preview.
        # verticalScrollBar() on QPlainTextEdit always returns a valid bar.
        vsb = self._editor.verticalScrollBar()
        if vsb is not None:
            vsb.valueChanged.connect(self._on_editor_scrolled)

    def _setup_shortcuts(self) -> None:
        shortcuts: dict[str, Callable[[], None]] = {
            "Ctrl+Z": self._editor.undo,
            "Ctrl+Y": self._editor.redo,
            "Ctrl+Shift+Z": self._editor.redo,
            "Ctrl+N": self._on_new,
            "Ctrl+O": self._on_open,
            "Ctrl+S": self._on_save,
            "Ctrl+Shift+S": self._on_save_as,
            "Ctrl+F": self._find_bar.show_bar,
            "Escape": self._find_bar.hide,
            "Ctrl+B": lambda: self._handle_insert("bold"),
            "Ctrl+I": lambda: self._handle_insert("italic"),
            "Ctrl+`": lambda: self._handle_insert("code"),
            "Ctrl+Shift+`": lambda: self._handle_insert("fence"),
            # Heading shortcuts
            "Ctrl+1": lambda: self._handle_insert("h1"),
            "Ctrl+2": lambda: self._handle_insert("h2"),
            "Ctrl+3": lambda: self._handle_insert("h3"),
            "Ctrl+4": lambda: self._handle_insert("h4"),
            "Ctrl+5": lambda: self._handle_insert("h5"),
            "Ctrl+6": lambda: self._handle_insert("h6"),
            # Font zoom
            "Ctrl+=": self._editor.zoom_in_font,
            "Ctrl++": self._editor.zoom_in_font,
            "Ctrl+-": self._editor.zoom_out_font,
            "Ctrl+P": self._on_print,
        }
        for key, slot in shortcuts.items():
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(slot)

    # ── Auto-save ────────────────────────────────────────────────────────────
    def _setup_autosave(self) -> None:
        self._autosave_timer = QTimer()
        self._autosave_timer.setInterval(_AUTOSAVE_INTERVAL_MS)
        self._autosave_timer.timeout.connect(self._do_autosave)
        self._autosave_timer.start()

    def _do_autosave(self) -> None:
        text = self._editor.toPlainText()
        if not text.strip():
            return
        try:
            self._autosave_path.write_text(text, encoding="utf-8")
        except Exception:
            pass

    def _clear_autosave(self) -> None:
        try:
            self._autosave_path.unlink(missing_ok=True)
        except Exception:
            pass

    def _check_autosave_recovery(self) -> None:
        if not self._autosave_path.exists():
            return
        reply = QMessageBox.question(
            self,
            "Recover unsaved work?",
            "An auto-saved version of your work was found.\n"
            "Would you like to restore it?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                text = self._autosave_path.read_text(encoding="utf-8")
                self._editor.setPlainText(text)
                self._document.text = text
            except Exception:
                pass
        else:
            self._clear_autosave()

    # ── Text changes ────────────────────────────────────────────────────────
    def _on_text_changed(self) -> None:
        self._document.text = self._editor.toPlainText()
        self._status.set_file(self._document.display_name)
        self._render_timer.start()

    def _render_preview(self) -> None:
        if self._current_view != "editor":
            self._preview.update_content(self._document.text)

    # ── Scroll sync ──────────────────────────────────────────────────────────
    def _on_editor_scrolled(self, value: int) -> None:
        if self._current_view == "editor":
            return
        vsb = self._editor.verticalScrollBar()
        if vsb is None:
            return
        max_val = vsb.maximum()
        if max_val == 0:
            return
        ratio = value / max_val
        page = self._preview.page()
        if page is not None:
            page.runJavaScript(
                f"window.scrollTo(0, (document.body.scrollHeight - window.innerHeight) * {ratio})"
            )

    # ── View modes ──────────────────────────────────────────────────────────
    def _on_view_changed(self, mode: str) -> None:
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

    # ── Insert helpers ───────────────────────────────────────────────────────
    def _handle_insert(self, action: str) -> None:
        inserts: dict[str, tuple[str, str, str | None]] = {
            "bold":   ("**", "**", "bold text"),
            "italic": ("*", "*", "italic text"),
            "code":   ("`", "`", "code"),
            "link":   ("[", "](url)", "link text"),
            "image":  ("![", "](url)", "alt text"),
        }
        heading_map = {
            "h1": "# ", "h2": "## ", "h3": "### ",
            "h4": "#### ", "h5": "##### ", "h6": "###### ",
        }

        if action == "table":
            snippet = (
                "\n| Column 1 | Column 2 | Column 3 |\n"
                "|----------|----------|----------|\n"
                "| Cell     | Cell     | Cell     |\n"
            )
            cur = self._editor.textCursor()
            cur.insertText(snippet)
            self._editor.setFocus()
            return

        if action == "fence":
            cur = self._editor.textCursor()
            selected = cur.selectedText()
            cur.insertText(f"\n```python\n{selected}\n```\n")
            self._editor.setFocus()
            return

        if action in heading_map:
            prefix = heading_map[action]
            cur = self._editor.textCursor()
            cur.movePosition(cur.MoveOperation.StartOfLine)
            doc = self._editor.document()
            if doc is not None:
                line_text = doc.findBlockByNumber(cur.blockNumber()).text()
                stripped = re.sub(r"^#+\s*", "", line_text)
                cur.movePosition(cur.MoveOperation.EndOfLine, cur.MoveMode.KeepAnchor)
                cur.insertText(f"{prefix}{stripped}")
            self._editor.setFocus()
            return

        if action in inserts:
            prefix, suffix, placeholder = inserts[action]
            self._insert_snippet(prefix, suffix, placeholder)

    def _insert_snippet(
        self, prefix: str, suffix: str, placeholder: str | None
    ) -> None:
        cur = self._editor.textCursor()
        had_selection = cur.hasSelection()
        selected = cur.selectedText() or placeholder or ""
        cur.insertText(f"{prefix}{selected}{suffix}")
        if not had_selection and placeholder:
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
        self._clear_autosave()

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
        self._load_file(Path(path))

    def _open_recent(self, path_str: str) -> None:
        if not self._check_unsaved():
            return
        p = Path(path_str)
        if not p.exists():
            QMessageBox.warning(self, "File not found", f"Could not find:\n{path_str}")
            self._remove_recent_file(path_str)
            return
        self._load_file(p)

    def _load_file(self, path: Path) -> None:
        self._document = Document.open(path)
        self._editor.setPlainText(self._document.text)
        self._status.set_file(self._document.display_name)
        if self._document.path is not None:
            self.setWindowTitle(f"MarkdownPro – {self._document.path.name}")
        self._add_recent_file(path)
        self._clear_autosave()

    def _on_save(self) -> None:
        if self._document.path is None:
            self._on_save_as()
            return
        self._document.save()
        self._status.set_file(self._document.display_name)
        self._clear_autosave()

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
        self._add_recent_file(self._document.path)
        self._clear_autosave()

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

        from PyQt6.QtCore import QMarginsF
        from PyQt6.QtGui import QPageLayout, QPageSize

        layout = QPageLayout(
            QPageSize(QPageSize.PageSizeId.A4),
            QPageLayout.Orientation.Portrait,
            QMarginsF(15, 15, 15, 15),
        )
        web_page = self._preview.page()
        if web_page is None:
            QMessageBox.warning(self, "Export failed", "Preview page is not available.")
            return

        path_str = path

        def _on_pdf_done(success: bool) -> None:
            try:
                web_page.pdfPrintingFinished.disconnect(_on_pdf_done)
            except Exception:
                pass
            if success:
                QMessageBox.information(self, "Exported", f"PDF saved to:\n{path_str}")
            else:
                QMessageBox.warning(
                    self, "Export failed", f"Could not save PDF to:\n{path_str}"
                )

        web_page.pdfPrintingFinished.connect(_on_pdf_done)
        web_page.printToPdf(path_str, layout)

    def _on_print(self) -> None:
        try:
            from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

            printer = QPrinter()
            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                web_page = self._preview.page()
                if web_page is not None:
                    getattr(web_page, "print")(printer)
        except ImportError:
            QMessageBox.information(
                self,
                "Print",
                "Printing requires PyQt6-Qt6PrintSupport.\n"
                "Install it with: pip install PyQt6-Qt6PrintSupport",
            )

    # ── Recent files ──────────────────────────────────────────────────────────
    def _recent_paths(self) -> list[str]:
        paths = self._settings.value("recent_files", [])
        return paths if isinstance(paths, list) else []

    def _add_recent_file(self, path: Path | None) -> None:
        if path is None:
            return
        paths = self._recent_paths()
        path_str = str(path)
        if path_str in paths:
            paths.remove(path_str)
        paths.insert(0, path_str)
        paths = paths[:_MAX_RECENT]
        self._settings.setValue("recent_files", paths)
        self._update_recent_menu()

    def _remove_recent_file(self, path_str: str) -> None:
        paths = self._recent_paths()
        if path_str in paths:
            paths.remove(path_str)
        self._settings.setValue("recent_files", paths)
        self._update_recent_menu()

    def _update_recent_menu(self) -> None:
        self._recent_menu.clear()
        paths = self._recent_paths()
        if not paths:
            placeholder = QAction("(No recent files)", self)
            placeholder.setEnabled(False)
            self._recent_menu.addAction(placeholder)
            return
        for p in paths:
            name = Path(p).name
            action = QAction(name, self)
            action.setToolTip(p)
            action.triggered.connect(lambda checked, path=p: self._open_recent(path))
            self._recent_menu.addAction(action)
        self._recent_menu.addSeparator()
        clear_act = QAction("Clear Recent Files", self)
        clear_act.triggered.connect(self._clear_recent_files)
        self._recent_menu.addAction(clear_act)

    def _clear_recent_files(self) -> None:
        self._settings.setValue("recent_files", [])
        self._update_recent_menu()

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
        self._apply_menu_theme(theme)
        self._render_preview()

    def _sync_os_theme(self) -> None:
        """Detect OS dark/light preference and apply matching theme on first run."""
        try:
            app = QApplication.instance()
            if not isinstance(app, QApplication):
                return
            hints = app.styleHints()
            if hints is None:
                return
            scheme = hints.colorScheme()
            is_dark = scheme == Qt.ColorScheme.Dark
            # Only auto-switch when no explicit preference has been saved yet.
            stored = self._settings.value("theme")
            if stored is None:
                auto_name = theme_for_color_scheme(is_dark)
                theme = THEMES.get(auto_name, THEMES[DEFAULT_THEME])
                self._theme = theme
                self._apply_app_theme(theme)
            # Watch for live OS changes
            hints.colorSchemeChanged.connect(self._on_os_color_scheme_changed)
        except Exception:
            pass

    def _on_os_color_scheme_changed(self, scheme: Qt.ColorScheme) -> None:
        try:
            is_dark = scheme == Qt.ColorScheme.Dark
            auto_name = theme_for_color_scheme(is_dark)
            theme = THEMES.get(auto_name, THEMES[DEFAULT_THEME])
            self._theme = theme
            self._apply_app_theme(theme)
            self._settings.setValue("theme", theme.name)
        except Exception:
            pass

    # ── Drag-and-drop ────────────────────────────────────────────────────────
    def dragEnterEvent(self, a0: QDragEnterEvent | None) -> None:  # type: ignore[override]
        if a0 is None:
            return
        mime = a0.mimeData()
        if mime is None or not mime.hasUrls():
            return
        if any(
            url.toLocalFile().lower().endswith((".md", ".markdown", ".txt"))
            for url in mime.urls()
        ):
            a0.acceptProposedAction()

    def dropEvent(self, a0: QDropEvent | None) -> None:  # type: ignore[override]
        if a0 is None:
            return
        mime = a0.mimeData()
        if mime is None:
            return
        for url in mime.urls():
            local = url.toLocalFile()
            if local.lower().endswith((".md", ".markdown", ".txt")):
                if self._check_unsaved():
                    self._load_file(Path(local))
                break

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
