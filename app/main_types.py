"""Protocol shared by the optional AI integration without circular imports."""
from __future__ import annotations
from typing import Protocol

class CitationLike(Protocol):
    section: str
    source: str
    excerpt: str
