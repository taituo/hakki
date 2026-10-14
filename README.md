# HÄKKI — Hackable Everything Device Index

An offline-friendly, filterable field guide to **208 hackable devices**, rebuilt as a responsive terminal-inspired catalog. No build tools, third-party UI libraries, remote fonts, or image hotlinking are required.

## Files

- `index.html` — GitHub Pages entry point.
- `katalogi.html` — generated catalog for local browsing.
- `hacker-ui.css` — all the styling, palettes, responsive grid, and visual design tokens.
- `hacker-ui.js` — enhanced card metadata, compact-view toggle, random target, keyboard shortcuts, and live status.
- `assets/commons/` — local Wikimedia Commons thumbnails plus credit/license metadata.
- `list` — source catalog; descriptions and links are preserved.
- `build_katalogi.py` — catalog generator; patched to keep English UI and load the custom files.
- `fetch_commons.py` and `manual_add.py` — image import/curation utilities.

## Use

Open `index.html` locally or serve the repository with `python3 -m http.server 8000` and visit `http://localhost:8000/`. Search by name or topic; filter by category (A–K), access route (S/F/H/E), difficulty (1–5), or body role. The archive loads 15 cards at a time as you scroll.

Press **/** or **Ctrl/⌘ + K** to focus search. Press **Escape** to clear it. Use **RANDOM TARGET** to jump to a random device from the current filters, **COMPACT** to change card density, and the palette buttons for Phosphor / Midnight / High Contrast. Appearance preferences are saved locally.

## Access routes

- **S:** software-controlled interaction (app, API, Bluetooth LE, IR, serial); stock firmware remains.
- **F:** alternative firmware, jailbreak, or software replacement.
- **H:** hardware intervention, soldering, UART/JTAG, microcontrollers, etc.
- **E:** experimental or uncertain routes.

Difficulty **1** is beginner-friendly; **5** is specialist-level. Body role describes whether a device is best used for expression, sound, sensing, movement, or computing.

## Image licensing

Of the 203 unique device models across 208 rows, 194 have a verified local Commons image; 9 use placeholders. Images are associated with author, license and source-page credits. Always follow the respective license for reuse; licenses vary and may require attribution or ShareAlike.

## Rebuild

```sh
python3 fetch_commons.py  # network; refresh Commons images and metadata
python3 manual_add.py     # curated additions
python3 build_katalogi.py # regenerate katalogi.html
cp katalogi.html index.html  # update Pages entry point after a rebuild
```

The generator reads the `## The catalog` section of `list` and leaves the source catalog unchanged. Local images are used for the rendered cards; project and image-search links can open external sites when clicked.

## Deploy

Commit `index.html`, `katalogi.html`, `hacker-ui.css`, `hacker-ui.js`, `build_katalogi.py` and the existing `assets/` files together so the new UI has all its resources. The new theme intentionally retains the original data and attribution links.