# Design principles — Bonnie&Slide school + expert composition rules

Read this before composing slides. It is the deep reference behind the composition
and readability sections of `SKILL.md`. Source: a focused expert consult cross-checked
against Bonnie&Slide's own materials (see Sources at the bottom).

> Factual note: Bonnie&Slide was founded by **Nikolay Pere and Svetlana Firsova**
> (working since 2015; Firsova ex-McCann/BBDO, authored brand guidelines for Sberbank,
> Megafon, Yandex). Do not misattribute the school to other names.

## Table of contents
1. Bonnie&Slide philosophy — recognizable traits
2. Slide composition checklist
3. Readability & anti-overlap (concrete numbers for 1920×1080)
4. Reusing a decomposed design system
5. HTML-slide specifics (1920×1080)
6. Anti-patterns to avoid

---

## 1. Bonnie&Slide philosophy — recognizable traits

The school sells the idea of the "killer slide": a slide is an advertising poster,
not a page of a document. It must "fire" in 3 seconds, not be read in a minute.

1. **One slide — one idea (the 1:1 rule).** Two ideas → two slides. Anything not
   serving the main message is deleted (the "rule of zero").
2. **The title is huge and primary.** Their signature move: one type family, title
   sizes **5–7× larger** than body. The title is often the largest object on the slide,
   bigger than any image.
3. **One type family for the whole deck.** Hierarchy comes from size, weight, and color —
   not from switching fonts. Preferred grotesques: Montserrat, Helvetica, Proxima Nova.
   Arial and Times New Roman are banned.
4. **Contrast is the main accent tool.** Sharp jumps: huge vs tiny, bold vs light, bright
   vs neutral. Vary size and color to spotlight what matters.
5. **"Add air."** Whitespace is a tool, not a flaw: large margins, big gaps between blocks,
   no element breathing down another's neck.
6. **Color by the 60–30–10 scheme.** 60% neutral background, 30% secondary, 10% one bright
   accent. "No rainbow" — no more than three main colors across the whole deck.
7. **6×6 rule and the rule of three.** No more than 6 lines of 6 words; group meaning in
   threes (3–6 elements max per row/list).
8. **Numbers as heroes.** Key figures set in title-scale type with a small caption, never
   buried in tables. Big number + small label is a recognizable B&S pattern.
9. **Slides don't repeat.** Composition alternates (full-bleed photo → card grid → one
   number → chart) to give the deck rhythm, not a stamped-from-one-master look.
10. **Real photography over clip art.** Quality full-bleed photos activate attention even in
    analytical decks; stock "little people with gears" is taboo.
11. **A chart reads in 10 seconds, a slide in 3.** One chart per slide, complex types
    simplified or split; everything secondary greyed out, the conclusion in the accent color.
12. **The finale is a call to action, not "Thanks for your attention."** The last slide
    restates the main idea and gives a contact or next step.

## 2. Slide composition checklist (apply per slide)

- [ ] **Title = conclusion, not topic** (action title): "Revenue grew 34% on retention",
      not "Revenue dynamics". Reading only the titles should convey the whole narrative.
- [ ] **One entry point.** There is an obvious single most-prominent element (title, number,
      or image). If the eye has nowhere to land first, the hierarchy is broken.
- [ ] **Three levels of hierarchy, max:** title → key content → captions/footnotes. Each
      level differs from its neighbor by ≥ 1.5–2× in size or radically in weight.
- [ ] **Modular grid:** 12 columns with fixed margins; all blocks snap to grid lines. No
      "eyeballed to the middle".
- [ ] **One alignment axis per group.** Left text edge is the main axis; don't mix
      left/center/right inside one block. Centering only for divider slides and lone numbers.
- [ ] **Proximity rule:** gap between meaning-groups ≥ 2× the gap inside a group. A caption
      sits right against its object, not equidistant between two.
- [ ] **≤ 5–7 objects** per slide (title, 3–4 content blocks, 1 decoration). Cards in a row: 3,
      max 4.
- [ ] **Text/visual balance:** either the visual dominates and text captions it, or text
      dominates and the visual supports. Two equal 50/50 halves is a weak composition.
- [ ] **System repeats:** title position, margins, sizes, and accent color are identical on
      every slide; the content layout changes, not the system.
