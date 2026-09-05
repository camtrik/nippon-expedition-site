"""Night: the poster voice. The one band above the fold."""
from __future__ import annotations

import html

from ...text import esc, pick
from ...workshop import workshop_ctas


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
