---
name: townhall_decompose-template
description: Decompose an existing presentation template into reusable, individually-filed design elements — icons, backgrounds, fonts, logos, colors, slide layouts, components, decorations, chart styles, imagery, and boilerplate copy — organized into a strict folder contract plus a machine-readable manifest, so townhall_compose-deck (and make-deck / use-design-system) can later rebuild decks from those exact parts. Use this whenever the user hands over a .pptx, an HTML deck, or slide screenshots and wants to "разобрать шаблон на элементы", "вытащить дизайн-элементы из презентации", "harvest a deck", "turn this template into a design system / kit", "extract icons/backgrounds/fonts from these slides", "make the parts reusable", or otherwise wants an existing presentation broken into building blocks for future assembly — even if they don't say the word "skill". This is the DECONSTRUCTION half of the townhall deck pipeline (its assembly half is townhall_compose-deck); reach for it specifically when the source is an already-designed presentation and the goal is a sorted parts bin, not a fresh style guide.
argument-hint: <path to .pptx / HTML deck / screenshot(s)> [target design-system slug]
allowed-tools: Read Write Edit Glob Grep Bash(python:*) Bash(python3:*) Bash(mkdir:*) Bash(cp:*) Bash(mv:*) Bash(ls:*) Bash(test:*) Agent mcp__chrome-devtools__*
---

# Decompose a Presentation Template

Take one already-designed presentation and break it into a **sorted parts bin** —
every icon, background, font, colour, layout, and block filed where the deck
builder can find it. The output is a design-system folder in the registry, so
`make-deck` and `use-design-system` pick it up with zero extra wiring.

The guiding idea: a builder should never have to re-derive the look. It opens
`manifest.json`, reads "backgrounds live in `backgrounds/`, here are the three we
have and when to use each," and drops them in. Your job is to make that manifest
honest and the folders clean.

## The folder contract (this is the point of the skill)

Everything lands in `~/.claude/design-systems/<slug>/`. That path is the org-level
registry every project auto-detects. The **required** files keep the kit
compatible with the existing ecosystem; the **subfolders** are the decomposed
elements. Never invent a different layout — the builder relies on these exact names.

```
~/.claude/design-systems/<slug>/
├── tokens.json        # REQUIRED. Standard schema (colors/fonts/spacing/radii/shadows).
│                      #   This is what use-design-system + make-deck Phase 0 read.
├── manifest.json      # REQUIRED. The MAP: indexes every asset below with role + when-to-use.
├── preview.html       # Visual contact sheet of the whole kit (open to eyeball it).
├── USAGE.md           # Short prose: how a builder should consume this kit.
│
├── colors/            # palette.json — named swatches with roles (bg/surface/text/accent/…).
├── fonts/             # Font files (.woff2/.ttf/.otf) + fontface.css snippet + a specimen note.
├── icons/             # UI glyphs/pictograms, one file each, SVG preferred, named by MEANING
│                      #   (icon-search.svg, not image7.png). Small, monochrome-ish, symbolic.
├── logos/             # Brand logo variants: full, mark-only, monochrome, inverse.
├── backgrounds/       # Full-slide backdrops, gradients, patterns, textures.
├── imagery/           # Content photos & illustrations (NOT backgrounds — things shown on a slide).
├── decorations/       # Decorative shapes: dividers, accents, frames, blobs, corner flourishes.
├── layouts/           # One .html per recurring slide archetype (title / section / content /
│                      #   two-col / quote / data / closing) + a note on when each is used.
├── components/        # Reusable blocks as .html: cards, stat tiles, callouts, tables, header/footer.
├── charts/            # chart-style.json (series colours, font, gridline rules) + example markup.
└── copy/              # Boilerplate text as .md: taglines, section titles, legal/footer, tone note.
```

