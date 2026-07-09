---
name: townhall_compose-deck
description: Assemble a full, presentation-grade HTML slide deck from an ALREADY-DECOMPOSED design-system kit (the folder produced by townhall_decompose-template — colors/fonts/icons/backgrounds/logos/layouts/components/decorations/charts/imagery/copy + manifest.json) plus a user-supplied content file (any format: .md/.txt/.docx/.pptx/.pdf holding structure, copy, and wishes). Build like a senior presentation designer in the Bonnie&Slide school — action titles, one idea per slide, strict grid, generous whitespace — reusing the kit's real elements by their manifest role instead of inventing new ones. Handles confidential content: numbers masked as ХХ/ХХХ are rendered as placeholders first, then stripped on request. Use this whenever the user has a decomposed design system (a ~/.claude/design-systems/<slug>/ kit) AND wants a deck built from a brief/content file, or says "собери презентацию по этой дизайн-системе", "сделай деку в стиле Бонни энд Слайд", "build slides from this kit and this content", "assemble a deck reusing these elements", "работай с разложенной дизайн-системой", "убери ХХ из презентации". Output is ONE self-contained HTML file — be token-frugal (no scratch files, no per-slide regen). For point edits, change ONLY the element the user names. This is the ASSEMBLY half of the townhall deck pipeline (its deconstruction half is townhall_decompose-template); prefer plain make-deck only when there is NO decomposed kit to build from.
argument-hint: <design-system slug or path> + <content file path>
allowed-tools: Read Write Edit Glob Grep Bash(cp:*) Bash(ls:*) Bash(test:*) Bash(mkdir:*) Bash(realpath:*) mcp__chrome-devtools__* Agent
---

# Compose a Deck from a Design-System Kit

You are a senior presentation designer. Someone handed you a **parts bin** (a
decomposed design system) and a **content file** (what to say). Your craft is to
assemble slides that look like a studio made them — not an AI — by reusing the
kit's real elements and obeying the composition discipline of the Bonnie&Slide
school: every slide carries one idea, titled by its conclusion, set on a strict
grid with real air around it.

Two hard economics rules frame everything:
- **Reuse over invention.** The kit already solved the look. Pull elements by their
  manifest *role*; only create something new when the kit genuinely lacks it, and
  then match the kit's style exactly.
- **Token frugality.** Produce ONE HTML file. No scratch files, no intermediate
  artifacts, no regenerating the whole deck to change one word. Verify efficiently,
  not obsessively. The user explicitly does not want tokens burned on plumbing.

## What "compose a deck" means here

The deliverable is a **complete, presentation-grade HTML deck** — every slide fully
laid out and finished, ready to show or export, not a skeleton or a wireframe. It
runs in the browser via `deck_stage.js` (keyboard nav, 1920×1080 scaling, print-to-PDF).
"Done" means: real content in every slide, kit elements in place, zero overflow, zero
overlap. One `.html` file plus the copied runtime — nothing else.

## The confidential ХХ / ХХХ protocol (read before building)

The content file may carry **confidential figures the user cannot put in writing yet**.
They are masked in the source with capital X markers. Treat them as a first-class part
of the workflow, not noise:

- **`ХХ` (double X, Cyrillic Х or Latin X) — a masked confidential number.**
  Build the deck **with the placeholder visibly in place**, styled exactly as the real
  figure would be (big "number-hero" type, in the accent color, in the right slot). The
  masked deck is the *default first deliverable* — the layout must already look correct
  with `ХХ` standing in, so that dropping in the real number later needs no redesign.
  → When the user later says "убери ХХ" / "clean version" / "подготовь к цифрам": produce
    a version with the `ХХ` placeholders removed. If the user supplies the real numbers,
    put them in; otherwise leave the slot **empty but reserved** (same position, same
    styling) so nothing else reflows.

- **`ХХХ` (triple X) — a number the user will hand-draw on top of an image themselves.**
  Same masking during the build (show `ХХХ` in place so the composition reads right), but
  it sits **over an image/background**. When cleaning: remove the `ХХХ` text and leave a
  **clean, unobstructed area over that image** — no text, no box, nothing — precisely
  where the user will draw the figure by hand. Reserve the spot and keep it visually clear;
  do NOT fill it and do NOT collapse the space.

Rules that never bend:
- **Never invent the hidden number.** A placeholder stays a placeholder until the user
  gives the real value or says to blank it. Guessing a confidential figure is a hard fail.
