# Design: migrate the literate document from LaTeX/PDF to HTML

**Status:** Agreed spec (pre-implementation)
**Date:** 2026-06-13
**Author:** XekriRedmane (with Claude)
**Scope:** Replace the LaTeX/`noweb.sty`/TikZ/PDF weave path with an HTML weave path. The
tangle path (byte-perfect `.asm` extraction) is **not** changed.

---

## 1. Motivation

The reverse-engineering document (`main.nw`) is currently a literate noweb source that
tangles to 6502 assembly and weaves to a PDF via `pdflatex`. Two problems motivate a
change:

- **Navigability.** A PDF is harder to navigate and read than HTML. The chunk-graph of a
  literate program is fundamentally a web of links; HTML is the native medium for it.
- **Diagrams.** LaTeX/TikZ diagrams are laborious to author and look bare. Mermaid produces
  better-looking flowcharts/state machines for far less effort, and renders natively in a
  browser.

The goal is an HTML document that is more navigable and friendlier to read than the PDF,
with Mermaid diagrams and a rich, clickable cross-reference web.

## 2. Goals and non-goals

**Goals**
- HTML is the sole human-readable output.
- Preserve the byte-perfect tangle and the entire chunk-graph cross-reference web.
- Author prose in Markdown; author diagrams in Mermaid.
- Multi-page, searchable, three-pane documentation site that works both from `file://` and
  on GitHub Pages.

**Non-goals**
- No change to the tangler, the `<<chunk>>=` chunk syntax, the assembly, or `verify.py`'s
  byte-perfect guarantee.
- No PDF output. The LaTeX path is retired (it remains in git history).
- No offline-bundled JS/CSS in v1 — third-party libraries load from CDN (internet required
  to *view*, accepted).

## 3. Invariant that makes this safe

**The tangler reads only code chunks; prose lives in doc chunks.** Therefore migrating prose
(LaTeX→Markdown) and diagrams **cannot change the tangled `.asm`**. `verify.py`'s byte-perfect
comparison against `reference/*.bin` must stay green at *every* commit of the migration, as
long as code chunks are not edited. The migration is a pure rendering change.

---

## 4. Decision log

Each decision lists the **choice**, the **rationale**, and the **rejected alternatives**.

### 4.1 PDF fate → **Retire PDF, go HTML-only**
HTML becomes the sole output; the LaTeX/TikZ pipeline is removed. Maximum freedom to redesign
the source. LaTeX source stays recoverable from git history.
*Rejected:* keep both permanently (forces source into a translatable subset forever, double
maintenance); keep both during transition (the text-flip to Markdown ends PDF buildability
anyway).

### 4.2 Source format → **Keep `<<chunk>>=` syntax + tangler; new weaver only**
The tangler is the verified byte-perfect backbone and `extract_chunk_info` already computes
the full cross-reference web (defines/uses/used-in, prev/next sublabels, chunk index,
identifier index) independent of output format. Only the LaTeX-emitting half of `weave.py`
is replaced.
*Rejected:* redesign chunk syntax (would force re-validating all 16 targets); brand-new tool
(discards proven machinery).

