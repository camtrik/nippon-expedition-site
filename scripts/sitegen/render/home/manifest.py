"""Day: the manifest voice. What is actually in the pack — the roster, the
units, the buildings."""
from __future__ import annotations

from ...config import DEFAULT_LANG
from ...text import esc, inline_md
from ..band import section_close, section_open


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
