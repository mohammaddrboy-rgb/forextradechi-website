#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the Farsi (/fa/) mirror for bilingual SEO.

The English .html files at the site root are the SOURCE OF TRUTH. This script:
  1. Converts the inline language <script> to URL-based (so /fa/ pages default to Farsi).
  2. Injects <link rel="alternate" hreflang="…"> into every English page (idempotent).
  3. Generates /fa/<page>.html — same content but Farsi as the default language,
     with Farsi <title>/description/OG, a self-canonical to the /fa/ URL, and all
     internal page links rewritten to /fa/…
  4. Regenerates sitemap.xml with hreflang alternates for both languages.

Run it after ANY change to the English pages (content, nav, footer):

    python build-fa.py
"""
import glob, re, os, io

BASE = "https://forextradechi.com"

# Farsi meta descriptions per page (SEO). Falls back to the Farsi <title> if missing.
FA_DESC = {
    "index.html": "مکتب فارکس — آموزش رایگان فارکس به زبان دری برای جامعهٔ افغان. از مبتدی تا پیشرفته.",
    "landing.html": "مکتب فارکس — فارکس را درست بیاموز. آموزش رایگان و صادقانهٔ فارکس به زبان دری.",
    "courses.html": "دوره‌های مکتب فارکس — دورهٔ پایهٔ ۱۳ درسی و دورهٔ پیشرفتهٔ ۲۱ درسی، رایگان و به زبان دری.",
    "islamic-finance.html": "فارکس از نگاه اسلامی — چارچوبی علمی برای معامله‌گر مسلمان: ربا، غرر، میسر و ارزیابی حساب اسلامی.",
    "tools.html": "ابزارهای رایگان مکتب فارکس — تقویم اقتصادی و ماشین‌حساب مدیریت ریسک.",
    "risk-calculator.html": "ماشین‌حساب ریسک فارکس — محاسبهٔ حجم معامله، مبلغ در معرض ریسک و نسبت ریسک به ریوارد.",
    "economic-calendar.html": "تقویم اقتصادی زندهٔ فارکس — رویدادهای مهم اقتصادی هفته را دنبال کنید.",
    "faq.html": "پرسش‌های متداول مکتب فارکس — آیا فارکس حلال است؟ رایگان است؟ چگونه شروع کنیم و چقدر سرمایه لازم است؟",
    "glossary.html": "واژه‌نامهٔ فارکس به زبان دری — پیپ، لات، اهرم، مارجین و اسپرد به زبان ساده.",
    "how-to-start.html": "چگونه فارکس را شروع کنیم — مسیری ساده و امن از مبانی و حساب دمو تا مدیریت ریسک و جامعه.",
    "articles.html": "مقالات و تحلیل هفتگی مکتب فارکس — به زبان دری و انگلیسی.",
    "join.html": "به کانال واتساپ مکتب فارکس بپیوندید — آموزش رایگان فارکس به زبان دری.",
    "about.html": "دربارهٔ مکتب فارکس — آموزش صادقانهٔ فارکس به زبان دری، بدون وعدهٔ سود و بدون فریب.",
    "disclaimer.html": "سلب مسئولیت مکتب فارکس — محتوای آموزشی، نه توصیهٔ مالی. معامله در فارکس با ریسک همراه است.",
}

OLD_HEAD = ("<script>(function(){try{var l=localStorage.getItem('mf-lang');if(l!=='fa')l='en';"
            "var d=document.documentElement;d.lang=l;d.dir=l==='fa'?'rtl':'ltr';}catch(e){}})();</script>")
NEW_HEAD = ("<script>(function(){var fa=location.pathname.indexOf('/fa/')!==-1;"
            "var d=document.documentElement;d.lang=fa?'fa':'en';d.dir=fa?'rtl':'ltr';})();</script>")

pages = sorted(f for f in glob.glob("*.html") if f != "404.html")

def en_url(fn):  return BASE + "/" if fn == "index.html" else BASE + "/" + fn
def fa_url(fn):  return BASE + "/fa/" if fn == "index.html" else BASE + "/fa/" + fn

def hreflang(fn):
    return ('  <link rel="alternate" hreflang="en" href="%s">\n'
            '  <link rel="alternate" hreflang="fa" href="%s">\n'
            '  <link rel="alternate" hreflang="x-default" href="%s">\n'
            % (en_url(fn), fa_url(fn), en_url(fn)))

def title_fa(html):
    m = re.search(r'data-title-fa="([^"]*)"', html)
    return m.group(1) if m else "مکتب فارکس"

# ---- 1 & 2: update English source pages (URL-based lang script + hreflang) ----
for fn in pages:
    t = io.open(fn, encoding="utf-8").read()
    if OLD_HEAD in t:
        t = t.replace(OLD_HEAD, NEW_HEAD)
    if 'hreflang="en"' not in t:
        t = re.sub(r'(<link rel="canonical"[^>]*>\n)', lambda m: m.group(1) + hreflang(fn), t, count=1)
    io.open(fn, "w", encoding="utf-8").write(t)

# ---- 3: generate /fa/ mirror ----
os.makedirs("fa", exist_ok=True)
for fn in pages:
    t = io.open(fn, encoding="utf-8").read()
    tf = title_fa(t)
    desc = FA_DESC.get(fn, tf)
    t = t.replace('<html lang="en" dir="ltr"', '<html lang="fa" dir="rtl"', 1)
    t = re.sub(r'<title>.*?</title>', '<title>' + tf + '</title>', t, count=1, flags=re.S)
    t = re.sub(r'(<meta name="description" content=")[^"]*(">)', lambda m: m.group(1) + desc + m.group(2), t, count=1)
    t = re.sub(r'(<meta property="og:title" content=")[^"]*(">)', lambda m: m.group(1) + tf + m.group(2), t, count=1)
    t = re.sub(r'(<meta property="og:description" content=")[^"]*(">)', lambda m: m.group(1) + desc + m.group(2), t, count=1)
    t = re.sub(r'(<meta property="og:url" content=")[^"]*(">)', lambda m: m.group(1) + fa_url(fn) + m.group(2), t, count=1)
    t = re.sub(r'(<link rel="canonical" href=")[^"]*(">)', lambda m: m.group(1) + fa_url(fn) + m.group(2), t, count=1)
    # rewrite internal page links to the /fa/ tree (assets & external links untouched)
    t = re.sub(r'href="/([a-z0-9-]+\.html)', r'href="/fa/\1', t)
    io.open(os.path.join("fa", fn), "w", encoding="utf-8").write(t)

# ---- 4: sitemap with hreflang alternates ----
def alts(fn):
    return ('    <xhtml:link rel="alternate" hreflang="en" href="%s"/>\n'
            '    <xhtml:link rel="alternate" hreflang="fa" href="%s"/>\n'
            '    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>\n'
            % (en_url(fn), fa_url(fn), en_url(fn)))

prio = {"index.html": "1.0", "landing.html": "0.9", "courses.html": "0.9"}
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
for fn in pages:
    p = prio.get(fn, "0.7")
    for loc in (en_url(fn), fa_url(fn)):
        sm.append('  <url>')
        sm.append('    <loc>%s</loc>' % loc)
        sm.append(alts(fn).rstrip("\n"))
        sm.append('    <priority>%s</priority>' % p)
        sm.append('  </url>')
sm.append('</urlset>\n')
io.open("sitemap.xml", "w", encoding="utf-8").write("\n".join(sm))

print("Built /fa/ mirror for %d pages, injected hreflang, regenerated sitemap." % len(pages))
