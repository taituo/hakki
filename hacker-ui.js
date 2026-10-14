/* HÄKKI enhancement layer — runs AFTER the original inline catalog code.
   Keeps original search/filter/sort/infinite-scroll behavior intact. */
(() => {
  "use strict";
  const $ = (query, parent = document) => parent.querySelector(query);
  const root = document.documentElement;
  const grid = $("#grid");
  const toolbar = $(".toolbar");
  const header = $(".masthead");
  if (!grid || !toolbar || !header) return;

  const status = document.createElement("div");
  status.className = "sysbar";
  status.innerHTML = '<span><i class="dot" aria-hidden="true"></i><strong>SYS ONLINE</strong></span><span>OPEN HARDWARE / OPEN KNOWLEDGE</span><span class="right">PUBLIC ACCESS · LOCAL IMAGE CACHE</span>';
  header.prepend(status);

  const heading = document.createElement("div");
  heading.className = "index-heading";
  heading.innerHTML = '<div><div class="eyebrow">// QUERY RESULTS</div><h2>DEVICE INDEX<span aria-hidden="true" style="color:var(--acc)">.</span></h2></div><div class="index-meta" id="query-status" aria-live="polite">DATABASE READY</div>';
  toolbar.after(heading);

  function restorePreference(key) {
    try { return localStorage.getItem(key); } catch (_) { return null; }
  }
  function savePreference(key, value) {
    try { localStorage.setItem(key, value); } catch (_) { /* private-mode safe */ }
  }

  const themes = $(".themes");
  if (themes) {
    const themeButtons = [...themes.querySelectorAll("[data-t]")];
    const syncTheme = () => themeButtons.forEach(button => button.setAttribute("aria-pressed", String(root.dataset.theme === button.dataset.t)));
    themeButtons.forEach(button => button.addEventListener("click", syncTheme));
    syncTheme();

    const density = document.createElement("button");
    density.className = "btn";
    density.type = "button";
    density.textContent = "⊞ COMPACT";
    density.title = "Switch between normal and compact card layouts";
    density.setAttribute("aria-label", "Toggle compact card layout");
    const initialCompact = restorePreference("hakki-compact") === "true";
    document.body.classList.toggle("compact", initialCompact);
    density.setAttribute("aria-pressed", String(initialCompact));
    density.addEventListener("click", () => {
      const value = document.body.classList.toggle("compact");
      density.setAttribute("aria-pressed", String(value));
      savePreference("hakki-compact", String(value));
    });
    themes.append(density);
  }

  const randomButton = document.createElement("button");
  randomButton.className = "btn";
  randomButton.type = "button";
  randomButton.textContent = "↗ RANDOM TARGET";
  randomButton.title = "Pick one device from the current filter results";
  randomButton.addEventListener("click", () => {
    if (typeof DATA === "undefined" || typeof match !== "function") return;
    const possible = DATA.filter(match);
    if (!possible.length) return;
    const device = possible[Math.floor(Math.random() * possible.length)];
    const reset = $("#reset");
    if (reset) reset.click();
    const search = $("#q");
    search.value = device.device;
    search.dispatchEvent(new Event("input", { bubbles: true }));
    heading.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  const topRow = $(".panel .row", toolbar);
  if (topRow) topRow.append(randomButton);

  const q = $("#q");
  document.addEventListener("keydown", event => {
    const tag = event.target && event.target.tagName;
    if ((event.key === "/" && !event.altKey && !event.metaKey && !event.ctrlKey && !["INPUT", "TEXTAREA", "SELECT"].includes(tag)) || ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k")) {
      event.preventDefault();
      q?.focus();
      q?.select();
    }
    if (event.key === "Escape" && document.activeElement === q) {
      q.value = "";
      q.dispatchEvent(new Event("input", { bubbles: true }));
      q.blur();
    }
  });

  // Decorate newly streamed cards without altering original catalog data.
  function decorateCards() {
    const records = typeof DATA !== "undefined" ? DATA : [];
    const byId = new Map(records.map(item => [String(item.id), item]));
    for (const card of grid.querySelectorAll("article.story:not([data-hacker-card])")) {
      card.dataset.hackerCard = "1";
      const meta = $(".story-meta", card);
      const id = meta?.textContent.match(/#(\d+)/)?.[1];
      const record = byId.get(id);
      if (!record) continue;
      meta.textContent = `NODE_${String(record.id).padStart(3,"0")}  /  SECTOR ${record.cat}`;
      meta.title = record.cat_title;
      const picture = $("img, .ph", card);
      if (picture) {
        const wrapper = document.createElement("div");
        wrapper.className = "media-wrap";
        picture.before(wrapper);
        wrapper.append(picture);
        const attribution = $(".cap", card);
        if (attribution) wrapper.append(attribution);
      }
      const tags = document.createElement("div");
      tags.className = "intel-tags";
      const values = [
        ["ROUTE " + record.route, "route"],
        ["LEVEL " + record.diff + "/5", ""],
        ["ROLE " + record.role, ""]
      ];
      values.forEach(([label, type]) => {
        const tag = document.createElement("span");
        tag.className = "intel-tag" + (type ? " " + type : "");
        tag.textContent = label;
        tags.append(tag);
      });
      const copy = $(".copy", card);
      if (copy) copy.before(tags);
    }
  }
  const count = $("#count");
  const queryStatus = $("#query-status");
  function updateStatus() {
    if (queryStatus) queryStatus.textContent = (count?.textContent || "DATABASE READY").toUpperCase();
  }
  if (count) new MutationObserver(updateStatus).observe(count, { childList: true, subtree: true, characterData: true });
  new MutationObserver(decorateCards).observe(grid, { childList: true });
  decorateCards();
  updateStatus();
})();