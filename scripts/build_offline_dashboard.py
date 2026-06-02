#!/usr/bin/env python3
"""
Build a fully self-contained, offline-capable copy of the dashboard.

Source of truth stays dashboard/VBX_Command_Center_Dashboard.html. This script
inlines the two external CDN dependencies — SheetJS (workbook parser) and the
Google Fonts (DM Serif Display / DM Sans / JetBrains Mono) — as base64 data so
the result needs no network at all. The viewer still reads the workbook the
operator uploads; no operational data is embedded.

    python scripts/build_offline_dashboard.py

Output -> output/VBX_Command_Center_Dashboard_offline.html  (gitignored)
"""
import base64
import os
import re
import urllib.request

SRC = "dashboard/VBX_Command_Center_Dashboard.html"
OUT = "output/VBX_Command_Center_Dashboard_offline.html"
GUIDE_SRC = "docs/HOW_TO_USE_Offline_Dashboard.md"
GUIDE_OUT = "output/VBX_Command_Center_Dashboard_offline_HOW-TO-USE.md"

FONTS_CSS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400"
    "&family=DM+Serif+Display:ital@0;1"
    "&family=JetBrains+Mono:wght@400;500;600;700&display=swap"
)
SHEETJS_URL = "https://cdn.sheetjs.com/xlsx-0.20.0/package/dist/xlsx.full.min.js"

# A modern-browser UA makes Google Fonts serve woff2 (smallest format).
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def fetch(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    return data if binary else data.decode("utf-8")


def inline_fonts(css):
    """Replace every url(https://fonts.gstatic.com/....woff2) with a data: URI."""
    cache = {}

    def repl(m):
        url = m.group(1)
        if url not in cache:
            woff2 = fetch(url, binary=True)
            b64 = base64.b64encode(woff2).decode("ascii")
            cache[url] = f"data:font/woff2;base64,{b64}"
        return f"url({cache[url]})"

    inlined = re.sub(r"url\((https://fonts\.gstatic\.com/[^)]+?\.woff2)\)", repl, css)
    return inlined, len(cache)


def main():
    html = open(SRC, encoding="utf-8").read()

    print("Fetching Google Fonts CSS ...")
    fonts_css = fetch(FONTS_CSS_URL)
    print("Inlining font files ...")
    fonts_css, n = inline_fonts(fonts_css)
    print(f"  inlined {n} woff2 files")

    print("Fetching SheetJS ...")
    sheetjs = fetch(SHEETJS_URL)
    # guard against an accidental </script> terminating the inline block
    sheetjs = sheetjs.replace("</script>", "<\\/script>")

    # Replace the two preconnect hints + the stylesheet <link> with inlined fonts.
    link_block = re.compile(
        r'<link rel="preconnect" href="https://fonts\.googleapis\.com">\s*'
        r'<link rel="preconnect" href="https://fonts\.gstatic\.com" crossorigin>\s*'
        r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/css2\?[^"]*">'
    )
    html, c1 = link_block.subn(
        lambda m: "<style>\n/* Inlined Google Fonts — offline build */\n" + fonts_css + "\n</style>",
        html,
    )
    assert c1 == 1, f"font <link> block not matched ({c1})"

    # Replace the SheetJS <script src=...> with an inline <script>.
    html, c2 = re.subn(
        r'<script src="https://cdn\.sheetjs\.com/[^"]*"></script>',
        lambda m: "<script>/* Inlined SheetJS " + SHEETJS_URL.split("/")[-1] + " */\n" + sheetjs + "\n</script>",
        html,
    )
    assert c2 == 1, f"SheetJS <script> not matched ({c2})"

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(html)

    # ship the recipient guide alongside the bundle
    wrote_guide = False
    if os.path.exists(GUIDE_SRC):
        open(GUIDE_OUT, "w", encoding="utf-8").write(open(GUIDE_SRC, encoding="utf-8").read())
        wrote_guide = True

    remaining = re.findall(r'(?:src|href)="https?://(?![^"]*data:)[^"]+"', html)
    size_mb = os.path.getsize(OUT) / 1e6
    print(f"\nWrote {OUT}  ({size_mb:.2f} MB)")
    if wrote_guide:
        print(f"Wrote {GUIDE_OUT}")
    print(f"Remaining external http refs: {len(remaining)}")
    for r in remaining:
        print("  !", r)


if __name__ == "__main__":
    main()