Element → folder cheat-sheet (maps the user's words to the bin):

| Source element | Goes to | Notes |
|---|---|---|
| эконки / значки / pictograms | `icons/` | vector if possible; name by meaning |
| фоны / backdrops / textures | `backgrounds/` | full-bleed, slide-sized |
| шрифты / typefaces | `fonts/` + `tokens.json.fonts` | copy the file AND record the family name |
| тексты / boilerplate copy | `copy/` | reusable strings only, not slide-specific prose |
| цвета / palette | `colors/palette.json` + `tokens.json.colors` | roles, not just hex |
| логотипы | `logos/` | keep every variant separate |
| раскладки слайдов | `layouts/` | one archetype per file |
| компоненты / blocks | `components/` | live HTML, not screenshots |
| декор | `decorations/` | shapes that aren't content or background |
| графики / charts | `charts/` | style preset, not the data |
| фото / illustrations | `imagery/` | content imagery |
| сетка / отступы | `tokens.json.spacing` + `USAGE.md` grid note | columns, margins, gutter |

If an asset genuinely fits nowhere, put it in a `misc/` folder and say so in the
manifest — an honest "unsorted" beats a wrong bin.

## Phase 0 — Identify the source and set the slug

1. Look at what the user gave you:
   - **`.pptx`** (also `.potx` / `.ppsx` / `.pptm` — same ZIP format) → richest source.
     Use the extractor script (Phase 1a).
   - **HTML deck** (`artifacts/*.html` with `<deck-stage>` or `<section>` slides) → parse directly (Phase 1b).
   - **Screenshot(s)** of slides → vision extraction (Phase 1c); you can recover colours,
     layouts, and copy, but NOT crisp asset files — say so plainly in the manifest.
2. Pick a **slug**: short kebab-case brand/deck name (e.g. `sber-dark-wizard`, `townhall-2026`).
   Prefer `$1` if the user gave one. Check `Bash(ls ~/.claude/design-systems/ 2>/dev/null)` —
   if the slug already exists, ask whether to **merge into** or **replace** it. Never silently overwrite.
3. `Bash(mkdir -p ~/.claude/design-systems/<slug>)` and the subfolders you'll actually fill.

## Phase 1a — Extract from .pptx (the common case)

Run the bundled extractor. It unzips the deck and does the deterministic work —
copying media, reading image sizes, pulling theme colours/fonts, slide text, and
layout names — so you can focus on classification.

```
python .claude/skills/townhall_decompose-template/scripts/pptx_extract.py "<template.pptx>" "<workdir>"
```

(Use `python3` if `python` is missing.) It writes `<workdir>/extract_report.json`
and dumps every image into `<workdir>/raw_media/`, every embedded font into
`<workdir>/raw_fonts/`. Read the report, then:

First, **read the `warnings` array** — it tells you up front if the theme is stock,
media is missing, or the size is unknown, so you never mistake a thin deck for a
broken run. Then work through the report:

- **Media** — each entry carries strong signals: `bucket_guess`, `w`/`h`, `alpha`
  (photos ~never have alpha; icons/decor usually do), `used_on` (which
  master/layout/slides reference it) and `used_count`, plus `dup_of` for repeats and
  `viewable:false` for EMF/WMF you can't open. **`used_on` is the most reliable
  signal**: an image on the slideMaster or on every layout is almost certainly a logo
  or a background; one referenced by a single slide is content imagery. Confirm the
  final call with your eyes — `Read` the `viewable` images before filing — then copy
  into `icons/`, `backgrounds/`, `logos/`, `imagery/`, `decorations/` with
  **meaningful names**. Skip anything with `dup_of` (file the original once).
- **Colours** — do NOT trust `theme_colors` blindly. If `theme_is_office_default` is
  true (or the warning fired), the theme is stock and the real palette lives in
  `color_histogram` — the actual `srgbClr` frequencies across all slides/shapes. Read
  the palette from the histogram's top entries (and, for image-heavy decks, sample the
  dominant colours of the backgrounds you filed). Record **roles**, not just hex.
- **Fonts** — record `theme_fonts` in `tokens.json`, and use `font_size_histogram`
  (real pt sizes with counts) to reconstruct the **type scale** (e.g. 50pt title /
  18pt body / 10pt caption). If `embedded_fonts` is non-empty, copy those files into
  `fonts/` and write a `@font-face` snippet; if fonts are only referenced, note the
  family and flag "needs the font file or a web substitute" in `USAGE.md`.
- **Text** — `slides[].text` is grouped by placeholder type (`ph`: title/body/ftr…).
  Mine recurring `ftr`/`title` entries for genuinely reusable copy (taglines, section
  titles, footer/legal) → `copy/`. Skip one-off body prose.
- **Layouts** — use each layout's `placeholders` geometry (type + x/y/w/h in px) as the
  literal skeleton: it tells you where the title/body/image zones sit. From those
  positions infer 4–7 archetypes and rebuild each as a clean HTML skeleton in
  `layouts/` (structure + token placeholders, not literal content). If `placeholders`
  is empty (content drawn straight on slides, common in image-background decks) and the
  archetypes are unclear, **ask the user for a PDF export of the deck** — `Read` handles
  PDF pages and lets you see the real rendered slides. Don't hallucinate layouts.
