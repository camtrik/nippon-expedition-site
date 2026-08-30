#!/usr/bin/env python3
"""
build.py — Render the bilingual site into site/_dist/.

Inputs
    content/i18n.json          page chrome strings, keyed by language
    content/home.json          landing page content, both languages per field
    content/faq.json           FAQ page content, both languages per field
    content/releases/*.md      one file per release, both languages inside
    site/_templates/*.html     page shells
    site/partials/*.html       <!-- include: NAME.html --> fragments
    site/assets/**             copied through unchanged

Output
    site/_dist/index.html                Chinese landing page (site root)
    site/_dist/en/index.html             English landing page
    site/_dist/changelog/index.html      Chinese changelog
    site/_dist/en/changelog/index.html   English changelog
    site/_dist/faq/index.html            Chinese FAQ
    site/_dist/en/faq/index.html         English FAQ
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
TEMPLATES_DIR = SITE / "_templates"
I18N_FILE = ROOT / "content" / "i18n.json"
HOME_FILE = ROOT / "content" / "home.json"
FAQ_FILE = ROOT / "content" / "faq.json"
RELEASES_DIR = ROOT / "content" / "releases"

DEFAULT_LANG = "zh"          # served at the site root
FALLBACK_ORIGIN = "https://camtrik.github.io"
LANGS = ["zh", "en"]         # order also drives the hreflang links

# name -> (template, url path under the language root)
PAGES = {
    "home": ("home.html", ""),
    "changelog": ("log.html", "changelog"),
    "faq": ("faq.html", "faq"),
}

INCLUDE_RE = re.compile(r"<!--\s*include:\s*([A-Za-z0-9_.\-]+)\s*-->")
ASSET_RE = re.compile(r'((?:href|src)="[^"]*assets/(?:css|js)/[^"]+\.(?:css|js))"')
FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
LANG_MARKER_RE = re.compile(r"^[ \t]*<!--\s*lang:\s*([a-zA-Z-]+)\s*-->[ \t]*$", re.MULTILINE)

KNOWN_TYPES = {"release", "content", "balance", "hotfix"}
# Which timeline an entry belongs to. The main mod carries the version number
# the whole site quotes; a submod ships on its own clock and must not perturb
# that number, so the two are counted and displayed apart.
CHANNEL_ORDER = ("main", "submod")
DEFAULT_CHANNEL = "main"
# A submod has no version number, so the date rides on each change instead of on
# the entry: one section per submod, newest line first, mirroring version.md.
BODY_DATE_RE = re.compile(r"^\s*-\s+(\d{4}-\d{2}-\d{2})\b", re.MULTILINE)

FONT_COVERAGE = ASSETS_DIR / "fonts" / "coverage.txt"
TAG_RE = re.compile(r"<[^>]+>")

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


def page_href(base: str, lang: str, page: str) -> str:
    """URL of `page` in `lang`, always ending in a slash."""
    parts = [base]
    if lang != DEFAULT_LANG:
        parts.append(lang)
    sub = PAGES[page][1]
    if sub:
        parts.append(sub)
    return "/".join(parts) + "/"


def pick(field, lang: str) -> str:
    """Read one bilingual field; fall back to the default language."""
    if isinstance(field, str):
        return field
    value = field.get(lang) or ""
    return value if value else field.get(DEFAULT_LANG, "")


def esc(field, lang: str) -> str:
    return html.escape(pick(field, lang))


# ------------------------------------------------------------ release files

def parse_front_matter(block: str) -> dict:
    """Minimal `key: value` parser — values are scalars, comma lists, or
    `key.<lang>` lines that collect into one bilingual dict, matching how the
    JSON content files keep both languages in a single field."""
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
        elif "." in key:
            field, lang = key.rsplit(".", 1)
            if not isinstance(meta.get(field), dict):
                meta[field] = {}
            meta[field][lang] = value
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

    title = meta.get("title") or ""
    if not meta.get("version") and not title:
        raise ValueError(
            f"{path.name}: front matter needs a `version`, or a `title.zh` heading "
            f"for an entry that does not ride the main mod's version number"
        )

    channel = meta.get("channel", DEFAULT_CHANNEL)
    if channel not in CHANNEL_ORDER:
        raise ValueError(
            f"{path.name}: unknown `channel` {channel!r}; expected one of {sorted(CHANNEL_ORDER)}"
        )

    date = meta.get("date", "")
    if date and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValueError(f"{path.name}: `date` must be YYYY-MM-DD, got {date!r}")

    entry_type = meta.get("type", "release" if channel == DEFAULT_CHANNEL else "")
    if entry_type and entry_type not in KNOWN_TYPES:
        raise ValueError(f"{path.name}: unknown `type` {entry_type!r}; expected one of {sorted(KNOWN_TYPES)}")

    bodies = split_lang_bodies(text[fm_match.end():])
    if not bodies:
        raise ValueError(f"{path.name}: no body content found")
    if DEFAULT_LANG not in bodies:
        raise ValueError(f"{path.name}: missing a `<!-- lang: {DEFAULT_LANG} -->` block")

    # Entries that date their individual changes sort on the newest of those,
    # so adding a line is the whole edit — no front-matter date to keep in step.
    body_dates = BODY_DATE_RE.findall(bodies[DEFAULT_LANG])
    sort_date = date or (max(body_dates) if body_dates else "")
    # The oldest dated line is the day that package went up. Two submods touched
    # the same day tie on sort_date, and there the newer package is the newer
    # thing — so this breaks the tie rather than leaving it to the filename.
    launch_date = min(body_dates) if body_dates else ""

    return {
        "source": path.name,
        "version": meta.get("version", ""),
        "title": title,
        "url": meta.get("url", ""),
        "channel": channel,
        "date": date,
        "sort_date": sort_date,
        "launch_date": launch_date,
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
    # Newest first, on four keys: latest activity — a dateless entry is one not
    # dated yet, so it belongs above everything dated — then the package's own
    # launch day, then the version, then the filename. The last one is arbitrary
    # but stable; it only decides two packages launched *and* touched the same
    # day, and renaming a file is the lever if that order is ever wrong.
    releases.sort(
        key=lambda r: (
            r["sort_date"] or "9999-99-99",
            r["launch_date"],
            version_key(r["version"]),
            r["source"],
        ),
        reverse=True,
    )
    return releases


# --------------------------------------------------------------- rendering

EXTERNAL_LINK_RE = re.compile(r'<a href="(https?://[^"]+)"')
# Python-Markdown ends a list at any blank line inside an item, silently folding
# the following bullets into one paragraph. Catch that instead of shipping it.
SWALLOWED_BULLET_RE = re.compile(r"<p>[^<]*(?:^|\s)- \S", re.MULTILINE)
# `- 2026-08-30 ...` in a submod section: the leading date is a label, not prose.
# Only top-level items carry one, so nested sub-bullets are left alone.
LIST_DATE_RE = re.compile(r"(<li>(?:<p>)?)(\d{4}-\d{2}-\d{2})\s+")


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


def render_release(release: dict, lang: str, i18n: dict, is_latest: bool) -> str:
    """Render one entry; markdown errors are re-raised with the source filename."""
    strings = i18n[lang]
    body_lang = lang if lang in release["bodies"] else DEFAULT_LANG
    notice = ""
    if body_lang != lang:
        notice = f'          <p class="release__untranslated">{html.escape(strings["UNTRANSLATED"])}</p>\n'

    badges = []
    if release["type"]:
        type_label = strings["TYPE"].get(release["type"], release["type"])
        badges.append(
            f'<span class="type-badge type-badge--{release["type"]}">{html.escape(type_label)}</span>'
        )
    for tag in release["tags"]:
        label = strings["TAGS"].get(tag, tag)
        slug = re.sub(r"[^a-z0-9]+", "-", tag.lower()).strip("-")
        badges.append(f'<span class="tag-pill tag-pill--{slug}">{html.escape(label)}</span>')

    try:
        body_html = render_markdown(release["bodies"][body_lang])
    except ValueError as exc:
        raise ValueError(f"{release['source']} [{body_lang}]: {exc}") from exc

    classes = "release release--latest" if is_latest else "release"
    date_html = (
        f'<span class="release__date">{html.escape(release["date"])}</span>'
        if release["date"] else ""
    )
    # A submod has no place in the main mod's version sequence, so it is headed
    # by its name instead. Set as prose, not as a number: no tabular figures.
    if release["title"]:
        name = esc(release["title"], lang)
        if release["url"]:
            heading = (
                f'<a class="release__version release__version--named" '
                f'href="{release["url"]}" target="_blank" rel="noopener">'
                f'{name}<span aria-hidden="true">↗</span></a>'
            )
        else:
            heading = f'<span class="release__version release__version--named">{name}</span>'
    else:
        heading = f'<span class="release__version">v{html.escape(release["version"])}</span>'
    version_attr = f' data-version="{html.escape(release["version"])}"' if release["version"] else ""

    return (
        f'      <article class="{classes}"{version_attr} '
        f'data-tags="{html.escape(" ".join(release["tags"]))}">\n'
        f'        <div class="release__head">\n'
        f'          {heading}\n'
        f'          {date_html}\n'
        f'          <span class="release__badges">{"".join(badges)}</span>\n'
        f'        </div>\n'
        f'{notice}'
        f'        <div class="release-body" lang="{html.escape(i18n[body_lang]["LANG_HTML"])}">\n'
        f'{body_html}\n'
        f'        </div>\n'
        f'      </article>\n'
    )


def group_by_channel(releases: list[dict]) -> dict[str, list[dict]]:
    return {ch: [r for r in releases if r["channel"] == ch] for ch in CHANNEL_ORDER}


def render_log_timeline(groups: dict[str, list[dict]], lang: str, i18n: dict, tabbed: bool) -> str:
    """The entries themselves. Each channel highlights its own newest entry —
    `--latest` marks the top of the list you are reading, not of the file set."""
    strings = i18n[lang]
    if not any(groups.values()):
        return f'      <p class="log-empty">{html.escape(strings["EMPTY"])}</p>\n'

    out = []
    for channel in CHANNEL_ORDER:
        group = groups[channel]
        if not group:
            continue
        # Only the main channel has a "latest": there an entry is one release.
        # A submod entry is that package's whole running log, so none of them is
        # newer than another — and their order is a date tie broken by filename.
        entries = "".join(
            render_release(r, lang, i18n, is_latest=(i == 0 and channel == DEFAULT_CHANNEL))
            for i, r in enumerate(group)
        )
        if not tabbed:
            return entries
        out.append(
            f'      <div class="log-panel log-panel--{channel}">\n{entries}      </div>\n'
        )
    return "".join(out)


def render_log_views(groups: dict[str, list[dict]], strings: dict) -> tuple[str, str]:
    """The channel switch: (radio inputs, label strip).

    CSS-only on purpose — the one script this site ships is the first-visit
    language check, and a tab strip is not worth a second. The inputs are a real
    radio group, so arrow keys and focus work without faking a JS tablist; they
    have to sit as direct children of .log-column for `:checked ~` to reach both
    the labels in the hero and the panels in the timeline.

    Returns two empty strings when a channel has nothing in it: one live tab
    beside one dead tab is worse than the plain list this page started as.
    """
    if not all(groups[ch] for ch in CHANNEL_ORDER):
        return "", ""

    inputs, tabs = [], []
    for i, channel in enumerate(CHANNEL_ORDER):
        checked = " checked" if i == 0 else ""
        inputs.append(
            f'        <input class="sr-only log-views__radio" type="radio" '
            f'name="log-view" id="log-view-{channel}"{checked}>\n'
        )
        tabs.append(
            f'              <label class="log-views__tab" for="log-view-{channel}">'
            f'{html.escape(strings["LOG_VIEWS"][channel])}'
            f'<span class="log-views__count">{len(groups[channel])}</span></label>\n'
        )
    strip = (
        f'            <div class="log-views" role="group" '
        f'aria-label="{html.escape(strings["LOG_VIEWS_LABEL"])}">\n'
        f'{"".join(tabs)}'
        f'              <span class="log-views__ink" aria-hidden="true"></span>\n'
        f'            </div>\n'
    )
    return "".join(inputs), strip


# ---------------------------------------------------------- landing page

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


def render_hero(home: dict, lang: str, strings: dict, base: str, latest: str) -> str:
    h = home["hero"]
    note = pick(h["note"], lang)
    note_html = f'\n        <p class="hero__note">{html.escape(note)}</p>' if note else ""
    cta = "".join(
        f'\n          <a class="cta{"" if i else " cta--lead"}" href="{url}" target="_blank" rel="noopener">'
        f'{html.escape(strings[key])}<span aria-hidden="true">↗</span></a>'
        for i, (key, url) in enumerate(workshop_ctas())
    )
    return f"""<section class="hero">
  <picture class="hero__art">
    <source type="image/webp" srcset="{base}/assets/img/harbour-1100.webp 1100w, {base}/assets/img/harbour-1800.webp 1800w" sizes="100vw">
    <img src="{base}/assets/img/harbour-1800.jpg" srcset="{base}/assets/img/harbour-1100.jpg 1100w, {base}/assets/img/harbour-1800.jpg 1800w" sizes="100vw" alt="{esc(h['art_alt'], lang)}" width="1920" height="1080" fetchpriority="high" decoding="async">
  </picture>
  <div class="hero__inner">
    <img class="hero__crest" src="{base}/assets/img/mon.webp" alt="{esc(h['crest_alt'], lang)}" width="80" height="80" decoding="async">
    <p class="hero__eyebrow">{esc(h['eyebrow'], lang)}</p>
    <h1 class="hero__title">
      <span class="hero__wordmark">{html.escape(h['wordmark'])}</span>
      <span class="hero__name">{esc(h['name'], lang)}</span>
    </h1>
    <p class="hero__premise">{esc(h['premise'], lang)}</p>{note_html}
    <div class="hero__actions">
      <p class="hero__actions-label">{html.escape(strings['HERO_CTA_LABEL'])}</p>
      <div class="hero__ctas">{cta}
      </div>
    </div>
    {latest}
  </div>
