# synthesize

Write or update the synthesis layer of main.nw: the chapters that explain how the game *works* as a game, independent of 6502 assembly. This is what makes the document useful to its audience.

## The audience

The reader of main.nw wants to learn how the game was written and how it works, in enough detail to **reproduce or port the game in any language, on any platform** — not just 6502 assembly on the Apple II. Annotated assembly alone does not serve this reader: they need the design recovered from the code, stated in platform-independent terms, with the assembly as evidence.

## Usage

```
/synthesize            # audit the synthesis layer, fill the biggest gap
/synthesize SUBSYSTEM  # write/update the synthesis for one subsystem
```

## What the synthesis layer contains

These are prose chapters/sections in main.nw, separate from (and cross-referencing) the per-routine chunks:

1. **Game overview** — what the player sees and does: objective, controls, scoring, lives, level progression, enemies and hazards. Written as if describing the game to someone who has never seen it.
2. **Architecture overview** — the program's shape: boot/load flow, the main loop and its frame structure, the major subsystems and how they communicate (shared zero-page state, flags, self-modifying patches). A diagram or table of the per-frame call sequence.
3. **Data structure reference** — every persistent game-state structure described abstractly: entity slot arrays, the record layouts, coordinate systems (world-X vs screen column, floor/band numbering), timers and counters. For each: fields, invariants, who reads/writes it. Pseudocode-style struct definitions are encouraged.
4. **Algorithm descriptions** — for each non-trivial mechanic, platform-independent pseudocode plus the design intent: spawning logic, AI/chase behavior, collision detection, physics (movement steps, gravity/jump arcs), PRNG, scoring rules, difficulty progression, animation sequencing.
5. **Rendering pipeline** — what is Apple II-specific (hi-res page layout, interlace blitting, page flipping, color artifacts) vs. what is portable (sprite frames, animation timing, dirty-region strategy). A porter needs to know which is which explicitly.
6. **Porting notes** — a section per subsystem flagging the 6502/Apple II idioms a port must replace: self-modifying code patterns and what state they encode, cycle-timing dependencies, memory-layout tricks, softswitch usage, and what the portable equivalent is.

## Process

1. **Audit.** List which of the six sections above exist in main.nw and which subsystems each covers. Compare against the subsystems actually documented at the assembly level (grep for `##`/`###` Markdown headings and the agent-memory notes). The gap list is the work queue.
2. **Recover the design, don't restate the code.** For each target subsystem, re-read the relevant annotated routines and write what the *programmer was implementing*: state machines and control flow (draw them as Mermaid `flowchart`/`stateDiagram` in ```mermaid blocks — accent stroke `#b03a2e` for win/critical paths, dashed `-.->` for death/discarded), formulas (in `$…$` math or pseudocode, not LDA/ADC sequences), tuning constants (collected into pipe tables with their gameplay meaning), and byte/record layouts (as HTML tables).
3. **Use the document's existing evidence.** Cross-reference routines and variables with `[[SYMBOL]]` refs. Reference rendered sprite/font images by their figures. Follow all prose rules in CLAUDE.md (address wrapping, symbol preference, Mermaid/table conventions).
4. **Pseudocode convention.** Use typed, language-neutral pseudocode in fenced code blocks (```text) or Markdown lists. Name things with the same symbols as the assembly (`ZP_PLAYER_Y` etc.) so the reader can drill down.
5. **Place chapters deliberately.** Synthesis chapters go before the assembly chapters they summarize (overview first, evidence after) or in a dedicated part — follow the document's established structure, and propose reorganization when the structure fights comprehension.
6. **Verify and commit.** Synthesis work is prose-only, but still run the full build gate (tangle, assemble, verify, then `/gen-html`) before committing — broken `[[ ]]` refs and malformed Mermaid blocks in new prose are common.

## Quality bar

A section is done when a competent programmer who has never seen 6502 assembly could reimplement that subsystem from the synthesis section alone, using the assembly chapters only to check edge cases. If a behavior can only be learned by reading the assembly, the synthesis is not done.
