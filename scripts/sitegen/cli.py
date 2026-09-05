"""Wiring: load everything, render every language x page, write site/_dist."""
from __future__ import annotations

import os
import shutil
import time
from datetime import datetime, timezone

from .config import (
    ASSETS_DIR,
    DEFAULT_LANG,
    DIST,
    FALLBACK_ORIGIN,
    LANGS,
    PAGES,
    ROOT,
)
from .content import load_faq, load_home, load_i18n
from .fonts import check_font_coverage
from .page import build_page
from .releases import collect_releases
from .templates import load_partials, load_templates
from .urls import normalize_base_path, page_href


def main() -> None:
    i18n = load_i18n()
    home = load_home()
    faq = load_faq()
    partials = load_partials()
    templates = load_templates()

    releases = collect_releases()
    base = normalize_base_path(os.environ.get("SITE_BASE_PATH", ""))
    origin = (os.environ.get("SITE_ORIGIN") or FALLBACK_ORIGIN).rstrip("/")
    build_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    cache_bust = str(int(time.time()))

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    if ASSETS_DIR.exists():
        shutil.copytree(
            ASSETS_DIR,
            DIST / "assets",
            ignore=lambda _d, names: [n for n in names if n.startswith(".")],
        )

    rendered = {}
    for lang in LANGS:
        for page in PAGES:
            text = build_page(page, lang, releases, home, faq, i18n, partials, templates[page],
                              base, origin, build_time, cache_bust)
            out = DIST / page_href("", lang, page).strip("/") / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding="utf-8")
            rendered[f"{lang}/{page}"] = text
            print(f"[build] {lang:>2} {page:<10} -> {out.relative_to(ROOT)}")

    check_font_coverage(rendered)

    for release in releases:
        gaps = [lang for lang in LANGS if lang not in release["bodies"]]
        if gaps:
            print(f"[build] WARNING: {release['source']} has no {'/'.join(gaps)} body; falling back to {DEFAULT_LANG}")

    print(f"[build] releases: {len(releases)}   partials: {len(partials)}")
    print(f"[build] BUILD_TIME = {build_time}")
    print(f"[build] SITE_BASE_PATH = {base or '/'}")
    print(f"[build] SITE_ORIGIN    = {origin}")
