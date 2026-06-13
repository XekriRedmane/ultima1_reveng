---
name: makeindata-subsystem
description: Ultima I MAKE.INDATA -- the one-shot initial-game-state / intro-art builder ($1E00, 13877 bytes). SCOUTED round 24; not yet decomposed.
metadata:
  type: project
---

MAKE.INDATA ($1E00-$5435, 13877 bytes) is NOT an overlay -- it is a one-shot
BUILDER BRUN at cold start (from U1.SYSTEM / the page-1 startup tail). It unpacks
the intro artwork and the initial game-state image into RAM, runs a copied-in
helper, and (per the OUT chapter's deduction) likely generates the packed world
map for /U1.VARS at $6000. Loads/runs at $1E00, well below the overlay base.
SCOUTED round 24; decompose next.

**STRUCTURE (page map):**
- $1E00-~$2000: CODE (~512 bytes). The decompressor + the build driver.
- ~$2200-$3E00: packed ART/data (high zero density, RLE-ish; the "*U*U*U"
  hi-res pixel runs). 
- $4000-$5435: more data; $49EC is a decompress SOURCE the driver points at.
- No ASCII strings anywhere -- pure binary (code + compressed graphics/map).

**THE BUILD DRIVER ($1F17, reached via JMP at $1E00):**
1. PAGE_COPY ($1EFD: copy $FF pages from ($06) to ($08)) is called twice:
   - copy $2000-$27FF (8 pages) -> $8700-$8EFF, then `JSR $8700` -- a helper
     routine makeindata STAMPS into $8700 and runs (installs FONT_DRAW / the
     $15B0 blitter? -- the u1intro chapter says MAKE.INDATA installs the
     low-RAM text helpers; verify the $8700 payload's role).
   - copy $27BD-... (38 pages, $26) -> $6000-... -- this is the ART_BASE region
     ($6000-$8Fxx) the U1.INTRO chapter consumes (ART_CASTLE/PANEL/STRIPS/WIPE/
     CURTAIN/BIRD). The decompressor (head $1E03/$1E47) unpacks the rest.
2. Sets the decompress pointer $00/$01 = $49EC and JSR $1E03 (decompressor).
3. JSR $8700 (the copied-in helper).
4. $1F5C clears HGR page 2 ($4000-$5FFF), flips to hi-res ($C057/$C052/
   TXTPAGE2/$C050), then an LFSR fizzle (LSR/ROR $00/$01, EOR #$B4) -- the same
   dissolve generator U1.INTRO uses; MAKE.INDATA likely pre-renders the title
   image into page 2 here.

**THE DECOMPRESSOR ($1E03 driver, $1E47 inner):** reads a byte stream via the
($00) pointer; a byte == sentinel $08 (set at $1E0D from the stream header)
introduces a run/copy; the $1E1D address math (TXA / AND #$C7 / ROR $02 /
ASL/ROL $03 ...) computes HI-RES screen row addresses from a row index 0..$BF
(192 rows) -- so it decompresses straight into the hi-res raster. $1D/$1F are
state flags (BIT $1D / BMI tests = which sub-pass). Decode this carefully; it is
the key to reading every ART_* blob AND (probably) the world map.

**WHAT IT RESOLVES when decompressed:**
- The ART_* EQU semantics in the U1.INTRO chapter (currently "named for the
  consumer, semantics pending") and the ONE remaining TODO-SYM
  (ART_BASE..$8Fxx upper bound, main.nw ~line 2398).
- The four-continent WORLD MAP: OUT round 12 found NO verbatim 4096-cell map in
  makeindata via a naive RLE scan -> the map is GENERATED/packed here. Render
  the four continents once the decompressor is understood (own graphics round).

**DECOMPOSITION PLAN (next round):** clone the gen_gen pipeline but with
BASE=0x1E00 (not $8956) and NO overlay engine-API EQUs (makeindata predates the
engine -- it calls ROM + its own code + the $8700 payload). (1) Disassemble the
$1E00-~$2000 code region fully (decompressor + driver). (2) Port the
decompressor to Python and run it on each packed blob to recover the artwork +
map as plain rasters. (3) Emit the packed data as labeled HEX spans (ART_* +
MAP_*). (4) Render the intro frames AND the four continents. This is the LAST
target -- finishing it clears the final ORG stub and the last TODO-SYM.
