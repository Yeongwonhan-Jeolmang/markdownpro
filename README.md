# MarkdownPro

A clean, distraction-free Markdown editor with live split preview, syntax highlighting, multiple themes, and export to HTML/PDF.

## Features

- **Live split preview** — editor and preview side-by-side, updates as you type
- **Scroll sync** — editor scroll position is mirrored in the preview pane
- **Syntax highlighting** — headings, bold, italic, code, links, strikethrough, task lists
- **Multiple themes** — Ink (dark), Parchment (warm light), Graphite (monochrome), Light (clean)
- **OS theme sync** — automatically follows your system dark/light preference on first launch
- **Undo / Redo** — full undo history via Ctrl+Z / Ctrl+Y (toolbar buttons + shortcuts)
- **Auto-save** — writes a recovery file every 60 seconds; prompts to restore after a crash
- **Recent files** — File → Open Recent remembers the last 10 opened files
- **Export** — HTML and PDF export; PDF confirmation shown only after the file is written
- **Print** — sends the rendered preview to any system printer via Ctrl+P
- **Find & Replace** — with live match count (Ctrl+F)
- **Insert shortcuts** — Ctrl+B bold, Ctrl+I italic, Ctrl+\` inline code, Ctrl+Shift+\` fenced code block, Ctrl+1–6 headings
- **Font zoom** — Ctrl+= / Ctrl+- adjusts editor font size
- **Word wrap toggle** — toggle soft-wrap for prose vs. code-heavy documents
- **Line numbers** — optional gutter with current-line accent
- **Cursor position** — status bar shows current line and column
- **Drag & drop** — drop a `.md` / `.markdown` / `.txt` file onto the window to open it

## Requirements

- Python 3.10+
- PyQt6 ≥ 6.6
- PyQt6-WebEngine ≥ 6.6
- markdown ≥ 3.5
- pymdown-extensions ≥ 10.0
- Pygments ≥ 2.17

Optional for printing:
- PyQt6-Qt6PrintSupport

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/Yeongwonhan-Jeolmang/markdownpro.git
cd markdownpro

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python main.py

# Optional: open a file directly
python main.py path/to/file.md
```

## Install as a package

```bash
pip install .
markdownpro
```

## Keyboard shortcuts

| Action | Shortcut |
|--------|----------|
| New file | Ctrl+N |
| Open file | Ctrl+O |
| Save | Ctrl+S |
| Save As | Ctrl+Shift+S |
| Undo | Ctrl+Z |
| Redo | Ctrl+Y or Ctrl+Shift+Z |
| Find & Replace | Ctrl+F |
| Bold | Ctrl+B |
| Italic | Ctrl+I |
| Inline code | Ctrl+\` |
| Fenced code block | Ctrl+Shift+\` |
| Heading 1–6 | Ctrl+1 through Ctrl+6 |
| Font size larger | Ctrl+= |
| Font size smaller | Ctrl+- |
| Print | Ctrl+P |
| Quit | Ctrl+Q |

## Project structure

```
markdownpro/
├── main.py               # Entry point
├── core/
│   ├── document.py       # Document model (load/save/change tracking)
│   ├── exporter.py       # HTML and PDF export
│   ├── page_builder.py   # Assembles the preview HTML page
│   └── renderer.py       # Markdown → HTML renderer
├── ui/
│   ├── main_window.py    # Main application window
│   ├── editor.py         # MarkdownEditor widget + syntax highlighter
│   ├── preview.py        # QWebEngineView preview pane
│   ├── toolbar.py        # Top toolbar
│   ├── statusbar.py      # Bottom status bar
│   └── find_replace.py   # Find & Replace bar
└── themes/
    └── __init__.py       # Theme definitions (Ink, Parchment, Graphite, Light)
```

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).
