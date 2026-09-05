"""Reading a bilingual field, and the little markdown the site allows."""
from __future__ import annotations

import html
import re

from .config import DEFAULT_LANG

EXTERNAL_LINK_RE = re.compile(r'<a href="(https?://[^"]+)"')
# Python-Markdown ends a list at any blank line inside an item, silently folding
# the following bullets into one paragraph. Catch that instead of shipping it.
SWALLOWED_BULLET_RE = re.compile(r"<p>[^<]*(?:^|\s)- \S", re.MULTILINE)
# `- 2026-08-30 ...` in a submod section: the leading date is a label, not prose.
# Only top-level items carry one, so nested sub-bullets are left alone.
LIST_DATE_RE = re.compile(r"(<li>(?:<p>)?)(\d{4}-\d{2}-\d{2})\s+")


def pick(field, lang: str) -> str:
    """Read one bilingual field; fall back to the default language."""
    if isinstance(field, str):
        return field
    value = field.get(lang) or ""
    return value if value else field.get(DEFAULT_LANG, "")


def esc(field, lang: str) -> str:
    return html.escape(pick(field, lang))


def render_markdown(text: str) -> str:
    import markdown as md_lib

    rendered = md_lib.Markdown(extensions=["tables", "fenced_code", "sane_lists"]).convert(text)
    if SWALLOWED_BULLET_RE.search(rendered):
        raise ValueError(
            "a list was broken by a blank line: bullets ended up inside a paragraph. "
            "Indent continuation text as a nested `    - ` sub-bullet instead of a blank-line paragraph."
        )
    rendered = LIST_DATE_RE.sub(r'\1<span class="entry-date">\2</span>', rendered)
    # Workshop / dependency links in entry bodies always leave the site.
    return EXTERNAL_LINK_RE.sub(r'<a href="\1" target="_blank" rel="noopener"', rendered)


def inline_md(field, lang: str) -> str:
    """Bold and code spans inside one bilingual string; no block markup."""
    import markdown as md_lib

    text = pick(field, lang)
    if not text:
        return ""
    rendered = md_lib.Markdown().convert(text).strip()
    if rendered.startswith("<p>") and rendered.endswith("</p>"):
        rendered = rendered[3:-4]
    return EXTERNAL_LINK_RE.sub(r'<a href="\1" target="_blank" rel="noopener"', rendered)