### 4.3 Prose language → **Markdown + keep `$…$` and `[[ ]]`**
Markdown is the natural authoring language for HTML and Mermaid. The existing prose uses a
constrained LaTeX subset (text/sections/lists/refs + inline-only `$…$` math), which migrates
mostly mechanically. `$…$` survives as-is (KaTeX); `[[ ]]` survives as the linked-ref marker.
*Rejected:* keep LaTeX source and translate at weave (builds/maintains a LaTeX→HTML
translator we don't want; agent keeps writing LaTeX for an HTML target); raw HTML in doc
chunks (verbose, unpleasant).

### 4.4 Navigation model → **Multi-page, smart split + full-site search**
One page per chapter; oversized chapters split at natural sub-boundaries (Mode overlays →
one page per overlay). Persistent sidebar TOC on every page + client-side full-site search.
*Rejected:* single giant page (~1 MB+ with 26+ diagrams, sluggish); strict per-chapter
(leaves the ~25k-line Mode-overlays monster page).

### 4.5 Mermaid rendering → **CDN mermaid.js (client-side)**
Author ```mermaid fenced blocks; the browser renders them from a CDN-loaded mermaid.js.
Smallest repo footprint; build stays pure-Python. *Tradeoff accepted:* viewing requires
internet.
*Rejected:* vendored mermaid.js (larger repo); build-time pre-render to SVG (adds
puppeteer/headless-Chromium — heavy/fragile build dependency).

### 4.6 Layout figures (memory maps, byte-fields) → **Semantic HTML tables**
The ~5 figures Mermaid handles poorly become CSS-styled HTML tables: memory maps as
address-range rows, byte-fields as offset/size/field rows. Cells carry anchors and `[[ ]]`
links to the symbols they name — more navigable than any TikZ picture.
*Rejected:* Mermaid block-beta (young/finicky, byte-fields not its strength); render to
PNG/SVG (static, not navigable, regenerated per edit).

### 4.7 Cross-reference web → **Full noweb parity + HTML enhancements**
Reproduce the entire noweb web as HTML links (chunk headers with `+=`/prev/next, used-in
backlinks, per-chunk Defines/Uses, inline identifier→definition links, chunk-index and
identifier-index pages), **plus** hover popovers previewing the linked chunk, collapsible
chunk bodies, and a per-symbol "all references" panel.
*Rejected:* parity-only (misses the friendlier-than-PDF affordances); streamlined (drops the
index pages).

### 4.8 Code rendering → **Weaver-side tokenizer (one pass)**
Extend the existing token pass so the weaver emits syntax-highlight spans
(mnemonic/number/comment/label/directive/string) **and** identifier→definition links in a
single pass, styled by CSS. 6502's instruction set is small and fixed.
*Rejected:* client highlighter + separate link pass (re-tokenization clobbers injected
`<a>` tags; no first-class 6502 grammar); no highlighting.

### 4.9 Page boundaries / URLs → **H1 default + explicit slugged markers**
Every H1 (chapter) starts a page; an author-placed marker carrying a stable slug forces extra
breaks (Mode-overlays → one slugged page per overlay). Boundaries and URLs live in the source,
survive edits/renames.
*Rejected:* automatic size threshold (URLs shift as content grows); central manifest (split
policy lives away from prose).

### 4.10 Full-site search → **Single prebuilt index + CDN lib**
The weaver emits one whole-site index (prose + chunk names + defined symbols; raw code bodies
excluded by default as noisy) loaded once via lunr/MiniSearch from CDN. Genuine full-site,
ranked, prefix/fuzzy; no extra build tool.
*Rejected:* Pagefind (adds Rust/Node build tool; sharding advantage unused at this scale);
naive whole-corpus blob (heaviest payload, weakest ranking).

### 4.11 Layout/theme → **Three-pane docs site**
Persistent left chapter→page TOC (collapsible), center content at a readable measure, right
"on this page" outline tracking scroll. Light/dark toggle (system default). Serif body, sans
UI, monospace code.
*Rejected:* two-pane (no in-page outline); minimal single-column (least always-on
navigation).

### 4.12 Hosting → **Both, robustly (`file://` + GitHub Pages)**
Must open by double-click in Chrome *and* publish to github.io. Concrete rules:
1. **Search index inlined as JS** (`search-index.js` → `window.SEARCH_INDEX = {…}`), never
   fetched JSON — Chrome blocks `fetch` over `file://`.
2. **All internal links relative** (`./`, `../foo.html`), never absolute — absolute breaks on
   `file://` (no root) and on GitHub project subpaths (`user.github.io/repo/`).
3. **Explicit `.html` filenames** in links — `file://` won't auto-serve a directory index.
4. **`.nojekyll`** at site root so GitHub Pages doesn't strip underscore-prefixed assets.
   CDN libs load over `https` even on a `file://` page.

### 4.13 `[[ ]]` link resolution → **Link chunk names + defined symbols; style the rest**
`[[X]]` matching a chunk name → link to that chunk; matching a `@ %def` identifier → link to
its defining chunk; otherwise (raw `[[$XXXX]]`, arbitrary code) → styled monospace, no link.
Uses only data already computed; un-symbolized addresses stay visibly unlinked as an RE nudge.
*Rejected:* feed `.sym`/EQU map to auto-link addresses (extra weave input, mis-links during
active RE); link only chunk names (fewer prose links).

---

## 5. Architecture

```
main.nw  ──>  weave.py
                ├─ extract_chunk_info()      (UNCHANGED — chunk graph)
                ├─ tangle()                  (UNCHANGED — byte-perfect .asm)
                └─ HTML weaver (NEW)         (replaces the LaTeX emitter)
                     ├─ Markdown → HTML (per doc chunk)
                     ├─ 6502 tokenizer + identifier links (per code chunk)
                     ├─ multi-page splitter (H1 + slugged markers)
                     ├─ cross-ref/link resolver (sublabel → page#anchor)
                     ├─ search-index.js emitter
                     └─ three-pane template + CSS/JS (popovers, collapse, search, toggle)
```

- **Reused as-is:** `extract_chunk_info`, `tangle`, `expand_chunk`, `postprocess_apstr`,
  `postprocess_local_macro_labels`, and the whole `ChunkInfo` graph (names/labels/sublabels,
  `defines`, `defines_used`, `names_used`, `sublabels_used_in`, prev/next sublabels).
- **Removed:** every `weave_*` method emitting `\nw…` LaTeX, `make_safe_string`/`tt` LaTeX
  escaping, the `noweb.sty` dependency.
- **Build command unchanged:** `python3 weave.py main.nw output` — now tangles *and* emits the
  HTML site into `output/`.

### 5.1 Source format additions
- **Prose:** Markdown (CommonMark + GFM pipe tables + fenced ```mermaid).
- **Math:** inline `$…$` preserved, rendered by KaTeX auto-render.
- **Links:** `[[ ]]` resolved per §4.13; `<<chunk>>` refs in code unchanged.
- **Page markers:** an explicit author-placed marker with a stable slug (exact token TBD in
  implementation, e.g. an HTML-comment directive) forces a page break and names the page URL.

### 5.2 Anchors / slugs
- Page URLs: chapter slug (from heading) or explicit marker slug; lowercase, stable.
- In-page anchors: chunk sublabels (already unique) for chunks; slugified headings for
  sections. Cross-page links resolve a target sublabel/anchor to `relative/path.html#anchor`.

---

## 6. Figure handling summary

| Bucket | Count | Disposition |
|---|---|---|
| Flowchart-family TikZ | ~24 | Re-authored as Mermaid (Claude per-diagram; user reviews) |
| Memory-map / byte-field layouts | ~5 | Semantic HTML tables with field anchors + `[[ ]]` links |
| Rendered pixel-art PNGs | 11 | Stay as `<img>`; `render_*.py` retained |
| `verbatim` blocks | 17 | Fenced `<pre>` (no highlighting) |
| Regular data tables (`tabular`/booktabs) | ~6 | Markdown pipe tables |

---

## 7. Migration plan

All work is performed by Claude (scripts + per-diagram conversion); the user reviews only.
`verify.py` must pass at every commit.

1. **Weaver-first.** Build the new HTML weaver and validate it on a small sample (a single
   chapter or synthetic mini-doc): confirm tangle is unchanged, HTML builds, and all features
   work (links, popovers, collapse, tokenizer, multi-page, search, Mermaid, KaTeX, tables,
   three-pane, `file://` + served).
2. **Mechanical text flip.** One script flips all prose LaTeX→Markdown (sections→headings,
   `\emph`/`\textbf`/`\texttt`→Markdown, lists, `\ref`/`\label`→anchors, captions), keeping
   `$…$` and `[[ ]]`, and leaving diagrams/tables as **flagged TODO placeholders**. One safe
   commit; `main.nw` becomes Markdown; `verify.py` green.
3. **Diagrams/tables in batches.** Convert the ~24 Mermaid diagrams and ~5 HTML-table layouts
   in reviewable batches; user checks rendered HTML each batch.
4. **Retire & rewire.** Remove the LaTeX preamble/`noweb.sty`/TikZ; rewire skills and docs.

---

## 8. Downstream wiring (mechanical defaults)

- **Weaver:** extend `weave.py`; build command stays `python3 weave.py main.nw output`.
- **Skills:** rename `gen-pdf` → `gen-html` (tangle + weave HTML + run image renderers +
  copy assets); `/assemble` unchanged; update `/synthesize` references.
- **`targets.json`:** rename `pdf_pregen` → `site_pregen` (runs the `render_*.py` PNG
  generators).
- **Docs:** rewrite `CLAUDE.md` Build-pipeline + Noweb/LaTeX→Markdown + Prose/diagram rules
  (the `[[ ]]` wrapping rule and ASCII-only-code-comment rule survive; LaTeX-escape rules
  go); update `reveng.md`, `README.md`.
- **Remove:** LaTeX preamble in `main.nw` head, `noweb.sty`, TikZ infrastructure.
  **Keep:** `render_*.py`, `images/`.
- **Numbering/tables:** numbered chapters/sections in TOC + headings; regular data tables →
  Markdown pipe tables.

## 9. Acceptance criteria

- `verify.py` passes for all 16 targets at every migration commit (byte-perfect unchanged).
- `python3 weave.py main.nw output` produces a multi-page HTML site that:
  - renders all prose, code (highlighted + identifier-linked), Mermaid, KaTeX, and tables;
  - provides the full cross-ref web + popovers/collapse/reference-panels;
  - has a working three-pane layout, light/dark toggle, and full-site search;
  - works both by double-clicking in Chrome (`file://`) and when served / on GitHub Pages.

## 10. Deferred / to-confirm during implementation
- Exact page-break marker token syntax.
- Final library choice lunr vs MiniSearch; exact CDN versions pinned.
- Serif/sans/mono font stack specifics; dark-mode palette.
- Whether to also index code bodies in search (default: no).
