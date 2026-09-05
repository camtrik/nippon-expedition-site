"""Stylesheets: one directory of parts per delivered file.

The sources sit outside site/assets/ on purpose — that tree is copied into the
output wholesale, and nobody should be served the parts as well as the bundle.
Concatenation is the whole build step: no minifier, no preprocessor, and no
separator comment, so the delivered file is byte for byte what the parts say.

Parts carry a numeric prefix, so the directory listing is the cascade order and
adding one is a new file rather than a code change.
"""
from __future__ import annotations

from pathlib import Path

from .config import CSS_BUNDLES, STYLES_DIR


def bundle_css(dist: Path) -> None:
    out_dir = dist / "assets" / "css"
    out_dir.mkdir(parents=True, exist_ok=True)
    for bundle in CSS_BUNDLES:
        src = STYLES_DIR / bundle
        parts = sorted(src.glob("*.css"))
        if not parts:
            # An empty bundle serves a page with no styles and no error — a
            # failure that only shows up in a screenshot. Stop here instead.
            raise SystemExit(f"no stylesheet parts in {src}; expected the sources of {bundle}.css")
        (out_dir / f"{bundle}.css").write_text(
            "".join(p.read_text(encoding="utf-8") for p in parts), encoding="utf-8"
        )
