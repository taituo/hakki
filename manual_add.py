#!/usr/bin/env python3
"""Manually add exact-title Commons images (curl download, license metadata)."""
import json, os, re, subprocess, urllib.request, urllib.parse, html as ihtml, time

UA = "hakki-catalog/1.0 (local research catalog)"
OUTDIR = "assets/commons"
MANIFEST = os.path.join(OUTDIR, "images.json")

JOBS = [
    ("Nexus 4 phones", "File:Nexus 4 front.JPG", "901-nexus-4-front.jpg"),
    ("Marlin 3D printers", "File:Large delta-style 3D printer.jpg", "902-delta-3d-printer.jpg"),
    ("Samsung NX1 / NX500", "File:Samsung WB350F front.jpg", "903-samsung-wb350f.jpg"),
    ("OpenWrt travel routers", "File:GL-iNet Travel Router and Wyze Camera - Hotel Room Security.jpg", "904-glinet-travel-router.jpg"),
    ("Klipper-compatible 3D printers", "File:Prusa i3 - RepRap 3D printer printing.jpg", "905-prusa-i3.jpg"),
]

def api_imageinfo(title):
    params = {"action": "query", "format": "json", "formatversion": "2",
              "titles": title, "prop": "imageinfo",
              "iiprop": "url|extmetadata|size", "iiurlwidth": "320"}
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        d = json.load(r)
    pages = d.get("query", {}).get("pages", [])
    return pages[0] if pages else None

def strip_html(s):
    return ihtml.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()

manifest = json.load(open(MANIFEST, encoding="utf-8"))
have = {m["device"] for m in manifest if m.get("status") == "ok"}
for device, title, fname in JOBS:
    if device in have:
        print("skip (already ok):", device)
        continue
    p = api_imageinfo(title)
    if not p or p.get("missing"):
        print("NOT FOUND:", title)
        continue
    ii = (p.get("imageinfo") or [{}])[0]
    thumb = (ii.get("thumburl") or ii.get("url") or "").split("?")[0]
    dest = os.path.join(OUTDIR, fname)
    r = subprocess.run(["curl", "-sS", "-m", "60", "-A", UA, thumb, "-o", dest],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(dest):
        print("DL FAIL:", title, r.stderr.strip()[:120])
        continue
    head = open(dest, "rb").read(12)
    magic = (head[:2] == b"\xff\xd8" or head[:8] == b"\x89PNG\r\n\x1a\n"
             or head[:4] in (b"RIFF", b"GIF8"))
    if not magic or os.path.getsize(dest) <= 2048:
        print("BAD BYTES:", title)
        try: os.remove(dest)
        except OSError: pass
        continue
    meta = ii.get("extmetadata") or {}
    lic = strip_html((meta.get("LicenseShortName") or {}).get("value", "")) or "ks. Commons-sivu"
    licurl = strip_html((meta.get("LicenseUrl") or {}).get("value", ""))
    artist = strip_html((meta.get("Artist") or {}).get("value", ""))
    credit = strip_html((meta.get("Credit") or {}).get("value", "")) or artist
    manifest.append({"device": device, "status": "ok", "checked_v": 2,
        "query": "manual exact-title", "match": "curated exact file",
        "title": p.get("title"), "file": fname, "thumb_url": ii.get("thumburl"),
        "page_url": ii.get("descriptionurl", ""), "license": lic,
        "license_url": licurl, "artist": artist[:200], "credit": credit[:200]})
    print("OK", device, "<-", p.get("title"))
    time.sleep(2)

# drop any non-ok leftovers, keep file tidy
manifest = [m for m in manifest if m.get("status") == "ok"]
json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("manifest ok entries:", len(manifest))
