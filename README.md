# Apple II Reverse-Engineering Template

A template repository for autonomously reverse engineering an Apple II game from a `.dsk` disk image into a literate-programming document (`main.nw`) that:

- assembles to **byte-perfect** copies of the original binaries,
- explains how the game works in enough detail to **reproduce or port it in any language, on any platform**, and
- weaves into a cross-referenced PDF with rendered sprites, fonts, and figures.

The work is done by Claude Code running the `reverse-engineer` agent, which operates continuously and unattended: it bootstraps reference binaries from the disk image, reverse engineers the boot chain, loader, game code, and data, renders graphics, writes platform-independent design chapters, and commits/pushes after every verified round.

## Quick start

1. **Create a new repository from this template** (GitHub: "Use this template"), clone it.
2. **Add the disk image**: copy your game's `.dsk` into the repo root and commit.
3. **Configure the container**: create a `.env` file next to `docker-compose.yml`:

   ```
   GIT_USER_NAME=Your Name
   GIT_USER_EMAIL=you@example.com
   ```

   **Authentication** — pick one:

   - **Subscription (Pro/Max):** leave `ANTHROPIC_API_KEY` unset. The first time
     you start the container, run `claude` (not `yolo`), complete the browser
     login it prompts for, then exit. The credentials are written to the
     persistent state dir (`CLAUDE_STATE_DIR`, symlinked to `~/.claude.json`
     inside the container), so you only log in once — later sessions and the
     `yolo` autonomous mode reuse it.
   - **API key:** add `ANTHROPIC_API_KEY=sk-ant-...` to the `.env` file. This
     uses metered API billing, which is **separate from and billed independently
     of a subscription** — long autonomous runs can get expensive this way.

   SSH keys for `git push` are mounted read-only from `~/.ssh` (see `docker-compose.yml`).
4. **Build and enter the container**:

   ```bash
   docker compose build
   docker compose run --rm re
   ```

5. **Start the agent** — inside the container:

   ```bash
   yolo        # alias for: claude --dangerously-skip-permissions
   ```

   then tell it:

   > Start reverse engineering the disk image. Work autonomously until done.

   The agent reads `reveng.md` (the process), `CLAUDE.md` (the conventions), and `TODO.md` (the loop state), and goes. Sessions are resumable: a fresh session picks up from the `/re-status` scoreboard and `TODO.md`.

## What's in the box

| Path | Purpose |
|---|---|
| `reveng.md` | The process bible: rounds, standing rules, autonomy protocol, definition of done |
| `CLAUDE.md` | Conventions: assembly style, chunk rules, annotation rules, prose rules, pitfalls |
| `main.nw` | Skeleton literate document (the agent fills it in) |
| `weave.py`, `noweb.sty` | Noweb tangler and LaTeX style |
| `targets.json.example` | Example project manifest (the real one is created during bootstrap) |
| `.claude/agents/reverse-engineer.md` | The autonomous driver agent |
| `.claude/skills/bootstrap/` | Round 0: disk image → reference binaries + manifest (`dsk_tool.py`) |
| `.claude/skills/re-status/` | Scoreboard of every completion criterion |
| `.claude/skills/assemble/` | Tangle + assemble + byte-perfect verification |
| `.claude/skills/disassemble/`, `re-next/`, `find-gaps/`, `trace-address/` | The RE loop |
| `.claude/skills/annotate/`, `chunk-placement/` | Documentation quality passes |
| `.claude/skills/synthesize/` | Platform-independent design chapters for porters |
| `.claude/skills/gen-pdf/` | PDF build |
| `.claude/scripts/dasm6502.py` | 6502 disassembler for reference binaries |
| `.claude/scripts/render_hires.py` | Apple II hi-res graphics rendering library (PNG output) |
| `Dockerfile`, `docker-compose.yml` | Agent container: Claude Code, dasm, texlive, Python (Pillow, absl-py), gh |

## Layout produced by a run

- `targets.json` — project manifest: game, disk image, sector order, assembly targets
- `reference/` — flat binaries extracted from the disk image (the ground truth)
- `maps/` — track/sector→page map files that make `reference/` reproducible
- `output/` — tangled `.asm`, assembled `.bin`/`.lst`/`.sym`, and the PDF (gitignored)
- `images/` — rendered sprites, fonts, and screens, embedded in the document
- `TODO.md` — the loop state: milestones, work queue, blocked list

## Requirements

- Docker (the container brings Claude Code, dasm, pdflatex, and Python deps)
- A Claude Code login: either a Pro/Max **subscription** (log in once inside the
  container) or an **Anthropic API key** (metered, billed separately) — see step 3
- The legal right to reverse engineer the disk image you supply
