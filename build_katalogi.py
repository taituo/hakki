#!/usr/bin/env python3
"""Build katalogi.html from list file. Run in /home/tiny/projects/häkki."""
import re, json, html, urllib.parse, os

SRC = "list"
DST = "katalogi.html"

full = open(SRC, encoding="utf-8").read()
catsec = full.split("## The catalog")[1].split("## Tools")[0]

CAT_META = {}  # letter -> title
items = []
cur = None; curtitle = ""
for line in catsec.splitlines():
    m = re.match(r"### ([A-K])\.\s*(.*)", line)
    if m:
        cur = m.group(1); curtitle = m.group(2).strip()
        CAT_META[cur] = curtitle
        continue
    if line.startswith("| ") and "Device / project" not in line and "---" not in line:
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if len(parts) >= 6:
            items.append({"cat": cur, "device": parts[0], "route": parts[1].replace("`",""),
                          "what": parts[2], "effort": parts[3], "role": parts[4], "linkmd": parts[5]})

def md_link(md):
    m = re.search(r"\[([^\]]*)\]\((https?[^)]+)\)", md)
    if m: return m.group(1).strip() or "Lähde", m.group(2).strip()
    return "Lähde", ""

def md_text(md):
    # strip markdown emphasis, keep readable text
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", md)
    t = re.sub(r"\*(.+?)\*", r"\1", t)
    t = re.sub(r"`(.+?)`", r"\1", t)
    return t.strip()

EMOJI = {"A":"🧸","B":"🤖","C":"🏠","D":"👁️","E":"🎹","F":"📸","G":"🌐","H":"🚁","I":"🎮","J":"💻","K":"📜"}

data = []
for i, it in enumerate(items):
    label, url = md_link(it["linkmd"])
    route_letters = sorted(set(re.findall(r"[SFHE]", it["route"])))
    m = re.match(r"(\d)/5", it["effort"])
    diff = int(m.group(1)) if m else 0
    role_tokens = [t.strip().lower() for t in it["role"].split("+")]
    data.append({
        "id": i+1,
        "cat": it["cat"],
        "cat_title": CAT_META[it["cat"]],
        "device": md_text(it["device"]),
        "route": it["route"],
        "route_letters": route_letters,
        "what": md_text(it["what"]),
        "effort": it["effort"],
        "diff": diff,
        "role": md_text(it["role"]),
        "role_tokens": role_tokens,
        "url": url,
        "emoji": EMOJI.get(it["cat"], "🔧"),
    })

# Use only cached, relevant Wikimedia Commons images with saved attribution.
# Missing matches stay clearly marked as placeholders.
image_manifest = {}
try:
    with open("assets/commons/images.json", encoding="utf-8") as f:
        image_manifest = {x.get("device"): x for x in json.load(f)}
except (OSError, ValueError):
    pass
for item in data:
    image = image_manifest.get(item["device"], {})
    image_path = image.get("file", "")
    if image.get("status") == "ok" and image_path and os.path.isfile(os.path.join("assets/commons", image_path)):
        item["image"] = "assets/commons/" + image_path
        item["image_title"] = image.get("title", "Wikimedia Commons")
        item["image_page"] = image.get("page_url", "")
        item["image_license"] = image.get("license", "Lisenssi tarkistettava lähdesivulta")
        item["image_artist"] = image.get("artist", "")
    else:
        item.update(image="", image_title="", image_page="", image_license="", image_artist="")

image_rows = sum(bool(x["image"]) for x in data)
image_devices = len({x["device"] for x in data if x["image"]})

# role base options present in data
roles_base = sorted({t for d in data for t in d["role_tokens"]})

js_data = json.dumps(data, ensure_ascii=False)
js_cats = json.dumps(CAT_META, ensure_ascii=False)
js_roles = json.dumps(roles_base, ensure_ascii=False)

