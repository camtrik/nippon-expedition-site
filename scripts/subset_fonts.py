#!/usr/bin/env python3
"""
subset_fonts.py — Cut LXGW WenKai GB down to the characters this site uses.

Why this exists
    The full typeface is 25 MB per weight, and the public CDN builds are
    ~2.9 MB over the wire for a page this size (LXGW's chunks are split by
    codepoint range, so ~500 scattered characters still pull in ~29 of them).
    Subsetting to exactly the characters that appear in content/ and the
    templates lands at ~230 KB for both weights combined.

Why the GB cut, and why Medium is declared as 700
    LXGW WenKai's default build descends from Klee One and keeps Japanese
    glyph forms for characters Chinese and Japanese share (者 骨 真 直 海 每).
    The GB build normalises those to mainland standard forms. Its price is
    that its heaviest face is Medium — there is no Bold — so the @font-face
    below maps Medium onto font-weight 700. Regular-to-Medium is a two-step
    jump and reads clearly as bold; the old PingFang stack could only manage
    Medium-to-Semibold, which is why emphasis was invisible.

Run this whenever a release entry introduces characters the current subset
does not cover. scripts/build.py fails loudly and names this command when
that happens, so you do not have to remember on your own.

    pip install fonttools brotli
    python3 scripts/subset_fonts.py

Outputs (all committed):
    site/assets/fonts/lxgw-wenkai-gb-{regular,medium}.<hash>.woff2
    site/assets/css/fonts.css        @font-face rules, hashed filenames
    site/assets/fonts/coverage.txt   every codepoint the subset covers
"""
from __future__ import annotations

import hashlib
import html
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = ROOT / "site" / "assets" / "fonts"
CSS_OUT = ROOT / "site" / "assets" / "css" / "fonts.css"
COVERAGE = FONTS_DIR / "coverage.txt"

FONT_VERSION = "v1.522"
RELEASE_URL = "https://github.com/lxgw/LxgwWenkaiGB/releases/download/{ver}/{file}"

# (source face, css font-weight range, output stem)
#
# Ranges rather than single values, because the stylesheets ask for weights
# these two faces do not sit on: body is 450 (chosen for Sofia Sans), and
# several chrome elements use 500. Pinning the faces at exactly 400 and 700
# would leave those to CSS's 400-to-500 matching rule, which does land on
# Regular but only by way of a fallback branch. Spelling the ranges out says
# it directly: anything up to 500 draws Regular, 600 and up draws Medium.
FACES = [
    ("LXGWWenKaiGB-Regular.ttf", "100 500", "lxgw-wenkai-gb-regular"),
    ("LXGWWenKaiGB-Medium.ttf", "600 900", "lxgw-wenkai-gb-medium"),
]

# Everything the renderer can put on the page. The renderer's own source is in
# the list because it can synthesise characters that appear in no content file.
#
# Deliberately not "scripts/*.py": that would sweep in this file, whose own
# prose about the GB cut names characters (骨 and friends) the site never
# renders. One stray codepoint means a new subset, new hashed filenames and a
# binary diff on a change that rendered nothing new.
SOURCE_GLOBS = [
    "content/*.json",
    "content/home/*.json",
    "content/releases/*.md",
    "site/_templates/*.html",
    "site/partials/*.html",
    "scripts/build.py",
    "scripts/sitegen/**/*.py",
]

# Punctuation and symbols the templates or future entries may reach for even
# when no current source file happens to contain them. Cheap to carry.
EXTRA = (
    "　、。〃〈〉《》「」『』【】〔〕・ー—…‥‧※"
    "！＂＃＄％＆＇（）＊＋，－．／：；＜＝＞？＠［＼］＾＿｀｛｜｝～"
    "±×÷≈≠≤≥←↑→↓↔√∞°′″¥€£§¶†‡•‰"
    "①②③④⑤⑥⑦⑧⑨⑩⚠✓✕→↗"
)


def collect_chars() -> set[str]:
    chars: set[str] = set(EXTRA)
    for pattern in SOURCE_GLOBS:
        for path in sorted(ROOT.glob(pattern)):
            # Unescape so an entity in a template (&copy;) is counted as the
            # character the browser will actually be asked to draw.
            chars |= set(html.unescape(path.read_text(encoding="utf-8")))
    # ASCII is served by Sofia Sans; control characters and the emoji
    # variation selector have no glyph to carry.
    return {c for c in chars if ord(c) > 0x7F and not (0xFE00 <= ord(c) <= 0xFE0F)}


def fetch(file_name: str, cache: Path) -> Path:
    dest = cache / file_name
    if dest.exists() and dest.stat().st_size > 1_000_000:
        return dest
    url = RELEASE_URL.format(ver=FONT_VERSION, file=file_name)
    print(f"[fonts] downloading {file_name} ({FONT_VERSION}) …")
    cache.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as resp, dest.open("wb") as fh:
        shutil.copyfileobj(resp, fh)
    return dest


def main() -> None:
    if shutil.which("pyftsubset") is None:
        raise SystemExit("pyftsubset not found — run: pip install fonttools brotli")

    chars = collect_chars()
    print(f"[fonts] {len(chars)} non-ASCII characters in content + templates")

    cache = Path(tempfile.gettempdir()) / "lxgw-wenkai-gb"
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    for stale in FONTS_DIR.glob("*.woff2"):
        stale.unlink()

    with tempfile.TemporaryDirectory() as tmp:
        char_file = Path(tmp) / "chars.txt"
        char_file.write_text("".join(sorted(chars)), encoding="utf-8")

        rules = []
        for src_name, weight, stem in FACES:
            src = fetch(src_name, cache)
            raw = Path(tmp) / f"{stem}.woff2"
            subprocess.run(
                [
                    "pyftsubset", str(src),
                    f"--text-file={char_file}",
                    "--flavor=woff2",
                    "--layout-features=*",
                    "--no-hinting",
                    f"--output-file={raw}",
                ],
                check=True,
            )
            digest = hashlib.sha256(raw.read_bytes()).hexdigest()[:8]
            out = FONTS_DIR / f"{stem}.{digest}.woff2"
            shutil.copyfile(raw, out)
            kb = out.stat().st_size / 1024
            print(f"[fonts] {out.name}  weight {weight}  {kb:.0f} KB")
            rules.append(
                "@font-face {\n"
                '  font-family: "LXGW WenKai GB";\n'
                "  font-style: normal;\n"
                f"  font-weight: {weight};\n"
                "  font-display: swap;\n"
                f'  src: url("../fonts/{out.name}") format("woff2");\n'
                "}\n"
            )

    header = (
        "/* Generated by scripts/subset_fonts.py — do not edit by hand.\n"
        f"   LXGW WenKai GB {FONT_VERSION}, subset to the {len(chars)} non-ASCII\n"
        "   characters this site actually renders. The GB cut uses mainland\n"
        "   standard glyph forms; its Medium face is mapped to weight 700\n"
        "   because the family ships no Bold. */\n\n"
    )
    CSS_OUT.write_text(header + "\n".join(rules), encoding="utf-8")
    COVERAGE.write_text("".join(sorted(chars)), encoding="utf-8")
    print(f"[fonts] wrote {CSS_OUT.relative_to(ROOT)} and {COVERAGE.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