- [ ] **Squint test:** at thumbnail size the slide still shows structure — a big title mass,
      blocks, an accent. If it becomes grey mush, there's too much text.

## 3. Readability & anti-overlap (1920×1080, concrete numbers)

**Type sizes (minimums):**
- Body: **≥ 24px** (comfortable 28–32px); captions/footnotes: **≥ 20px** — nothing goes
  below 20px, including copyright lines.
- Subheads: 40–56px; slide titles: 64–96px; hero titles and big numbers: 120–200px.
- Kickers/eyebrows: 20–24px, caps allowed with letter-spacing 0.05–0.15em.

**Margins & spacing:**
- Safe slide margins: **80–120px** all sides. Content never crosses them (exception:
  full-bleed backgrounds and decoration deliberately bleeding off-canvas).
- Inter-block gap: 24–48px; card inner padding: 32–48px.

**Line & leading:**
- Line length: **45–75 characters** (~`max-width: 28–36ch`, ≤ ~900px for body). Text spanning
  the full 1920px is forbidden.
- line-height: titles 1.05–1.15; subheads 1.2–1.3; body 1.4–1.5; big numbers 0.9–1.0.
- A paragraph on a slide is ≤ 3–4 lines; beyond that, cut or move to the next slide.

**Contrast:**
- Text/background: min **4.5:1** (WCAG AA) for text < 36px, **3:1** for ≥ 36px bold. Verify by
  computation, not by eye.
- Text over a photo — only with a backing, three legal techniques: (a) darkening overlay over
  the whole photo `rgba(0,0,0,.45–.6)`; (b) gradient scrim on the text side
  `linear-gradient(90deg, rgba(0,0,0,.75), transparent 60%)`; (c) an opaque/semi panel under
  the text block. Bare text on a photo is always forbidden, even if it looks readable now.
- Grey text: no lighter than #767676 on white; on dark, secondary text no darker than
  rgba(255,255,255,.65).

**Anti-overlap:**
- No absolute-positioning of text blocks "by coordinates" next to each other — only flow
  containers (grid/flex) that physically cannot collide.
- Between any two text blocks there is a guaranteed gap, not "they just happen to be far
  apart". When text lengthens, the block must push its neighbor, never overlap it.
- Long Russian words (see §5) require hyphenation, or the word overflows its container or
  breaks the grid.

## 4. Reusing a decomposed design system (folders + manifest.json)

1. **Manifest before markup.** Read manifest.json in full before the first slide and build a
   "palette of the day": color roles (primary/accent/bg/text), font pairs, available layouts,
   the icon and background sets. The whole deck is assembled from this menu.
2. **Pick by role, not by taste.** Not "this blue is pretty" but "I need the role `accent`".
   Not "I'll grab a big font" but "the role `display`". If the system has a `big-number`
   layout, a number slide is built from it, not drawn anew.
3. **Search order when an element is missing:** (1) another element of the same role;
   (2) an adjacent-role element applied per the system's rules (e.g. secondary instead of
   accent); (3) a composition of existing components; (4) only then — create something new.
4. **New = derivative only.** A new color only via `oklch()` from existing tokens (shift
   lightness/chroma at the same hue); a new layout = recombination of existing grid zones; a
   new icon in the same line/fill/corner style as the `icons/` folder (match stroke-width and
   corner radius against a sample). Inventing a new hue, new typeface, or new icon style is
   forbidden.
5. **Decorations & backgrounds — sparingly.** Decoration: max 1–2 per slide, only where it
   doesn't fight content. Don't mix folder backgrounds with home-made gradients.
6. **The copy/ folder sets the tone.** Boilerplate defines tone of voice; new phrasing keeps
   the same register (title length, presence of periods, caps or not).
7. **Log every deviation.** If you had to create a missing element, flag it in the summary as
   a candidate to add to the system — don't dissolve it silently.

## 5. HTML-slide specifics (1920×1080)

1. **Slide frame:** fixed `width:1920px; height:1080px` + stage scaling. Inside — CSS Grid:
   outer `grid-template-rows: auto 1fr auto` (title zone / content / footer); content zone
   `grid-template-columns: repeat(12, 1fr)` with `gap: 32–48px` and `padding: 80–120px`.
2. **Type scale as tokens.** Define the scale in CSS variables (e.g. 20/24/32/48/72/120/180)
   and use only it. Arbitrary `font-size: 37px` is forbidden: the scale is the rhythm.
