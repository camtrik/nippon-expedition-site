"""One release entry per file: parse the front matter, split the two language
bodies, and put the whole set in the order the changelog reads in."""
from __future__ import annotations

import re
from pathlib import Path

from .config import (
    CHANNEL_ORDER,
    DEFAULT_CHANNEL,
    DEFAULT_LANG,
    KNOWN_TYPES,
    RELEASES_DIR,
)

FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
LANG_MARKER_RE = re.compile(r"^[ \t]*<!--\s*lang:\s*([a-zA-Z-]+)\s*-->[ \t]*$", re.MULTILINE)

# A submod has no version number, so the date rides on each change instead of on
# the entry: one section per submod, newest line first, mirroring version.md.
BODY_DATE_RE = re.compile(r"^\s*-\s+(\d{4}-\d{2}-\d{2})\b", re.MULTILINE)


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


def group_by_channel(releases: list[dict]) -> dict[str, list[dict]]:
    return {ch: [r for r in releases if r["channel"] == ch] for ch in CHANNEL_ORDER}


def latest_released(groups: dict[str, list[dict]]) -> dict | None:
    """The version number every "latest" stamp on the site quotes."""
    # The stamp quotes the main mod's current *released* version, on this page
    # and on the other two. Two entries can sit above that one and must not be
    # mistaken for it: a submod, which sorts in on its own release date, and an
    # entry with no date, which by this repo's convention is a version that has
    # not shipped to the Workshop yet. Neither is a number to quote at players.
    return next((r for r in groups["main"] if r["version"] and r["date"]), None)
