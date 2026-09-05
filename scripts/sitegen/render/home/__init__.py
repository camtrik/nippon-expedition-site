"""The landing page, in the four voices site/_templates/home.html sets out:
night, day, night, day. The order blocks appear in belongs to that template —
these modules only say what each block contains.
"""
from __future__ import annotations

from .hero import render_hero
from .manifest import (
    render_buildings,
    render_companions,
    render_lords,
    render_overview,
    render_units,
)
from .reference import render_ai, render_compat, render_credits, render_relocations
from .victory import render_victory


def render_home(home: dict, lang: str, strings: dict, base: str, latest: str) -> dict[str, str]:
    """Every {{HOME_*}} block the landing template asks for."""
    return {
        "HOME_HERO": render_hero(home, lang, strings, base, latest),
        "HOME_OVERVIEW": render_overview(home, lang),
        "HOME_LORDS": render_lords(home, lang, base),
        "HOME_COMPANIONS": render_companions(home, lang, base),
        "HOME_UNITS": render_units(home, lang, base),
        "HOME_BUILDINGS": render_buildings(home, lang),
        "HOME_VICTORY": render_victory(home, lang),
        "HOME_RELOCATIONS": render_relocations(home, lang),
        "HOME_AI": render_ai(home, lang),
        "HOME_COMPAT": render_compat(home, lang),
        "HOME_CREDITS": render_credits(home, lang),
    }
