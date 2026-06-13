"""HTML weaver for the literate noweb source (prototype).

This is the new weave backend described in html-migration-design.md. It REUSES
weave.py's tangler and chunk-graph analysis unchanged (the byte-perfect path)
and replaces only the output backend: instead of emitting LaTeX, it emits a
multi-page, three-pane, searchable HTML site.

Pipeline per source file:
  1. weave.Weaver.extract_chunk_info()  -> the chunk graph (UNCHANGED)
  2. weave.Weaver.tangle()              -> byte-perfect .asm (UNCHANGED)
  3. build_layout()  -> assign every chunk + heading to a page, build the
                        sublabel/name/ident -> (page, anchor) resolver maps
  4. render          -> Markdown (mistune) for doc chunks, a one-pass 6502
                        tokenizer + identifier links for code chunks
  5. emit            -> one HTML file per page + chunk/identifier index pages,
                        plus assets/ (style.css, app.js, site-data.js, .nojekyll)

Prose authoring rules the weaver assumes (see design doc):
  - Markdown (CommonMark + pipe tables + fenced ```mermaid).
  - Inline math stays as $...$ (rendered to \\( \\) for KaTeX).
  - [[X]] links: chunk name -> chunk; @ %def symbol -> its definition;
    anything else (raw $XXXX, undefined symbol) -> styled, no link.
  - A page starts at every H1 and at every explicit page marker:
        <!-- nwpage: slug | Page Title -->
    Page-breaking constructs must begin a doc-chunk line (not inside a fence).
"""

import html
import pathlib
import re
import shutil
from typing import Sequence

from absl import app

from weave import Weaver, ChunkInfo


# --- 6502 / dasm token tables (for syntax highlighting) ---------------------
MNEMONICS = set(
    "LDA LDX LDY STA STX STY TAX TAY TXA TYA TSX TXS ADC SBC AND ORA EOR CMP "
    "CPX CPY INC INX INY DEC DEX DEY ASL LSR ROL ROR BIT JMP JSR RTS RTI BRK "
    "NOP CLC SEC CLI SEI CLV CLD SED BCC BCS BEQ BNE BMI BPL BVC BVS PHA PLA "
    "PHP PLP".split()
)
DIRECTIVES = set(
    "PROCESSOR ORG SUBROUTINE EQU EQM DC DV HEX BYTE WORD MAC ENDM MACRO SEG "
    "RORG REND ALIGN DS INCLUDE INCBIN INCDIR IF ELSE ENDIF EIF REPEAT REPEND "
    "ECHO ERR SET SUBROUTINE LIST PROCESSOR".split()
)

# Page marker:  <!-- nwpage: slug | Title -->
PAGE_MARKER = re.compile(r"^\s*<!--\s*nwpage:\s*([-\w]+)\s*\|\s*(.+?)\s*-->\s*$")
ATX_HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")
CHUNKREF = re.compile(r"<<([-._ 0-9A-Za-z]*)>>")
# Inline code token scanner for the code part of an assembly line.
TOKRE = re.compile(
    r"""(?P<str>"[^"]*"|'[^']*')
      | (?P<num>\#?\$[0-9A-Fa-f]+|\#?%[01]+|\#[0-9]+|\b[0-9]+\b)
      | (?P<id>\.?[A-Za-z_][A-Za-z0-9_]*)
      | (?P<ws>[ \t]+)
      | (?P<other>.)""",
    re.VERBOSE,
)

# Pinned CDN dependencies (viewing requires internet, per design 4.5).
CDN_MERMAID = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"
CDN_KATEX_CSS = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css"
CDN_KATEX_JS = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"
CDN_KATEX_AUTO = (
    "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
)
CDN_MINISEARCH = "https://cdn.jsdelivr.net/npm/minisearch@7.1.0/dist/umd/index.min.js"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def slugify(text: str, used: set[str]) -> str:
    """Lowercase, dash-separated, unique-within-`used` slug."""
    # Strip a little markdown so slugs are clean.
    text = re.sub(r"\[\[(.+?)\]\]", r"\1", text)
    text = re.sub(r"[`*_]", "", text)
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    s = s or "section"
    base, n = s, 2
    while s in used:
        s = f"{base}-{n}"
        n += 1
    used.add(s)
    return s