</section>
"""


def workshop_ctas() -> list[tuple[str, str]]:
    """Every workshop listing: the mod itself, its English translation, then the
    optional submods — same order on both language pages, since the English
    listing is a translation of the first one rather than a second main mod.
    The hero CTAs and the footer row are both generated from this list, so a new
    listing only has to be added here — and to home.json's `submods` if it is a
    compatibility patch, which is the one place the copy actually differs."""
    return [
        ("WS_MAIN_ZH", "https://steamcommunity.com/workshop/filedetails/?id=3790908242"),
        ("WS_MAIN_EN", "https://steamcommunity.com/workshop/filedetails/?id=3790908523"),
        ("WS_AI", "https://steamcommunity.com/workshop/filedetails/?id=3790907897"),
        ("WS_NRS", "https://steamcommunity.com/sharedfiles/filedetails/?id=3792001152"),
        ("WS_CATHAY", "https://steamcommunity.com/sharedfiles/filedetails/?id=3792252212"),
        ("WS_YINYIN", "https://steamcommunity.com/sharedfiles/filedetails/?id=3792695478"),
    ]


def render_overview(home: dict, lang: str) -> str:
    """Mostly one-line points. An item carrying a `name` is a submod instead:
    it gets its workshop link as the heading and its own points underneath,
    because a patch needs to say what it is for, not just that it exists."""
    o = home["overview"]
    rows = []
    for i in o["items"]:
        if not i.get("name"):
            rows.append(f'      <li>{inline_md(i, lang)}</li>\n')
            continue
        points = "".join(
            f'          <li>{inline_md(pt, lang)}</li>\n' for pt in i.get("points", [])
        )
        # A patch with nothing to enumerate gets the note alone, not an empty list.
        points_html = (
            f'        <ul class="overview__mod-points">\n{points}        </ul>\n'
            if points else ""
        )
        rows.append(
            f'      <li class="overview__mod">\n'
            f'        <a class="overview__mod-name" href="{i["url"]}" target="_blank" rel="noopener">'
            f'{esc(i["name"], lang)}<span aria-hidden="true">↗</span></a>\n'
            f'        <p class="overview__mod-note">{inline_md(i["note"], lang)}</p>\n'
            f'{points_html}'
            f'      </li>\n'
        )
    return (section_open("overview", lang, o["title"]) +
            f'    <ul class="overview__list">\n{"".join(rows)}    </ul>\n' + section_close())


def lord_card(person: dict, lang: str, base: str, captioned: bool) -> str:
    """One recruitment card. A lone card sits directly above its own <h3>, so
    captioning it would print the name twice — it takes the name as alt text
    instead. In the trio the captions are the name line, so alt is empty and
    the caption does the naming."""
    name = esc(person["name"], lang)
    caption = f'\n            <span class="cast__name">{name}</span>' if captioned else ""
    return (
        f'          <li class="cast">\n'
        f'            <img class="cast__art" src="{base}/assets/img/char-{person["slug"]}.webp" '
        f'alt="{"" if captioned else name}" width="240" height="520" loading="lazy" decoding="async">'
        f'{caption}\n'
        f'          </li>\n'
    )


def render_lords(home: dict, lang: str, base: str) -> str:
    """A roster read as three bands, with the cards alternating sides so the
    section has a rhythm instead of one long left rail: the admiral, then the
    three companions, then the two types you recruit as many of as you can pay
    for — those two share a band because they are the same kind of entry and
    two more full-height rows would have made the section twice as tall.

    A band with one card names its character in the heading; a band with several
    labels each card instead, because a shared heading cannot say which face is
    which. `rank` colours the eyebrow — one-of-a-kind versus recruitable is the
    section's only real split, and every eyebrow being jade hid it."""
    d = home["lords"]
    bands = ""
    for row in d["rows"]:
        cards, entries = "", ""
        for i in row["items"]:
            people = i.get("people")
            heading = ("" if people else
                       f'          <h3 class="lord__name">{esc(i["name"], lang)}</h3>\n')
            if people:
                cards += "".join(lord_card(p, lang, base, captioned=True) for p in people)
            else:
                cards += lord_card(i, lang, base, captioned=False)
            entries += (
                f'        <div class="lord__entry lord--{i["rank"]}">\n'
                f'          <p class="lord__kind">{esc(i["kind"], lang)}</p>\n'
                f'{heading}'
                f'          <p class="lord__body">{inline_md(i["body"], lang)}</p>\n'
                f'        </div>\n'
            )
        bands += (
            f'      <li class="lord lord--cards-{row["side"]}">\n'
            f'        <ul class="lord__cast">\n{cards}        </ul>\n'
            f'        <div class="lord__entries">\n{entries}        </div>\n'
            f'      </li>\n'
        )
    return (section_open("lords", lang, d["title"]) +
            f'    <ul class="lords">\n{bands}    </ul>\n' + section_close())


