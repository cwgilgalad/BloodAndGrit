#!/usr/bin/env python3
"""Build the self-contained Player's Book.

Reads player-src.html, inlines every `assets/imgNN.ext` referenced in the
source as a base64 data URI, and writes blood-and-grit.html. Discovery is
by regex on the source, so new refs are picked up automatically and
unreferenced assets are skipped. Idempotent: rebuilding yields byte-identical
output.
"""
import base64, mimetypes, os, re, sys

from nav_tools import add_detailed_toc
from perdition_map import player_map_html

SRC = "player-src.html"
OUT = "blood-and-grit.html"

html = open(SRC, encoding="utf-8").read()

# Drop the player-facing map of Perdition Basin into Appendix E.
html = html.replace("<!--PERDITION_MAP-->", player_map_html())

# Grow the simple Contents into a generated two-level detailed Contents.
html = add_detailed_toc(html)

refs = sorted(set(re.findall(r'assets/img\d+\.\w+', html)))
for ref in refs:
    if not os.path.exists(ref):
        sys.exit(f"missing asset: {ref}")
    mime = mimetypes.guess_type(ref)[0] or "application/octet-stream"
    b64 = base64.b64encode(open(ref, "rb").read()).decode("ascii")
    html = html.replace(ref, f"data:{mime};base64,{b64}")

open(OUT, "w", encoding="utf-8", newline="").write(html)
print(f"built {OUT}: {len(html)} bytes, {len(refs)} image(s) inlined: {', '.join(refs)}")
