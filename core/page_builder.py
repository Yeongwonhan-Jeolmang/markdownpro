"""
core/page_builder.py
Wraps a rendered HTML fragment in a full, styled HTML page for the preview pane. Credits go to Anna Zieleman and Florian van den Bersselaar for this section.
"""

from __future__ import annotations
from themes import AppTheme
from core.renderer import MarkdownRenderer


def build_page(fragment: str, theme: AppTheme, code_css: str) -> str:
    """Return a complete HTML page string for display in QWebEngineView."""
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
  background: {theme.preview_bg};
  color: {theme.preview_fg};
}}
body {{
  font-family: 'Georgia', 'Palatino Linotype', serif;
  line-height: 1.75;
  max-width: 780px;
  margin: 0 auto;
  padding: 3rem 2rem 6rem;
  background: {theme.preview_bg};
  color: {theme.preview_fg};
}}

/* ── Typography ────────────────────────────── */
h1, h2, h3, h4, h5, h6 {{
  font-family: 'Inter', 'Helvetica Neue', system-ui, sans-serif;
  font-weight: 700;
  line-height: 1.25;
  margin-top: 2em;
  margin-bottom: .5em;
  letter-spacing: -0.02em;
}}
h1 {{ font-size: 2.25rem; border-bottom: 2px solid {theme.accent}; padding-bottom: .3em; }}
h2 {{ font-size: 1.65rem; }}
h3 {{ font-size: 1.3rem; }}
h4 {{ font-size: 1.05rem; font-weight: 600; }}
h5, h6 {{ font-size: 0.95rem; font-weight: 600; color: #777; }}

p {{ margin: 1em 0; }}

/* ── Links ─────────────────────────────────── */
a {{ color: {theme.accent}; text-decoration: none; border-bottom: 1px solid transparent; transition: border-color .15s; }}
a:hover {{ border-bottom-color: {theme.accent}; }}

/* ── Code ──────────────────────────────────── */
code {{
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
  font-size: .85em;
  background: rgba(0,0,0,.06);
  border-radius: 3px;
  padding: .1em .35em;
}}
pre {{
  border-radius: 8px;
  overflow: auto;
  margin: 1.5em 0;
  font-size: .85rem;
  line-height: 1.6;
}}
pre code {{
  background: transparent;
  padding: 0;
}}
.highlight {{ border-radius: 8px; overflow: hidden; }}
.highlight pre {{ margin: 0; padding: 1.25rem 1.5rem; }}

/* ── Pygments ──────────────────────────────── */
{code_css}

/* ── Blockquote ────────────────────────────── */
blockquote {{
  margin: 1.5em 0;
  padding: .75em 1.25em;
  border-left: 3px solid {theme.accent};
  background: rgba(0,0,0,.03);
  color: #555;
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
  background: rgba(0,0,0,.05);
  font-family: 'Inter', system-ui, sans-serif;
  font-weight: 600;
  text-align: left;
  padding: .65em 1em;
  border-bottom: 2px solid rgba(0,0,0,.12);
}}
td {{
  padding: .6em 1em;
  border-bottom: 1px solid rgba(0,0,0,.07);
}}
tr:last-child td {{ border-bottom: none; }}
tr:hover td {{ background: rgba(0,0,0,.025); }}

/* ── Lists ─────────────────────────────────── */
ul, ol {{ padding-left: 1.75em; margin: 1em 0; }}
li {{ margin: .35em 0; }}
li > ul, li > ol {{ margin: .3em 0; }}

/* ── HR ─────────────────────────────────────── */
hr {{ border: none; border-top: 1px solid rgba(0,0,0,.12); margin: 2.5em 0; }}

/* ── Images ─────────────────────────────────── */
img {{ max-width: 100%; border-radius: 6px; display: block; margin: 1em auto; }}

/* ── Admonitions ────────────────────────────── */
.admonition {{
  border-radius: 6px;
  padding: 1em 1.25em;
  margin: 1.5em 0;
  border-left: 4px solid #aaa;
  background: rgba(0,0,0,.04);
}}
.admonition.note {{ border-color: {theme.accent}; }}
.admonition.warning {{ border-color: #e6a817; background: rgba(230,168,23,.07); }}
.admonition.danger {{ border-color: #e05252; background: rgba(224,82,82,.07); }}
.admonition.tip {{ border-color: #4caf7d; background: rgba(76,175,125,.07); }}
.admonition-title {{
  font-family: 'Inter', system-ui, sans-serif;
  font-weight: 700;
  font-size: .85rem;
  text-transform: uppercase;
  letter-spacing: .07em;
  margin-bottom: .5em;
}}

/* ── TOC ─────────────────────────────────────── */
.toc {{
  background: rgba(0,0,0,.03);
  border: 1px solid rgba(0,0,0,.08);
  border-radius: 8px;
  padding: 1rem 1.5rem;
  margin: 1.5em 0;
  display: inline-block;
  min-width: 200px;
}}
.toc ul {{ list-style: none; padding-left: 1em; margin: .25em 0; }}
.toc > ul {{ padding-left: 0; }}

/* ── Footnotes ───────────────────────────────── */
.footnote {{ font-size: .82rem; color: #777; border-top: 1px solid rgba(0,0,0,.1); margin-top: 3rem; padding-top: 1rem; }}

/* ── Definition list ─────────────────────────── */
dl {{ margin: 1em 0; }}
dt {{ font-weight: 700; margin-top: .75em; }}
dd {{ padding-left: 1.5em; color: #555; }}

/* ── Permalink anchors ───────────────────────── */
.headerlink {{ opacity: 0; font-size: .75em; padding-left: .4em; color: {theme.accent}; }}
h1:hover .headerlink, h2:hover .headerlink, h3:hover .headerlink,
h4:hover .headerlink, h5:hover .headerlink, h6:hover .headerlink {{ opacity: 1; }}

/* ── Selection ───────────────────────────────── */
::selection {{ background: {theme.accent}33; }}

/* ── Smooth scroll ───────────────────────────── */
html {{ scroll-behavior: smooth; }}
</style>
</head>
<body>
{fragment}
</body>
</html>"""