def render_companions(home: dict, lang: str, base: str) -> str:
    c = home["companions"]
    tiers = "".join(
        f'<li class="tier">{esc(t, lang)}</li>' for t in c["tiers"]
    )
    # Chapters are a real sequence, so they get real numerals: the campaign's
    # own 壹/贰/叁/肆 in Chinese, roman numerals in English.
    numerals = c["numerals"].get(lang) or c["numerals"][DEFAULT_LANG]
    cards = ""
    for item in c["items"]:
        chapters = "".join(
            f'          <li class="chapter"><span class="chapter__no" aria-hidden="true">{numerals[n]}</span>'
            f'<span class="chapter__name">{esc(ch, lang)}</span></li>\n'
            for n, ch in enumerate(item["chapters"])
        )
        cards += f"""      <li class="companion">
        <img class="companion__art" src="{base}/assets/img/companion-{item['slug']}.jpg" alt="{esc(item['name'], lang)}" width="800" height="450" loading="lazy" decoding="async">
        <h3 class="companion__name">{esc(item['name'], lang)}</h3>
        <p class="companion__label">{esc(c['chapters_label'], lang)}</p>
        <ol class="chapters">
{chapters}        </ol>
      </li>
"""
    notes = "".join(f'        <li>{inline_md(n, lang)}</li>\n' for n in c["notes"])
    return (section_open("companions", lang, c["title"], lede=c["lede"]) +
            f"""    <div class="bond">
      <p class="bond__label">{esc(c['tiers_label'], lang)}</p>
      <ol class="bond__tiers">{tiers}</ol>
      <ul class="bond__notes">
{notes}      </ul>
    </div>
    <ul class="companions">
{cards}    </ul>
""" + section_close())


