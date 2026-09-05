"""The shell every landing-page band is built inside."""
from __future__ import annotations

from ..text import esc


def section_open(slug: str, lang: str, title, extra: str = "", lede=None) -> str:
    """Shared section shell: an eyebrow-styled heading plus optional lede."""
    head = f'<section class="band band--{slug}{(" " + extra) if extra else ""}" id="{slug}">\n'
    head += '  <div class="band__inner">\n'
    head += f'    <h2 class="band__title">{esc(title, lang)}</h2>\n'
    if lede:
        head += f'    <p class="band__lede">{esc(lede, lang)}</p>\n'
    return head


def section_close() -> str:
    return "  </div>\n</section>\n"
