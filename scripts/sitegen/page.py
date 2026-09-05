"""One rendered page: collect every placeholder, then fill the template."""
from __future__ import annotations

import html

from .releases import group_by_channel, latest_released
from .render.faq import render_faq
from .render.home import render_home
from .render.log import render_log
from .templates import apply_includes, cache_bust, substitute
from .urls import page_href
from .workshop import workshop_ctas


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
    cache_stamp: str,
) -> str:
    strings = i18n[lang]

    groups = group_by_channel(releases)
    newest = latest_released(groups)

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
    values.update(render_log(groups, lang, i18n, strings))

    if page == "home":
        values.update(render_home(home, lang, strings, base, hero_latest))

    if page == "faq":
        values.update(
            render_faq(faq, lang, strings, log_href, newest["version"] if newest else "")
        )

    page_meta = strings["PAGES"][page]
    values["T_PAGE_TITLE"] = page_meta["TITLE"]
    values["T_META_DESCRIPTION"] = page_meta["DESCRIPTION"]

    # Most strings land as {{T_KEY}}; these three are used raw in attributes.
    verbatim = {"LANG_HTML", "OG_LOCALE", "WORKSHOP_URL"}
    for key, value in strings.items():
        if isinstance(value, str):
            values[key if key in verbatim else f"T_{key}"] = value

    text = apply_includes(template, partials)
    text = substitute(text, values, f"{lang}/{page}")
    return cache_bust(text, cache_stamp)