def render_units(home: dict, lang: str, base: str) -> str:
    u = home["units"]
    groups = ""
    for group in u["groups"]:
        cards = "".join(
            f'          <li class="unit">\n'
            f'            <img class="unit__art" src="{base}/assets/img/unit-{i["slug"]}.webp" alt="" '
            f'width="240" height="520" loading="lazy" decoding="async">\n'
            f'            <span class="unit__name">{esc(i["name"], lang)}</span>\n'
            f'          </li>\n'
            for i in group["items"]
        )
        groups += (
            f'      <div class="unit-group">\n'
            f'        <h3 class="unit-group__name">{esc(group["name"], lang)}</h3>\n'
            f'        <ul class="units">\n{cards}        </ul>\n'
            f'      </div>\n'
        )
    return (section_open("units", lang, u["title"]) + groups + section_close())


def render_buildings(home: dict, lang: str) -> str:
    b = home["buildings"]
    rows = "".join(
        f'      <li class="build">\n'
        f'        <h3 class="build__name">{esc(i["name"], lang)}</h3>\n'
        f'        <p class="build__body">{inline_md(i["body"], lang)}</p>\n'
        f'      </li>\n'
        for i in b["items"]
    )
    return (section_open("buildings", lang, b["title"]) +
            f'    <ul class="builds">\n{rows}    </ul>\n' + section_close())


