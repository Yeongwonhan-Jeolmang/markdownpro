"""
core/page_builder.py
Wraps a rendered HTML fragment in a full, styled HTML page for the preview pane.
All colours are driven by theme tokens.
"""

from __future__ import annotations
from themes import AppTheme


def build_page(fragment: str, theme: AppTheme, code_css: str) -> str:
    """Return a complete HTML page string for display in QWebEngineView."""

    # Overlay helpers: on dark backgrounds we lighten; on light we darken.
    if theme.preview_dark:
        overlay_sm  = "rgba(255,255,255,.05)"
        overlay_md  = "rgba(255,255,255,.07)"
        overlay_lg  = "rgba(255,255,255,.10)"
        overlay_row = "rgba(255,255,255,.03)"
        hr_color    = "rgba(255,255,255,.10)"
    else:
        overlay_sm  = "rgba(0,0,0,.04)"
        overlay_md  = "rgba(0,0,0,.06)"
        overlay_lg  = "rgba(0,0,0,.09)"
        overlay_row = "rgba(0,0,0,.025)"
        hr_color    = "rgba(0,0,0,.10)"

    p  = theme.preview_bg
    f  = theme.preview_fg
    fd = theme.preview_fg_dim
    ps = theme.preview_surface
    pb = theme.preview_border
    a  = theme.accent

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
/* ── Reset ─────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

/* ── Page ──────────────────────────────────── */
html {{
  font-size: 16px;
  background: {p};
  color: {f};
  scroll-behavior: smooth;
}}
body {{
  font-family: 'Georgia', 'Palatino Linotype', serif;
  line-height: 1.75;
  max-width: 780px;
  margin: 0 auto;
  padding: 3rem 2rem 6rem;
  background: {p};
  color: {f};
}}

/* ── Typography ────────────────────────────── */
h1, h2, h3, h4, h5, h6 {{
  font-family: 'Inter', 'Helvetica Neue', system-ui, sans-serif;
  font-weight: 700;
  line-height: 1.25;
  margin-top: 2em;
  margin-bottom: .5em;
  letter-spacing: -0.02em;
  color: {f};
}}
h1 {{ font-size: 2.25rem; border-bottom: 2px solid {a}; padding-bottom: .3em; }}
h2 {{ font-size: 1.65rem; }}
h3 {{ font-size: 1.3rem; }}
h4 {{ font-size: 1.05rem; font-weight: 600; }}
h5, h6 {{ font-size: 0.95rem; font-weight: 600; color: {fd}; }}

p {{ margin: 1em 0; }}

/* ── Links ─────────────────────────────────── */
a {{ color: {a}; text-decoration: none; border-bottom: 1px solid transparent; transition: border-color .15s; }}
a:hover {{ border-bottom-color: {a}; }}

/* ── Inline code ───────────────────────────── */
code {{
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
  font-size: .85em;
  background: {ps};
  color: {f};
  border: 1px solid {pb};
  border-radius: 3px;
  padding: .1em .35em;
}}

/* ── Fenced code blocks ────────────────────── */
pre {{
  border-radius: 8px;
  overflow: auto;
  margin: 1.5em 0;
  font-size: .85rem;
  line-height: 1.6;
  background: {ps};
  border: 1px solid {pb};
}}
pre code {{
  background: transparent;
  border: none;
  padding: 0;
  color: inherit;
}}
.highlight {{ border-radius: 8px; overflow: hidden; border: 1px solid {pb}; }}
.highlight pre {{ margin: 0; padding: 1.25rem 1.5rem; border: none; border-radius: 0; }}

/* ── Pygments ──────────────────────────────── */
{code_css}

/* ── Blockquote ────────────────────────────── */
blockquote {{
  margin: 1.5em 0;
  padding: .75em 1.25em;
  border-left: 3px solid {a};
  background: {overlay_sm};
  color: {fd};
  font-style: italic;
  border-radius: 0 6px 6px 0;
}}
blockquote p {{ margin: 0; }}