- **Grid** — derive `grid` (columns/margins/gutter) from the placeholder x-positions
  and the slide size. If they don't imply a clean grid, write `grid: null` rather than
  defaulting to "12 columns" out of habit — the builder must not trust an invented grid.

## Phase 1b — Extract from an HTML deck

`Read` the file. Pull the `:root` custom properties / CSS variables → colours,
fonts, spacing, radii (straight into `tokens.json`). Extract inline `<svg>` blocks
→ `icons/` or `decorations/`. Extract `background-image` / `<img>` assets → the
right folder. Lift repeated section structures → `layouts/`; repeated card/callout
markup → `components/`. This source is the cleanest — you get real code, reuse it.

## Phase 1c — Extract from screenshots

Delegate the visual read to `Skill: ingest-screenshot` for token extraction, then
continue here to build the folder structure. You can reconstruct palette, fonts
(best guess), layouts, and copy. You **cannot** recover vector icons or crisp
backgrounds — record what you rebuilt vs. what's approximated, and set each
manifest entry's `source` to `"screenshot-approx"` so the builder knows it's lossy.

## Phase 2 — Write tokens.json (compatibility spine)

This exact schema is what `use-design-system` and `make-deck` already read. Keep it.

```json
{
  "name": "<slug>",
  "colors": { "bg": "#…", "surface": "#…", "text": "#…", "muted": "#…",
              "primary": "#…", "accent": "#…" },
  "fonts":  { "display": "…", "body": "…", "mono": "…" },
  "spacing": [4, 8, 12, 16, 24, 32, 48, 64],
  "radii":  { "sm": 4, "md": 8, "lg": 16 },
  "shadows": ["…"]
}
```

Use real values from the source. Do not invent a colour that isn't in the deck; if
you need an in-between shade, derive it with `oklch()` from an existing one and say so.

## Phase 3 — Write manifest.json (the map the builder reads)

`tokens.json` covers the abstract style; `manifest.json` covers the concrete parts.
This schema is a **contract with `townhall_compose-deck`** — it reads exactly these
fields to pick parts by role without opening files. Honor it precisely.

