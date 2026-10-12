#!/usr/bin/env python3
"""Fetch relevant Wikimedia Commons thumbnails + license metadata.

- One Commons API query per unique device (plus 1 fallback query if needed).
- Strict relevance filter: only bitmap images whose title contains device tokens.
- Downloads 640px thumbnails to assets/commons/, writes assets/commons/images.json.
- Polite: 1.2s between requests, retries on 429, resumable.
Run in /home/tiny/projects/häkki.
"""
import json, os, re, time, html as ihtml, urllib.request, urllib.parse, urllib.error

UA = {"User-Agent": "hakki-catalog/1.0 (local research catalog; contact: local)"}
API = "https://commons.wikimedia.org/w/api.php"
OUTDIR = "assets/commons"
MANIFEST = os.path.join(OUTDIR, "images.json")
CACHE = os.path.join(OUTDIR, "_search_cache.json")
CHECK_V = 2  # bump when filter/query logic changes so old "missing" rows are retried
PAUSE = 0.6  # polite delay between Commons API calls (429s are retried with backoff)

STOP = {"with","from","compatible","robot","smart","generic","selected","supported",
        "models","model","specific","series","legacy","older","various","using",
        "class","family","toys","toy","phones","phone","devices","device","plus",
        "type","based","board","boards","modules","module","radios","radio",
        "the","and","for","with","new","old","original","small","large","mini",
        "numerous","existing","retired","dead","broken","cheap","modern",
        "incomplete","historical","historic","custom","early","advanced",
        "classic","only","entire","whole"}
DENY = {"vessel","conical","lacma","beylagan","century","kyrkoruin","house","church",
        "ruin","street","school","pdf","djvu","coat of arms","blason","football",
        "basketball","cricket","rugby","tournament","election","parliament"}
BITMAP_EXT = (".jpg", ".jpeg", ".png", ".webp")

# Exact Commons titles that proved irrelevant (people, places, manuscripts,
# vehicles, paintings...). Never accept these.
EXCLUDE_TITLES = {
    "File:Van's RV-4 - G-SPRK (48733773512).jpg",
    "File:Tribunal examinador SpheroPhoto.jpg",
    "File:Nybblehallen.JPG",
    "File:Enumeration of some dash variants with their names shown on a grid.png",
    "File:Former St. Elmo Hotel, Henrietta, TX IMG 6839.JPG",
    "File:Fisher-Price Picture Story Camera.jpg",
    "File:Kawasaki ZZ-R 600.jpg",
    "File:World in 500 CE.png",
    "File:Xiaomi Mi Fit 5.jpg",
    "File:Grabstaette Hugo und Max Toelle Wuppertal.JPG",
    "File:The Dreame of Chaucer Book of the Duchess.jpg",
    "File:Xiaomi Store Portugal.jpg",
    "File:AncientEgyptianRelief-QueenTuya-ROM.png",
    "File:Manhattan Bridge Construction 1909.jpg",
    "File:2014-0428-IMG 5143-Jct Points and Switch Arm linkage (bot SW, alt angle).JPG",
    "File:Tracy Caldwell Dyson in Cupola ISS.jpg",
    "File:Scales Tarn and the descent to Sharp Edge - geograph.org.uk - 1750057.jpg",
    "File:Design for Curtains MET DP804477.jpg",
    "File:Libeň, krmítko z PET lahve.jpg",
    "File:Numerous tyre marks on a muddy Norfolk track - geograph.org.uk - 2165409.jpg",
    "File:RTSP cat.jpg",
    "File:Toshiba Portege 3500 Tablet PC.JPG",
    "File:Nokia 1600.jpg",
    "File:Google Cheque epayservice.jpg",
    "File:Korg Wavestation front.png",
    "File:Iridescent clouds during snowfall 1.jpg",
    "File:Mike critter ESEAP.jpg",
    "File:Beijing Subway Maps - Line 6.png",
    "File:Woman Using a Samsung VR Headset at SXSW 2015 (2015-03-15 14.10.24 by Nan Palmero).jpg",
    "File:Museum of Modern Art Saitama 2010.jpg",
    "File:Marlin Stutzman.jpg",
    "File:Grejsdalen-klipper-1963.jpg",
    "File:Open Source OpenTx Ubuntu (15807299948).jpg",
    "File:Lego bricks.jpg",
    "File:Glitch Firefox on Android phone.png",
    "File:2010년 7월 29일 경기도 용인시 한국소방산업기술원 제16기 소방간부후보생 방문 사진 019 최광모 Kwangmo's iPhone.jpg",
    "File:Metro PCS (14840831066).jpg",
    "File:RD 24 - AN-TPS-80 Ground-Air Task Oriented Radar Stands Forward Deployed in Sakishima Islands (8567784).jpg",
    "File:IGo 90W Universal Laptop Charger tips.jpg",
    "File:Sapphire Radeon 6870 slotblech IMGP3493.jpg",
    "File:Incomplete Graffito.jpg",
    "File:Mark Mowers, Gottéron-Langnau, 15.01.2010.jpg",
    "File:Boost circuit.png",
    "File:Old guitar (photo by Anita Hart).jpg",
    "File:Fischertechnik Baustein.jpg",
    "File:Ikea almhult.jpg",
    "File:WowWee Alive Chimpanzee.jpg",
    "File:Red Cadillac ELR.jpg",
    "File:Cadillac ELR (1).jpg",
    "File:Cadillac ELR (2).jpg",
    "File:Cadillac ELR interior.jpg",
    "File:Unknown Chinese Maker Tin Wind Up Search and Rescue Robot With Detachable Dog Head Jeep Back Side.jpg",
    "File:Boost switching regulator.png",
    "File:Standing figurine holding a quadruped MET DP101694.jpg",
    "File:Tuya Volcanic Field.jpg",
    "File:Samsung Blogger Lounge Party SXSW 2015 (2015-03-15 19.49.07 by Nan Palmero).jpg",
    "File:Billy the Marlin 2011.jpg",
    "File:Feeder mice.jpg",
    "File:KORG Polysix.jpg",
    "File:Samsung Blogger Lounge Party SXSW 2015 DJ (2015-03-15 21.01.31 by Nan Palmero).jpg",
    "File:Marlin Hurt.jpg",
    "File:Quadruped MET ME69 243.jpg",
    "File:Travel Coventry route 13.jpg",
    "File:Klipper dock.png",
    "File:Galaxy Nexus smartphone.jpg",
}