/* ── Tables ────────────────────────────────── */
table {{
  width: 100%;
  border-collapse: collapse;
  margin: 1.5em 0;
  font-size: .9rem;
}}
th {{
  background: {ps};
  font-family: 'Inter', system-ui, sans-serif;
  font-weight: 600;
  text-align: left;
  padding: .65em 1em;
  border-bottom: 2px solid {pb};
  color: {f};
}}
td {{
  padding: .6em 1em;
  border-bottom: 1px solid {pb};
  color: {f};
}}
tr:last-child td {{ border-bottom: none; }}
tr:hover td {{ background: {overlay_row}; }}

/* ── Lists ─────────────────────────────────── */
ul, ol {{ padding-left: 1.75em; margin: 1em 0; }}
li {{ margin: .35em 0; }}
li > ul, li > ol {{ margin: .3em 0; }}

/* ── HR ─────────────────────────────────────── */
hr {{ border: none; border-top: 1px solid {hr_color}; margin: 2.5em 0; }}

/* ── Images ─────────────────────────────────── */
img {{ max-width: 100%; border-radius: 6px; display: block; margin: 1em auto; }}

/* ── Admonitions ────────────────────────────── */
.admonition {{
  border-radius: 6px;
  padding: 1em 1.25em;
  margin: 1.5em 0;
  border-left: 4px solid {fd};
  background: {overlay_sm};
}}
.admonition.note   {{ border-color: {a}; background: {overlay_sm}; }}
.admonition.warning {{ border-color: #d4900a; background: rgba(212,144,10,.10); }}
.admonition.danger  {{ border-color: #d94f4f; background: rgba(217,79,79,.10); }}
.admonition.tip     {{ border-color: #3daa70; background: rgba(61,170,112,.10); }}
.admonition-title {{
  font-family: 'Inter', system-ui, sans-serif;
  font-weight: 700;
  font-size: .85rem;
  text-transform: uppercase;
  letter-spacing: .07em;
  margin-bottom: .5em;
  color: {f};
}}

/* ── TOC ─────────────────────────────────────── */
.toc {{
  background: {ps};
  border: 1px solid {pb};
  border-radius: 8px;
  padding: 1rem 1.5rem;
  margin: 1.5em 0;
  display: inline-block;
  min-width: 200px;
}}
.toc ul {{ list-style: none; padding-left: 1em; margin: .25em 0; }}
.toc > ul {{ padding-left: 0; }}

/* ── Footnotes ───────────────────────────────── */
.footnote {{
  font-size: .82rem;
  color: {fd};
  border-top: 1px solid {hr_color};
  margin-top: 3rem;
  padding-top: 1rem;
}}

/* ── Definition list ─────────────────────────── */
dl {{ margin: 1em 0; }}
dt {{ font-weight: 700; margin-top: .75em; color: {f}; }}
dd {{ padding-left: 1.5em; color: {fd}; }}

/* ── Permalink anchors ───────────────────────── */
.headerlink {{ opacity: 0; font-size: .75em; padding-left: .4em; color: {a}; }}
h1:hover .headerlink, h2:hover .headerlink, h3:hover .headerlink,
h4:hover .headerlink, h5:hover .headerlink, h6:hover .headerlink {{ opacity: 1; }}

/* ── Selection ───────────────────────────────── */
::selection {{ background: {a}44; }}

/* ── Scrollbar ───────────────────────────────── */
::-webkit-scrollbar {{ width: 8px; height: 8px; }}
::-webkit-scrollbar-track {{ background: {p}; }}
::-webkit-scrollbar-thumb {{ background: {pb}; border-radius: 4px; border: 2px solid {p}; }}
::-webkit-scrollbar-thumb:hover {{ background: {fd}; }}
::-webkit-scrollbar-corner {{ background: {p}; }}
</style>
</head>
<body>
{fragment}
</body>
</html>"""
