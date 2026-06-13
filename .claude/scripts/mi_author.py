#!/usr/bin/env python3
"""Author the MAKE.INDATA chapter and write it to /tmp/mi_chapter.nw.

Produces the full noweb replacement for the old single-stub
`\section{MAKE.INDATA}` ... `<<makeindata.asm>>` block in main.nw.
"""
BASE = 0x1E00
REF = open('reference/makeindata.bin', 'rb').read()


def seg(a, b):
    return REF[a - BASE:b - BASE]


def hexlines(data, indent='        '):
    out = []
    for i in range(0, len(data), 8):
        row = data[i:i + 8]
        out.append(indent + 'HEX ' + ' '.join(f'{b:02x}' for b in row))
    return '\n'.join(out)


payload = hexlines(seg(0x2000, 0x27BD))
art = hexlines(seg(0x27BD, 0x49EC))
stream = hexlines(seg(0x49EC, 0x5435))

CH = r"""\section{MAKE.INDATA}
\label{sec:makeindata}

\texttt{MAKE.INDATA} is the cold-start \emph{builder}: the very first
program \texttt{U1.SYSTEM} chains to (before \texttt{U1.INTRO}). Unlike
every other code file in the game it is not an overlay and never calls the
\texttt{MI.U1} engine --- it predates the engine, runs once at [[$1E00]]
well below the overlay base, and then is discarded. Its whole job is to
unpack two hi-res title screens and a slab of intro artwork into memory,
dissolve the publisher logo onto the screen, and leave the castle picture
sitting on hi-res page~1 for \texttt{U1.INTRO} to animate.

The file is 13877 bytes: 512 bytes of code at [[$1E00]]--[[$1FFF]] and
three packed data regions. Two small, near-identical \textbf{RLE
decompressors} do all the work --- one built into this file, one stamped
into low memory at [[$8700]] and run there. Between them they reconstruct:

\begin{itemize}
  \item the \textbf{castle title} (the night scene of Lord British's
        castle by the sea), decompressed straight onto hi-res page~1
        ([[HGR1]]) from the stream at [[MI_TITLE_STREAM]];
  \item the \textbf{ORIGIN SYSTEMS} publisher logo, unpacked to a buffer
        at [[$9600]] by the [[$8700]] payload, then dissolved onto hi-res
        page~2 ([[HGR2]]) by the fizzle reveal;
  \item the \textbf{intro artwork} --- the key frames, castle strips, gate
        panels, sky-wipe rows, curtain and bird sprites the
        \texttt{U1.INTRO} animation draws from --- block-copied verbatim to
        [[ART_BASE]] ([[$6000]]--[[$85FF]]).
\end{itemize}

Recovering the two compressed screens (by porting the decompressor to a
small 6502 emulator, \texttt{.claude/scripts/makeindata\_emu.py}) is what
finally pins the \texttt{ART\_*} blobs the \texttt{U1.INTRO} chapter named
only by their consumers, and settles that chapter's last open question
about the artwork extent: the region ends at [[$85FF]], not the guessed
[[$8Fxx]].

\begin{figure}[ht]
  \centering
  \includegraphics[width=0.8\textwidth]{images/makeindata_title.png}
  \caption{The castle-title screen recovered by replaying the
    [[MI_DECOMP]] stream decompressor on [[MI_TITLE_STREAM]]: the night
    scene of Lord British's castle by the sea, dropped onto hi-res page~1.
    \texttt{U1.INTRO} paints over this picture frame by frame.}
  \label{fig:mi-title}
\end{figure}

\begin{figure}[ht]
  \centering
  \includegraphics[width=0.8\textwidth]{images/makeindata_origin.png}
  \caption{The \textsc{Origin Systems Inc.} publisher logo, unpacked to
    [[$9600]] by the [[$8700]] payload and dissolved onto hi-res page~2 by
    the [[MI_FIZZLE]] reveal. This is the first thing the player sees.}
  \label{fig:mi-origin}
\end{figure}

\subsection{Defines}

The builder talks only to the ROM, to its own routines, and to the payload
it stamps into [[$8700]]; it needs no engine symbols. The zero page is its
private scratch (stream pointers, the decompressor state machine, the
fizzle's \textsc{lfsr}). The high data buffers ([[$8700]], [[$9600]]) and
the artwork base ([[ART_BASE]]) are shared with the payload and with
\texttt{U1.INTRO}.

<<makeindata defines>>=
; --- Zero page: decompressor + driver scratch ---
MI_SRC          EQU $00         ; compressed-stream pointer (lo/hi)
MI_DST          EQU $02         ; hi-res raster destination pointer
MI_BACK         EQU $04         ; saved stream pointer (back-reference)
MI_VAL          EQU $06         ; current data byte / copy source pointer
MI_REP          EQU $07         ; background-run outer repeat count
MI_SENT_A       EQU $08         ; run sentinel A / copy dest pointer
MI_SENT_B       EQU $09         ; run sentinel B / fizzle masked-bit scratch
MI_RUNLEN       EQU $1C         ; vertical-run remaining length
MI_F_RUN        EQU $1D         ; bit7: inside a vertical run
MI_SPAN         EQU $1E         ; background-run span counter
MI_F_BACK       EQU $1F         ; bit7: inside a background run
MI_PAGES        EQU $FF         ; PAGE_COPY page counter
MI_ROWS         EQU $F9         ; background-run inner row counter
MI_COL          EQU $1B         ; decompressor row counter (X mirror)
; --- Soft switches and ROM ---
KBD             EQU $C000       ; keyboard data / strobe-pending flag
DRIVE_OFF       EQU $C0E8       ; slot 6 drive motor off (delay tap)
TXTCLR          EQU $C050       ; graphics on
MIXCLR          EQU $C052       ; full-screen graphics
TXTPAGE2        EQU $C055       ; display hi-res page 2
HIRES           EQU $C057       ; hi-res mode
; --- Buffers shared with the payload and U1.INTRO ---
MI_PAYLOAD      EQU $8700       ; stamped-in font/logo unpacker + its stream
HGR2            EQU $4000       ; hi-res page 2 (the fizzle target)
LOGO_BUF        EQU $9600       ; ORIGIN logo image (built by the payload)
ART_BASE        EQU $6000       ; intro artwork base (see U1.INTRO chapter)
@ %def MI_SRC MI_DST MI_BACK MI_VAL MI_REP MI_SENT_A MI_SENT_B MI_RUNLEN
@ %def MI_F_RUN MI_SPAN MI_F_BACK MI_PAGES MI_ROWS MI_COL KBD DRIVE_OFF
@ %def TXTCLR MIXCLR TXTPAGE2 HIRES MI_PAYLOAD HGR2 LOGO_BUF ART_BASE

\subsection{Entry and the stream decompressor}

The file's first instruction jumps over the decompressor to the build
driver; the decompressor itself is the entry point the driver
[[JSR]]s back into.

<<makeindata entry>>=
        ORG $1E00
MI_ENTRY:
        JMP MI_BUILD                    ; skip the decompressor to the driver
@ %def MI_ENTRY

The decompressor reconstructs a 192-row by 40-byte hi-res screen
\emph{column by column}. The outer driver [[MI_DECOMP]] walks the 40
columns right-to-left ([[Y]] = 39..0) and, within each column, the 192
rows bottom-to-top ([[MI_COL]] = 191..0). For every row it converts the
row index into that scanline's hi-res base address with the canonical
Apple~II interleave math (the [[AND #$C7]] / [[ROR]]--[[ROL]] dance fills
[[MI_DST]] with the page-1 base [[$2000]] plus the row's interleaved
offset), then calls the inner state machine [[MI_DECODE]] to emit one cell.

Two header bytes at the head of the stream load the run \textbf{sentinels}
[[MI_SENT_A]] and [[MI_SENT_B]]: a literal whose value equals neither
sentinel is stored as-is, while a sentinel byte introduces a run.

<<makeindata decomp driver>>=
        ORG $1E03
MI_DECOMP:
        SUBROUTINE
        ; Decompress an RLE stream onto a hi-res page-1 raster.
        ;
        ; Inputs:
        ;   MI_SRC  -- pointer to the compressed stream (lo/hi)
        ;
        ; Behavior:
        ;   Reads two sentinel bytes, then fills the 40x192 hi-res
        ;   screen column-by-column (Y=39..0), row-by-row within each
        ;   column (MI_COL=191..0). Each row index is converted to its
        ;   hi-res scanline base in MI_DST by the interleave math, then
        ;   MI_DECODE emits one cell of the column.
        ;
        ; Modifies:
        ;   MI_DST, MI_COL, the decoder state (MI_F_RUN/MI_F_BACK/...)
        ; Clobbers: A, X, Y
        LDX #$00
        STX MI_F_RUN                    ; MI_F_RUN <- #$00 (no run yet)
        STX MI_F_BACK                   ; MI_F_BACK <- #$00
        STX MI_ROWS                     ; MI_ROWS <- #$00
        LDA (MI_SRC,X)                  ; first header byte = sentinel A
        STA MI_SENT_A
        INC MI_SRC
        LDA (MI_SRC,X)                  ; second header byte = sentinel B
        STA MI_SENT_B
        INC MI_SRC
        LDY #$27                        ; Y <- #$27 (column 39)
.col    LDX #$BF                        ; X <- #$BF (row 191)
        STX MI_COL
.row    TXA                             ; --- row index -> hi-res base ---
        AND #$C7
        STA MI_DST
        ORA #$08
        STA MI_DST+1
        TXA
        ASL
        ASL
        ROR MI_DST
        ASL
        ROL MI_DST+1
        ROR MI_DST
        ASL
        ROL MI_DST+1
        ASL
        ROR MI_DST
        JSR MI_DECODE                   ; emit one cell into [MI_DST]+Y
        DEC MI_COL
        LDX MI_COL
        CPX #$FF
        BNE .row                        ; until the column is exhausted
        DEY
        CPY #$FF
        BNE .col                        ; until all 40 columns are done
        RTS
@ %def MI_DECOMP

The inner decoder [[MI_DECODE]] is a small state machine with three
modes, selected by the two run flags, and it is tightly interwoven: the
run continuations branch back into the header parser and share a single
store-and-return exit. We keep the whole [[$1E47]]--[[$1EFC]] machine in
one scope. In the idle state it fetches the next stream byte: if it
matches sentinel~A it begins a \emph{vertical run} (a [[(length, value)]]
pair painted straight down the column); if it matches sentinel~B it begins
a \emph{background run} (a [[(rows, span)]] pair that fills many rows with
a value, can repeat across a span, and saves a back-reference so a region
can be replayed); otherwise the byte is a literal cell. The two run states
([[.run]] for sentinel~A, [[.back]] for sentinel~B) resume mid-run on the
next call without re-reading the header.

<<makeindata decode>>=
        ORG $1E47
MI_DECODE:
        SUBROUTINE
        ; Emit one decompressed cell into [MI_DST]+Y; advance the stream.
        ;
        ; Behavior:
        ;   Idle: fetch a byte. ==MI_SENT_A -> start a vertical run
        ;   (length MI_RUNLEN, value MI_VAL). ==MI_SENT_B -> start a
        ;   background run (MI_ROWS rows, MI_SPAN span; saves MI_BACK).
        ;   Else store the literal. The run states (.run/.back) resume on
        ;   later calls via MI_F_RUN / MI_F_BACK and rejoin the header
        ;   parser to nest runs; .store_ret is the common exit.
        ;
        ; Modifies: MI_SRC, the decoder state, [MI_DST]+Y
        ; Clobbers: A, X
        LDX #$00
        BIT MI_F_RUN
        BMI .run                         ; resume a vertical run
        BIT MI_F_BACK
        BMI .back                        ; resume a background run
        LDA (MI_SRC,X)
        STA MI_VAL
        CMP MI_SENT_A
        BNE .not_a
.startA INC MI_SRC                       ; --- sentinel A: (length, value) ---
        BNE .a1
        INC MI_SRC+1
.a1     LDA (MI_SRC,X)
        STA MI_RUNLEN
        INC MI_SRC
        BNE .a2
        INC MI_SRC+1
.a2     LDA (MI_SRC,X)
        STA MI_VAL
        INC MI_SRC
        BNE .a3
        INC MI_SRC+1
.a3     SEC
        ROR MI_F_RUN                     ; enter vertical-run state
        BNE .run
.not_a  CMP MI_SENT_B
        BNE .literal
        INC MI_SRC                       ; --- sentinel B: (rows, span) ---
        BNE .b1
        INC MI_SRC+1
.b1     LDA (MI_SRC,X)
        STA MI_REP
        STA MI_ROWS
        INC MI_SRC
        BNE .b2
        INC MI_SRC+1
.b2     LDA (MI_SRC,X)
        STA MI_SPAN
        INC MI_SRC
        BNE .b3
        INC MI_SRC+1
.b3     LDA MI_SRC
        STA MI_BACK                      ; save the stream ptr for replay
        LDA MI_SRC+1
        STA MI_BACK+1
        LDA #$80
        STA MI_F_BACK                    ; enter background-run state
        BNE .back
.literal LDA MI_VAL
        STA (MI_DST),Y
        INC MI_SRC
        BNE .store_ret
        INC MI_SRC+1
.store_ret RTS
        ; --- .run: vertical-run continuation ($1EB1) ---
.run    LDA MI_VAL
        STA (MI_DST),Y
        DEC MI_RUNLEN
        BNE .store_ret                   ; more run cells -> store and return
        LDA #$00
        STA MI_F_RUN                     ; vertical run finished
        BIT MI_F_BACK
        BPL .store_ret                   ; no background run -> done
        DEC MI_ROWS
        DEC MI_ROWS                      ; charge the run against the budget
        BNE .tail
        ; --- .back: background-run fetch ($1EC7) ---
.back   LDA (MI_SRC,X)
        CMP MI_SENT_A
        BNE .store
        LDA MI_ROWS
.chkrow BNE .startA                      ; rows remain: nest a vertical run
        LDA MI_BACK
        STA MI_SRC
        LDA MI_BACK+1
        STA MI_SRC+1                     ; rewind to the saved region
        BNE .chkrow                      ; re-test the (reloaded) budget
.store  STA (MI_DST),Y
        INC MI_SRC
        BNE .tail
        INC MI_SRC+1
.tail   DEC MI_ROWS
        BNE .store_ret
        LDA MI_REP
        STA MI_ROWS                      ; reload the row budget
        DEC MI_SPAN
        BEQ .span_done
        LDA MI_BACK
        STA MI_SRC
        LDA MI_BACK+1
        STA MI_SRC+1                     ; rewind for the next span row
        RTS
.span_done
        LDA #$00
        STA MI_F_BACK                    ; the background run is finished
        RTS
@ %def MI_DECODE

\subsection{The page-copy helper}

[[MI_PAGE_COPY]] copies [[MI_PAGES]] whole pages from [[(MI_VAL)]] to
[[(MI_SENT_A)]]; the driver sets the pointers and the page count in [[X]],
[[Y]], [[A]] before each call. It is the only thing in the file that moves
the two block regions (the payload and the artwork) into place.

<<makeindata page copy>>=
        ORG $1EFD
MI_PAGE_COPY:
        SUBROUTINE
        ; Copy MI_PAGES whole pages from (MI_VAL) to (MI_SENT_A).
        ;
        ; Inputs: X/Y = source lo/hi, A = dest hi (dest lo forced 0),
        ;         MI_PAGES = page count.
        ;
        ; Behavior:
        ;   Sets the source/dest pointers from X/Y/A, then copies one
        ;   page at a time, bumping both page bytes, until MI_PAGES
        ;   reaches zero.
        ;
        ; Clobbers: A, Y, MI_VAL, MI_SENT_A
        STX MI_VAL
        STY MI_VAL+1
        STA MI_SENT_B                    ; A holds dest hi here
        LDY #$00
        STY MI_SENT_A
.loop   LDA (MI_VAL),Y
        STA (MI_SENT_A),Y
        INY
        BNE .loop
        INC MI_VAL+1
        INC MI_SENT_B
        DEC MI_PAGES
        BNE .loop
        RTS
@ %def MI_PAGE_COPY

\subsection{The payload: the ORIGIN-logo unpacker}

The 8 pages the builder copies to [[MI_PAYLOAD]] ([[$8700]]) are themselves
a tiny program plus its own packed stream. Run by [[MI_BUILD]], the payload
first zeroes [[$9600]]--[[$B5FF]], then unpacks a high-bit-flagged
\textsc{rle} stream (bytes with bit~7 clear are literals; a byte with
bit~7 set is a [[(value, count)]] run) into that buffer, setting bit~7 on
every output byte, and stops when the destination reaches page [[$B7]]. The
result is the \textsc{Origin Systems} logo image at [[LOGO_BUF]] that the
fizzle reveals. We keep the whole region as one labelled blob; it is data
within this file (it executes only after relocation to [[$8700]]).

<<makeindata payload image>>=
        ORG $2000
MI_PAYLOAD_IMAGE:
__PAYLOAD__
@ %def MI_PAYLOAD_IMAGE

\subsection{The intro artwork}

The 38 pages the builder copies to [[ART_BASE]] are the pixel art the
\texttt{U1.INTRO} animation draws from --- the five progressively complete
key frames, the castle strip stream, the two gate panels, the beat
strips, the sky-wipe pixel and mask rows, the curtain panels and the bird
sprite. The \texttt{U1.INTRO} chapter labels each blob by its consumer
([[ART_BASE]], [[ART_CASTLE]], [[ART_PANEL_A]]/[[ART_PANEL_B]],
[[ART_STRIPS]], [[ART_WIPE_PIX]]/[[ART_WIPE_MASK]], [[ART_CURTAIN]]/%
[[ART_CURTAIN2]], [[ART_BIRD]]); those labels are run-address [[EQU]]s in
that chapter, and the bytes here are their on-disk source. The region runs
[[$6000]]--[[$85FF]] at run time (so it is loaded with a leading
[[$E2]]-byte gap of zeros before the first frame, and is fully populated
through [[$85FF]]).

<<makeindata art image>>=
        ORG $27BD
MI_ART_IMAGE:
__ART__
@ %def MI_ART_IMAGE

\subsection{The castle-title stream}

The packed stream [[MI_DECOMP]] reads to build the castle title on hi-res
page~1 (figure~\ref{fig:mi-title}). Its first two bytes are the run
sentinels; the rest is the column-major run/literal program documented in
[[MI_DECODE]]. It runs to the end of the file.

<<makeindata title stream>>=
        ORG $49EC
MI_TITLE_STREAM:
__STREAM__
@ %def MI_TITLE_STREAM

\subsection{The build driver}

[[MI_BUILD]] is the program proper. It stamps the [[$8700]] payload into
low memory and copies the artwork to [[ART_BASE]], reconstructs the castle
title onto page~1, runs the payload (which builds the \textsc{Origin} logo
at [[LOGO_BUF]]), and then dissolves the logo onto the screen.

<<makeindata build>>=
        ORG $1F17
MI_BUILD:
        SUBROUTINE
        ; The one-shot builder: reconstruct the two title screens.
        ;
        ; Behavior:
        ;   Stamps the $8700 payload + the $6000 artwork into place,
        ;   decompresses the castle title onto page 1, runs the payload
        ;   (which unpacks the ORIGIN logo to $9600), fizzle-reveals the
        ;   logo onto page 2, then spins a key-abortable settle delay.
        ;
        ; Clobbers: everything; control returns to U1.SYSTEM's chain.
        LDX #<MI_PAYLOAD_IMAGE          ; copy 8 pages -> $8700 payload
        LDY #>MI_PAYLOAD_IMAGE
        LDA #$08
        STA MI_PAGES
        LDA #>MI_PAYLOAD
        JSR MI_PAGE_COPY
        LDX #<MI_ART_IMAGE              ; copy 38 pages -> ART_BASE
        LDY #>MI_ART_IMAGE
        LDA #$26
        STA MI_PAGES
        LDA #>ART_BASE
        JSR MI_PAGE_COPY
        LDA #<MI_TITLE_STREAM           ; decompress the castle title
        STA MI_SRC                      ;   onto hi-res page 1
        LDA #>MI_TITLE_STREAM
        STA MI_SRC+1
        JSR MI_DECOMP
        JSR MI_PAYLOAD                  ; build the ORIGIN logo at $9600
        JSR MI_FIZZLE                   ; dissolve the logo onto page 2
        LDX #$0A                        ; --- post-reveal settle delay ---
        LDA #$00
.delay  BIT KBD
        BMI .done                       ; abort on a keypress
        BIT DRIVE_OFF
.outer  PHA
.inner  SBC #$01
        BNE .inner
        PLA
        SBC #$01
        BNE .outer
        DEX
        BNE .delay
.done   RTS
@ %def MI_BUILD

\subsection{The fizzle reveal}

The fizzle picks the screen bit to set from a table of eight single-bit
masks, indexed by the top three bits of the \textsc{lfsr} state.

<<makeindata fizzle mask>>=
        ORG $1FD8
MI_FIZZLE_MASK:
        HEX 80 40 20 10 08 04 02 01
@ %def MI_FIZZLE_MASK

[[MI_FIZZLE]] clears hi-res page~2, switches the display to it, and then
runs a 16-bit \textsc{lfsr} fizzle dissolve: it walks every pixel address
in pseudo-random order, copying that pixel from the \textsc{Origin} logo at
[[LOGO_BUF]] onto page~2 through a single-bit mask from [[MI_FIZZLE_MASK]].
A keypress short-circuits to [[MI_LOGO_BLIT]], which copies the whole logo
at once.

<<makeindata fizzle>>=
        ORG $1F5C
MI_FIZZLE:
        SUBROUTINE
        ; Clear page 2, show it, and dissolve the ORIGIN logo onto it.
        ;
        ; Behavior:
        ;   The LFSR (MI_SRC, taps EOR #$B4) visits every pixel address in
        ;   pseudo-random order; each step copies one masked pixel from
        ;   LOGO_BUF to HGR2. A keypress jumps to MI_LOGO_BLIT (instant).
        ; Clobbers: A, X, Y, MI_SRC/MI_DST/MI_VAL/MI_SENT_B
        LDA #$00
        TAY
        STA MI_SRC
        LDX #$40
        STX MI_SRC+1                     ; clear $4000-$5FFF (page 2)
.clr    STA (MI_SRC),Y
        INY
        BNE .clr
        INC MI_SRC+1
        LDX MI_SRC+1
        CPX #$60
        BNE .clr
        BIT HIRES
        BIT MIXCLR
        BIT TXTPAGE2
        BIT TXTCLR                       ; display hi-res page 2
        LDX #$FF
        STX MI_SRC
        STX MI_SRC+1                     ; LFSR seed = $FFFF
.step   INX
        STX MI_REP
        STX MI_SENT_A
.lfsr   LSR MI_SRC+1                     ; advance the 16-bit LFSR
        ROR MI_SRC
        BCC .noxor
        LDA MI_SRC+1
        EOR #$B4                         ; feedback taps
        STA MI_SRC+1
.noxor  LDA MI_SRC
        STA MI_DST                       ; low byte -> screen + source offset
        STA MI_BACK+1
        LDA MI_SRC+1
        AND #$1F
        CLC
        ADC #$40
        STA MI_DST+1                     ; page-2 address ($40..$5F)
        ADC #$56
        STA MI_VAL                       ; logo address hi ($96..$B5)
        LDA MI_SRC+1
        AND #$E0
        ROL
        ROL
        ROL
        ROL
        TAY
        LDA MI_FIZZLE_MASK,Y             ; pick the single-bit mask
        TAX
        LDY #$00
        AND (MI_BACK+1),Y                ; logo pixel under the mask
        STA MI_SENT_B
        TXA
        EOR #$FF
        AND (MI_DST),Y                   ; clear that bit on the screen
        ORA MI_SENT_B
        STA (MI_DST),Y                   ; OR the logo pixel in
        BIT KBD
        BMI MI_LOGO_BLIT                 ; keypress -> reveal at once
        INC MI_REP
        BNE .lfsr
        INC MI_SENT_A
        BNE .lfsr
        LDA LOGO_BUF                     ; patch the one address $0000
        STA HGR2                         ;   the LFSR never visits
        RTS
@ %def MI_FIZZLE

[[MI_LOGO_BLIT]] is the keypress short-circuit: with [[Y]]=0 from the
dissolve loop it block-copies the whole logo from [[LOGO_BUF]] to [[HGR2]],
[[$20]] pages, and returns.

<<makeindata logo blit>>=
        ORG $1FE0
MI_LOGO_BLIT:
        SUBROUTINE
        ; Instant reveal: copy the whole ORIGIN logo onto hi-res page 2.
        ;
        ; Behavior:
        ;   Entered from MI_FIZZLE with Y=0 on a keypress; block-copies
        ;   the $20-page logo from $9600 (LOGO_BUF) to $4000 (HGR2).
        ;
        ; Clobbers: A, X, Y, MI_DST/MI_VAL
        STY MI_DST
        STY MI_BACK+1
        LDA #$40
        STA MI_DST+1                     ; dest = $4000 (page 2)
        LDA #$96
        STA MI_VAL                       ; source = $9600 (logo) hi byte
        LDX #$20
.loop   LDA (MI_BACK+1),Y
        STA (MI_DST),Y
        INY
        BNE .loop
        INC MI_VAL
        INC MI_DST+1
        DEX
        BNE .loop
        RTS
@ %def MI_LOGO_BLIT

Three [[BRK]] bytes pad the code region out to the page boundary at
[[$2000]], where the data regions begin.

<<makeindata code pad>>=
        ORG $1FFD
MI_CODE_PAD:
        HEX 00 00 00
@ %def MI_CODE_PAD

\subsection{Assembling the file}

The collection chunk lays the code and data regions out in ascending
address order.

<<makeindata.asm>>=
        PROCESSOR 6502
<<makeindata defines>>
<<makeindata entry>>
<<makeindata decomp driver>>
<<makeindata decode>>
<<makeindata page copy>>
<<makeindata build>>
<<makeindata fizzle>>
<<makeindata fizzle mask>>
<<makeindata logo blit>>
<<makeindata code pad>>
<<makeindata payload image>>
<<makeindata art image>>
<<makeindata title stream>>
@
"""

CH = CH.replace('__PAYLOAD__', payload)
CH = CH.replace('__ART__', art)
CH = CH.replace('__STREAM__', stream)

open('/tmp/mi_chapter.nw', 'w').write(CH)
print('wrote /tmp/mi_chapter.nw', len(CH), 'chars')