def strip_md(text: str) -> str:
    """Cheap markdown -> plain text for TOC labels and search."""
    text = re.sub(r"\[\[(.+?)\]\]", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"[*_]{1,2}", "", text)
    return text.strip()


class Page:
    def __init__(self, slug: str, filename: str, title: str):
        self.slug = slug
        self.filename = filename
        self.title = title
        self.parts: list[str] = []        # rendered HTML fragments, in order
        self.headings: list[tuple[int, str, str]] = []  # (level, text, anchor)


class HtmlWeaver:
    def __init__(self):
        self.weaver = Weaver()
        self.md = None  # mistune instance, built once maps exist

    # ---------------------------------------------------------------- layout
    def split_docchunk(self, lines: Sequence[str]):
        """Fence-aware split of a doc chunk into segments at page triggers.

        Yields (trigger, seg_lines) where trigger is None, ('h1', title) or
        ('marker', slug, title). The trigger line itself is NOT included in
        seg_lines for markers; for H1 it IS (the heading renders in content).
        """
        seg: list[str] = []
        trigger = None
        in_fence = False
        first = True
        for line in lines:
            if FENCE.match(line):
                in_fence = not in_fence
                seg.append(line)
                continue
            if not in_fence:
                m = PAGE_MARKER.match(line)
                if m:
                    if seg or not first:
                        yield (trigger, seg)
                    seg, trigger, first = [], ("marker", m.group(1), m.group(2)), False
                    continue
                h = ATX_HEADING.match(line)
                if h and len(h.group(1)) == 1:
                    if seg or not first:
                        yield (trigger, seg)
                    seg, trigger, first = [line], ("h1", h.group(2)), False
                    continue
            seg.append(line)
        yield (trigger, seg)

    def scan_headings(self, seg_lines: Sequence[str]):
        """Fence-aware list of (level, raw_text) headings in a segment."""
        out, in_fence = [], False
        for line in seg_lines:
            if FENCE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            h = ATX_HEADING.match(line)
            if h:
                out.append((len(h.group(1)), h.group(2)))
        return out

    def build_layout(self, lines, chunks):
        """Pass 1: assign chunks/headings to pages; build resolver maps."""
        self.pages: list[Page] = []
        self.units: list[tuple] = []          # ('doc', page_idx, seg, anchors) | ('code', page_idx, chunk)
        self.label_loc: dict[str, tuple[str, str]] = {}  # \label id -> (page, anchor)
        page_slugs: set[str] = set()
        anchor_slugs: set[str] = set()
        cur = None  # current Page index

        def new_page(slug, title):
            filename = "index.html" if not self.pages else f"{slug}.html"
            self.pages.append(Page(slug, filename, title))
            return len(self.pages) - 1

        sublabel_loc: dict[str, tuple[str, str]] = {}
        label_loc: dict[str, tuple[str, str]] = {}

        def process_doc(seg_lines):
            nonlocal cur
            for trig, seg in self.split_docchunk(seg_lines):
                if trig and trig[0] == "h1":
                    cur = new_page(slugify(trig[1], page_slugs), strip_md(trig[1]))
                elif trig and trig[0] == "marker":
                    cur = new_page(slugify(trig[1], page_slugs), trig[2])
                if cur is None:  # content before the first trigger
                    cur = new_page(slugify("home", page_slugs), "Home")
                anchors = []
                for level, text in self.scan_headings(seg):
                    a = slugify(text, anchor_slugs)
                    anchors.append(a)
                    self.pages[cur].headings.append((level, strip_md(text), a))
                # Record \label-derived anchors for site-wide cross-page refs.
                for mm in re.finditer(r'<a id="([^"]+)"', "\n".join(seg)):
                    self.label_loc.setdefault(
                        mm.group(1), (self.pages[cur].filename, mm.group(1)))
                self.units.append(("doc", cur, seg, anchors))

        # The prose before the first chunk is NOT in `chunks` (weave.py treats
        # it as an unrepresented leading doc chunk) -- process it explicitly.
        lead_end = chunks[0].start if chunks else len(lines)
        if lead_end > 0:
            process_doc(lines[:lead_end])

        for chunk in chunks:
            if chunk.kind == "doc":
                process_doc(lines[chunk.start + 1 : chunk.end])
            else:  # code chunk
                if cur is None:
                    cur = new_page(slugify("home", page_slugs), "Home")
                fn = self.pages[cur].filename
                sublabel_loc[chunk.sublabel] = (fn, chunk.sublabel)
                if chunk.sublabel == chunk.label:
                    label_loc[chunk.label] = (fn, chunk.label)
                self.units.append(("code", cur, chunk))

        # Resolver maps.
        self.sublabel_loc = sublabel_loc
        self.sublabel_to_chunk = {c.sublabel: c for c in chunks if c.name}
        name_to_label = {c.name: c.label for c in chunks if c.name}
        self.name_loc = {n: label_loc[l] for n, l in name_to_label.items() if l in label_loc}
        ident_to_chunk: dict[str, ChunkInfo] = {}
        for c in chunks:
            for ident in c.defines:
                ident_to_chunk[ident] = c
        self.ident_to_chunk = ident_to_chunk
        self.ident_loc = {
            i: sublabel_loc[c.sublabel] for i, c in ident_to_chunk.items()
            if c.sublabel in sublabel_loc
        }

    # ---------------------------------------------------------- mistune setup
    def build_md(self):
        import mistune

        weaver = self

        def plugin_refs(md):
            LINKREF = r"\[\[(?P<lr>.+?)\]\]"
            MATH = r"(?<!\$)\$(?!\$)(?P<mx>[^\$\n]+?)\$(?!\$)"

            def parse_lr(inline, m, state):
                state.append_token({"type": "linkref", "raw": m.group("lr")})
                return m.end()

            def parse_mx(inline, m, state):
                state.append_token({"type": "mathx", "raw": m.group("mx")})
                return m.end()

            md.inline.register("linkref", LINKREF, parse_lr, before="link")
            md.inline.register("mathx", MATH, parse_mx, before="emphasis")

        class R(mistune.HTMLRenderer):
            cur_page = "index.html"
            head_q: list[str] = []
            head_i = 0

            def _href(self, loc):
                fn, anchor = loc
                return f"#{anchor}" if fn == self.cur_page else f"{fn}#{anchor}"

            def linkref(self, body):
                name = body.strip()
                if name in weaver.name_loc:
                    loc = weaver.name_loc[name]
                    return (f'<a class="ref chunkref" href="{self._href(loc)}" '
                            f'data-pop="{loc[1]}">&#x27E8;{esc(name)}&#x27E9;</a>')
                if name in weaver.ident_loc:
                    loc = weaver.ident_loc[name]
                    return (f'<a class="ref symref" href="{self._href(loc)}" '
                            f'data-pop="{loc[1]}"><code>{esc(name)}</code></a>')
                return f'<code class="addr">{esc(name)}</code>'

            def mathx(self, body):
                return f'<span class="math">\\({esc(body)}\\)</span>'

            def link(self, text, url, title=None):
                # Resolve a same-page #label that actually lives on another page
                # (cross-page \ref targets).
                if url.startswith("#"):
                    loc = weaver.label_loc.get(url[1:])
                    if loc and loc[0] != self.cur_page:
                        url = f"{loc[0]}#{loc[1]}"
                t = f' title="{esc(title)}"' if title else ""
                return f'<a href="{esc(url)}"{t}>{text}</a>'

            def block_code(self, code, info=None):
                if (info or "").strip() == "mermaid":
                    return f'<div class="mermaid">{esc(code)}</div>\n'
                return f'<pre class="verbatim"><code>{esc(code)}</code></pre>\n'

            def block_html(self, html):
                # Author raw-HTML blocks (e.g. layout-figure tables) are passed
                # through verbatim, so mistune's inline rules never see them.
                # Resolve [[ ]] refs here so layout cells can link to symbols.
                return re.sub(r"\[\[(.+?)\]\]",
                              lambda m: self.linkref(m.group(1)), html) + "\n"

            def heading(self, text, level, **attrs):
                anchor = ""
                if self.head_i < len(self.head_q):
                    anchor = self.head_q[self.head_i]
                    self.head_i += 1
                idattr = f' id="{anchor}"' if anchor else ""
                link = (f'<a class="hlink" href="#{anchor}">#</a>' if anchor else "")
                return f"<h{level}{idattr}>{text}{link}</h{level}>\n"

        # escape=False is required on the renderer instance: when a custom
        # renderer is passed, create_markdown's own escape flag is ignored, so
        # raw HTML blocks/inlines would otherwise be escaped.
        self._renderer = R(escape=False)
        self.md = mistune.create_markdown(
            renderer=self._renderer, plugins=["table", plugin_refs]
        )

    # ----------------------------------------------------------- code chunks
    def render_code_line(self, line: str) -> str:
        """One assembly line -> highlighted HTML with identifier/chunk links."""
        # Split trailing comment at the first ';' (outside strings — approx).
        code, comment = line, ""
        in_str = False
        for i, ch in enumerate(line):
            if ch in "\"'":
                in_str = not in_str
            elif ch == ";" and not in_str:
                code, comment = line[:i], line[i:]
                break

        out = []
        # Leading label:  LABEL:  or  .local:
        mlbl = re.match(r"^(\.?[A-Za-z_][\w]*)(:)", code)
        rest = code
        if mlbl:
            out.append(f'<span class="lbl">{esc(mlbl.group(1))}</span>'
                       f'<span class="pun">:</span>')
            rest = code[mlbl.end():]

        # Process chunk refs interspersed with tokenizable text.
        pos = 0
        for m in CHUNKREF.finditer(rest):
            out.append(self.tokenize(rest[pos:m.start()]))
            name = m.group(1).strip()
            if name in self.name_loc:
                loc = self.name_loc[name]
                href = (f"#{loc[1]}" if loc[0] == self._renderer.cur_page
                        else f"{loc[0]}#{loc[1]}")
                out.append(f'<a class="chunkref" href="{href}" data-pop="{loc[1]}">'
                           f'&#x27E8;{esc(name)}&#x27E9;</a>')
            else:
                out.append(f'<span class="chunkref">&#x27E8;{esc(name)}&#x27E9;</span>')
            pos = m.end()
        out.append(self.tokenize(rest[pos:]))

        if comment:
            out.append(f'<span class="cm">{esc(comment)}</span>')
        return "".join(out)

    def tokenize(self, text: str) -> str:
        out = []
        for m in TOKRE.finditer(text):
            kind = m.lastgroup
            tok = m.group()
            if kind == "ws":
                out.append(tok)
            elif kind == "str":
                out.append(f'<span class="str">{esc(tok)}</span>')
            elif kind == "num":
                out.append(f'<span class="num">{esc(tok)}</span>')
            elif kind == "id":
                out.append(self.id_token(tok))
            else:
                out.append(f'<span class="pun">{esc(tok)}</span>')
        return "".join(out)

    def id_token(self, tok: str) -> str:
        if tok in self.ident_loc:
            loc = self.ident_loc[tok]
            href = (f"#{loc[1]}" if loc[0] == self._renderer.cur_page
                    else f"{loc[0]}#{loc[1]}")
            return (f'<a class="idlink" href="{href}" data-pop="{loc[1]}">'
                    f'{esc(tok)}</a>')
        up = tok.upper()
        if up in MNEMONICS:
            return f'<span class="mn">{esc(tok)}</span>'
        if up in DIRECTIVES:
            return f'<span class="dir">{esc(tok)}</span>'
        return f'<span class="sym">{esc(tok)}</span>'

    def render_code_chunk(self, chunk: ChunkInfo, lines) -> str:
        body_lines = lines[chunk.start + 1 : chunk.end]
        cont = "+=" if chunk.prev_sublabel else "="
        nameref = ""
        if chunk.name in self.name_loc:
            loc = self.name_loc[chunk.name]
            href = (f"#{loc[1]}" if loc[0] == self._renderer.cur_page
                    else f"{loc[0]}#{loc[1]}")
            nameref = f' <a class="pageref" href="{href}">[{chunk.number}]</a>'

        code_html = "\n".join(self.render_code_line(l) for l in body_lines)

        # Footer: prev/next, used-in, Defines, Uses.
        foot = []
        nav = []
        if chunk.prev_sublabel and chunk.prev_sublabel in self.sublabel_loc:
            loc = self.sublabel_loc[chunk.prev_sublabel]
            nav.append(f'<a href="{self._loc_href(loc)}">&#x25C1; prev</a>')
        if chunk.next_sublabel and chunk.next_sublabel in self.sublabel_loc:
            loc = self.sublabel_loc[chunk.next_sublabel]
            nav.append(f'<a href="{self._loc_href(loc)}">next &#x25B7;</a>')
        if nav:
            foot.append('<div class="chunk-nav">' + " ".join(nav) + "</div>")

        if chunk.sublabels_used_in:
            used = []
            for sl in chunk.sublabels_used_in:
                if sl in self.sublabel_loc:
                    c2 = self.sublabel_to_chunk.get(sl)
                    label = esc(c2.name) if c2 else "chunk"
                    used.append(f'<a href="{self._loc_href(self.sublabel_loc[sl])}" '
                                f'data-pop="{sl}">&#x27E8;{label}&#x27E9;</a>')
            if used:
                foot.append('<div class="used-in">Used in ' + ", ".join(used) + "</div>")
        else:
            foot.append('<div class="used-in not-used">(root chunk &mdash; tangled to file)</div>')

        if chunk.defines:
            defs = ", ".join(f'<code>{esc(d)}</code>' for d in sorted(chunk.defines))
            foot.append(f'<div class="defines">Defines {defs}</div>')
        if chunk.defines_used:
            uses = []
            for d in sorted(chunk.defines_used):
                if d in self.ident_loc:
                    uses.append(f'<a href="{self._loc_href(self.ident_loc[d])}" '
                                f'data-pop="{self.ident_loc[d][1]}"><code>{esc(d)}</code></a>')
            if uses:
                foot.append('<div class="uses">Uses ' + ", ".join(uses) + "</div>")

        return (
            f'<section class="chunk" id="{chunk.sublabel}">'
            f'<div class="chunk-head">'
            f'<button class="collapse" title="collapse/expand"></button>'
            f'<span class="chunk-title">&#x27E8;{esc(chunk.name)}{nameref}&#x27E9;{cont}</span>'
            f'</div>'
            f'<div class="chunk-body"><pre class="asm">{code_html}</pre></div>'
            f'<div class="chunk-foot">' + "".join(foot) + "</div>"
            f"</section>\n"
        )

    def _loc_href(self, loc):
        fn, anchor = loc
        return f"#{anchor}" if fn == self._renderer.cur_page else f"{fn}#{anchor}"

    # --------------------------------------------------------------- render
    def render(self, lines):
        search_docs = []
        chunk_meta = {}
        for unit in self.units:
            page = self.pages[unit[1]]
            self._renderer.cur_page = page.filename
            if unit[0] == "doc":
                _, _, seg, anchors = unit
                self._renderer.head_q = anchors
                self._renderer.head_i = 0
                text = "\n".join(seg)
                if text.strip():
                    page.parts.append(self.md(text))
                # search docs per heading segment
                heads = self.scan_headings(seg)
                if heads and anchors:
                    page.parts  # no-op
                    title = strip_md(heads[0][1])
                    search_docs.append({
                        "id": f"{page.filename}#{anchors[0]}",
                        "t": title, "u": f"{page.filename}#{anchors[0]}",
                        "k": "section", "b": strip_md(text)[:400],
                    })
            else:
                chunk = unit[2]
                page.parts.append(self.render_code_chunk(chunk, lines))
                body = lines[chunk.start + 1 : chunk.end]
                snippet = "\n".join(body[:6])
                chunk_meta[chunk.sublabel] = {
                    "n": chunk.name, "u": f"{page.filename}#{chunk.sublabel}",
                    "p": page.title, "s": snippet[:400],
                }
                search_docs.append({
                    "id": f"{page.filename}#{chunk.sublabel}",
                    "t": chunk.name, "u": f"{page.filename}#{chunk.sublabel}",
                    "k": "chunk", "b": "\n".join(body)[:400],
                })
                for d in chunk.defines:
                    search_docs.append({
                        "id": f"sym:{d}", "t": d,
                        "u": f"{page.filename}#{chunk.sublabel}",
                        "k": "symbol", "b": f"symbol {d}",
                    })
        self.search_docs = search_docs
        self.chunk_meta = chunk_meta

    # ------------------------------------------------------------- emit site
    def build_toc(self) -> str:
        out = ['<ul class="toc">']
        for p in self.pages:
            out.append(f'<li><a href="{p.filename}">{esc(p.title)}</a>')
            subs = [h for h in p.headings if h[0] == 2]
            if subs:
                out.append("<ul>")
                for _, text, anchor in subs:
                    out.append(f'<li><a href="{p.filename}#{anchor}">{esc(text)}</a></li>')
                out.append("</ul>")
            out.append("</li>")
        out.append("</ul>")
        # Extra index pages.
        out.append('<ul class="toc toc-aux">'
                   '<li><a href="chunk-index.html">Chunk index</a></li>'
                   '<li><a href="identifier-index.html">Identifier index</a></li>'
                   "</ul>")
        return "\n".join(out)

    def page_outline(self, page: Page) -> str:
        items = [h for h in page.headings if h[0] in (2, 3)]
        if not items:
            return ""
        out = ['<nav class="outline"><div class="outline-title">On this page</div><ul>']
        for level, text, anchor in items:
            out.append(f'<li class="lvl{level}"><a href="#{anchor}">{esc(text)}</a></li>')
        out.append("</ul></nav>")
        return "\n".join(out)

    def page_html(self, page: Page, doc_title: str) -> str:
        toc = self.build_toc()
        outline = self.page_outline(page)
        content = "\n".join(page.parts)
        return PAGE_TEMPLATE.format(
            title=esc(page.title), doc_title=esc(doc_title), toc=toc,
            outline=outline, content=content,
            mermaid=CDN_MERMAID, katex_css=CDN_KATEX_CSS, katex_js=CDN_KATEX_JS,
            katex_auto=CDN_KATEX_AUTO, minisearch=CDN_MINISEARCH,
        )

    def index_page(self, slug, title, doc_title, body_html) -> str:
        p = Page(slug, f"{slug}.html", title)
        p.parts.append(body_html)
        return self.page_html(p, doc_title)

    def chunk_index_html(self) -> str:
        names = sorted({c.name for c in self.chunks if c.name})
        rows = []
        for n in names:
            if n not in self.name_loc:
                continue
            loc = self.name_loc[n]
            rows.append(f'<li><a href="{loc[0]}#{loc[1]}">&#x27E8;{esc(n)}&#x27E9;</a></li>')
        return '<h1>Chunk index</h1><ul class="index-list">' + "".join(rows) + "</ul>"

    def ident_index_html(self) -> str:
        idents = sorted(self.ident_to_chunk)
        rows = []
        for i in idents:
            loc = self.ident_loc.get(i)
            if not loc:
                continue
            rows.append(f'<li><a href="{loc[0]}#{loc[1]}"><code>{esc(i)}</code></a></li>')
        return '<h1>Identifier index</h1><ul class="index-list">' + "".join(rows) + "</ul>"

    def site_data_js(self) -> str:
        import json
        return ("window.SEARCH_INDEX = " + json.dumps(self.search_docs) + ";\n"
                "window.CHUNK_META = " + json.dumps(self.chunk_meta) + ";\n")

    def weave(self, lines, chunks, output_dir, filename):
        self.chunks = chunks
        doc_title = self.pages[0].title if self.pages else "Document"
        outdir = pathlib.Path(output_dir)
        outdir.mkdir(parents=True, exist_ok=True)
        assets = outdir / "assets"
        assets.mkdir(exist_ok=True)

        for page in self.pages:
            (outdir / page.filename).write_text(self.page_html(page, doc_title))
        (outdir / "chunk-index.html").write_text(
            self.index_page("chunk-index", "Chunk index", doc_title, self.chunk_index_html()))
        (outdir / "identifier-index.html").write_text(
            self.index_page("identifier-index", "Identifier index", doc_title,
                            self.ident_index_html()))

        # Assets: copy static web/ files, generate data + .nojekyll.
        web = pathlib.Path(__file__).parent / "web"
        for fn in ("style.css", "app.js"):
            src = web / fn
            if src.exists():
                shutil.copy(src, assets / fn)
        (assets / "site-data.js").write_text(self.site_data_js())
        (outdir / ".nojekyll").write_text("")

    # ------------------------------------------------------------------ run
    def run(self, files, output_dir):
        pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
        for fileno, filename in enumerate(files):
            with open(filename) as f:
                lines = [l.rstrip("\n") for l in f.readlines()]
            chunks = self.weaver.extract_chunk_info(lines, filename, fileno)
            # 1) byte-perfect tangle (identical code path to weave.py)
            self.weaver.tangle(lines, chunks, output_dir, filename)
            # 2) HTML weave
            self.build_layout(lines, chunks)
            self.build_md()
            self.render(lines)
            self.weave(lines, chunks, output_dir, filename)
            print(f"Wove {len(self.pages)} pages + 2 index pages from {filename}.")


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} &middot; {doc_title}</title>
<link rel="stylesheet" href="{katex_css}">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="topbar">
  <button id="menu-toggle" class="iconbtn" title="Menu">&#9776;</button>
  <span class="brand">{doc_title}</span>
  <div class="search"><input id="q" type="search" placeholder="Search (/)"
       autocomplete="off"><div id="results"></div></div>
  <button id="theme-toggle" class="iconbtn" title="Toggle theme">&#9680;</button>
</header>
<div class="page-grid">
  <nav class="left" id="left">{toc}</nav>
  <main id="main">{content}</main>
  <aside class="right">{outline}</aside>
</div>
<div id="popover" class="popover" hidden></div>
<script src="{mermaid}"></script>
<script src="{katex_js}"></script>
<script src="{katex_auto}"></script>
<script src="{minisearch}"></script>
<script src="assets/site-data.js"></script>
<script src="assets/app.js"></script>
</body>
</html>
"""


def main(argv):
    args = argv[1:]
    src = args[0] if args else "sample.nw"
    out = args[1] if len(args) > 1 else "output"
    HtmlWeaver().run([src], out)


if __name__ == "__main__":
    app.run(main)
