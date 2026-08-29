#!/usr/bin/env python3
"""
build.py — Render the bilingual changelog site into site/_dist/.

Inputs
    content/i18n.json          page chrome strings, keyed by language
    content/releases/*.md      one file per release, both languages inside
    site/_templates/log.html   page shell
    site/partials/*.html       <!-- include: NAME.html --> fragments
    site/assets/**             copied through unchanged

Output
    site/_dist/index.html      Chinese (default language, site root)
    site/_dist/en/index.html   English
    site/_dist/assets/**

Usage
    python3 scripts/build.py
    python3 -m http.server 8000 --directory site/_dist

Set SITE_BASE_PATH when the site is served from a subpath (GitHub Pages
project sites) and SITE_ORIGIN for the scheme+host used in canonical /
og:image URLs. The Pages workflow passes both automatically.
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
DIST = SITE / "_dist"
PARTIALS_DIR = SITE / "partials"
ASSETS_DIR = SITE / "assets"
TEMPLATE = SITE / "_templates" / "log.html"
I18N_FILE = ROOT / "content" / "i18n.json"
RELEASES_DIR = ROOT / "content" / "releases"

DEFAULT_LANG = "zh"          # served at the site root
FALLBACK_ORIGIN = "https://camtrik.github.io"
LANGS = ["zh", "en"]         # order also drives the hreflang links

INCLUDE_RE = re.compile(r"<!--\s*include:\s*([A-Za-z0-9_.\-]+)\s*-->")
ASSET_RE = re.compile(r'((?:href|src)="[^"]*assets/(?:css|js)/[^"]+\.(?:css|js))"')
FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
LANG_MARKER_RE = re.compile(r"^[ \t]*<!--\s*lang:\s*([a-zA-Z-]+)\s*-->[ \t]*$", re.MULTILINE)

KNOWN_TYPES = {"release", "content", "balance", "hotfix"}


# ------------------------------------------------------------------ helpers

def load_partials() -> dict[str, str]:
    if not PARTIALS_DIR.exists():
        return {}
    return {p.name: p.read_text(encoding="utf-8") for p in PARTIALS_DIR.glob("*.html")}


def normalize_base_path(raw: str | None) -> str:
    if not raw:
        return ""
    path = raw.strip()
    if path in {"", "/"}:
        return ""
    if not path.startswith("/"):
        path = "/" + path
    return path.rstrip("/")


def lang_href(base: str, lang: str) -> str:
    """URL of the changelog page in `lang`, always ending in a slash."""
    return f"{base}/" if lang == DEFAULT_LANG else f"{base}/{lang}/"


# ------------------------------------------------------------ release files

def parse_front_matter(block: str) -> dict:
    """Minimal `key: value` parser — values are scalars or comma lists."""
    meta: dict = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"front matter line is not `key: value`: {line!r}")
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if key == "tags":
            meta[key] = [t.strip() for t in value.split(",") if t.strip()]
        else:
            meta[key] = value
    return meta


def split_lang_bodies(body: str) -> dict[str, str]:
    """Split markdown on `<!-- lang: xx -->` markers into per-language chunks."""
    matches = list(LANG_MARKER_RE.finditer(body))
    if not matches:
        return {DEFAULT_LANG: body.strip()}
    bodies: dict[str, str] = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        bodies[m.group(1).lower()] = body[m.end():end].strip()
    return {k: v for k, v in bodies.items() if v}


def parse_release(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    fm_match = FRONT_MATTER_RE.match(text)
    if not fm_match:
        raise ValueError(f"{path.name}: missing `---` front matter block")
    meta = parse_front_matter(fm_match.group(1))

    for required in ("version", "date"):
        if not meta.get(required):
            raise ValueError(f"{path.name}: front matter is missing `{required}`")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", meta["date"]):
        raise ValueError(f"{path.name}: `date` must be YYYY-MM-DD, got {meta['date']!r}")

    entry_type = meta.get("type", "release")
    if entry_type not in KNOWN_TYPES:
        raise ValueError(f"{path.name}: unknown `type` {entry_type!r}; expected one of {sorted(KNOWN_TYPES)}")

    bodies = split_lang_bodies(text[fm_match.end():])
    if not bodies:
        raise ValueError(f"{path.name}: no body content found")
    if DEFAULT_LANG not in bodies:
        raise ValueError(f"{path.name}: missing a `<!-- lang: {DEFAULT_LANG} -->` block")

    return {
        "source": path.name,
        "version": meta["version"],
        "date": meta["date"],
        "type": entry_type,
        "tags": meta.get("tags", []),
        "bodies": bodies,
    }


def version_key(version: str) -> tuple:
    """Sort 1.10.0 above 1.9.0; unparseable segments fall back to 0."""
    parts = re.split(r"[.\-+]", version)
    return tuple(int(p) if p.isdigit() else 0 for p in parts)


def collect_releases() -> list[dict]:
    if not RELEASES_DIR.exists():
        return []
    releases = [parse_release(p) for p in sorted(RELEASES_DIR.glob("*.md"))]
    releases.sort(key=lambda r: (r["date"], version_key(r["version"])), reverse=True)
    return releases


# --------------------------------------------------------------- rendering

EXTERNAL_LINK_RE = re.compile(r'<a href="(https?://[^"]+)"')


def render_markdown(text: str) -> str:
    import markdown as md_lib

    rendered = md_lib.Markdown(extensions=["tables", "fenced_code", "sane_lists"]).convert(text)
    # Workshop / dependency links in entry bodies always leave the site.
    return EXTERNAL_LINK_RE.sub(r'<a href="\1" target="_blank" rel="noopener"', rendered)


def render_release(release: dict, lang: str, i18n: dict, is_latest: bool) -> str:
    strings = i18n[lang]
    body_lang = lang if lang in release["bodies"] else DEFAULT_LANG
    notice = ""
    if body_lang != lang:
        notice = f'          <p class="release__untranslated">{html.escape(strings["UNTRANSLATED"])}</p>\n'

    type_label = strings["TYPE"].get(release["type"], release["type"])
    badges = [
        f'<span class="type-badge type-badge--{release["type"]}">{html.escape(type_label)}</span>'
    ]
    for tag in release["tags"]:
        label = strings["TAGS"].get(tag, tag)
        slug = re.sub(r"[^a-z0-9]+", "-", tag.lower()).strip("-")
        badges.append(f'<span class="tag-pill tag-pill--{slug}">{html.escape(label)}</span>')

    classes = "release release--latest" if is_latest else "release"
    body_html = render_markdown(release["bodies"][body_lang])

    return (
        f'      <article class="{classes}" data-version="{html.escape(release["version"])}" '
        f'data-tags="{html.escape(" ".join(release["tags"]))}">\n'
        f'        <div class="release__rail"><span class="release__dot"></span></div>\n'
        f'        <div class="release__card">\n'
        f'          <div class="release__head">\n'
        f'            <span class="release__version">v{html.escape(release["version"])}</span>\n'
        f'            <span class="release__date">{html.escape(release["date"])}</span>\n'
        f'            <span class="release__badges">{"".join(badges)}</span>\n'
        f'          </div>\n'
        f'{notice}'
        f'          <div class="release-body" lang="{html.escape(i18n[body_lang]["LANG_HTML"])}">\n'
        f'{body_html}\n'
        f'          </div>\n'
        f'        </div>\n'
        f'      </article>\n'
    )


def build_page(
    lang: str,
    releases: list[dict],
    i18n: dict,
    partials: dict[str, str],
    template: str,
    base: str,
    origin: str,
    build_time: str,
    cache_bust: str,
) -> str:
    strings = i18n[lang]

    if releases:
        entries = "".join(
            render_release(r, lang, i18n, is_latest=(i == 0)) for i, r in enumerate(releases)
        )
        latest_version = f'v{releases[0]["version"]}'
        latest_date = releases[0]["date"]
    else:
        entries = f'      <p class="log-empty">{html.escape(strings["EMPTY"])}</p>\n'
        latest_version = "—"
        latest_date = "—"

    values = {
        "SITE_BASE_PATH": base,
        "BUILD_TIME": build_time,
        "RELEASES": entries,
        "LATEST_VERSION": latest_version,
        "LATEST_DATE": latest_date,
        "SITE_URL": f"{origin}{base}",
        "HREF_SELF": lang_href(base, lang),
        "HREF_ZH": lang_href(base, "zh"),
        "HREF_EN": lang_href(base, "en"),
        "ABS_HREF_SELF": origin + lang_href(base, lang),
        "ABS_HREF_ZH": origin + lang_href(base, "zh"),
        "ABS_HREF_EN": origin + lang_href(base, "en"),
        "CLASS_ZH_ACTIVE": " lang-switch__item--active" if lang == "zh" else "",
        "CLASS_EN_ACTIVE": " lang-switch__item--active" if lang == "en" else "",
    }
    # Most strings land as {{T_KEY}}; these three are used raw in attributes.
    verbatim = {"LANG_HTML", "OG_LOCALE", "WORKSHOP_URL"}
    for key, value in strings.items():
        if isinstance(value, str):
            values[key if key in verbatim else f"T_{key}"] = value

    text = INCLUDE_RE.sub(lambda m: partials.get(m.group(1), m.group(0)), template)
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)

    leftovers = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", text)))
    if leftovers:
        raise ValueError(f"[{lang}] unresolved placeholders: {', '.join(leftovers)}")

    if cache_bust:
        text = ASSET_RE.sub(lambda m: f'{m.group(1)}?v={cache_bust}"', text)
    return text


# -------------------------------------------------------------------- main

def main() -> None:
    if not TEMPLATE.exists():
        raise SystemExit(f"template not found at {TEMPLATE}")

    i18n = json.loads(I18N_FILE.read_text(encoding="utf-8"))
    missing = [lang for lang in LANGS if lang not in i18n]
    if missing:
        raise SystemExit(f"content/i18n.json is missing language(s): {', '.join(missing)}")

    partials = load_partials()
    template = TEMPLATE.read_text(encoding="utf-8")
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

    for lang in LANGS:
        page = build_page(lang, releases, i18n, partials, template, base, origin, build_time, cache_bust)
        out = DIST / "index.html" if lang == DEFAULT_LANG else DIST / lang / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding="utf-8")
        print(f"[build] {lang:>2} -> {out.relative_to(ROOT)}")

    for release in releases:
        gaps = [lang for lang in LANGS if lang not in release["bodies"]]
        if gaps:
            print(f"[build] WARNING: {release['source']} has no {'/'.join(gaps)} body; falling back to {DEFAULT_LANG}")

    print(f"[build] releases: {len(releases)}   partials: {len(partials)}")
    print(f"[build] BUILD_TIME = {build_time}")
    print(f"[build] SITE_BASE_PATH = {base or '/'}")
    print(f"[build] SITE_ORIGIN    = {origin}")


if __name__ == "__main__":
    main()
