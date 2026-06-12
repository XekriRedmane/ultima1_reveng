# gen-pdf

Generate the PDF from the literate noweb document.

## Instructions

Run these commands from the project root. If any step fails, stop and report the failure.

1. Ensure the output directory exists: `mkdir -p output`
2. Tangle: `python3 weave.py main.nw output`
3. Copy support files: `cp noweb.sty output/ && cp -r images output/` (skip the images copy if the project has no `images/` yet)
4. Run any project-specific pre-generation commands listed in the `pdf_pregen` array of `targets.json`, in order. (For example, a project with generated font tables would list its generator scripts here. An empty array means nothing to do.)
5. Run pdflatex once: `cd output && pdflatex -interaction=nonstopmode main.tex`
6. Run pdflatex again to resolve references: `pdflatex -interaction=nonstopmode main.tex`

## Acceptance

- `pdflatex` must exit without a LaTeX error (missing chunk, bad `[[ ]]`, undefined control sequence). Fix errors before declaring success.
- Undefined-reference and overfull-hbox warnings are acceptable but worth noting in the report.
