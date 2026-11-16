# Agent brief - shared by every fan-out page of learn-api-docs-changelogs-with-phoebe

Filled from `~/.claude/skills/course-builder/references/agent-brief.template.md` on 2026-11-16.
Internal build document: never link it from an audience page.

You are writing ONE static HTML session page. No servers, no npm. **If your target file already
exists on disk, do not write it; report that and stop.** Write the file, return its path and one
line of coverage. No HTML in your reply.

## Read first, in this order

1. The template page. Copy its structure, classes, SVG grammar and quiz markup EXACTLY, including
   how many options each question has (FOUR options, "A · ...", "B · ...", "C · ...", "D · ..."):
   `/Users/phoebe.fu/Documents/claude_work/github_repo/learn-api-docs-changelogs-with-phoebe/courses/01-who-reads-the-docs.html`
   For rhythm you may also skim the bench page
   `/Users/phoebe.fu/Documents/claude_work/github_repo/learn-api-docs-changelogs-with-phoebe/courses/05-the-changelog-checker.html`
2. The source map: every verified fact, its evidence tier, per-session coverage, the seams, the
   Parcelpoint v1 / v1.5 / v2 API facts and the bench canon. Use ONLY its facts and numbers; never
   invent a statistic; if a fact is missing, teach the uncertainty.
   `/Users/phoebe.fu/Documents/claude_work/github_repo/learn-api-docs-changelogs-with-phoebe/materials/official-course-map.md`
3. The stylesheet `:root` block for the palette tokens (first 30 lines):
   `/Users/phoebe.fu/Documents/claude_work/github_repo/learn-api-docs-changelogs-with-phoebe/assets/style.css`
4. If your page quotes a Parcelpoint field, path or enum, check it in the generator
   `/Users/phoebe.fu/Documents/claude_work/github_repo/learn-api-docs-changelogs-with-phoebe/materials/build_adc_sample.py`
   (functions parcelpoint_v1, parcelpoint_v2, parcelpoint_v15). Never invent a field that is not there.

## Page skeleton (keep every component)

toolbar (crumb EXACTLY "learn-api-docs-changelogs-with-phoebe / Session N of 6" with the repo name
linked to ../index.html, #toggle-all, #zoom-toggle) · masthead (eyebrow
"Learn API Docs &amp; Changelogs with Phoebe · Session N of 6", h1 with one `<span class="accent">`,
.sub, .chip-row with the level chip given in your outline, an audience chip "Engineers who ship APIs,
platform and DX teams, tech writers", one more audience chip of your choice, `.chip.time` "45 min",
.agenda a1-a4 with flex weights 1/4/5/1) · main.wrap · section#intro (Part 0 "Where we start": kicker,
.lede, .legend pills as in the template, .callout.win "★ What you walk out with tonight.") ·
3 Parts, each `section.section#part-N` with section-kicker (klabel "Part N · covers ...", h2,
`.tag.concept "N min live"`), a `.lede`, ONE figure, `details.card` accordions (summary: `.mode.live`
or `.mode.self`, title, `.mini`, `.caret ▶`), at least one `.callout.example` with `span.ex-pill`
"Real world" on the page · section#demo-1 Build-along (klabel "Build-along", h2, kicker
`.tag.demo "★ 22 min · everyone builds"`, .lede, ONE figure, `.steps > .step`, each step a `<p>` with
the code box BELOW it as `.prompt-box.good` carrying a `span.label` "★ Step N · ...") · section#exercise
Homework (klabel "Homework", h2 "Before session N+1", `.tag.exercise "30 min"`, ol of 4 items) ·
section#quiz (klabel "Check yourself", h2 "Three questions", the passport line, 3 x
`.quiz-q data-answer="0-based"` with `p.qtext`, four `button.qopt`, `p.qwhy`; vary the correct letter
across the three; one `p.quiz-score` after the last) · section#official, klabel "Sources covered", h2
EXACTLY "What this session teaches, and where it came from", `.covered > .covered-row` (pill solid ✓ /
light ◐ + name + note), then the `.mono` line EXACTLY "Every fact on this page, and its verification
tier, is recorded in the course's source map." · section.cheat#cheatsheet (h3
"Session N cheat sheet <span>· pin this</span>", .grid-2 of six .cheat-item with b + span) ·
`.callout.next` with `.nx-pill` "Next session" · footer.pagefoot ·
`<script src="../assets/app.js?v=1"></script>`.

Head: copy the template's social meta block with this page's own title/description/url
(`https://phoebefu6.github.io/learn-api-docs-changelogs-with-phoebe/courses/<file>`, og-image
`.../assets/og-cover.png`); `<title>Session N · <short title> - learn api docs changelogs with phoebe</title>`;
`<link rel="stylesheet" href="../assets/style.css?v=1">`. Nothing else external.

