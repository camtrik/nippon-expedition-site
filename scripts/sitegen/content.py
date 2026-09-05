"""Loading content/: the interface strings and the two prose files."""
from __future__ import annotations

import json

from .config import FAQ_FILE, HOME_FILE, I18N_FILE, LANGS, PAGES


def load_i18n() -> dict:
    i18n = json.loads(I18N_FILE.read_text(encoding="utf-8"))
    missing = [lang for lang in LANGS if lang not in i18n]
    if missing:
        raise SystemExit(f"content/i18n.json is missing language(s): {', '.join(missing)}")
    for lang in LANGS:
        gaps = [p for p in PAGES if p not in i18n[lang].get("PAGES", {})]
        if gaps:
            raise SystemExit(f"content/i18n.json [{lang}] has no PAGES entry for: {', '.join(gaps)}")
    return i18n


def load_home() -> dict:
    return json.loads(HOME_FILE.read_text(encoding="utf-8"))


def load_faq() -> dict:
    return json.loads(FAQ_FILE.read_text(encoding="utf-8"))
