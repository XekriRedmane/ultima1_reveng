---
name: diagram-infrastructure
description: Diagram & figure conventions for Ultima I main.nw -- now Mermaid + HTML tables (the document weaves to HTML via weave_html.py; the old TikZ/LaTeX campaign was migrated).
metadata:
  type: project
---

main.nw LEANS IN to diagrams/flowcharts augmenting the prose (decided WITH
the user). The document now weaves to a multi-page **HTML site**
(`weave_html.py`); the original TikZ/PGF "diagram campaign" was fully
migrated to **Mermaid + HTML tables** (38 figures). Author all new diagrams
the Mermaid way -- never TikZ, never a LaTeX `figure` environment.

**Why:** the byte-perfect RE is the evidence base; diagrams are pure
prose-side augmentation. They render in the browser from CDN mermaid.js, so
there is no build dependency and no shell-escape concern.

**How to apply:**

- FLOWCHARTS / STATE MACHINES / CALL GRAPHS -> a fenced ```mermaid block
  (`flowchart TB`/`LR`, `stateDiagram`), followed immediately by a
  `**Figure — <caption>.**` paragraph. Cross-reference it from prose with a
  Markdown link to its anchor; put `<a id="fig:..."></a>` before the block
  if other prose needs to point at it.

- SHARED VISUAL LANGUAGE (reuse on every diagram so the set looks uniform):
  * accent = brick `#b03a2e`. Win/critical paths: `classDef win
    fill:#f6dccb,stroke:#b03a2e,stroke-width:2px;` on nodes, and
    `linkStyle N stroke:#b03a2e,stroke-width:2px,color:#b03a2e` on the
    critical edge(s) (N is the 0-based edge index in declaration order --
    count carefully; `<-->` and dotted edges each count as one).
  * dashed `-.->` for death/discarded/secondary paths.
  * shapes: `([...])` stadium for start/terminal, `{{...}}` hexagon for a
    hub (e.g. OUT), `{...}` diamond for a decision, `[/.../]` parallelogram
    for I/O (key poll, fetch), `[...]` rectangle for a process.

- MERMAID LABEL PITFALLS (learned converting the 38):
  * AVOID raw `<` / `>` inside node *labels* -- the lexer can choke even in
    quoted strings. Reword ("under"/"over") or use the unicode glyphs. The
    `<-->` edge syntax at statement level is fine.
  * Quote any label / edge-label containing `()`, `:`, `=`, or commas, e.g.
    `["..."]` and `|"yes (= Space Ace)"|`.
  * `<br/>` makes a line break; `$NN`, middle-dot, multiplication-sign and
    plus/minus glyphs are fine literally.
  * The weaver HTML-escapes the block and mermaid entity-decodes it, so
    escaping is correct -- write the characters you want mermaid to see.

- BYTE-FIELD / RECORD / MEMORY-MAP LAYOUTS -> a block-level **HTML table**
  (`<table class="bytefield">` offset/size/field; `<table class="memmap">`
  address-band with a `<tr class="hot">` highlight; `<table class="soa">`
  for structure-of-arrays). Raw HTML must start at column 0 with blank
  lines around it; `[[ ]]` inside it is still resolved, so link field cells
  to their symbols. NOT Mermaid (block-beta is too fragile for these).

- DATA / LOOKUP TABLES -> Markdown pipe tables. Wrap a raw `$NN` value that
  sits next to another `$` (error-code/opcode tables) in backticks so the
  `$…$` math rule can't read the span between them as math.

- RENDERED PIXEL ART (fonts, tiles, sprites, screens) stays a PNG produced
  by a `render_*.py` script and embedded with `![alt](images/<name>.png)` +
  a `**Figure — …**` caption. The weaver copies `images/` into the site.

- QUALITY BAR (every diagram): FAITHFUL to the RE'd behaviour (derive every
  transition/branch from the asm + subsystem memory; a wrong diagram is
  worse than none); captioned and referenced from prose; symbols not raw
  hex except in memory/disk-layout tables; PROSE-SIDE ONLY (never touch a
  code chunk -- the 16/16 byte-perfect verify stays green). Build check is
  `/gen-html` (weave_html.py) with a link check reporting 0 broken links.

INVENTORY: 23 Mermaid diagrams + ~15 tables cover every warranting
subsystem across the Design and Implementation parts (mode FSM, win FSM,
mode-loop template + OUT/DNG/SPA variants, dungeon generator, NPC/combat AI,
chargen point-buy, double-buffer/tile-blit/ray-march/sprite rendering, boot
& load chain, GAME_LOAD, command dispatch, disk formatter, Mondain AI, the
two MAKE.INDATA decompressors; player/object/TCMAPS layouts, the file-
library/MLI/STUPH/vector/DNG-spell/perspective/memory-map tables). Adding a
figure for a new subsystem follows the same recipe.