First `details.card` in the FIRST Part is `open`; no other. Sentence case headings. Warm
practitioner voice, concrete, never dry. Inside prompt-boxes escape `&` `<` `>`. 450 to 650 lines
is guidance about depth, never a target: never collapse whitespace, dissolve a list into a
paragraph, or drop a component to fit.

## Hard rules (a violation is rework)

- NEVER an em dash or en dash, anywhere (prose, code, aria-labels, comments). Hyphen only.
- No meta text: never "this course", "in this course", "the course teaches", "banned here". State
  the professional norm directly with its reason. The two exact estate phrases above are the only
  self-references; "session 5" cross-references are fine.
- Attribution "by Phoebe Fu". Never "built with" a tool.
- Every number comes from the map or is labelled constructed. For constructed data print "your
  numbers will differ", never invented outputs as if run.
- Contested or missing evidence: teach the disagreement; never resolve what the literature has not.
- Citations in the exact form of the map's appendix; anything marked reported is "reported".
- NEVER "lottery" or "lotteries"; say the mechanism.
- Default to the English word. No Chinese terms are needed on these pages.
- Titles, widget ids and class names must not collide with siblings. Do not reuse these titles:
  "Why docs fail", "Sentences that work", "Structure readers scan", "The README", "Diataxis",
  "Reference docs, ADRs, changelogs", "Docs as code", "Edit and ship", "Error messages",
  "Boundaries and contracts", "Actions authoring". Do not use class prefixes `rbp-`, `mcl-`, `rfm-`;
  `adc-` belongs to the bench engine; your figures use the `sNx` prefix below.
- Course-specific: every mention of Parcelpoint is labelled "Constructed Parcelpoint example" (or
  "constructed" in the same sentence). Never Phoebe's employers, clients or projects. Do not invent
  other company cases; real-world stories come from the map (GitHub, Stripe, Google AIP-185,
  Petstore, FastAPI, oasdiff, the RFCs, Keep a Changelog, SemVer).
- Tools (Postman, Redocly, Stoplight, Swagger UI, contract testers, mock servers, linters) are named
  only as a category in a Self-study card. No build-along needs an account or a server: every
  build-along runs in the page (reading, writing YAML/JSON in prompt boxes, or an inline widget where
  your outline allows one).
- Re-verify warning: Stripe's current version and GitHub's supported versions change; say "at the
  time of writing (November 2026)" when you quote them.
- Seams: general docs craft belongs to Learn Tech Writing; link it, never reteach it (one-card recap
  at most). Links are absolute https (list below).

## Figure grammar (hand-drawn, every figure)

Palette, ONLY these hexes (no invented greys): #1A4715 (primary) · #12330E (deep) · #2F6B1C (mid) ·
#B7D6A3 (soft) · #EEF6E8 (tint) · #17231A (ink) · #4C5A47 (muted) · #C6D3BE (faint) · #DEE7D8
(hairline) · #F2B33D (marigold, a FILL only, never text) · #6B4700 (marigold ink, text) · #FDF3DC
(marigold tint) · #FCFDFB (paper) · `#FFFFFF` · universal reds `#991B1B` `#FEF2F2` `#FCA5A5` only for a
wrong-way panel or a breaking change.

- `<figure class="zoomable">` > `<svg viewBox="0 0 880 H" xmlns="http://www.w3.org/2000/svg" role="img"
  aria-label="the data, not the shape">` > `<defs>` + `<style>` + content, then
  `<figcaption>🔍 Click to zoom - takeaway</figcaption>`. Grow H, never W.
- Prefix unique per figure, used for every class and id: `s{session}{letter}`, e.g. s2a, s2b, s2c,
  s2d for session 2's four figures (filter `s2aSk`, hatch `s2aHc`, arrow `s2aAr`, classes `.s2aH` ...).
- `<defs>` holds three things with the figure prefix P: a wobble filter `id="PSk"`
  (`feTurbulence type="fractalNoise" baseFrequency="0.02" numOctaves="2" seed="<int>"` +
  `feDisplacementMap scale="2.4" xChannelSelector="R" yChannelSelector="G"`, `x="-3%" y="-3%"
  width="106%" height="106%"`), a hachure pattern `id="PHc"` (7x7 userSpaceOnUse, rotate(-38), one
  #1A4715 line, opacity .5), an open arrowhead `id="PAr"` (path `M1 1 L9 5 L1 9`, fill none, #17231A
  stroke 1.6). ALL shapes sit inside ONE `<g filter="url(#PSk)" fill="none" stroke="#17231A"
  stroke-width="2" stroke-linecap="round" stroke-linejoin="round">`; rects carry a tiny rotation (-4 to
  4 degrees for hand-placed items, under 1 for panels). Fills: white, #EEF6E8, the hachure for "the
  pile" or "the data", #1A4715 with white text for "the one source" (the spec), and #F2B33D ONLY for
  the one thing the figure is about. One doodle anchor per figure, simple strokes, never a mascot.
  Text classes: `.PH` 800 12px #17231A heading · `.PL` 600 12px #17231A label · `.PS` 400 11px #4C5A47
  · `.PB` 800 11px #6B4700 · `.PV` 800 16-20px #12330E value · `.PW` 800 12px #FFFFFF on a #1A4715
  fill · `.PA` 700 11px #1A4715 axis caption · `.PR` 800 11-12px #991B1B for breaking · `.PN` 400 12px
  #4C5A47 note. Text on a #F2B33D fill is #17231A, never white. Hand-stacked items must not overlap as
  painted rects (the gate flags a pile).