def goals_list(goals, lang: str) -> str:
    return "".join(f'        <li>{inline_md(g, lang)}</li>\n' for g in goals)


def render_victory(home: dict, lang: str) -> str:
    """The signature block: one short victory, then two long ones.

    The two long victories are concurrent, not alternatives — a reader can
    complete both. Keep the copy saying so; the two-armed layout is only a
    split of one objective into two, never a choice between them.
    """
    v = home["victory"]
    s = v["short"]
    routes = ""
    for route in v["routes"]:
        routes += f"""      <article class="route route--{route['tag'].lower()}">
        <p class="route__kind"><span class="route__tag" aria-hidden="true">{html.escape(route['tag'])}</span>{esc(route['kind'], lang)}</p>
        <h3 class="route__name">{esc(route['name'], lang)}</h3>
        <blockquote class="route__quote"><p>{esc(route['quote'], lang)}</p></blockquote>
        <ul class="goals">
{goals_list(route['goals'], lang)}        </ul>
      </article>
"""
    return f"""<section class="band band--victory" id="victory">
  <div class="band__inner">
    <h2 class="band__title">{esc(v['title'], lang)}</h2>
    <div class="fork">
      <article class="trunk">
        <p class="trunk__kind">{esc(s['kind'], lang)}</p>
        <h3 class="trunk__name">{esc(s['name'], lang)}</h3>
        <blockquote class="trunk__quote"><p>{esc(s['quote'], lang)}</p></blockquote>
        <ul class="goals">
{goals_list(s['goals'], lang)}        </ul>
      </article>
      <div class="fork__split" aria-hidden="true"></div>
      <div class="routes">
{routes}      </div>
    </div>
  </div>
</section>
"""


