#!/usr/bin/env python3
"""Regenerate the slide manifest embedded in index.html from the PNGs in slides/.

Slides are ordered by the numeric prefix of their filename ("12_Foo-bar.png"),
and the rest of the filename becomes the slide title. Run after adding,
removing or renaming slides:

    python3 build.py
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SLIDE_DIR = os.path.join(ROOT, "slides")
INDEX = os.path.join(ROOT, "index.html")
# Optional per-slide extras, keyed by filename without the number prefix or
# extension ("30_httpsfoo.png" -> "httpsfoo"), so entries survive renumbering.
EMBEDS = os.path.join(ROOT, "embeds.json")
EMBED_KEYS = {"title", "embed", "link"}
MARKER = re.compile(r"(const SLIDES = /\*__SLIDES__\*/)[\s\S]*?;\n")


def sort_key(name):
    m = re.match(r"^(\d+)_", name)
    return (int(m.group(1)) if m else 10**6, name)


def main():
    files = sorted(
        (f for f in os.listdir(SLIDE_DIR) if f.lower().endswith(".png")),
        key=sort_key,
    )
    if not files:
        sys.exit(f"No PNGs found in {SLIDE_DIR}")

    extras = {}
    if os.path.exists(EMBEDS):
        extras = json.load(open(EMBEDS, encoding="utf-8"))
    for key, extra in extras.items():
        unknown = set(extra) - EMBED_KEYS
        if unknown:
            sys.exit(f"embeds.json '{key}': unknown field(s) {sorted(unknown)}")
        for field in ("embed", "link"):
            if field in extra and not extra[field].startswith("https://"):
                sys.exit(f"embeds.json '{key}': {field} must be an https:// URL")

    slides, used = [], set()
    for i, f in enumerate(files, start=1):
        slug = re.sub(r"^\d+_", "", f)[:-4]
        title = slug.replace("-", " ").strip()
        # Some exports drop the title entirely (e.g. when it starts with a quote).
        entry = {"file": f, "title": title or f"Slide {i}"}
        if slug in extras:
            used.add(slug)
            entry.update(extras[slug])
        slides.append(entry)

    for key in sorted(set(extras) - used):
        print(f"warning: embeds.json entry '{key}' matches no slide", file=sys.stderr)

    html = open(INDEX, encoding="utf-8").read()
    payload = json.dumps(slides, indent=2, ensure_ascii=False).replace("</", "<\\/")
    html, n = MARKER.subn(lambda m: m.group(1) + payload + ";\n", html, count=1)
    if n != 1:
        sys.exit("Could not find the SLIDES marker in index.html")

    open(INDEX, "w", encoding="utf-8").write(html)
    print(f"Wrote {len(slides)} slides into index.html ({len(used)} with embeds.json extras)")


if __name__ == "__main__":
    main()