- ALL `<text>` outside the filtered group, sans stack, never below 10.5px.
- Fit: max chars ≈ (box width - 20) / 7 at 12px, 6.4px/char at 11px; full-width note under 110 chars;
  40px between neighbouring point labels; bottom note 22px below the last row, H clears it by 8px. No
  line, arrow or curve may cross a label (the scanner flags line-through-text and text-out-of-box).
  When in doubt, shorten.
- Floor: one figure per Part plus one in the build-along. Draw the MECHANISM (where the spec feeds the
  page, where a drift is caught, which header carries which date), never a metaphor literally, never
  decoration.

## Voice and honesty

Every Part gets a real-world story from the map (GitHub REST reference and versions page, Stripe
versioning and changelog, Google AIP-185, Swagger Petstore, FastAPI, oasdiff, the RFCs, Keep a
Changelog, SemVer, the OpenAPI migration post). Constructed cases say "constructed" on the page:
Parcelpoint and its consumers. Nothing on the page claims a measured outcome that was not measured.

## Cross-links (absolute URLs)

- Tech writing s5 Diataxis: https://phoebefu6.github.io/learn-tech-writing-with-phoebe/courses/05-diataxis.html
- Tech writing s6 reference/ADRs/changelogs: https://phoebefu6.github.io/learn-tech-writing-with-phoebe/courses/06-reference-adrs-changelogs.html
- Tech writing error messages: https://phoebefu6.github.io/learn-tech-writing-with-phoebe/courses/91-error-messages.html
- Tech writing s7 docs as code: https://phoebefu6.github.io/learn-tech-writing-with-phoebe/courses/07-docs-as-code.html
- GitHub for builders s5 Actions: https://phoebefu6.github.io/learn-github-for-builders-with-phoebe/courses/05-actions-authoring.html
- System design s2: https://phoebefu6.github.io/learn-system-design-with-phoebe/courses/02-boundaries-and-contracts.html
- Hub: https://phoebefu6.github.io/learn-with-phoebe/

## Footer chain and session titles

Footer left: "Session N of 6 · learn-api-docs-changelogs-with-phoebe · by Phoebe Fu &nbsp;·&nbsp; 📚 <a href="https://phoebefu6.github.io/learn-with-phoebe/">Learn with Phoebe ↗</a>"
Footer right: "<a href="PREV">← Prev: <short title></a> &nbsp;·&nbsp; <a href="NEXT">Next: <short title> →</a>"
(session 6: "← Prev: The changelog checker" and "<a href="../index.html">Course home →</a>").

Files and titles (h1 may be phrased differently but keeps the substance; the card title is fixed):
1. `01-who-reads-the-docs.html` · Docs as the API's interface: who reads them and what they need (short: "Docs as the API's interface")
2. `02-spec-first-openapi.html` · Spec-first: describing an API in OpenAPI 3.1 (short: "Spec-first in OpenAPI 3.1")
3. `03-reference-pages.html` · Reference pages that answer the real question (short: "Reference pages")
4. `04-examples-that-run.html` · Examples that run: quickstarts, samples and tests that keep them true (short: "Examples that run")
5. `05-the-changelog-checker.html` · The bench: changelog checker (short: "The changelog checker")
6. `06-versioning-and-deprecation.html` · Versioning and deprecation: a changelog someone can act on (short: "Versioning and deprecation")

Bench canon you may quote (printed by the session 5 widget): Parcelpoint v1 to v2 = 30 changes, 12
breaking / 16 non-breaking / 2 docs-only, MAJOR 1.4.2 to 2.0.0; consumers: 4 of 6 hit; honest bump 0
broken without warning and 4 warned; shipped as a minor (1.5.0) 4 of 6 broken without warning. v1 to
v1.5 = 7 changes (0/6/1) MINOR 1.5.0. Wording fix = 3 docs-only, PATCH 1.4.3. Petstore edited = 14
(3/10/1) MAJOR. Quote nothing else from the bench.
