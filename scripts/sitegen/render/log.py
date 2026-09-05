"""The changelog page: one article per entry, split across two channels."""
from __future__ import annotations

import html
import re

from ..config import CHANNEL_ORDER, DEFAULT_CHANNEL, DEFAULT_LANG
from ..text import esc, render_markdown


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


def render_log(groups: dict[str, list[dict]], lang: str, i18n: dict, strings: dict) -> dict[str, str]:
    """Every {{...}} block the changelog template asks for."""
    view_inputs, view_strip = render_log_views(groups, strings)
    return {
        "LOG_VIEW_INPUTS": view_inputs,
        "LOG_VIEWS": view_strip,
        "RELEASES": render_log_timeline(groups, lang, i18n, tabbed=bool(view_strip)),
    }
