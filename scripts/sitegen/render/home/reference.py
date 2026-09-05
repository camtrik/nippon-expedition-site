"""Day: reference material. Tables, caveats, thanks."""
from __future__ import annotations

from ...text import esc, inline_md
from ..band import section_close, section_open


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
