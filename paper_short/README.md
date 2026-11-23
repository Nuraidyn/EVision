# Condensed paper (paper_short): build instructions

Condensed, journal-length version (about 11,000 words of running text, appendix of stable
robustness tables only) of "Comparing Methods for Building Reliable Prediction Intervals for
Machine-Learning Inflation Forecasts in Commodity-Dependent Economies". The full version is in
`../paper/` and is not changed by this directory.

**Status: the LaTeX source has NOT been compiled.** No LaTeX compiler exists on the machine on
which it was written. It was checked only by the static checker below (references, citations,
braces, environments, placeholders, defined macros). Expect to fix small typesetting problems
(overfull boxes, float placement) on the first real build.

## Layout

| Path | Content |
|---|---|
| `main.tex` | Preamble, macros (including `\ExplainerStatus`), `\input` of the sections |
| `sections/*.tex` | abstract, introduction, related, methods, data (design), results, discussion, limitations, conclusion, reproducibility, appendix |
| `references.bib` | Copy of the bibliography of the full version |
| `figures/*.pdf`, `tables/*.tex` | Copies (unedited) of the generated files of `../paper/` that this version uses |

The paper is self-contained: upload the contents of this directory (or `paper_short.zip`) to
Overleaf and compile `main.tex` (pdfLaTeX, BibTeX). Packages: amsmath, amssymb, amsthm,
booktabs, array, multirow, graphicx, xcolor, float, caption, microtype, geometry, natbib
(`plainnat`), hyperref, fontenc, inputenc.

## Build

```
cd paper_short
latexmk -pdf main.tex
```

or `pdflatex main.tex; bibtex main; pdflatex main.tex; pdflatex main.tex`.

## Static check (no LaTeX needed)

From the repository root:

```
scripts/thesis/.venv/Scripts/python.exe scripts/thesis/paper/check_tex.py paper_short --wordcount
scripts/thesis/.venv/Scripts/python.exe -m pytest scripts/thesis/paper/tests -q
```

## Notes

- The one-sentence result of the language-model explanation layer evaluation (one model, v1 and
  post hoc v2) is the macro `\ExplainerStatus` in `main.tex`; the longer text and the table are in
  `sections/results.tex`.
- Moved out of the main text (see the full version in `../paper/` and the repository): per-check
  detail (S4/S5 tables, shock-rule validity, Kazakhstan, stress), the protocol change log with
  commit hashes, data snapshot hashes and the long reproduction commands.
- Honesty conventions are those of the full version: "pre-specified" (never "pre-registered"),
  a contrast with undefined or above 7 pp MDE is "inconclusive", S6/S7 are post hoc, Chronos
  accuracy only on the 22 clean months with the leakage caveat.
