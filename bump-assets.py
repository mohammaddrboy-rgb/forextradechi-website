#!/usr/bin/env python3
"""Cache-busting helper for the Maktab Forex static site.

Run this AFTER editing assets/css/global.css or assets/js/site.js and BEFORE deploying.
It stamps a fresh version onto the CSS/JS <link>/<script> references in every .html file,
so visitors' browsers fetch the new files instead of an old cached copy.

    python bump-assets.py            # uses today's date, e.g. ?v=20260922
    python bump-assets.py 20260922b  # or pass an explicit version string
"""
import glob, re, sys, datetime

ver = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().strftime("%Y%m%d")
pat = re.compile(r'(/assets/(?:css/global\.css|js/site\.js))(?:\?v=[^"]*)?"')
changed = 0
for f in glob.glob("*.html"):
    t = open(f, encoding="utf-8").read()
    new = pat.sub(lambda m: m.group(1) + "?v=" + ver + '"', t)
    if new != t:
        open(f, "w", encoding="utf-8").write(new)
        changed += 1
print(f"Stamped ?v={ver} on {changed} HTML file(s).")