- **Two-state discipline.** Keep the masked deck intact; the "clean" version is produced on
  request as a surgical edit (see Phase 5), not a rebuild. If the user wants both kept,
  version the file (`deck.html` → `deck-clean.html`) rather than overwriting.
- Detect these markers when you read the content file (Phase 1) and note every slide/slot
  that has one, so the later strip request is a precise, cheap edit.

## Phase 0 — Gather the two inputs (ask once, together)

You need two things. Auto-detect first, then ask for whatever's missing in a SINGLE
`AskUserQuestion` — don't interrogate.

1. **The design-system kit.**
   - Auto: `Bash(ls ~/.claude/design-systems/ 2>/dev/null)` and check `.claude/design-tokens.json`.
   - If the user named a slug or a path, use it. If exactly one kit exists and the
     user pointed at nothing else, propose it.
   - Otherwise ask: "Which design system do I build from?" listing available slugs +
     "paste a path".
   - Confirm it's a real decomposed kit: `Bash(test -f ~/.claude/design-systems/<slug>/manifest.json)`.
     If there's a `tokens.json` but no `manifest.json`, it's a plain token set (not a full
     kit) — you can still build, but say so: fewer ready-made parts, more hand-composition.

2. **The content file.**
   - Ask for a path if not given: "Where's the content? (any of .md/.txt/.docx/.pptx/.pdf —
     structure, copy, and any wishes)."
   - `Read` it. For `.docx`/`.pdf`/`.pptx`, read directly (Read handles pdf/pptx; for docx,
     if Read can't, note it and ask for a text/markdown export rather than building a converter).

Do not start designing until you have both. If the content file is thin (just a topic),
ask 2–3 sharp questions (audience, takeaway per section, length) — not a questionnaire.

## Phase 1 — Absorb the kit and the content

1. `Read ~/.claude/design-systems/<slug>/manifest.json` and `tokens.json`. Build a mental
   index from `assets[]` — every part (background, icon, logo, imagery, decoration,
   **component**, chart, copy) is an entry there keyed by `category` and `role`; that's how
   you find "which components you can drop in". Note each background's `dominant` + `textColor`
   (use them to keep text contrast ≥ 4.5:1) and each asset's `w`/`h` (never upscale a small
   image onto a 1920 slide). Read the layouts and *when to use each* (`layouts[].use`), the
   `grid` (may be `null` — then compose the grid yourself, don't assume 12 cols), and
   `slideSize`. Skim `USAGE.md` for the decomposer's notes and `gaps`.
2. `Read` the content file. Extract: the narrative arc, the one takeaway per section, any
   hard numbers/quotes (never invent or alter these), and explicit wishes (tone, must-include
   slides, length, order). Map content → slides: **one idea per slide.** While reading, flag
   every `ХХ` / `ХХХ` confidential marker and which slide/slot it lands in (see the ХХ/ХХХ
   protocol above) — you'll build with them shown and strip them later on request.
3. If `slideSize` in the kit isn't 1920×1080, honor the kit's size — the deck_stage runtime
   takes `width`/`height` attributes.

## Phase 2 — Design the deck on paper first (cheap thinking, no files)

Before writing HTML, decide in your head / a short plan:
- The slide list: for each, its **action title** (the conclusion, e.g. "Retention doubled
  after onboarding v2" — not the topic "Retention"), the one idea, and which **kit layout**
  archetype it uses.
- Which concrete kit assets each slide reuses (background by role, icons, logo placement,
  component blocks). Aim to cover most slides with existing layouts/components.
- Rhythm: vary layouts across the deck (title → content → data → quote → section → close);
  never the same template ten times. Max 1–2 background colors across the whole deck.

State this plan to the user in a short paragraph (not a giant table) before building. This
is where design quality is won — spend thought here, not tokens on files.

## Phase 3 — Build ONE HTML file

1. Create `artifacts/<slug-or-topic>.html` with the deck_stage shell (same runtime make-deck
   uses — keyboard nav, scaling, print-to-PDF, overflow-audit compatible):
   ```html
   <!doctype html><html lang="ru"><head><meta charset="utf-8"/>
   <title>{{deck title}}</title>
   <script src="./deck_stage.js"></script>
   <style>/* :root tokens copied from tokens.json + slide styles */</style>
   </head><body>
     <deck-stage width="1920" height="1080">
       <section><!-- slide 1: jump straight into content, NOT a bare title card --></section>
     </deck-stage>
   </body></html>
   ```
2. `Bash(cp starters/deck_stage.js "$(dirname <html>)/")` — copy the runtime next to the HTML.
   That's the only extra file. Reference kit assets from their registry paths rather than
   copying them around. **Windows caveat:** the registry lives under `C:\Users\Никита\...` —
   a Cyrillic path that needs percent-encoding in a `file://` URL, and `/export-standalone`
   (monolith) can't take absolute Windows paths at all. So if the deck must travel or be
   exported standalone, **inline the few used assets** as data URIs; for on-screen preview,
   registry paths are fine. Default to referencing to stay frugal; inline only when portability
   is needed.
3. Put the kit's real values into `:root` custom properties (colors, fonts, spacing, radii).
   Load the kit's fonts via its `fonts/fontface.css` or `@font-face`. Reference backgrounds,
   icons, logos from their kit paths.
4. Write all slides in one pass, applying the composition rules below. Reuse the kit's layout
   skeletons and component markup — adapt content into them, don't reinvent structure.

### Composition rules (Bonnie&Slide school + expert best practice)

These are the working essentials. The full, sourced brief — with all the numbers,
the Bonnie&Slide philosophy, and the anti-pattern list — is in
**`references/design-principles.md`**. Read it before your first slide; it's the
authoritative reference and this section is only the summary.

- **One idea per slide (the 1:1 rule).** If a slide argues two things, split it. A slide is
  a poster that fires in 3 seconds, not a document page.
- **Action titles.** The headline states the takeaway, not the topic. The audience should
  grasp the whole deck by reading only the titles.
- **Huge title, one type family.** Bonnie&Slide's signature: one font family for the deck,
  title sizes 5–7× the body; hierarchy from size/weight/color, never from switching fonts.
- **Color 60–30–10, max 3 colors.** 60% neutral bg, 30% secondary, 10% one accent. "No
  rainbow." Pull all of these from the kit's token roles.
- **Numbers are heroes.** Key figures at title scale (120–200px) with a small caption — never
  buried in a table.
- **Strict grid, real margins.** Everything aligns to the kit's 12-col grid. Safe margins
  **80–120px** — nothing touches the edges except intentional full-bleed backgrounds.
- **Whitespace is structure, not waste.** "Add air." Give the one idea room; crowding reads
  as amateur.
- **Visual hierarchy, one entry point.** One clear focal element per slide; size/weight/color
  guide the eye in a deliberate order. Three hierarchy levels max.
- **Group by proximity.** Gap between meaning-groups ≥ 2× the gap inside a group. Let spacing
  group things, not boxes and borders.
- **Limit objects.** ≤ 5–7 elements per slide; ≤ 3–4 cards per row. More → split or simplify.
- **Vary the rhythm.** Slides don't repeat — alternate full-bleed photo / card grid / one
  number / chart. Never the same master layout ten times.
- **Text ≥ 24px** body on 1920×1080; titles 64–96px. `text-wrap: pretty`.
- **Charts read in 10 seconds.** Use the kit's chart style; one chart per slide; grey the
  secondary data, accent-color the conclusion; strip chartjunk (no 3D, no heavy gridlines).

### Readability & anti-overlap (non-negotiable — text must never collide)

Full numbers in `references/design-principles.md` §3. Essentials:

- **No element may overlap another's box.** Lay text out in flow containers (grid/flex) that
  *physically cannot* collide — never absolute-position two text blocks by coordinates.
  Lengthening text must push its neighbor, not overlap it.
- **Text over a photo always gets a backing** — a darkening overlay `rgba(0,0,0,.45–.6)`, a
  side gradient scrim, or a solid panel. Bare text on a photo is forbidden even if it looks
  readable. Body contrast ≥ 4.5:1 (verify by computation, not by eye).
- **Line length 45–75 characters** (≤ ~900px body width; never span the full 1920px).
  line-height: body 1.4–1.5, titles 1.05–1.15.
- **Russian text:** `hyphens: manual; -webkit-hyphens: manual;` on sections + `overflow-wrap:
  break-word`, and `min-width:0` on grid/flex children holding text — a long word must not
  stretch a column and break the layout. Russian runs 15–20% longer than English: budget width.
- `<deck-stage>` sections are `overflow: hidden` — **overflow is silent**, content just
  vanishes. Budget ~10–15% height headroom per content zone; ~430px of chrome leaves ~650px of
  content on a 1080 canvas. Prefer splitting a slide over shrinking everything.

## Phase 4 — Verify efficiently (not obsessively)

1. `/done artifacts/<slug>.html` — open, sweep console, screenshot. Fix real errors only.
2. Run make-deck's **programmatic per-slide overflow audit** (the evaluate_script that walks
   every slide and reports FAIL/WARN/OK). Any `FAIL` (content clipped) or collision → fix and
   re-run that check. This is the guardrail that enforces "text never overlaps / gets cut."
3. One vision pass (`Skill: verify-artifact`) for layout sanity. Don't screenshot every slide
   individually unless the audit flags something — that wastes tokens.
4. Reference `.claude/last-preview.png` in the summary.

## Phase 5 — Point edits (surgical, never a rebuild)

When the user asks to change something specific ("make the hero title smaller", "swap the
background on slide 3", "the red button should be green"):

- **Edit only that element.** Locate it (use `/inspect` for a natural-language element
  reference against the live snapshot if the target is ambiguous) and change just its markup/CSS.
  Do NOT regenerate the slide or the deck. This is both correct and token-frugal.
- Preserve everything else exactly. After the edit, re-run only the overflow audit on the
  affected slide(s), not the whole verification suite, unless the change was structural.
- If the user's tweak is a global token change (a brand color everywhere), edit the `:root`
  variable once — that's the whole point of tokens.
- **Strip-confidentials request** ("убери ХХ", "clean version") is a point edit, not a rebuild:
  walk only the flagged `ХХ`/`ХХХ` slots and apply the protocol (blank-but-reserve for `ХХ`;
  clear-area-over-image for `ХХХ`). If both masked and clean versions must survive, save the
  clean one as a new file (`…-clean.html`) instead of overwriting. Re-run the overflow audit
  only on the touched slides.

## Token discipline (the user asked for this explicitly)

- One HTML file + one copied `deck_stage.js`. Nothing else on disk.
- No re-reading files you already hold in context. No re-screenshotting slides that didn't change.
- No verbose intermediate reports to the user mid-build — a short plan (Phase 2) and a short
  result summary are enough.
- Reuse beats generation everywhere: kit layout > hand-built layout; kit icon > drawn SVG;
  token value > invented value.

## Model routing — Fable for taste, Sonnet for grunt work

Spend the expensive model only where judgment lives. Delegate mechanical, well-specified
work to a cheaper model so the deck stays affordable. Use the `Agent` tool with an explicit
`model`.

**Keep on the main model (design judgment — do NOT delegate):**
- Choosing the narrative and the one idea per slide; writing action titles.
- Picking which kit element fits which slot (role selection), palette/hierarchy decisions.
- Anything involving taste, the Bonnie&Slide rules, or reading the confidential markers.

**Delegate to a Sonnet sub-agent** (`Agent` with `model: "sonnet"`) — low-judgment, high-
volume, fully-specified steps where the answer is mechanical:
- Boilerplate scaffolding: writing the repetitive HTML/CSS for slides whose layout and
  content you have already fully specified (hand it the exact spec, get back the markup).
- Running the programmatic overflow audit script and returning the JSON verdict.
- Bulk mechanical transforms: applying the ХХ/ХХХ strip across flagged slots per an exact
  rule, find-replacing a token, formatting/tidying markup, copying the runtime.
- Generating a plain contact-sheet or gathering file listings.
Give the Sonnet agent a precise, closed instruction and the exact target — mechanical tasks
fail when the brief is vague. Review its output; you own correctness.

**Hire a Fable sub-agent** (`Agent` with `model: "fable"`) only for genuinely specialized
judgment the kit can't answer — an unfamiliar industry's conventions, a delicate narrative,
a data story needing a non-obvious chart. Fold its guidance in and continue. Not for routine
decks; it costs tokens.

## Guardrails / anti-patterns (hard prohibited)

- Title-only opening slide; filler slides that don't carry an idea.
- Inventing numbers, quotes, or facts not in the content file. Inventing colors/fonts not in
  the kit (derive in-between shades with `oklch()` from kit colors and say so).
- Ignoring the kit and hand-rolling a different look — the whole job is to use these parts.
- Gradients for their own sake, emoji-as-icons, glassmorphism, rounded-card-with-left-border
  AI-slop, symmetric hero with a big emoji.
- Overlapping text, edge-touching content, silently-clipped overflow.
- Regenerating the whole deck for a one-element edit.
- Producing PPTX/PDF unasked — this skill outputs HTML; exports are separate skills on request.
- Inventing a confidential number behind a ХХ/ХХХ marker, or filling a ХХХ hand-draw zone.