# Manual query overrides: device string -> better Commons queries tried first.
QUERY_OVERRIDES = {
    "Sphero Mini / SPRK+ / BOLT": ["Sphero robot", "Sphero BOLT", "Sphero Ollie"],
    "Sphero RVR / RVR+": ["Sphero RVR", "Sphero robot"],
    "Sphero BB-8 / R2-D2 toys": ["Sphero BB-8 toy", "Sphero robot"],
    "Talking Elmo / singing plush toys": ["Elmo plush toy", "Sesame Street Elmo"],
    "iRobot Roomba 500/600 + Create 2": ["iRobot Roomba", "Roomba vacuum"],
    "Older iRobot Roomba 400/500": ["iRobot Roomba", "Roomba vacuum"],
    "Xiaomi Mi Robot Vacuum V1": ["Xiaomi robot vacuum", "Mi Robot Vacuum"],
    "Roborock S5 Max / S4 Max": ["Roborock vacuum", "Roborock S5"],
    "Dreame D9 (not D9 Max)": ["Dreame vacuum cleaner", "Dreame robot vacuum"],
    "Dreame D9 Pro": ["Dreame vacuum cleaner", "Dreame robot vacuum"],
    "Dreame F9": ["Dreame vacuum cleaner", "Dreame robot vacuum"],
    "Dreame L10 Pro / Z10 Pro": ["Dreame vacuum cleaner", "Dreame robot vacuum"],
    "Current unsupported Roborock / Dreame": ["Roborock vacuum", "robot vacuum cleaner"],
    "Xiaomi 1C / 1T": ["Xiaomi smartphone", "Xiaomi Mi phone"],
    "Xiaomi / Ninebot scooters": ["Xiaomi electric scooter", "Ninebot scooter"],
    "Tuya Beken BK7231 devices": ["Tuya smart switch", "Tuya IoT"],
    "Tuya bulbs / sockets with accessible local keys": ["Tuya smart bulb", "smart bulb"],
    "Philips Hue lights / bridge": ["Philips Hue"],
    "SwitchBot Bot / Curtain / Meter": ["SwitchBot"],
    "Dyson fans / purifiers": ["Dyson fan", "Dyson purifier"],
    "Smart scales / BLE thermometers / toothbrushes": ["digital weighing scale", "bathroom scale"],
    "Motorized blinds / curtains": ["window blinds", "roller blind"],
    "Cheap aquarium feeders / pet feeders": ["pet feeder", "aquarium feeder"],
    "Numerous generic IP cameras": ["IP camera", "surveillance camera"],
    "RTSP/ONVIF existing IP cameras": ["IP camera", "network camera"],
    "Old Android phone / tablet": ["Android tablet", "Android smartphone"],
    "Old Nokia internet tablets / Maemo devices": ["Nokia N900", "Nokia Internet Tablet"],
    "Google Cast-enabled speakers": ["Google Home speaker", "Google Nest speaker"],
    "Korg NTS-1": ["Korg NTS-1"],
    "Korg minilogue xd / prologue": ["Korg minilogue", "Korg synthesizer"],
    "Mutable Instruments Braids / Clouds / Rings": ["Mutable Instruments", "eurorack module"],
    "Critter & Guitari Organelle": ["Organelle synthesizer", "Critter Guitari"],
    "Line 6 / Zoom multi-effects": ["Line 6 guitar effect", "guitar multi effect pedal"],
    "Samsung NX1 / NX500": ["Samsung NX1", "Samsung mirrorless camera"],
    "Modern compatible Wi-Fi routers": ["Wi-Fi router", "wireless router"],
    "Supported ASUS routers": ["Asus router", "Asuswrt router"],
    "FreshTomato compatible routers": ["FreshTomato", "Linksys WRT54G"],
    "OpenWrt travel routers": ["travel router", "OpenWrt router"],
    "Klipper-compatible 3D printers": ["Klipper 3D printer", "3D printer"],
    "GRBL CNC / laser controller boards": ["GRBL CNC", "CNC shield Arduino"],
    "Retired inkjet printers / scanners": ["inkjet printer", "printer mechanism"],
    "Betaflight-compatible FPV flight controllers": ["FPV quadcopter", "Betaflight drone"],
    "OpenTX compatible radio transmitters": ["FrSky Taranis", "RC transmitter"],
    "ExpressLRS radios": ["ExpressLRS", "FPV receiver"],
    "LEGO / toy RC cars with dead controllers": ["LEGO Technic car", "LEGO RC car"],
    "Android phones (supported)": ["Android smartphone"],
    "Privacy-focused supported Android phones": ["GrapheneOS", "Google Pixel phone"],
    "iPhone 7 class": ["iPhone 7"],
    "Supported PCs / ThinkPads": ["ThinkPad laptop"],
    "Supported older laptops": ["ThinkPad X200", "Libreboot laptop"],
    "Supported Chromebooks": ["Chromebook laptop"],
    "Selected ThinkPads": ["ThinkPad laptop"],
    "Supported laptop/mainboard families": ["laptop motherboard", "ThinkPad motherboard"],
    "Supported security-oriented computers": ["Librem laptop", "Purism laptop"],
    "AMD Radeon RX 480 4 GB (some launch units)": ["Radeon RX 480", "AMD graphics card"],
    "Incomplete Rockbox ports": ["Rockbox iPod", "Rockbox player"],
    "OpenMower-supported mower chassis": ["OpenMower", "robotic lawn mower"],
    "Fischertechnik / LEGO WeDo 2.0 BLE controllers": ["Fischertechnik robot", "LEGO WeDo"],
    "LEGO BOOST / Powered Up / Technic hubs": ["LEGO Boost", "LEGO Powered Up"],
    "Old guitar amp with analog footswitch input": ["guitar amplifier"],
    "IKEA TRÅDFRI / DIRIGERA devices": ["IKEA Tradfri", "Tradfri bulb"],
    "Tuya Zigbee sensors / lamps": ["Zigbee smart plug", "Zigbee lamp"],
    "Zigbee / Z-Wave plugs, blinds, buttons": ["Zigbee smart plug", "smart plug"],
    "WowWee MiP": ["MiP robot", "WowWee MiP robot"],
    "WowWee Roboraptor / Roboreptile": ["Roboraptor", "WowWee robot"],
    "WowWee RS Media": ["WowWee RS Media", "WowWee robot"],
    "WowWee CHiP robot dog": ["WowWee CHiP dog", "robot dog toy"],
    "Petoi Bittle X / Nybble Q": ["Petoi robot dog", "Bittle robot"],
    "Dash / Dot educational robots": ["Wonder Workshop", "Dash Wonder Workshop"],
    "Fisher-Price Chatter Telephone": ["Fisher-Price telephone", "Fisher Price toy"],
    "Crazyflie 2.x": ["Crazyflie 2.0", "Bitcraze Crazyflie"],
    "EdgeTX compatible transmitters": ["EdgeTX radio", "EdgeTX"],
    "Duet / RepRapFirmware controllers": ["Duet WiFi", "Duet 3D printer"],
    "Old ESP8266 AT-only modules": ["ESP8266 module", "ESP8266"],
    "Marlin 3D printers": ["3D printer"],
    "Samsung NX1 / NX500": ["Samsung camera", "Samsung NX"],
    "Petoi Bittle / Nybble (legacy)": ["Petoi Bittle dog", "OpenCat quadruped"],
    "Generic Wi-Fi robot vacuums / Tuya OEM": ["robot vacuum cleaner"],
    "Samsung SmartThings appliances": ["SmartThings hub", "Samsung SmartThings"],
    "Xiaomi Dafang / selected Wyze Cam": ["Wyze camera", "Xiaomi Dafang"],
    "Smart TVs with Android TV / Chromecast": ["Android TV", "smart TV"],
    "Sonos compatible network speakers": ["Sonos speaker"],
    "Any Bluetooth A2DP speaker": ["Bluetooth speaker"],
    "Old smart photo frame / Android digital frame": ["digital photo frame"],
    "Vacuum robots with lidar modules": ["robot vacuum lidar", "vacuum robot"],
    "NikonHacker": ["Nikon DSLR", "Nikon camera"],
    "Original Eureka-ROM Chromecast": ["Chromecast"],
    "Free60 Xbox 360 Linux": ["Xbox 360 console"],
    "iPodLinux": ["iPod Linux", "iPod classic"],
    "iDroid / OpeniBoot": ["iPhone 3G", "first iPhone"],
    "Project Sandcastle": ["iPhone 7", "Project Sandcastle"],
    "Xbox 360": ["Xbox 360 console"],
}
DENY = {"vessel","conical","lacma","beylagan","century","kyrkoruin","house","church",
        "ruin","street","school","pdf","djvu","coat of arms","blason","football",
        "basketball","cricket","rugby","tournament","election","parliament"}
