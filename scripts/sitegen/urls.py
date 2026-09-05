"""Where a page lives, and how a base path is spelled."""
from __future__ import annotations

from .config import DEFAULT_LANG, PAGES


def normalize_base_path(raw: str | None) -> str:
    if not raw:
        return ""
    path = raw.strip()
    if path in {"", "/"}:
        return ""
    if not path.startswith("/"):
        path = "/" + path
    return path.rstrip("/")


def page_href(base: str, lang: str, page: str) -> str:
    """URL of `page` in `lang`, always ending in a slash."""
    parts = [base]
    if lang != DEFAULT_LANG:
        parts.append(lang)
    sub = PAGES[page][1]
    if sub:
        parts.append(sub)
    return "/".join(parts) + "/"
