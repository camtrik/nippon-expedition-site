"""The template layer: partials, includes, and {{PLACEHOLDER}} substitution.

Deliberately not a template engine — includes are one non-recursive pass and
substitution is str.replace, which is the whole vocabulary the three page
shells need. Adding a real engine would add a dependency and a second syntax
for people who only ever edit copy.
"""
from __future__ import annotations

import re

from .config import PAGES, PARTIALS_DIR, TEMPLATES_DIR

INCLUDE_RE = re.compile(r"<!--\s*include:\s*([A-Za-z0-9_.\-]+)\s*-->")
ASSET_RE = re.compile(r'((?:href|src)="[^"]*assets/(?:css|js)/[^"]+\.(?:css|js))"')


def load_partials() -> dict[str, str]:
    if not PARTIALS_DIR.exists():
        return {}
    return {p.name: p.read_text(encoding="utf-8") for p in PARTIALS_DIR.glob("*.html")}


def load_templates() -> dict[str, str]:
    templates = {}
    for page, (filename, _) in PAGES.items():
        path = TEMPLATES_DIR / filename
        if not path.exists():
            raise SystemExit(f"template not found at {path}")
        templates[page] = path.read_text(encoding="utf-8")
    return templates


def apply_includes(template: str, partials: dict[str, str]) -> str:
    """One pass, so a partial cannot include another. An unknown name is left
    in the output as written rather than silently vanishing."""
    return INCLUDE_RE.sub(lambda m: partials.get(m.group(1), m.group(0)), template)


def substitute(text: str, values: dict[str, str], where: str) -> str:
    """Fill every {{KEY}}; a placeholder nobody supplied is a build error, not
    a stray {{...}} shipped to a reader."""
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    leftovers = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", text)))
    if leftovers:
        raise ValueError(f"[{where}] unresolved placeholders: {', '.join(leftovers)}")
    return text


def cache_bust(text: str, stamp: str) -> str:
    """Version the stylesheet and script URLs in one rendered page. Keyed on
    the URL in the HTML, so it does not care where the file came from."""
    if not stamp:
        return text
    return ASSET_RE.sub(lambda m: f'{m.group(1)}?v={stamp}"', text)