BITMAP_EXT = (".jpg", ".jpeg", ".png", ".webp")

# Curated Wikipedia fallbacks for famous items: substring -> enwiki title
WIKI_CURATED = {
    "furby connect": "Furby Connect",
    "anki vector": "Anki (company)",
    "anki cozmo": "Cozmo",
    "roomba": "Roomba",
    "lego mindstorms ev3": "Lego Mindstorms EV3",
    "kinect": "Kinect",
    "raspberry pi pico": "Raspberry Pi",
    "esp32": "ESP32",
    "esp8266": "ESP8266",
}

def api(params, retries=4):
    q = urllib.parse.urlencode(params)
    for attempt in range(retries):
        req = urllib.request.Request(API + "?" + q, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.load(r)
        except Exception as e:
            s = str(e)
            if "429" in s or "500" in s or "timed out" in s.lower():
                time.sleep(5 * (attempt + 1))
                continue
            raise
    raise RuntimeError("API failed after retries: " + q[:120])

def clean_device(dev):
    t = dev.replace("**", "").strip()
    return t

def query_candidates(dev):
    if dev in QUERY_OVERRIDES:
        return QUERY_OVERRIDES[dev][:3]
    t = clean_device(dev)
    parts = [p.strip() for p in t.split("/") if p.strip()]
    cands = []
    for p in parts[:3]:
        p2 = re.sub(r"\([^)]*\)", "", p).strip(" -–—:,;")
        p2 = re.sub(r"\s+", " ", p2)
        if p2:
            cands.append(p2)
    # also brand+first-model fallback: first two words of first candidate,
    # plus single brand word so e.g. "Furby Connect" falls back to "Furby"
    if cands:
        w = cands[0].split()
        lowered = {c.lower() for c in cands}
        if len(w) > 2:
            cands.append(" ".join(w[:2]))
            lowered.add(" ".join(w[:2]).lower())
        if w and len(w[0]) >= 3 and w[0].lower() not in STOP:
            if w[0].lower() not in lowered:
                cands.append(w[0])
                lowered.add(w[0].lower())
        if len(w) >= 2:
            two = " ".join(w[:2])
            if two.lower() not in lowered:
                cands.append(two)
    # dedupe, cap 3
    seen, out = set(), []
    for c in cands:
        if c.lower() not in seen:
            seen.add(c.lower()); out.append(c)
    return out[:3]

def tokens(s):
    out = []
    for t in re.findall(r"[a-z0-9]{3,}", s.lower()):
        if t in STOP:
            continue
        if t.isdigit():
            continue  # bare numbers (600, 360...) match unrelated files
        out.append(t)
    return out

def relevant(title, toks):
    tl = title.lower()
    if not tl.startswith("file:"):
        return False, "not-file"
    if not tl.endswith(BITMAP_EXT):
        return False, "not-bitmap"
    if any(d in tl for d in DENY):
        return False, "denylist"
    hits = sum(1 for t in toks if t in tl)
    need = 1 if len(toks) <= 2 else 2
    if hits >= need:
        return True, f"{hits}/{len(toks)} tokens"
    return False, f"only {hits}/{len(toks)} tokens"

def commons_search(query):
    params = {"action": "query", "format": "json", "formatversion": "2",
              "generator": "search", "gsrsearch": query + " filetype:bitmap",
              "gsrnamespace": "6", "gsrlimit": "10",
              "prop": "imageinfo", "iiprop": "url|extmetadata|size",
              "iiurlwidth": "640"}
    d = api(params)
    return d.get("query", {}).get("pages", []) or []

def strip_html(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    return ihtml.unescape(s).strip()

def pick(pages, toks):
    for p in pages:
        if p.get("title") in EXCLUDE_TITLES:
            continue
        ok, why = relevant(p.get("title", ""), toks)
        if ok:
            return p, why
    return None, "no-relevant"

def small_thumb(url):
    # Thumbor-style stable pattern: .../thumb/<h>/<name>/NNNpx-<name>
    # 320px is plenty for the 96px card display and downloads far faster.
    m = re.search(r"(.*/)(\d+)px-", url or "")
    if m:
        return url.replace("/%spx-" % m.group(2), "/320px-", 1)
    return url

def file_path_url(title, width=320):
    # Officially recommended thumbnail route: redirects to a scaled thumb
    # on the (unthrottled) thumb cluster. Never download originals directly:
    # upload.wikimedia.org answers those with HTTP 429.
    name = (title or "").split(":", 1)[-1].replace(" ", "_")
    return "https://commons.wikimedia.org/wiki/Special:FilePath/%s?width=%d" % (
        urllib.parse.quote(name), width)

def download(url, dest, title=""):
    # Prefer the API's scaled thumb; fall back to the direct file URL.
    # (Special:FilePath is throttled; originals may 429 during bursts,
    #  hence the explicit 429 backoff below plus magic-byte validation.)
    url = small_thumb((url or "").split("?")[0])
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
                f.write(r.read())
            head = open(dest, "rb").read(12)
            magic = (head[:2] == b"\xff\xd8" or head[:8] == b"\x89PNG\r\n\x1a\n"
                     or head[:4] in (b"RIFF", b"GIF8"))
            if magic and os.path.getsize(dest) > 2048:
                return True
        except urllib.error.HTTPError as e:
            if getattr(e, "code", None) == 429:
                time.sleep(60)
                continue
            time.sleep(10)
        except Exception:
            time.sleep(10)
    try:
        if os.path.exists(dest):
            os.remove(dest)
    except OSError:
        pass
    return False

def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return (s[:50] or "img")

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    full = open("list", encoding="utf-8").read()
    catsec = full.split("## The catalog")[1].split("## Tools")[0]
    devs = []
    for line in catsec.splitlines():
        if line.startswith("| ") and "Device / project" not in line and "---" not in line:
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            devs.append(re.sub(r"\*", "", parts[0]).strip())
    uniq = []
    for d in devs:
        if d not in uniq:
            uniq.append(d)
    print(f"unique devices: {len(uniq)} / rows {len(devs)}")
    cache = {}
    if os.path.exists(CACHE):
        cache = json.load(open(CACHE, encoding="utf-8"))
    manifest = {}
    if os.path.exists(MANIFEST):
        try:
            manifest = {m["device"]: m for m in json.load(open(MANIFEST, encoding="utf-8"))}
        except Exception:
            manifest = {}
    # reuse already-downloaded files when several devices share one Commons title
    title_to_file = {m.get("title"): m.get("file") for m in manifest.values()
                     if m.get("status") == "ok" and m.get("file")
                     and os.path.exists(os.path.join(OUTDIR, m["file"]))}
    found = missing = 0
    for i, dev in enumerate(uniq):
        cur = manifest.get(dev)
        if cur and cur.get("checked_v") == CHECK_V and cur.get("status") == "ok" \
                and cur.get("file") and os.path.exists(os.path.join(OUTDIR, cur["file"])):
            found += 1
            continue
        if cur and cur.get("checked_v") == CHECK_V and cur.get("status") == "missing":
            missing += 1
            continue
        cands = query_candidates(dev)
        entry = None
        reason = ""
        for q in cands:
            ck = "commons:" + q.lower()
            if ck not in cache:
                try:
                    cache[ck] = commons_search(q)
                except Exception as e:
                    reason = f"api-error {e}"
                    break
                time.sleep(PAUSE)
            pages = cache[ck]
            p, why = pick(pages, tokens(q))
            if p:
                entry = (p, q, why)
                break
            reason = f"q={q!r}: {why}"
        if entry:
            p, qused, why = entry
            ii = (p.get("imageinfo") or [{}])[0]
            thumb = ii.get("thumburl") or ii.get("url")
            meta = ii.get("extmetadata") or {}
            lic = strip_html((meta.get("LicenseShortName") or {}).get("value", "")) or "ks. Commons-sivu"
            licurl = strip_html((meta.get("LicenseUrl") or {}).get("value", ""))
            artist = strip_html((meta.get("Artist") or {}).get("value", ""))
            credit = strip_html((meta.get("Credit") or {}).get("value", "")) or artist
            ext = ".jpg"
            m = re.search(r"\.(jpe?g|png|webp|gif)(?:\s|$)", (p.get("title") or "").lower())
            if m:
                ext = "." + m.group(1)
                if ext == ".jpeg":
                    ext = ".jpg"
            fname = title_to_file.get(p.get("title"))
            if fname:
                manifest[dev] = {"device": dev, "status": "ok", "checked_v": CHECK_V,
                    "query": qused, "match": why, "title": p.get("title"),
                    "file": fname, "thumb_url": thumb,
                    "page_url": ii.get("descriptionurl", ""),
                    "license": lic, "license_url": licurl,
                    "artist": artist[:200], "credit": credit[:200],
                    "shared": True}
                found += 1
                print(f"[{i+1}/{len(uniq)}] SHARE {dev!r} <- {p.get('title')}")
            else:
                fname = f"{i+1:03d}-{slug(qused)}{ext}"
                if thumb and download(thumb, os.path.join(OUTDIR, fname),
                                      title=p.get("title")):
                    title_to_file[p.get("title")] = fname
                    manifest[dev] = {"device": dev, "status": "ok", "checked_v": CHECK_V,
                        "query": qused, "match": why, "title": p.get("title"),
                        "file": fname, "thumb_url": thumb,
                        "page_url": ii.get("descriptionurl", ""),
                        "license": lic, "license_url": licurl,
                        "artist": artist[:200], "credit": credit[:200]}
                    found += 1
                    print(f"[{i+1}/{len(uniq)}] OK {dev!r} <- {p.get('title')} ({why})")
                else:
                    if fname and os.path.exists(os.path.join(OUTDIR, fname)):
                        try: os.remove(os.path.join(OUTDIR, fname))
                        except OSError: pass
                    manifest[dev] = {"device": dev, "status": "missing",
                                     "checked_v": CHECK_V,
                                     "reason": "download-error/too-small"}
                    missing += 1
                    print(f"[{i+1}/{len(uniq)}] DL-FAIL {dev!r}")
        else:
            manifest[dev] = {"device": dev, "status": "missing", "checked_v": CHECK_V,
                             "reason": reason or "no-relevant", "queries": cands}
            missing += 1
            print(f"[{i+1}/{len(uniq)}] MISSING {dev!r} ({reason})")
        if i % 10 == 0:
            json.dump(cache, open(CACHE, "w", encoding="utf-8"))
            json.dump(list(manifest.values()), open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        time.sleep(0.2)
    json.dump(cache, open(CACHE, "w", encoding="utf-8"))
    json.dump(list(manifest.values()), open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ok = sum(1 for m in manifest.values() if m.get("status") == "ok")
    miss = sum(1 for m in manifest.values() if m.get("status") != "ok")
    print(f"DONE unique ok={ok} missing={miss}")

if __name__ == "__main__":
    main()
