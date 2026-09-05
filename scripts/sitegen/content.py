"""Loading content/: the interface strings and the two prose files."""
from __future__ import annotations

import json

from .config import FAQ_FILE, HOME_DIR, I18N_FILE, LANGS, LEGACY_HOME_FILE, PAGES


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
    """The landing page copy: one file per band, each wrapping its own key so a
    file says what it is. Merge order does not matter — every renderer asks for
    a band by name, and the order blocks appear in belongs to the template."""
    if LEGACY_HOME_FILE.exists():
        raise SystemExit(
            f"{LEGACY_HOME_FILE} still exists, but the landing page copy now lives in "
            f"{HOME_DIR}/ — edits to the old file would be silently ignored"
        )
    home: dict = {}
    for path in sorted(HOME_DIR.glob("*.json")):
        for key, value in json.loads(path.read_text(encoding="utf-8")).items():
            if key in home:
                raise SystemExit(f"{path.name}: section {key!r} is already defined elsewhere")
            home[key] = value
    if not home:
        raise SystemExit(f"no landing page content found in {HOME_DIR}/")
    return home


def load_faq() -> dict:
    return json.loads(FAQ_FILE.read_text(encoding="utf-8"))