3. **Overflow is the silent killer.** `overflow:hidden` on a section clips overflow with no
   console error — the slide looks "done" but text was eaten. Rules: (a) budget **~10–15%
   height headroom** in every content zone — never design flush to the edge; (b) after each
   slide, programmatically check `scrollHeight > clientHeight` / `scrollWidth > clientWidth`
   on the section and key containers — that is the overflow audit; (c) don't set fixed heights
   on text blocks inside cards; let content dictate height and let the grid align rows.
4. **`min-width:0 / min-height:0` on grid/flex children holding text.** By default a grid item
   won't shrink below its content — a long word stretches the column and breaks the layout.
   Explicit `min-width:0` + word-break fixes it.
5. **Russian text — hyphenation mandatory.** Base: `hyphens: manual` on sections + `&shy;` in
   known-long title words ("конкурентоспособность", "производительность"), or `lang="ru"` +
   `hyphens:auto` for body; safety net against container breakage: `overflow-wrap: break-word`.
   Russian words average 15–20% longer than English — columns sized "for English" overflow in
   Russian: budget block widths with that slack.
6. **Don't rely on `vh/vw` inside a slide** — sizes are px relative to the 1920×1080 canvas;
   the wrapper scales. `scrollIntoView` is forbidden (breaks the preview).
7. **Images:** always `object-fit: cover` + a fixed image zone in the grid; `max-width:100%`.
   A photo never dictates grid size.
8. **Charts — SVG with a fixed viewBox**, axis labels in the same scale tokens (≥ 20px in
   canvas coordinates), not the default 12px of chart libraries.

## 6. Anti-patterns — avoid categorically

1. Topic-title instead of conclusion-title ("About the company", "Our team").
2. Wall of text / bullets of 2–3 lines each — a slide-document instead of a slide-poster.
3. The same master layout for 10 slides straight (title on top + bullets) — no visual rhythm.
4. More than three colors; rainbow cards each in its own color "for beauty".
5. Purple-blue gradients, glassmorphism, neon glow — instant "AI presentation" marker.
6. Emoji as icons; icons from three different sets (different stroke, style, corners).
7. Text directly over a photo with no scrim/panel — "readable for now" doesn't count.
8. Type below 20–24px on a 1920×1080 canvas ("we'll explain it in small grey in the corner").
9. Two+ typefaces without a system; a display font in body text; Inter/Roboto/Arial as
   "default design".
10. Perfectly even spacing between everything — the proximity rule is dead: a caption sits
    equidistant from "its" and "someone else's" image.
11. Content flush to the slide edges or sprawled across the full 1920px as a 200-char line.
12. Invented numbers, "approximate" percentages, fake client logos — any fact not from the brief.
13. An Excel-grade chart: 8 series, side legend, everything equally bright, no conclusion.
14. Hand-drawn "little people" SVG illustrations — use a labeled placeholder and request a
    real asset instead.
15. A final "Thanks for your attention!" slide on an empty background — use a conclusion/CTA/contact.
16. Invisible overflow: a slide shipped without checking `scrollHeight/clientHeight` — clipped
    `overflow:hidden` text, a long Russian word escaping its card.

---

## Sources
- Bonnie&Slide — about the academy (founders, history): https://bonnieandslide.com/about
- B&S blog, "Базовые правила презентации" (60–30–10, 6×6, rule of three, 1:1, rule of zero,
  3 seconds): https://bonnieandslide.com/blog/baza-prezentacii
- B&S blog, "10 правил оформления презентации" (one type family, titles ×5–7, "no rainbow",
  charts in 10 seconds): https://bonnieandslide.com/blog/10-pravil-oformlenie-prezentacii
- Nikolay Pere, AdIndex, "10 лайфхаков убойных презентаций" (air, contrast, varied slides,
  CTA over "thanks"): https://adindex.ru/publication/opinion/creative/2018/07/25/172960.phtml
- "Учебник убойных презентаций" (school methodology): https://books.bonnieandslide.com/

Sections 2, 3, 5 synthesize widely-accepted best practice (action titles from the Barbara
Minto / McKinsey school, WCAG contrast, typographic norms) with specifics for the 1920×1080
format; the Bonnie&Slide claims are backed by the sources above.
