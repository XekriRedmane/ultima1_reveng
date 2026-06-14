# gen-html

Generate the multi-page HTML site from the literate noweb document.

## Instructions

Run these commands from the project root. If any step fails, stop and report the failure.

1. Run any project-specific pre-generation commands listed in the `site_pregen` array of `targets.json`, in order. These regenerate rendered image assets (the `render_*.py` scripts) that the prose references. An empty array means nothing to do.
2. Weave (this also tangles the `.asm` files as a side effect, using the same byte-perfect tangler as `/assemble`):
   `python3 weave_html.py main.nw output_site`
3. The site is written to `output_site/`: one HTML page per chapter (oversized chapters such as the mode overlays are split per overlay via `<!-- nwpage: slug | Title -->` markers), plus `chunk-index.html`, `identifier-index.html`, and an `assets/` directory (CSS, JS, the inlined search index, `.nojekyll`). Static files under `web/` (`style.css`, `app.js`) are copied into `assets/` automatically.

## Viewing

- **Locally:** open `output_site/index.html` in a browser (works over `file://`), or serve it: `python3 -m http.server -d output_site 8000`.
- **GitHub Pages:** publish the `output_site/` directory as-is (it includes `.nojekyll`; all links are relative).
- Mermaid, KaTeX, and the search library load from CDN, so viewing needs an internet connection.

## Acceptance

- `weave_html.py` must exit without error.
- The expected pages exist and internal links resolve. A quick check:
  `python3 - <<'PY'` … cross-check every `href` against the set of page files and their `id=` anchors; report any broken link.
- Visually confirm Mermaid diagrams, `$…$` math (KaTeX), tables, code highlighting, search, and dark/light mode render in the browser.

## Notes

- The weaver reuses `weave.py`'s `extract_chunk_info` (chunk graph) and `tangle` (byte-perfect `.asm`) unchanged; only the output backend differs. So a green `/assemble` and a green `gen-html` are consistent by construction.
- Prose is Markdown; diagrams are Mermaid (```mermaid fenced blocks); layout/data tables are Markdown pipe tables or block-level HTML tables; `[[ ]]` cross-references and `$…$` math are preserved. See `html-migration-design.md` for the full format spec.
