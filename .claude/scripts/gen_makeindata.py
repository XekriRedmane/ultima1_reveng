#!/usr/bin/env python3
"""Generate the MAKE.INDATA chapter noweb source for main.nw.

MAKE.INDATA is the one-shot art/title builder BRUN at cold start. It is
code-light (512 bytes at $1E00-$1FFF) and data-heavy (~13 KB of packed
hi-res art). This script emits:

  * hand-written, fully-labelled code chunks for $1E00-$1FFC (the two
    decompressors' driver/inner, PAGE_COPY, the build driver, the fizzle
    reveal, the mask table, the instant-copy path, and the BRK padding);
  * HEX data spans for the three data regions (the $8700 font/logo payload
    image, the $6000 intro-art image, and the packed title-castle stream).

Run from the project root; it prints the chapter to stdout.
"""

BASE = 0x1E00
REF = open('reference/makeindata.bin', 'rb').read()


def seg(a, b):
    return REF[a - BASE:b - BASE]


def hexlines(data, indent='        '):
    """Emit HEX directives, <= 8 bytes per line."""
    out = []
    for i in range(0, len(data), 8):
        row = data[i:i + 8]
        out.append(indent + 'HEX ' + ' '.join(f'{b:02x}' for b in row))
    return '\n'.join(out)


# ---------------------------------------------------------------------------
# Data spans (addresses are the LOAD addresses in the file image at $1E00..)
# ---------------------------------------------------------------------------
PAYLOAD_LO = 0x2000     # source the driver copies to $8700 (8 pages)
PAYLOAD_HI = 0x27BD     # art region begins here (payload page tail is zero pad)
ART_LO = 0x27BD         # source the driver copies to $6000 (38 pages)
ART_HI = 0x49EC         # title stream begins here
STREAM_LO = 0x49EC      # the packed castle-title stream
STREAM_HI = 0x5435      # end of file


def emit():
    print(CHAPTER)


CHAPTER = r'''__CHAPTER_BODY__'''


if __name__ == '__main__':
    payload = seg(PAYLOAD_LO, PAYLOAD_HI)
    art = seg(ART_LO, ART_HI)
    stream = seg(STREAM_LO, STREAM_HI)
    print('payload', len(payload), 'art', len(art), 'stream', len(stream),
          'total', len(payload) + len(art) + len(stream) + (PAYLOAD_LO - BASE))
    # sanity: code(0x200) + payload + art + stream == filelen
    assert (PAYLOAD_LO - BASE) + len(payload) + len(art) + len(stream) == len(REF), \
        'region coverage mismatch'
    print('coverage OK; file len', len(REF))
