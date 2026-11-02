#!/usr/bin/env python3
"""Build static GitHub Pages output from the ONE editable site-config.js."""
from pathlib import Path
import html
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "dist"
data = (ROOT / "assets/js/site-config.js").read_text(encoding="utf-8")
match = re.search(r"window\.YF_SITE_CONFIG\s*=\s*(\{.*?\});\s*/\* END SITE DATA \*/", data, re.S)
if not match:
    raise SystemExit("Invalid config: JSON data marker missing")
settings = json.loads(match.group(1))
brand, seo = settings["brand"], settings["seo"]
name = brand["name"].strip()
if not name:
    raise SystemExit("Empty brand.name")
url = seo["baseUrl"].rstrip("/") + "/"
if not url.startswith("https://"):
    raise SystemExit("Set a full HTTPS URL in seo.baseUrl")
for original, desired in settings["media"].items():
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*\.(?:webp|jpg|png|avif)", original):
        raise SystemExit("Invalid media key: " + original)
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*\.(?:webp|jpg|png|avif)", desired):
        raise SystemExit("Invalid image name: " + desired)
    if not (ROOT / "assets/images" / desired).is_file():
        raise SystemExit("Missing configured image: " + desired)
if not (ROOT / "assets/images" / seo["ogImage"]).is_file():
    raise SystemExit("Missing OG image")
# Check both favicon variants before copying files to the published site.
favicons = settings["favicon"]
for variant in ("light", "dark"):
    filename = favicons[variant]
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*\.svg", filename):
        raise SystemExit("Invalid favicon filename: " + filename)
    if not (ROOT / "assets/images" / filename).is_file():
        raise SystemExit("Missing favicon: " + filename)
if favicons.get("mixed") not in ("light", "dark"):
    raise SystemExit("favicon.mixed must be light or dark")
if DEST.exists():
    shutil.rmtree(DEST)
DEST.mkdir()
shutil.copytree(ROOT / "assets", DEST / "assets")

content = (ROOT / "index.html").read_text(encoding="utf-8")
default_icon = favicons[favicons["mixed"]]
content, icon_count = re.subn(
    r'(<link rel="icon" type="image/svg\+xml" href=")[^"]+(">)',
    lambda m: m.group(1) + "assets/images/" + default_icon + m.group(2),
    content, count=1
)
if icon_count != 1:
    raise SystemExit("Missing favicon link in HTML")
def replace_one(pattern, value):
    global content
    content, count = re.subn(pattern, lambda _: value, content, count=1, flags=re.S)
    if count != 1:
        raise SystemExit("Missing source SEO field: " + pattern)

for original, desired in settings["media"].items():
    content = content.replace("assets/images/" + original, "assets/images/" + desired)
    for css in (DEST / "assets/css").glob("*.css"):
        text = css.read_text(encoding="utf-8")
        old = "../images/" + original
        if old in text:
            css.write_text(text.replace(old, "../images/" + desired), encoding="utf-8")

role = seo["roleUk"] + " " if brand.get("isPerson") else ""
title = role + name + " | " + seo["titleSuffixUk"]
description = seo["descriptionUk"]
esc = lambda s: html.escape(str(s), quote=True)
replace_one(r"<title>.*?</title>", "<title>" + esc(title) + "</title>")
replace_one(r'<meta name="description" content="[^"]*">', '<meta name="description" content="' + esc(description) + '">')
replace_one(r'<meta name="robots" content="[^"]*">', '<meta name="robots" content="' + esc(seo["robots"]) + '">')
replace_one(r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="' + esc(url) + '">')
for key, value in {
    "og:title": title, "og:description": description, "og:url": url,
    "og:image": url + "assets/images/" + seo["ogImage"]
}.items():
    replace_one(r'<meta property="' + re.escape(key) + r'" content="[^"]*">',
                '<meta property="' + key + '" content="' + esc(value) + '">')
structured = {
    "@context": "https://schema.org", "@type": "WebPage",
    "name": title, "description": description, "url": url,
    "inLanguage": "uk", "isPartOf": {"@type": "WebSite", "name": name, "url": url}
}
if brand.get("isPerson"):
    structured["about"] = {"@type": "Person", "name": name, "jobTitle": seo["roleUk"]}
jsonld = json.dumps(structured, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
replace_one(r'<script type="application/ld\+json">.*?</script>',
            '<script type="application/ld+json">' + jsonld + '</script>')

parts = name.upper().split(" ", 1)
def brand_link(match):
    suffix = parts[1] if len(parts) == 2 else ""
    wrapper = "small" if 'class="logo"' in match.group(1) else "span"
    return match.group(1) + esc(parts[0]) + "<" + wrapper + ">" + esc(suffix) + "</" + wrapper + ">" + match.group(3)
content, count = re.subn(r'(<a\b[^>]*data-site-brand[^>]*>)(.*?)(</a>)',
                         brand_link, content, flags=re.S)
if count != 3:
    raise SystemExit("Expected three brand links; got " + str(count))
replace_one(r'<h2 id="yf-about-details-title">.*?</h2>',
            '<h2 id="yf-about-details-title">' + esc(name.upper()) + '</h2>')
content, copyright_count = re.subn(r'(<span class="yf-year">2026</span>)[^<]*',
                                    lambda m: m.group(1) + ' ' + esc(name) + ' · Усі права захищено',
                                    content, count=1)
if copyright_count != 1:
    raise SystemExit("Copyright marker missing")
(DEST / "index.html").write_text(content, encoding="utf-8")
print("Built dist/ for", name, "—", url)
