#!/usr/bin/env python3
"""
build.py — Render the bilingual site into site/_dist/.

Inputs
    content/i18n.json          page chrome strings, keyed by language
    content/home.json          landing page content, both languages per field
    content/faq.json           FAQ page content, both languages per field
    content/releases/*.md      one file per release, both languages inside
    site/_templates/*.html     page shells
    site/partials/*.html       <!-- include: NAME.html --> fragments
    site/assets/**             copied through unchanged

Output
    site/_dist/index.html                Chinese landing page (site root)
    site/_dist/en/index.html             English landing page
    site/_dist/changelog/index.html      Chinese changelog
    site/_dist/en/changelog/index.html   English changelog
    site/_dist/faq/index.html            Chinese FAQ
    site/_dist/en/faq/index.html         English FAQ
    site/_dist/assets/**

Usage
    python3 scripts/build.py
    python3 -m http.server 8000 --directory site/_dist

Set SITE_BASE_PATH when the site is served from a subpath (GitHub Pages
project sites) and SITE_ORIGIN for the scheme+host used in canonical /
og:image URLs. The Pages workflow passes both automatically.

The implementation lives in scripts/sitegen/ — start at cli.main().
"""
from __future__ import annotations

import sys
from pathlib import Path

# scripts/ is already sys.path[0] when this file is run directly; saying so
# explicitly keeps the import working under `python3 -P` / PYTHONSAFEPATH=1.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sitegen.cli import main

if __name__ == "__main__":
    main()