**Contract rules (don't drift):**
- **`category` is an enum equal to the folder names:** `background | icon | logo |
  imagery | decoration | component | chart | copy | font`. Every filed part — including
  components, copy snippets, and chart styles — is an entry in `assets[]` with its
  category. If it's only in a folder but not in `assets[]`, the builder can't see it.
- **Required on every raster asset:** `w`, `h` (px) — the builder needs them to avoid
  upscaling a 800×450 image onto a 1920 slide.
- **`sourceSlides`**: which slide numbers the part came from (from the report's
  `used_on`) — gives the builder usage context and the user provenance.
- **Backgrounds also carry** `dominant` (1–3 hex) and `textColor` (which text colour
  stays legible on them) — the builder must compute ≥4.5:1 contrast, so give it numbers.
- **Honesty flags:** `dupOf` (skip duplicates), `viewable:false` (EMF/WMF or
  screenshot-approx the builder shouldn't trust as pixel-perfect).
- Only add a field if the builder makes a decision from it without opening the file.
  Everything "just in case" goes in `notes` or nowhere.

```json
{
  "name": "<slug>",
  "source": { "type": "pptx|html|screenshot", "file": "…", "slide_count": 6 },
  "slideSize": { "w": 1280, "h": 720 },
  "grid": { "columns": 12, "marginPx": 64, "gutterPx": 24 },
  "assets": [
    { "id": "bg-hero-dark", "category": "background", "path": "backgrounds/hero-dark.png",
      "w": 5120, "h": 2880, "sourceSlides": [1], "dominant": ["#0B1F17", "#12352A"],
      "textColor": "#FFFFFF", "role": "title & section dividers", "source": "pptx" },
    { "id": "icon-shield", "category": "icon", "path": "icons/shield.svg",
      "w": 96, "h": 96, "sourceSlides": [3], "role": "security/trust bullets", "source": "pptx" },
    { "id": "logo-mark-white", "category": "logo", "path": "logos/mark-white.svg",
      "w": 240, "h": 64, "sourceSlides": [1,2,3,4,5,6], "role": "top-left chrome on dark slides", "source": "pptx" },
    { "id": "card-stat", "category": "component", "path": "components/stat-card.html",
      "role": "single KPI with big number + caption", "source": "pptx" },
    { "id": "footer-legal", "category": "copy", "path": "copy/footer.md",
      "role": "confidentiality line on every slide", "source": "pptx" }
  ],
  "layouts": [
    { "id": "title", "path": "layouts/title.html", "use": "opening slide, one bold claim" },
    { "id": "two-col", "path": "layouts/two-col.html", "use": "text left, visual right" }
  ],
  "gaps": [ "fonts referenced but not embedded: Golos Text — needs web font" ]
}
```

The `role` and `use` fields are the whole value — they tell a future builder *when*
to reach for each part. Write them as if briefing a junior designer.

## Phase 4 — preview.html + USAGE.md

- **preview.html** — a single contact sheet: colour swatches (with roles), the type
  scale in the real fonts, an icon grid, background thumbnails, and a render of each
  layout skeleton. This is how the user (and future-you) remembers what's in the kit
  at a glance. Follow the anti-slop rules (no gradients-for-their-own-sake, no emoji).
- **USAGE.md** — 15–25 lines, prose, addressed to the builder: which font is display
  vs body, the grid/margins, which background pairs with which text colour, any gaps
  to fill. This is the natural-language companion to the manifest.

## Phase 5 — Verify and report

1. `Bash(ls -R ~/.claude/design-systems/<slug>)` — confirm every non-empty category
   has files and no folder is a lie (empty folder referenced in the manifest = fix it).
2. Sanity-check `manifest.json` paths all resolve (no entry points at a missing file).
3. `/preview ~/.claude/design-systems/<slug>/preview.html` (or `/done`) to eyeball the kit.
4. Report to the user: the slug, a one-line inventory ("6 backgrounds, 11 icons, 2 logos,
   5 layouts, palette of 7, 2 fonts"), and the exact next command:
   **`/townhall_compose-deck` will build a deck from this kit** (its natural consumer);
   `/make-deck` also auto-detects it, and `/use-design-system <slug>` loads it explicitly.

## Model routing — keep taste on the main model, delegate mechanics to Sonnet

Spend the expensive model only on judgment. Use the `Agent` tool with an explicit
`model` to hand well-specified grunt work to a cheaper Sonnet sub-agent.

**Keep on the main model (do NOT delegate — this is the skill's value):**
- Looking at images and deciding icon / logo / background / photo / decoration, and
  naming them by meaning.
- Reading the palette when the theme is stock Office; assigning colour roles.
- Inferring the 4–7 layout archetypes; writing `role` / `use` / USAGE.md.
- The merge-vs-replace decision on an existing slug.

**Delegate to a Sonnet sub-agent** (`Agent` with `model: "sonnet"`) — closed, mechanical steps:
- Running `pptx_extract.py` and condensing the 200-line report into a short summary
  (counts, warnings, top colours) so the full JSON never bloats the main context.
- **Executing a filing table you already decided**: you hand it rows like
  `raw_media/image7.png → icons/shield.svg, category:icon, role:"…"`; it does the
  mkdir/cp/rename and assembles `assets[]` strictly from the table. Rule: *Sonnet never
  makes a classification call — it only executes the table; anything not in the table it
  reports back rather than filing on its own.*
- Generating `preview.html` from a fixed template once tokens + manifest exist.
- Phase 5 verification: checking every manifest path resolves, no folder is empty, JSON valid.
- Phase 1b mechanics: extracting `:root` variables, inline `<svg>`, `background-image`
  from an HTML deck as a raw list (no interpretation).

Always review the sub-agent's output — you own correctness.

## Guardrails

- **Don't invent.** No fabricated colours, fake icon names, or layouts the deck never had.
  A smaller honest kit beats a padded one.
- **Name by meaning, not by index.** `icon-arrow-right.svg`, not `image12.png`. The builder
  searches by concept.
- **A folder in the manifest must contain real files.** Empty categories are simply omitted,
  not listed with nothing behind them.
- **Preserve, then reuse.** Copy original asset files verbatim where possible; only
  regenerate (e.g. re-trace a raster icon to SVG) when it clearly helps reuse, and note it.
- **Screenshots are lossy** — always flag approximated assets so the builder doesn't trust
  a reconstructed background as pixel-perfect.
