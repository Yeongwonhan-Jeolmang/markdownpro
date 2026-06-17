"""
themes/__init__.py
All visual themes for the app shell (editor + chrome) and the HTML preview.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class AppTheme:
    name: str
    # Editor palette
    editor_bg: str
    editor_fg: str
    editor_sel: str
    editor_line: str
    editor_font: str
    # Chrome palette
    bg: str
    surface: str
    border: str
    fg: str
    fg_dim: str
    accent: str
    accent_fg: str
    # Pygments style name
    code_style: str
    # Preview colors
    preview_bg: str
    preview_fg: str
    preview_fg_dim: str
    preview_surface: str
    preview_border: str
    preview_dark: bool


THEMES: dict[str, AppTheme] = {
    "Ink": AppTheme(
        name="Ink",
        editor_bg="#1B1E27",
        editor_fg="#C9D1E0",
        editor_sel="#2E3A52",
        editor_line="#22263A",
        editor_font="'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
        bg="#111318",
        surface="#1B1E27",
        border="#2A2E3E",
        fg="#C9D1E0",
        fg_dim="#6B7494",
        accent="#5E9BF0",
        accent_fg="#FFFFFF",
        code_style="dracula",
        preview_bg="#1B1E27",
        preview_fg="#C9D1E0",
        preview_fg_dim="#6B7494",
        preview_surface="#22263A",
        preview_border="#2A2E3E",
        preview_dark=True,
    ),
    "Parchment": AppTheme(
        name="Parchment",
        editor_bg="#FDF6E3",
        editor_fg="#3B2D1E",
        editor_sel="#E6D5B0",
        editor_line="#F5EDD4",
        editor_font="'JetBrains Mono', 'Fira Code', monospace",
        bg="#EDE4CC",
        surface="#FDF6E3",
        border="#D4C59A",
        fg="#3B2D1E",
        fg_dim="#9E8B72",
        accent="#C05F2A",
        accent_fg="#FFFFFF",
        code_style="friendly",
        preview_bg="#FDF6E3",
        preview_fg="#2C1E10",
        preview_fg_dim="#9E8B72",
        preview_surface="#F0E6CC",
        preview_border="#D4C59A",
        preview_dark=False,
    ),
    "Graphite": AppTheme(
        name="Graphite",
        editor_bg="#212121",
        editor_fg="#E0E0E0",
        editor_sel="#3A3A3A",
        editor_line="#282828",
        editor_font="'JetBrains Mono', 'Fira Code', monospace",
        bg="#181818",
        surface="#212121",
        border="#333333",
        fg="#E0E0E0",
        fg_dim="#777777",
        accent="#EEEEEE",
        accent_fg="#181818",
        code_style="monokai",
        preview_bg="#1A1A1A",
        preview_fg="#DEDEDE",
        preview_fg_dim="#888888",
        preview_surface="#272727",
        preview_border="#333333",
        preview_dark=True,
    ),
    "Light": AppTheme(
        name="Light",
        editor_bg="#FFFFFF",
        editor_fg="#1A1A1A",
        editor_sel="#B5D5FF",
        editor_line="#F5F7FA",
        editor_font="'JetBrains Mono', 'Fira Code', monospace",
        bg="#F0F2F5",
        surface="#FFFFFF",
        border="#DCDFE6",
        fg="#1A1A1A",
        fg_dim="#767676",
        accent="#0066CC",
        accent_fg="#FFFFFF",
        code_style="friendly",
        preview_bg="#FFFFFF",
        preview_fg="#1A1A1A",
        preview_fg_dim="#666666",
        preview_surface="#F5F7FA",
        preview_border="#E0E4EC",
        preview_dark=False,
    ),
}

DEFAULT_THEME = "Ink"


def theme_for_color_scheme(is_dark: bool) -> str:
    """Return a theme name that matches the OS color scheme."""
    return "Ink" if is_dark else "Light"