page = """<!DOCTYPE html>
<html lang="fi" data-theme="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Häkki — Hackable Everything -katalogi (208 laitetta)</title>
<style>
:root{--bg:#f6f4ee;--card:#ffffff;--ink:#1d1b16;--muted:#6b655a;--line:#e4ddcf;--acc:#b3541e;--acc2:#1e6f5c;--badge:#efe9db;--shadow:0 2px 10px rgba(30,25,15,.08)}
[data-theme="dark"]{--bg:#141310;--card:#1e1c17;--ink:#f0e9da;--muted:#b3a88f;--line:#38322a;--acc:#f0a35e;--acc2:#5fd0ae;--badge:#2a261f;--shadow:0 2px 12px rgba(0,0,0,.5)}
[data-theme="contrast"]{--bg:#ffffff;--card:#ffffff;--ink:#000;--muted:#333;--line:#000;--acc:#005fcc;--acc2:#007a3d;--badge:#eef4ff;--shadow:none}
[data-theme="play"]{--bg:#fff7ed;--card:#fff;--ink:#3b1d5e;--muted:#7a5淳99}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans",sans-serif}
header{position:sticky;top:0;z-index:5;background:var(--card);border-bottom:1px solid var(--line);padding:14px 18px}
.wrap{max-width:1200px;margin:0 auto;padding:0 18px 60px}
h1{font-size:1.5rem;margin:.2em 0 .1em}
.sub{color:var(--muted);font-size:.95rem;max-width:70ch}
.toolbar{display:grid;gap:10px;margin:16px 0}
.panel{background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);padding:14px}
.row{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
input[type=search],select{background:var(--bg);color:var(--ink);border:1px solid var(--line);border-radius:10px;padding:9px 12px;font-size:.95rem}
input[type=search]{flex:1;min-width:220px}
label{font-size:.85rem;color:var(--muted)}
.chipset{display:flex;flex-wrap:wrap;gap:6px}
.chip{border:1px solid var(--line);background:var(--bg);border-radius:999px;padding:4px 10px;font-size:.83rem;cursor:pointer;user-select:none}
.chip[aria-pressed=true]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.btn{border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:10px;padding:8px 12px;cursor:pointer;font-size:.9rem}
.btn.primary{background:var(--acc);border-color:var(--acc);color:#fff}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;margin-top:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:var(--shadow);display:flex;flex-direction:column}
.illus{display:flex;align-items:center;gap:12px;padding:14px;border-bottom:1px dashed var(--line);background:linear-gradient(180deg,transparent,rgba(127,127,127,.08))}
.product-img{width:96px;height:76px;object-fit:contain;background:#fff;border:1px solid var(--line);border-radius:10px;flex:none}
.emo{font-size:2.4rem;line-height:1;flex:none;width:64px;height:64px;display:grid;place-items:center;border-radius:14px;background:var(--badge);border:1px solid var(--line)}
.illus small{color:var(--muted)}
.body{padding:12px 14px;display:flex;flex-direction:column;gap:8px;flex:1}
.badges{display:flex;flex-wrap:wrap;gap:6px;font-size:.75rem}
.b{background:var(--badge);border:1px solid var(--line);border-radius:999px;padding:2px 9px}
.b.route{font-weight:700}
.desc{font-size:.92rem}
.meta{font-size:.8rem;color:var(--muted)}
.links{margin-top:auto;display:flex;flex-wrap:wrap;gap:8px;padding-top:6px}
.links a{font-size:.85rem;color:var(--acc2)}
.count{font-weight:700}
footer{color:var(--muted);font-size:.85rem;margin-top:22px}
.skip{position:absolute;left:-999px}
.themes{display:flex;gap:6px;flex-wrap:wrap}
details{font-size:.9rem;color:var(--muted)}
</style>
</head>
<body>
<header><div class="wrap" style="padding:0">
<h1>🧰 Häkki — Hackable Everything -katalogi</h1>
<div class="sub">208 laiteriviä <em>list</em>-tiedostosta. ${image_devices} laitemallille löytyi paikallinen Wikimedia Commons -kuva; muissa korteissa näkyy kuvapaikkamerkki ja kuvahaku. Kuvaukset ja lähdelinkit säilytetty alkuperäisestä. Teemat + suodattimet + haku toimivat offline.</div>
</div></header>
<div class="wrap">
<div class="toolbar">
<div class="panel">
<div class="row">
<input id="q" type="search" placeholder="Haku: esim. Furby, Roomba, ESP32, Valetudo…" aria-label="Haku">
<select id="sort" aria-label="Järjestys">
<option value="cat">Järjestys: kategoria + nimi</option>
<option value="diff-asc">Vaikeus: helpoin ensin</option>
<option value="diff-desc">Vaikeus: vaikein ensin</option>
<option value="name">Nimi A–Ö</option>
</select>
<button class="btn" id="reset">Tyhjennä</button>
</div>
<div class="row" style="margin-top:10px">
<div class="themes" role="group" aria-label="Teema">
<label>Teema:</label>
<button class="btn" data-t="auto">☀️ Vaalea</button>
<button class="btn" data-t="dark">🌙 Tumma</button>
<button class="btn" data-t="contrast">🔲 Kontrasti</button>
</div>
<div><span class="count" id="count"></span> <span id="hint"></span></div>
</div>
</div>
<div class="panel">
<div class="row"><label>Kategoria</label><select id="fcat"><option value="">Kaikki (A–K)</option></select></div>
<div class="row" style="margin-top:8px"><label>Reitti:</label><div class="chipset" id="routes"></div></div>
<div class="row" style="margin-top:8px"><label>Vaikeus:</label><div class="chipset" id="diffs"></div></div>
<div class="row" style="margin-top:8px"><label>Kehorooli:</label><div class="chipset" id="roles"></div></div>
<details style="margin-top:8px"><summary>Reittien selitykset (S/F/H/E)</summary>
S = ohjelmisto (app/API/BLE/IR/serial, vakiofirmis säilyy) · F = vaihtoehtofirmis/jailbreak · H = hardware (avaa, juota, UART/JTAG, mikrokontrolleri) · E = kokeellinen/epävarma reitti. Vaikeus 1 aloittelija … 5 spesialisti. Kehorooli: laitteen paras rooli kehona (face/voice/mobile/arm/sensor/ambient/mechanism/platform/none).</details>
</div>
</div>
<div class="grid" id="grid"></div>
<footer>
<p><strong>Kuvat:</strong> ${image_devices} / 203 yksilöllisestä laitemallista on paikallinen Commons-kuva; ${203-image_devices} jäi ilman varmennettua osumaa ja näytetään paikkamerkkinä. Kortti kertoo kuvan tekijän, lisenssin ja lähdesivun. Käytä kuvia ilmoitetun lisenssin ehdoilla. Muut kortit tarjoavat Wikimedia- ja Openverse-haut.</p>
<p>Lähde: paikallinen <code>list</code>-tiedosto (12.10.2026). Tätä HTML:ää voi teemata yllä olevilla napeilla; valinta tallentuu selaimeen.</p>
</footer>
</div>
<script>
const DATA = __DATA__;
const CATS = __CATS__;
const ROLEBASE = __ROLES__;
const $ = s => document.querySelector(s);
const state = {q:"",cat:"",routes:new Set(),diffs:new Set(),roles:new Set(),sort:"cat"};
// theme
const root=document.documentElement;
const saved=localStorage.getItem("hakki-theme"); if(saved) root.dataset.theme=saved;
document.querySelectorAll("[data-t]").forEach(b=>b.onclick=()=>{root.dataset.theme=b.dataset.t;localStorage.setItem("hakki-theme",b.dataset.t);});
// build filters
const fcat=$("#fcat");
Object.entries(CATS).forEach(([k,v])=>{const o=document.createElement("option");o.value=k;o.textContent=k+". "+v;fcat.appendChild(o);});
function chips(el,vals,store){vals.forEach(v=>{const c=document.createElement("button");c.className="chip";c.textContent=v;c.setAttribute("aria-pressed","false");c.onclick=()=>{const on=c.getAttribute("aria-pressed")==="true";c.setAttribute("aria-pressed",String(!on));if(!on)store.add(v);else store.delete(v);render();};el.appendChild(c);});}
chips($("#routes"),["S","F","H","E"],state.routes);
chips($("#diffs"),["1","2","3","4","5"],state.diffs);
chips($("#roles"),ROLEBASE,state.roles);
$("#q").oninput=e=>{state.q=e.target.value.toLowerCase();render();};
fcat.onchange=e=>{state.cat=e.target.value;render();};
$("#sort").onchange=e=>{state.sort=e.target.value;render();};
$("#reset").onclick=()=>{state.q="";state.cat="";state.routes.clear();state.diffs.clear();state.roles.clear();$("#q").value="";fcat.value="";document.querySelectorAll(".chip").forEach(c=>c.setAttribute("aria-pressed","false"));render();};
function match(d){
 if(state.cat&&d.cat!==state.cat)return false;
 if(state.routes.size&&![...state.routes].some(r=>d.route_letters.includes(r)))return false;
 if(state.diffs.size&&!state.diffs.has(String(d.diff)))return false;
 if(state.roles.size&&![...state.roles].some(r=>d.role_tokens.includes(r)))return false;
 if(state.q){const hay=(d.device+" "+d.what+" "+d.role+" "+d.route+" "+d.cat_title).toLowerCase();if(!state.q.split(/\\s+/).every(w=>hay.includes(w)))return false;}
 return true;
}
function card(d){
 const w=encodeURIComponent(d.device);
 return `<article class="card">
 <div class="illus">${d.image?`<img class="product-img" src="${esc(d.image)}" alt="${esc(d.device)} — ${esc(d.image_title)}" loading="lazy">`:`<div class="emo">${d.emoji}</div>`}<div><strong>${d.cat}. ${esc(d.cat_title).slice(0,60)}</strong><br><small>${d.image?`📷 Commons-kuva: ${esc(d.image_title)}`:`🖼️ Ei varmennettua paikallista laitekuvaa — kuvituspaikka.`}</small></div></div>
 <div class="body">
 <div><strong>#${d.id} ${esc(d.device)}</strong></div>
 <div class="badges"><span class="b route">${esc(d.route)}</span><span class="b">Vaikeus ${esc(d.effort)}</span><span class="b">${esc(d.role)}</span><span class="b">Kat. ${esc(d.cat)}</span></div>
 <div class="desc">${esc(d.what)}</div>
 <div class="links">
 ${d.url?`<a href="${esc(d.url)}" target="_blank" rel="noopener">📖 Projekti / docs ↗</a>`:`<span class="meta">Ei lähdelinkkiä</span>`}
 <a href="https://commons.wikimedia.org/w/index.php?search=${w}&title=Special:MediaSearch&type=image" target="_blank" rel="noopener">🖼️ Wikimedia-haku ↗</a>
 <a href="https://openverse.org/search/image?q=${w}" target="_blank" rel="noopener">🖼️ Openverse-haku ↗</a>
 </div>
 <div class="meta">${d.image?`Kuvan tekijä: ${esc(d.image_artist||"Commons-tiedot")}; lisenssi: ${esc(d.image_license)}. <a href="${esc(d.image_page)}" target="_blank" rel="noopener">Kuvan lähde ↗</a>`:`Kuvaa ei löytynyt varmennetusta lähteestä; avaa kuvahaku alta.`} Kuvaus säilytetty list-tiedostosta.</div>
 </div></article>`;
}
function esc(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function render(){
 let arr=DATA.filter(match);
 if(state.sort==="name")arr.sort((a,b)=>a.device.localeCompare(b.device,"fi"));
 else if(state.sort==="diff-asc")arr.sort((a,b)=>a.diff-b.diff||a.device.localeCompare(b.device,"fi"));
 else if(state.sort==="diff-desc")arr.sort((a,b)=>b.diff-a.diff||a.device.localeCompare(b.device,"fi"));
 else arr.sort((a,b)=>a.cat.localeCompare(b.cat)||a.device.localeCompare(b.device,"fi"));
 $("#grid").innerHTML=arr.map(card).join("");
 $("#count").textContent=`Näytetään ${arr.length} / ${DATA.length}`;
 $("#hint").textContent=arr.length===0?"— ei osumia, tyhjennä suodattimet.":"";
}
render();
</script>
</body>
</html>
"""

# fix accidental corrupted css line from drafting
page = page.replace("--muted:#7a5淳99}", "--muted:#7a5f8a}")
page = page.replace("__DATA__", js_data).replace("__CATS__", js_cats).replace("__ROLES__", js_roles)
page = page.replace("${image_devices}", str(image_devices)).replace("${203-image_devices}", str(203 - image_devices))
open(DST, "w", encoding="utf-8").write(page)
print(f"wrote {DST}: {len(data)} items, {len(page)//1024} KB")