def render_relocations(home: dict, lang: str) -> str:
    d = home["relocations"]
    rows = "".join(
        f'          <tr><td>{esc(r["lord"], lang)}</td><td>{esc(r["dest"], lang)}</td></tr>\n'
        for r in d["rows"]
    )
    return (section_open("relocations", lang, d["title"], lede=d["lede"]) +
            f"""    <div class="table-scroll">
      <table class="reloc">
        <thead><tr><th scope="col">{esc(d['head']['lord'], lang)}</th><th scope="col">{esc(d['head']['dest'], lang)}</th></tr></thead>
        <tbody>
{rows}        </tbody>
      </table>
    </div>
""" + section_close())


def render_ai(home: dict, lang: str) -> str:
    a = home["ai"]
    items = "".join(f'      <li>{inline_md(i, lang)}</li>\n' for i in a["items"])
    link = a["more_link"]
    more = (f'    <p class="band__tail">{esc(a["more"], lang)} '
            f'<a href="{link["url"]}" target="_blank" rel="noopener">{esc(link["label"], lang)}'
            f'<span aria-hidden="true">↗</span></a>{esc(a["more_tail"], lang)}</p>\n')
    return (section_open("ai", lang, a["title"], lede=a["lede"]) +
            f'    <ul class="prose-list">\n{items}    </ul>\n' + more + section_close())


def render_compat(home: dict, lang: str) -> str:
    c = home["compat"]
    items = "".join(f'      <li>{inline_md(i, lang)}</li>\n' for i in c["items"])
    return (section_open("compat", lang, c["title"]) +
            f'    <ul class="prose-list">\n{items}    </ul>\n' + section_close())


