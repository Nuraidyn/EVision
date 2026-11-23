# Paper: build instructions

LaTeX article "Comparing Methods for Building Reliable Prediction Intervals for
Machine-Learning Inflation Forecasts in Commodity-Dependent Economies".

**Status: the LaTeX source has NOT been compiled.** No LaTeX compiler exists on the machine on
which it was written. It was checked only by the static checker below (references, citations,
braces, environments, placeholders, defined macros). Expect to fix small typesetting problems
(overfull boxes, float placement) on the first real build.

## Layout

| Path | Content |
|---|---|
| `main.tex` | Preamble, `\input` of `numbers.tex` (optional) and of the sections |
| `sections/*.tex` | One file per section (abstract, introduction, related, methods, architecture, data, results, discussion, limitations, conclusion, reproducibility, appendix) |
| `references.bib` | Bibliography (entries marked "details to verify" in the `note` field must be checked) |
| `figures/*.pdf`, `tables/*.tex`, `numbers.tex` | Generated; do not edit by hand |

Packages used: amsmath, amssymb, amsthm, booktabs, array, multirow, graphicx, xcolor, float,
caption, microtype, geometry, natbib (`plainnat`), hyperref, fontenc, inputenc. All ship with
TeX Live and MiKTeX.

## Build

1. Regenerate figures, tables and number macros from the committed results (from the repository root):

   ```
   scripts/thesis/.venv/Scripts/python.exe scripts/thesis/paper/build_paper_assets.py
   ```

2. Compile (from `paper/`):

   ```
   cd paper
   latexmk -pdf main.tex
   ```

   or, without latexmk:

   ```
   pdflatex main.tex
   bibtex main
   pdflatex main.tex
   pdflatex main.tex
   ```

## Static check (no LaTeX needed)

```
scripts/thesis/.venv/Scripts/python.exe scripts/thesis/paper/check_tex.py paper --wordcount
scripts/thesis/.venv/Scripts/python.exe -m pytest scripts/thesis/paper/tests -q
```

The checker verifies `\input`/`\includegraphics` targets, `\ref`/`\eqref` labels and label
uniqueness, `\cite` keys and required BibTeX fields, balance of braces, `$` and environments,
placeholder strings, undefined control sequences, and basic text-mode hygiene (non-ASCII,
unescaped `_`, `&`, `#`). It does not replace a compiler run.

## Honesty conventions in the text

- "Pre-specified" (never "pre-registered"): a self-attested commit history.
- Outcomes of R1-R5 and E1-E5 are stated as in `docs/thesis/manuscript/main.md`.
- A contrast with an undefined or above 7 pp minimum detectable difference is "inconclusive".
- S6 and S7 are post hoc; Chronos accuracy claims are limited to the 22 clean months and
  flagged as leakage-uncertain; the language-model explainer evaluation is reported as pre-specified v1 and post hoc v2
  (one model, single-reader validation by the model, no human review).
- Numbers in the running text were written from `main.md`; tables and figures come from the
  committed results through `build_paper_assets.py`.
