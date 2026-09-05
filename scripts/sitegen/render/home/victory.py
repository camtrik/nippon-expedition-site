"""Night again: the campaign's own fiction, and the fork it turns on."""
from __future__ import annotations

import html

from ...text import esc, inline_md
from ..band import section_close, section_open


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
    return section_open("victory", lang, v["title"]) + f"""    <div class="fork">
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
""" + section_close()
