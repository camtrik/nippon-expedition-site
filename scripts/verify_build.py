#!/usr/bin/env python3
"""
verify_build.py — Prove that a change to the build renders the same site.

Builds the tree twice — once from a git ref, once from the working tree — and
compares site/_dist byte for byte. Two values legitimately differ between any
two builds and are normalised away first: the cache-busting `?v=` stamp and the
`BUILD_TIME` footer timestamp. Everything else must match exactly.

Both builds run in both of the environments the site actually ships in: served
from a domain root, and served from a GitHub Pages project subpath. The second
is the one AGENTS.md calls the easiest thing to break, and it is invisible in a
plain local preview.

The whole of _dist is compared, not just the HTML, so concatenated stylesheets
and copied assets are covered too. Build stdout is compared as well: a release
dropped from a channel that renders empty would not show up in the HTML.

Usage
    python3 scripts/verify_build.py                    # baseline = HEAD
    python3 scripts/verify_build.py --baseline abc1234 # baseline = that commit

Exits non-zero on any difference. No dependencies beyond the build's own.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The only two values that change from one build of identical sources to the
# next. Both patterns are deliberately narrow: BUILD_TIME_RE requires the
# " HH:MM UTC" tail so that release dates (bare YYYY-MM-DD) are left alone.
CACHE_BUST_RE = re.compile(r"\?v=\d+")
BUILD_TIME_RE = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC")

ENVS = {
    "root": {},
    "subpath": {
        "SITE_BASE_PATH": "/nippon-expedition-site",
        "SITE_ORIGIN": "https://camtrik.github.io",
    },
}

MAX_DIFF_LINES = 40


def normalize(text: str) -> str:
    text = CACHE_BUST_RE.sub("?v=CACHEBUST", text)
    return BUILD_TIME_RE.sub("BUILD_TIME", text)


def build(tree: Path, env_extra: dict[str, str]) -> str:
    """Run the build in `tree`; return its normalised stdout."""
    env = {k: v for k, v in os.environ.items() if k not in ENVS["subpath"]}
    env.update(env_extra)
    proc = subprocess.run(
        [sys.executable, "scripts/build.py"],
        cwd=tree, env=env, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout + proc.stderr)
        raise SystemExit(f"build failed in {tree} (exit {proc.returncode})")
    return normalize(proc.stdout)


def snapshot(dist: Path) -> dict[str, bytes]:
    """Every file under `dist`, keyed by relative path, HTML normalised."""
    if not dist.is_dir():
        raise SystemExit(f"no build output at {dist}")
    out: dict[str, bytes] = {}
    for path in sorted(p for p in dist.rglob("*") if p.is_file()):
        rel = str(path.relative_to(dist))
        raw = path.read_bytes()
        if path.suffix == ".html":
            raw = normalize(raw.decode("utf-8")).encode("utf-8")
        out[rel] = raw
    return out


def compare(label: str, before: dict[str, bytes], after: dict[str, bytes]) -> list[str]:
    problems = []
    for rel in sorted(set(before) - set(after)):
        problems.append(f"[{label}] missing from new build: {rel}")
    for rel in sorted(set(after) - set(before)):
        problems.append(f"[{label}] new build has an extra file: {rel}")
    for rel in sorted(set(before) & set(after)):
        if before[rel] == after[rel]:
            continue
        problems.append(f"[{label}] content differs: {rel}")
        problems.extend(text_diff(before[rel], after[rel]))
    return problems


def text_diff(old: bytes, new: bytes) -> list[str]:
    import difflib
    try:
        a, b = old.decode("utf-8"), new.decode("utf-8")
    except UnicodeDecodeError:
        return ["    (binary file)"]
    lines = list(difflib.unified_diff(
        a.splitlines(), b.splitlines(), "before", "after", lineterm="", n=1))
    trimmed = ["    " + line for line in lines[:MAX_DIFF_LINES]]
    if len(lines) > MAX_DIFF_LINES:
        trimmed.append(f"    … {len(lines) - MAX_DIFF_LINES} more diff lines")
    return trimmed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--baseline", default="HEAD",
                    help="git ref to build as the 'before' side (default: HEAD)")
    args = ap.parse_args()

    tmp = Path(tempfile.mkdtemp(prefix="npex-verify-"))
    worktree = tmp / "baseline"
    subprocess.run(["git", "worktree", "add", "--detach", str(worktree), args.baseline],
                   cwd=ROOT, check=True, capture_output=True)
    print(f"[verify] baseline {args.baseline} -> {worktree}")

    problems: list[str] = []
    try:
        for name, env_extra in ENVS.items():
            print(f"[verify] building both trees, env: {name}")
            before_out = build(worktree, env_extra)
            before = snapshot(worktree / "site" / "_dist")
            after_out = build(ROOT, env_extra)
            after = snapshot(ROOT / "site" / "_dist")

            problems += compare(name, before, after)
            if before_out != after_out:
                problems.append(f"[{name}] build stdout differs:")
                problems += text_diff(before_out.encode(), after_out.encode())
            print(f"[verify]   {len(before)} files compared")
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(worktree)],
                       cwd=ROOT, check=False, capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)

    if problems:
        print()
        for line in problems:
            print(line)
        print(f"\n[verify] FAILED — {sum(1 for p in problems if not p.startswith('    '))} difference(s)")
        return 1

    print("[verify] OK — output is byte-identical in both environments")
    return 0


if __name__ == "__main__":
    sys.exit(main())
