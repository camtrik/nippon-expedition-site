"""The FAQ page.

The page is a ledger rather than a list: each category hangs off one vertical
rule, with its name held in the left rail while its questions scroll past.
The rail is what tells a reader where they are, so it is set at display size
— the category is the structure here, not a caption over it.
"""
from __future__ import annotations

import html

from ..text import esc, inline_md


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


def render_faq(faq: dict, lang: str, strings: dict, log_href: str, version: str) -> dict[str, str]:
    """Every {{FAQ_*}} block the FAQ template asks for."""
    return {
        "FAQ_STAMP": render_faq_stamp(strings, version),
        "FAQ_BANDS": render_faq_bands(faq, lang, strings),
        "FAQ_TAIL": render_faq_tail(faq, lang, strings, log_href),
    }