def render_credits(home: dict, lang: str) -> str:
    c = home["credits"]
    items = "".join(
        f'      <li><a href="{i["url"]}" target="_blank" rel="noopener">{esc(i["label"], lang)}'
        f'<span aria-hidden="true">↗</span></a></li>\n'
        for i in c["items"]
    )
    return (section_open("credits", lang, c["title"], lede=c["lede"]) +
            f'    <ul class="credits">\n{items}    </ul>\n'
            f'    <p class="band__tail">{esc(c["tail"], lang)}</p>\n' + section_close())


# ------------------------------------------------------------------- FAQ page
#
# The page is a ledger rather than a list: each category hangs off one vertical
# rule, with its name held in the left rail while its questions scroll past.
# The rail is what tells a reader where they are, so it is set at display size
# — the category is the structure here, not a caption over it.

def faq_count(strings: dict, n: int) -> str:
    return strings["FAQ_COUNT"]["one" if n == 1 else "other"].format(n=n)


def render_faq_stamp(strings: dict, version: str) -> str:
    """Which release the answers are written against. The FAQ is versioned
    content, and saying so as a stamp beats saying so in a sentence."""
    if not version:
        return ""
    label = strings["FAQ_CURRENT"].format(version=version)
    return f'<p class="faq-stamp">{html.escape(label)}</p>'


def render_faq_bands(faq: dict, lang: str, strings: dict) -> str:
    """One band per category: sticky rail, then the questions on the rule.

    Questions carry an id so a single answer can be linked to from a Workshop
    comment; the rule lights up jade beside whichever one was linked to.
    """
    blocks = ""
    for section in faq["sections"]:
        items = ""
        for item in section["items"]:
            status = item.get("status")
            flag = ""
            if status:
                label = strings["FAQ_STATUS"][status].format(version=item["version"])
                flag = (f'              <span class="faq-flag faq-flag--{status}">'
                        f'{html.escape(label)}</span>\n')
            body = "".join(
                f'              <p>{inline_md(par, lang)}</p>\n' for par in item["answer"]
            )
            for link in item.get("links", []):
                body += (f'              <p class="faq-link"><a href="{link["url"]}" '
                         f'target="_blank" rel="noopener">{esc(link["label"], lang)}'
                         f'<span aria-hidden="true">↗</span></a></p>\n')
            items += (
                f'          <li class="faq-item" id="q-{html.escape(item["slug"])}">\n'
                f'            <div class="faq-item__head">\n'
                f'              <h3 class="faq-q">{inline_md(item["question"], lang)}</h3>\n'
                f'{flag}'
                f'            </div>\n'
                f'            <div class="faq-a">\n{body}            </div>\n'
                f'          </li>\n'
            )
        blocks += (
            f'      <section class="faq-band" id="{html.escape(section["slug"])}">\n'
            f'        <div class="faq-band__rail">\n'
            f'          <h2 class="faq-band__title">{esc(section["title"], lang)}</h2>\n'
            f'          <p class="faq-band__count">'
            f'{html.escape(faq_count(strings, len(section["items"])))}</p>\n'
            f'        </div>\n'
            f'        <ul class="faq-list">\n{items}        </ul>\n'
            f'      </section>\n'
        )
    return blocks


def render_faq_tail(faq: dict, lang: str, strings: dict, log_href: str) -> str:
    """Closing pointer to the changelog — the FAQ says what is true now, the
    changelog says when it changed, and only one of them should list fixes."""
    return (f'<p class="faq-tail">{esc(faq["tail"], lang)} '
            f'<a href="{log_href}">{html.escape(strings["FAQ_TAIL_LINK"])} →</a></p>')


# --------------------------------------------------------------- page shell

