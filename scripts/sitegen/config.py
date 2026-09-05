"""Paths and the knobs every other module reads.

A leaf: this imports nothing from the rest of the package, so a constant can be
read without pulling in the renderers.
"""
from __future__ import annotations

from pathlib import Path

# scripts/sitegen/config.py -> scripts/sitegen -> scripts -> repo root.
ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"
DIST = SITE / "_dist"
PARTIALS_DIR = SITE / "partials"
ASSETS_DIR = SITE / "assets"
TEMPLATES_DIR = SITE / "_templates"
STYLES_DIR = SITE / "styles"
I18N_FILE = ROOT / "content" / "i18n.json"
HOME_DIR = ROOT / "content" / "home"
LEGACY_HOME_FILE = ROOT / "content" / "home.json"
FAQ_FILE = ROOT / "content" / "faq.json"
RELEASES_DIR = ROOT / "content" / "releases"

DEFAULT_LANG = "zh"          # served at the site root
FALLBACK_ORIGIN = "https://camtrik.github.io"
LANGS = ["zh", "en"]         # order also drives the hreflang links

# name -> (template, url path under the language root)
PAGES = {
    "home": ("home.html", ""),
    "changelog": ("log.html", "changelog"),
    "faq": ("faq.html", "faq"),
}

KNOWN_TYPES = {"release", "content", "balance", "hotfix"}
# Which timeline an entry belongs to. The main mod carries the version number
# the whole site quotes; a submod ships on its own clock and must not perturb
# that number, so the two are counted and displayed apart.
CHANNEL_ORDER = ("main", "submod")
DEFAULT_CHANNEL = "main"

# One delivered stylesheet per entry, built from site/styles/<name>/*.css.
# fonts.css is not here: subset_fonts.py generates it into site/assets/css/
# and it rides along with the rest of the assets.
CSS_BUNDLES = ("base", "home", "log", "faq")

FONT_COVERAGE = ASSETS_DIR / "fonts" / "coverage.txt"
