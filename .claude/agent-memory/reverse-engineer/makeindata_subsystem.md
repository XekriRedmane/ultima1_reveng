---
name: makeindata-subsystem
description: Ultima I MAKE.INDATA -- the cold-start title/art builder ($1E00, 13877 bytes). DECOMPOSED round 25, byte-perfect; both title screens recovered + rendered.
metadata:
  type: project
---

MAKE.INDATA ($1E00-$5435, 13877 bytes) is the cold-start BUILDER (the first
program U1.SYSTEM chains to, before U1.INTRO). NOT an overlay -- it predates the
MI.U1 engine, runs once at $1E00 (well below the overlay base), never calls the
engine, and is discarded. DECOMPOSED round 25; byte-perfect (13877/13877).

**WHAT IT DOES (the build driver MI_BUILD $1F17, reached via JMP at $1E00):**
1. MI_PAGE_COPY ($1EFD: copy N pages (X/Y src, A=dest hi) to ($08)) twice:
   - 8 pages $2000(file) -> $8700, then JSR $8700 -- the payload (see below).
   - 38 pages $27BD(file) -> $6000 -- the intro ART region (ART_BASE..$85FF).
2. Sets MI_SRC=$49EC and JSR MI_DECOMP -- decompress the castle title onto
   hi-res PAGE 1 ($2000).
3. JSR MI_PAYLOAD ($8700) -- builds the ORIGIN logo at $9600.
4. JSR MI_FIZZLE ($1F5C) -- clears page 2, displays it, LFSR-dissolves the
   ORIGIN logo from $9600 onto page 2. Keypress -> MI_LOGO_BLIT (instant copy).
5. Key-abortable settle delay, RTS back to U1.SYSTEM's chain.
Net result: castle title sits ready on hi-res page 1 for U1.INTRO to animate;
ORIGIN logo is the first thing shown (page 2). Two title screens, both built.

**THE STREAM DECOMPRESSOR (MI_DECOMP $1E03 driver + MI_DECODE $1E47 inner):**
Fills a 40x192 hi-res page COLUMN-MAJOR (Y=39..0 cols, MI_COL=191..0 rows). The
$1E1D math (TXA/AND #$C7/ROR-ROL dance) is the CANONICAL Apple II hi-res row->
addr formula targeting $2000 (verified against the standard formula). Header =
2 sentinel bytes ($08/$09 here). MI_DECODE is a 3-mode state machine, ONE tightly
interwoven scope ($1E47-$1EFC, kept as one SUBROUTINE -- the run continuations
branch back into the header parser at .startA and share a single store-and-return
exit .store_ret): literal store; sentinel-A = vertical (length,value) run down
the column; sentinel-B = background (rows,span) run with a saved back-reference
(MI_BACK) that rewinds the stream to replay a region. Every stream-ptr advance is
a full 16-bit INC $00/BNE/INC $01 (NOT bare INC -- the first decompose attempt
diverged 83 bytes by using bare INC).

**THE $8700 PAYLOAD (file $2000-$27FF, runs at $8700):** itself a tiny RLE
unpacker + its own packed stream (starts at run-addr $876F = file $206F). Zeroes
$9600-$B5FF, unpacks a high-bit-flagged stream (bit7 clear = literal, bit7 set =
(value,count) run), ORs #$80 onto EVERY output byte, stops when dest hi == $B7.
Output = the ORIGIN SYSTEMS INC. logo (a hires page-2-layout image at $9600).

**DATA REGIONS (exact, byte-perfect coverage = 512 code + these three):**
- MI_PAYLOAD_IMAGE $2000-$27BC (1981 b): the $8700 payload (code+its stream).
- MI_ART_IMAGE     $27BD-$49EB (8751 b): the intro art, copied to $6000. Runs
  $6000-$85FF; first $E2 bytes are zero pad before the first frame. THIS is the
  on-disk source of the U1.INTRO chapter's ART_* EQUs (ART_BASE $6000 ..
  ART_BIRD $81CA, data through $85FF). Resolved the last TODO-SYM: art ends at
  $85FF, NOT the guessed $8Fxx.
- MI_TITLE_STREAM  $49EC-$5434 (2633 b): the packed castle-title stream
  MI_DECOMP reads. Consumes to end-of-file.
- The $27BD art src and the $2000 payload page overlap by 67 zero bytes (pad).

**RENDERED (standing rule):** images/makeindata_title.png (the castle-by-the-sea
night scene -- moon, stars, castle, blue sea) + images/makeindata_origin.png (the
ORIGIN SYSTEMS INC. logo). Both embedded as figures.

**PIPELINE / TOOLS kept for reuse:**
- .claude/scripts/makeindata_emu.py -- a tiny scoped 6502 emulator (the right
  way to recover output from tricky backward-branch decompressors -- emulate,
  don't hand-translate control flow). decompress_at(src_addr) returns the page-1
  raster; running the $8700 payload then reading $9600 gives the logo.
- .claude/scripts/makeindata_decomp.py -- an early hand-port (superseded by the
  emulator; keep the emulator as canonical).
- .claude/scripts/render_makeindata.py -- de-interleaves both pages and renders.
- .claude/scripts/mi_author.py -- the chapter generator (code chunks hand-written
  + faithfully transcribed; data emitted as HEX). Heading level = \section under
  the "Game data" chapter (\subsection inside), label sec:makeindata.

**WORLD MAP NOTE:** OUT round 12 deduced the world map is GENERATED (no verbatim
4096-cell stream). MAKE.INDATA does NOT contain or build the /U1.VARS world map
either -- it only builds the two TITLE screens + the intro art. The $9600 buffer
is the ORIGIN logo, not a map. The four-continent map render remains tied to OUT's
RLE map loader (the packed maps live in /U1.VARS, absent from the crack disk), not
to makeindata. So "render the four continents" is NOT a makeindata deliverable;
it would need the /U1.VARS file which the 4am crack omits. Record as blocked.
