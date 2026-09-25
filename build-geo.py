#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GEO (Generative Engine Optimization) — inject machine-readable structured data
so AI answer engines (ChatGPT Search, Perplexity, Gemini, Google AI Overviews) can
read, trust and CITE the site, in both languages.

Adds, per page and per language (English on root pages, Farsi on /fa/ pages):
  - FAQPage schema on faq.html  (extracted from the on-page Q&A)
  - DefinedTermSet schema on glossary.html (extracted from the on-page terms)
  - Person schema on about.html (the founder)
  - WebSite schema on index.html

Each block is wrapped in <!-- geo:jsonld --> … <!-- /geo:jsonld --> and is idempotent.

RUN ORDER (important): run this AFTER build-fa.py, because build-fa regenerates /fa/
from the English pages and would otherwise carry English schema onto Farsi pages.

    python build-geo.py
"""
import glob, re, os, io, json, html

SITE = "https://forextradechi.com"

def lang_of(path):
    p = path.replace("\\", "/")
    return "fa" if "/fa/" in p or p.startswith("fa/") else "en"

def clean(s):
    return html.unescape(re.sub(r"\s+", " ", s)).strip()

def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))

# ---- extractors (return list per pair, each with en/fa) ----
def extract_faq(text):
    items = []
    for chunk in text.split('<div class="acc-item">')[1:]:
        q = re.search(r'<span><span class="lang-en">(.*?)</span><span class="lang-fa">(.*?)</span></span>', chunk, re.S)
        a = re.search(r'<div class="acc-panel-inner">\s*<p[^>]*><span class="lang-en">(.*?)</span><span class="lang-fa">(.*?)</span></p>', chunk, re.S)
        if q and a:
            items.append({"q": {"en": clean(q.group(1)), "fa": clean(q.group(2))},
                          "a": {"en": clean(a.group(1)), "fa": clean(a.group(2))}})
    return items

def extract_terms(text):
    items = []
    for chunk in text.split('<div class="term">')[1:]:
        n = re.search(r'<h3><span class="lang-en">(.*?)</span><span class="lang-fa">(.*?)</span></h3>', chunk, re.S)
        d = re.search(r'<p><span class="lang-en">(.*?)</span><span class="lang-fa">(.*?)</span></p>', chunk, re.S)
        if n and d:
            items.append({"n": {"en": clean(n.group(1)), "fa": clean(n.group(2))},
                          "d": {"en": clean(d.group(1)), "fa": clean(d.group(2))}})
    return items

# ---- schema builders ----
def website_schema(lang):
    desc = {"en": "Free forex education in Dari and English for the Afghan community.",
            "fa": "آموزش رایگان فارکس به دری و انگلیسی برای جامعهٔ افغان."}[lang]
    return {"@context": "https://schema.org", "@type": "WebSite",
            "name": "Maktab Forex", "alternateName": "مکتب فارکس",
            "url": SITE + "/", "inLanguage": ["fa", "en"], "description": desc,
            "publisher": {"@type": "Organization", "name": "Maktab Forex", "url": SITE + "/"}}

def person_schema(lang):
    desc = {"en": "Founder of Maktab Forex, in the forex industry since 2012, specialising in market analysis and in educating, training and mentoring traders. Holds a Bachelor's in Business Administration and is pursuing an MBA.",
            "fa": "بنیان‌گذار مکتب فارکس، فعال در صنعت فارکس از سال ۲۰۱۲، متخصص در تحلیل بازار و آموزش، تربیت و راهنمایی معامله‌گران. دارای لیسانس مدیریت بازرگانی و در حال تحصیل کارشناسی ارشد (MBA)."}[lang]
    return {"@context": "https://schema.org", "@type": "Person",
            "name": "Mohammad Akhondzadeh", "alternateName": "محمد آخوندزاده",
            "jobTitle": "Founder & Instructor",
            "worksFor": {"@type": "Organization", "name": "Maktab Forex", "url": SITE + "/"},
            "knowsAbout": ["Forex", "Technical analysis", "Price action", "Risk management", "Trading psychology", "Islamic finance"],
            "knowsLanguage": ["Dari", "Persian", "English"],
            "url": SITE + "/about.html", "image": SITE + "/assets/img/founder.jpg",
            "description": desc}

def faq_schema(items, lang):
    return {"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": lang,
            "mainEntity": [{"@type": "Question", "name": it["q"][lang],
                            "acceptedAnswer": {"@type": "Answer", "text": it["a"][lang]}} for it in items]}

def termset_schema(items, lang):
    name = {"en": "Forex Glossary", "fa": "واژه‌نامهٔ فارکس"}[lang]
    return {"@context": "https://schema.org", "@type": "DefinedTermSet", "name": name, "inLanguage": lang,
            "hasDefinedTerm": [{"@type": "DefinedTerm", "name": it["n"][lang], "description": it["d"][lang]} for it in items]}

GEO_RE = re.compile(r'\n?  <!-- geo:jsonld -->.*?<!-- /geo:jsonld -->', re.S)

def inject(path, schema):
    t = io.open(path, encoding="utf-8").read()
    t = GEO_RE.sub("", t)  # remove any previous block (idempotent)
    block = '\n  <!-- geo:jsonld -->\n  <script type="application/ld+json">\n  %s\n  </script>\n  <!-- /geo:jsonld -->' % dumps(schema)
    t = t.replace("</head>", block + "\n</head>", 1)
    io.open(path, "w", encoding="utf-8").write(t)

count = 0
for path in glob.glob("*.html") + glob.glob("fa/*.html"):
    base = os.path.basename(path)
    lang = lang_of(path)
    text = io.open(path, encoding="utf-8").read()
    schema = None
    if base == "faq.html":
        schema = faq_schema(extract_faq(text), lang)
    elif base == "glossary.html":
        schema = termset_schema(extract_terms(text), lang)
    elif base == "about.html":
        schema = person_schema(lang)
    elif base == "index.html":
        schema = website_schema(lang)
    if schema is not None:
        inject(path, schema)
        count += 1
print("Injected GEO structured data into %d files." % count)