def build_page(
    page: str,
    lang: str,
    releases: list[dict],
    home: dict,
    faq: dict,
    i18n: dict,
    partials: dict[str, str],
    template: str,
    base: str,
    origin: str,
    build_time: str,
    cache_bust: str,
) -> str:
    strings = i18n[lang]

    groups = group_by_channel(releases)
    view_inputs, view_strip = render_log_views(groups, strings)
    entries = render_log_timeline(groups, lang, i18n, tabbed=bool(view_strip))

    # The stamp quotes the main mod's current *released* version, on this page
    # and on the other two. Two entries can sit above that one and must not be
    # mistaken for it: a submod, which sorts in on its own release date, and an
    # entry with no date, which by this repo's convention is a version that has
    # not shipped to the Workshop yet. Neither is a number to quote at players.
    newest = next((r for r in groups["main"] if r["version"] and r["date"]), None)
    if newest:
        latest_stamp = f'<strong>v{html.escape(newest["version"])}</strong>'
        if newest["date"]:
            latest_stamp += f' · <strong>{html.escape(newest["date"])}</strong>'
    else:
        latest_stamp = "<strong>—</strong>"

    log_href = page_href(base, lang, "changelog")
    hero_latest = (
        f'<a class="hero__latest" href="{log_href}">'
        f'<span class="hero__latest-label">{html.escape(strings["LATEST"])}</span>'
        f'{latest_stamp}<span class="hero__latest-go">{html.escape(strings["NAV_LOG"])} →</span></a>'
    ) if releases else ""

    values = {
        "SITE_BASE_PATH": base,
        "BUILD_TIME": build_time,
        "FOOTER_WS_LINKS": "".join(
            f'      <a href="{url}" target="_blank" rel="noopener">'
            f'{html.escape(strings[key])} ↗</a>\n'
            for key, url in workshop_ctas()
        ).rstrip("\n"),
        "RELEASES": entries,
        "LOG_VIEW_INPUTS": view_inputs,
        "LOG_VIEWS": view_strip,
        "LATEST_STAMP": latest_stamp,
        "SITE_URL": f"{origin}{base}",
        "HREF_SELF": page_href(base, lang, page),
        "HREF_ZH": page_href(base, "zh", page),
        "HREF_EN": page_href(base, "en", page),
        "HREF_HOME": page_href(base, lang, "home"),
        "HREF_LOG": log_href,
        "HREF_FAQ": page_href(base, lang, "faq"),
        "ABS_HREF_SELF": origin + page_href(base, lang, page),
        "ABS_HREF_ZH": origin + page_href(base, "zh", page),
        "ABS_HREF_EN": origin + page_href(base, "en", page),
        "PAGE_LANG": lang,
        "PAGE_NAME": page,
        "CLASS_ZH_ACTIVE": " lang-switch__item--active" if lang == "zh" else "",
        "CLASS_EN_ACTIVE": " lang-switch__item--active" if lang == "en" else "",
        "CLASS_LOG_ACTIVE": " site-nav__link--current" if page == "changelog" else "",
        "CLASS_FAQ_ACTIVE": " site-nav__link--current" if page == "faq" else "",
    }

    if page == "home":
        values.update({
            "HOME_HERO": render_hero(home, lang, strings, base, hero_latest),
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
        })

    if page == "faq":
        values.update({
            "FAQ_STAMP": render_faq_stamp(strings, newest["version"] if newest else ""),
            "FAQ_BANDS": render_faq_bands(faq, lang, strings),
            "FAQ_TAIL": render_faq_tail(faq, lang, strings, log_href),
        })

    page_meta = strings["PAGES"][page]
    values["T_PAGE_TITLE"] = page_meta["TITLE"]
    values["T_META_DESCRIPTION"] = page_meta["DESCRIPTION"]

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
        raise ValueError(f"[{lang}/{page}] unresolved placeholders: {', '.join(leftovers)}")

    if cache_bust:
        text = ASSET_RE.sub(lambda m: f'{m.group(1)}?v={cache_bust}"', text)
    return text


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


# -------------------------------------------------------------------- main

def main() -> None:
    i18n = json.loads(I18N_FILE.read_text(encoding="utf-8"))
    missing = [lang for lang in LANGS if lang not in i18n]
    if missing:
        raise SystemExit(f"content/i18n.json is missing language(s): {', '.join(missing)}")
    for lang in LANGS:
        gaps = [p for p in PAGES if p not in i18n[lang].get("PAGES", {})]
        if gaps:
            raise SystemExit(f"content/i18n.json [{lang}] has no PAGES entry for: {', '.join(gaps)}")

    home = json.loads(HOME_FILE.read_text(encoding="utf-8"))
    faq = json.loads(FAQ_FILE.read_text(encoding="utf-8"))
    partials = load_partials()
    templates = {}
    for page, (filename, _) in PAGES.items():
        path = TEMPLATES_DIR / filename
        if not path.exists():
            raise SystemExit(f"template not found at {path}")
        templates[page] = path.read_text(encoding="utf-8")

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


if __name__ == "__main__":
    main()
