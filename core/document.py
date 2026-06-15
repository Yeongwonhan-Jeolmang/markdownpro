"""
core/document.py
Represents an open Markdown document with save/load and change-tracking.
"""

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Document:
    path: Optional[Path] = None
    text: str = ""
    _saved_text: str = field(default="", init=False, repr=False)

    # ── state ──────────────────────────────────────────────────────────────
    @property
    def is_modified(self) -> bool:
        return self.text != self._saved_text

    @property
    def display_name(self) -> str:
        name = self.path.name if self.path else "Untitled"
        return f"{'●  ' if self.is_modified else ''}{name}"

    # ── I/O ────────────────────────────────────────────────────────────────
    @classmethod
    def open(cls, path: Path) -> "Document":
        text = path.read_text(encoding="utf-8")
        doc = cls(path=path, text=text)
        doc._saved_text = text
        return doc

    def save(self, path: Optional[Path] = None) -> None:
        target = path or self.path
        if target is None:
            raise ValueError("No path specified")
        self.path = target
        target.write_text(self.text, encoding="utf-8")
        self._saved_text = self.text

    def new(self) -> None:
        self.path = None
        self.text = ""
        self._saved_text = ""
