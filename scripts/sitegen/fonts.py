"""The guard that keeps one sentence from rendering in two typefaces."""
from __future__ import annotations

import html
import re

from .config import FONT_COVERAGE

TAG_RE = re.compile(r"<[^>]+>")


def check_font_coverage(pages: dict[str, str]) -> None:
    """Fail if a page needs a character the subset webfont does not carry.

    site/assets/fonts/ holds LXGW WenKai GB cut down to exactly the characters
    the site renders. A character outside that cut falls through to the system
    stack, so one sentence ends up in two typefaces — the same failure the
    --font-sans ordering comment in base.css describes. Catch it at build time
    rather than in a screenshot.
    """
    if not FONT_COVERAGE.exists():
        print("[build] WARNING: no font coverage manifest; run scripts/subset_fonts.py")
        return

    covered = set(FONT_COVERAGE.read_text(encoding="utf-8"))
    missing: dict[str, set[str]] = {}
    for lang, page in pages.items():
        text = html.unescape(TAG_RE.sub(" ", page))
        gaps = {
            c for c in text
            if ord(c) > 0x7F and not (0xFE00 <= ord(c) <= 0xFE0F) and c not in covered
        }
        if gaps:
            missing[lang] = gaps

    if missing:
        detail = "; ".join(
            f"[{lang}] {''.join(sorted(chars))}" for lang, chars in sorted(missing.items())
        )
        raise SystemExit(
            f"font subset is missing {sum(len(c) for c in missing.values())} character(s): {detail}\n"
            "These would render in a fallback typeface, mid-sentence. Regenerate with:\n"
            "    pip install fonttools brotli && python3 scripts/subset_fonts.py"
        )
