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
<html lang="en" data-theme="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HÄKKI // Hackable Everything — 208 devices</title>
<style>
:root{--bg:#e9e4d4;--paper:#faf7ee;--ink:#1a1814;--muted:#6f675a;--line:#ddd4bf;--acc:#9a3b1e;--acc2:#1e6f5c;--rule:#1a1814;--badge:#f0ebdb;--shadow:none}
[data-theme="dark"]{--bg:#0f0e0b;--paper:#171612;--ink:#ece4d2;--muted:#a89d86;--line:#3a342a;--acc:#f0a35e;--acc2:#5fd0ae;--rule:#ece4d2;--badge:#24211b}
[data-theme="contrast"]{--bg:#fff;--paper:#fff;--ink:#000;--muted:#222;--line:#000;--acc:#005fcc;--acc2:#007a3d;--rule:#000;--badge:#eef4ff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans",sans-serif;-webkit-font-smoothing:antialiased}
.paper{background:var(--paper);padding:0 clamp(14px,3vw,44px) 60px;min-height:100vh}
.masthead{text-align:center;padding:26px 0 0}
.masthead .source{font-size:.78rem;letter-spacing:.35em;text-transform:uppercase;color:var(--muted);margin:0}
.masthead h1{font-size:clamp(2.6rem,8vw,4.2rem);margin:.08em 0 .1em;font-weight:900;letter-spacing:-.02em;line-height:1}
.rule-thick{border:0;border-top:4px solid var(--rule);margin:12px 0 0}
.rule-thin{border:0;border-top:1px solid var(--rule);margin:3px 0 0}
.edition{display:flex;justify-content:space-between;gap:6px 14px;flex-wrap:wrap;font-size:.8rem;padding:8px 2px;color:var(--muted)}
.edition strong{color:var(--ink)}
.lede{font-size:.95rem;color:var(--muted);text-align:center;max-width:60ch;margin:10px auto 0}
.toolbar{position:sticky;top:0;z-index:5;background:var(--paper);padding:12px 0;border-bottom:1px solid var(--line)}
.panel{background:var(--paper);border:1px solid var(--line);padding:12px}
.row{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
input[type=search],select{background:var(--paper);color:var(--ink);border:1px solid var(--line);padding:9px 12px;font-size:.95rem;font-family:inherit}
input[type=search]{flex:1;min-width:200px}
label{font-size:.82rem;color:var(--muted)}
.chipset{display:flex;flex-wrap:wrap;gap:6px}
.chip{border:1px solid var(--line);background:var(--paper);color:var(--ink);padding:4px 10px;font-size:.83rem;cursor:pointer;user-select:none;font-family:inherit}
.chip[aria-pressed=true]{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.btn{border:1px solid var(--line);background:var(--paper);color:var(--ink);padding:8px 12px;cursor:pointer;font-size:.9rem;font-family:inherit}
.count{font-weight:700}
article.story{padding:15px 0;border-bottom:1px solid var(--line);break-inside:avoid}
.feed{columns:255px;column-gap:20px}
.story-meta{font-size:.66rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:0 0 5px}
.story h2{font-size:1.08rem;line-height:1.25;margin:0 0 8px;font-weight:800;letter-spacing:-.01em}
.story img{width:100%;height:auto;display:block;border:1px solid var(--line);background:#fff}
.cap{font-size:.7rem;color:var(--muted);margin:5px 0 0}
.ph{border:1px dashed var(--line);padding:18px 12px;text-align:center;color:var(--muted)}
.ph .big{font-size:2rem}
.copy{font-size:.83rem;line-height:1.5;margin:8px 0}
.links{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:.78rem}
.links a{color:var(--acc2)}
#sentinel{padding:26px 0 10px;text-align:center;color:var(--muted);font-size:.9rem}
footer{color:var(--muted);font-size:.85rem;margin-top:26px;border-top:4px solid var(--rule);padding-top:14px}
.themes{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
details{font-size:.9rem;color:var(--muted)}
</style>
<link rel="stylesheet" href="hacker-ui.css">
</head>
<body>
<div class="paper">
<header class="masthead">
<p class="source">OPEN DEVICE INTELLIGENCE // FIELD GUIDE</p>
<h1>HÄKKI<span class="cursor" aria-hidden="true">_</span></h1>
<hr class="rule-thick"><hr class="rule-thin">
<div class="edition">
<span><strong>ARCHIVE / VOL. 01</strong></span>
<span>12 October 2026</span>
<span><strong>${image_devices}</strong> images / 208 devices</span>
</div>
<hr class="rule-thin"><hr class="rule-thick">
<p class="lede">Robots, toys, vacuums, household devices, and forgotten electronics. Explore 208 moddable machines with original project descriptions, documentation links, and locally cached images. Filter the archive. Find your next target.</p>
</header>
<div class="toolbar">
<div class="panel">
<div class="row">
<input id="q" type="search" placeholder="Search devices / Furby, Roomba, ESP32, Valetudo... (press /)" aria-label="Search devices">
<select id="sort" aria-label="Sort order">
<option value="cat">Sort: category + name</option>
<option value="diff-asc">Difficulty: easiest first</option>
<option value="diff-desc">Difficulty: hardest first</option>
<option value="name">Name A–Z</option>
</select>
<button class="btn" id="reset">Clear filters</button>
</div>
<div class="row" style="margin-top:10px">
<div class="themes" role="group" aria-label="Color palette">
<label>Palette:</label>
<button class="btn" data-t="auto">◉ Phosphor</button>
<button class="btn" data-t="dark">◈ Midnight</button>
<button class="btn" data-t="contrast">◻ Contrast</button>
</div>
<div><span class="count" id="count"></span> <span id="hint"></span></div>
</div>
</div>
<div class="panel">
<div class="row"><label>Category</label><select id="fcat"><option value="">All sectors (A–K)</option></select></div>
<div class="row" style="margin-top:8px"><label>Access route:</label><div class="chipset" id="routes"></div></div>
<div class="row" style="margin-top:8px"><label>Difficulty:</label><div class="chipset" id="diffs"></div></div>
<div class="row" style="margin-top:8px"><label>Body role:</label><div class="chipset" id="roles"></div></div>
<details style="margin-top:8px"><summary>How access routes work (S/F/H/E)</summary>
S = software (app/API/BLE/IR/serial, stock firmware remains). F = alternative firmware or jailbreak. H = hardware (open, solder, UART/JTAG, microcontrollers). E = experimental or unverified route. Difficulty: 1 = beginner, 5 = specialist. Body role = best use of the device as an interactive body (face/voice/mobile/arm/sensor/ambient/mechanism/platform/none).</details>
</div>
</div>
<div class="feed" id="grid"></div>
<div id="sentinel" aria-live="polite"></div>
<footer>
<p><strong>Images:</strong> ${image_devices} / 203 unique device models have a locally stored Commons image; ${203-image_devices} have no verified image and display a placeholder. Each image credits its author, license and source. Reuse images only under their stated licenses; missing images have a search link.</p>
<p>Source: local <code>list</code> file (12 October 2026). The interface works offline with the original image assets. Palette and density choices are stored in your browser.</p>
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
 const img=d.image
  ?`<img src="${esc(d.image)}" alt="${esc(d.device)} — ${esc(d.image_title)}" loading="lazy" decoding="async">
    <p class="cap">${esc(d.image_title)} · ${esc(d.image_artist||"Commons")} (${esc(d.image_license)}) <a href="${esc(d.image_page)}" target="_blank" rel="noopener">source ↗</a></p>`
  :`<div class="ph"><div class="big">${d.emoji}</div></div>`;
 const extra=d.image?"":` <a href="https://commons.wikimedia.org/w/index.php?search=${w}&title=Special:MediaSearch&type=image" target="_blank" rel="noopener">🔍 image search ↗</a>`;
 return `<article class="story">
 <p class="story-meta">#${d.id} · ${esc(d.cat_title)} · ${esc(d.route)} · ${esc(d.effort)} · ${esc(d.role)}</p>
 <h2>${esc(d.device)}</h2>
 ${img}
 <p class="copy">${esc(d.what)}</p>
 <div class="links">
 ${d.url?`<a href="${esc(d.url)}" target="_blank" rel="noopener">↗ Project / docs</a>`:`<span>No source link</span>`}${extra}
 </div>
 </article>`;
}
function esc(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
const PAGE=15;
let list=[], shown=0;
const sentinel=$("#sentinel");
function render(){
 list=DATA.filter(match);
 if(state.sort==="name")list.sort((a,b)=>a.device.localeCompare(b.device,"en"));
 else if(state.sort==="diff-asc")list.sort((a,b)=>a.diff-b.diff||a.device.localeCompare(b.device,"en"));
 else if(state.sort==="diff-desc")list.sort((a,b)=>b.diff-a.diff||a.device.localeCompare(b.device,"en"));
 else list.sort((a,b)=>a.cat.localeCompare(b.cat)||a.device.localeCompare(b.device,"en"));
 shown=0;
 $("#grid").innerHTML="";
 appendMore();
}
function appendMore(){
 const next=list.slice(shown,shown+PAGE);
 if(next.length){
  $("#grid").insertAdjacentHTML("beforeend",next.map(card).join(""));
  shown+=next.length;
 }
 if(list.length===0){
  $("#count").textContent="No matches";
  $("#hint").textContent="— change or clear filters.";
  sentinel.textContent="";
 }else{
  $("#count").textContent=`Showing ${shown} / ${list.length}`;
  $("#hint").textContent="";
  sentinel.textContent=shown<list.length?"Scroll to load more devices...":"— End of index —";
 }
}
new IntersectionObserver(es=>{if(es[0].isIntersecting)appendMore();},{rootMargin:"600px"}).observe(sentinel);
render();
</script>
<script src="hacker-ui.js"></script>
</body>
</html>
"""

# fix accidental corrupted css line from drafting
page = page.replace("--muted:#7a5淳99}", "--muted:#7a5f8a}")
page = page.replace("__DATA__", js_data).replace("__CATS__", js_cats).replace("__ROLES__", js_roles)
page = page.replace("${image_devices}", str(image_devices)).replace("${203-image_devices}", str(203 - image_devices))
open(DST, "w", encoding="utf-8").write(page)
print(f"wrote {DST}: {len(data)} items, {len(page)//1024} KB")
