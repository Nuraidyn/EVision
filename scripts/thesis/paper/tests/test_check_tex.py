"""Tests for scripts/thesis/paper/check_tex.py (run with the thesis venv: ``-m pytest``)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import check_tex as ct  # noqa: E402

REPO = HERE.parents[3]

GOOD_BIB = r"""
@article{a2020,
  author = {A, B.},
  title = {T},
  journal = {J},
  year = {2020},
  note = {Details to verify}
}
@book{b2019,
  author = {B, C.},
  title = {Book},
  publisher = {P},
  year = {2019}
}
"""

GOOD_MAIN = r"""\documentclass{article}
\usepackage{amsmath}
\newcommand{\foo}{bar}
\begin{document}
\input{sections/s1}
\bibliography{references}
\end{document}
"""

GOOD_SECTION = r"""\section{Intro}\label{sec:intro}
Text \foo{} cites \citep{a2020,b2019} and refers to Section~\ref{sec:intro}.
\begin{equation}\label{eq:one}
x_t = y_t
\end{equation}
See \eqref{eq:one}. A table input: \input{tables/tab_panels.tex}
"""


def make_paper(tmp_path: Path, main=GOOD_MAIN, section=GOOD_SECTION, bib=GOOD_BIB) -> Path:
    (tmp_path / "sections").mkdir()
    (tmp_path / "main.tex").write_text(main, encoding="utf-8")
    (tmp_path / "sections" / "s1.tex").write_text(section, encoding="utf-8")
    (tmp_path / "references.bib").write_text(bib, encoding="utf-8")
    return tmp_path


def checks(issues, name):
    return [i for i in issues if i.check == name]


def test_good_paper_has_no_issues(tmp_path):
    paper = make_paper(tmp_path)
    assert ct.run_checks(paper) == []


def test_interface_files_are_allowed_when_missing(tmp_path):
    section = GOOD_SECTION + r"\includegraphics[width=\linewidth]{figures/fig_pipeline.pdf}" + "\n"
    paper = make_paper(tmp_path, section=section)
    assert checks(ct.run_checks(paper), "input") == []


def test_missing_input_and_graphic_reported(tmp_path):
    section = GOOD_SECTION + r"\input{sections/nope}" + "\n" + r"\includegraphics{figures/other.pdf}" + "\n"
    paper = make_paper(tmp_path, section=section)
    msgs = [i.message for i in checks(ct.run_checks(paper), "input")]
    assert any("sections/nope" in m for m in msgs)
    assert any("figures/other.pdf" in m for m in msgs)


def test_undefined_and_duplicate_labels(tmp_path):
    section = GOOD_SECTION + r"\label{sec:intro} see \ref{sec:missing} and \eqref{eq:nope}" + "\n"
    paper = make_paper(tmp_path, section=section)
    issues = ct.run_checks(paper)
    assert any("duplicate" in i.message for i in checks(issues, "label"))
    msgs = [i.message for i in checks(issues, "ref")]
    assert any("sec:missing" in m for m in msgs) and any("eq:nope" in m for m in msgs)


def test_unknown_citation_key(tmp_path):
    section = GOOD_SECTION + r"Also \citet{ghost2099} and \cite{a2020, ghost2}." + "\n"
    paper = make_paper(tmp_path, section=section)
    msgs = [i.message for i in checks(ct.run_checks(paper), "cite")]
    assert any("ghost2099" in m for m in msgs) and any("ghost2" in m for m in msgs)
    assert not any("a2020" in m for m in msgs)


def test_cite_with_optional_arguments(tmp_path):
    section = GOOD_SECTION + r"\citep[see][p.~3]{a2020} and \citet[TOST;][]{b2019}." + "\n"
    paper = make_paper(tmp_path, section=section)
    assert checks(ct.run_checks(paper), "cite") == []


def test_bib_required_fields(tmp_path):
    bib = GOOD_BIB + "\n@article{bad, author={X}, title={Y}, year={2000}}\n@inproceedings{bad2, title={Y}, booktitle={B}, year={2000}}\n"
    paper = make_paper(tmp_path, bib=bib)
    msgs = [i.message for i in checks(ct.run_checks(paper), "bib")]
    assert any("bad:" in m and "journal" in m for m in msgs)
    assert any("bad2:" in m and "author" in m for m in msgs)


def test_parse_bib_values_with_nested_braces():
    e = ct.parse_bib("@article{k, author={Cand{\\`e}s, E.}, title={The {PID} way}, journal={J}, year={2020}}")
    assert e["k"]["fields"]["author"] == "Cand{\\`e}s, E."
    assert e["k"]["fields"]["title"] == "The {PID} way"


def test_unbalanced_braces_and_environments(tmp_path):
    section = GOOD_SECTION + "\\textbf{open\n\\begin{itemize}\n\\item x\n"
    paper = make_paper(tmp_path, section=section)
    msgs = [i.message for i in checks(ct.run_checks(paper), "balance")]
    assert any("unclosed" in m for m in msgs)
    assert any("itemize" in m and "never closed" in m for m in msgs)


def test_mismatched_environment(tmp_path):
    section = GOOD_SECTION + "\\begin{itemize}\n\\item x\n\\end{enumerate}\n"
    paper = make_paper(tmp_path, section=section)
    msgs = [i.message for i in checks(ct.run_checks(paper), "balance")]
    assert any("closes" in m for m in msgs)


def test_odd_dollar_signs(tmp_path):
    section = GOOD_SECTION + "\nA broken $x_t formula.\n"
    paper = make_paper(tmp_path, section=section)
    assert any("odd number" in i.message for i in checks(ct.run_checks(paper), "balance"))


@pytest.mark.parametrize("bad", ["TODO fix", "to be TBD", "[insert result]", "CITATION NEEDED", "[VERIFY x]", "wait ... what"])
def test_placeholders_detected(tmp_path, bad):
    paper = make_paper(tmp_path, section=GOOD_SECTION + "\n" + bad + "\n")
    assert checks(ct.run_checks(paper), "placeholder")


def test_placeholder_in_comment_is_ignored(tmp_path):
    paper = make_paper(tmp_path, section=GOOD_SECTION + "\n% TODO this is only a comment\n")
    assert checks(ct.run_checks(paper), "placeholder") == []


def test_undefined_macro_detected_and_defined_macro_ok(tmp_path):
    paper = make_paper(tmp_path, section=GOOD_SECTION + "\nUses \\undefinedthing here and \\foo.\n")
    msgs = [i.message for i in checks(ct.run_checks(paper), "macro")]
    assert any("undefinedthing" in m for m in msgs)
    assert not any("\\foo" in m for m in msgs)


def test_macro_defined_in_section_file_counts(tmp_path):
    paper = make_paper(tmp_path, section=GOOD_SECTION + "\n\\newcommand{\\local}{x}\\local\n")
    assert checks(ct.run_checks(paper), "macro") == []


def test_unknown_environment(tmp_path):
    paper = make_paper(tmp_path, section=GOOD_SECTION + "\n\\begin{weirdenv}\nx\n\\end{weirdenv}\n")
    assert any("weirdenv" in i.message for i in checks(ct.run_checks(paper), "macro"))


def test_hygiene_underscore_ampersand_nonascii(tmp_path):
    section = GOOD_SECTION + "\nbad_name and R&D and caf\u00e9 and 5# items.\n"
    paper = make_paper(tmp_path, section=section)
    msgs = [i.message for i in checks(ct.run_checks(paper), "hygiene")]
    assert any("'_'" in m for m in msgs)
    assert any("'&'" in m for m in msgs)
    assert any("non-ASCII" in m for m in msgs)
    assert any("'#'" in m for m in msgs)


def test_hygiene_allows_math_underscore_and_tabular_ampersand(tmp_path):
    section = GOOD_SECTION + "\nMath $a_b$ and \\texttt{x\\_y}.\n\\begin{tabular}{ll}\na & b \\\\\n\\end{tabular}\n"
    paper = make_paper(tmp_path, section=section)
    assert checks(ct.run_checks(paper), "hygiene") == []


def test_generated_table_with_unbalanced_braces_is_reported(tmp_path):
    paper = make_paper(tmp_path)
    (paper / "tables").mkdir()
    (paper / "tables" / "tab_panels.tex").write_text("\\begin{tabular}{l}\na {\\\\\n\\end{tabular}\n", encoding="utf-8")
    assert checks(ct.run_checks(paper), "balance")


def test_strip_comments_keeps_escaped_percent():
    assert ct.strip_comments("50\\% done % comment") == "50\\% done "


def test_word_count_ignores_math_and_commands(tmp_path):
    paper = make_paper(tmp_path, section="\\section{A}\nOne two $x_t$ three \\textbf{four}.\n")
    assert ct.body_word_count(paper) == 5  # A one two three four


def test_real_paper_passes():
    paper = REPO / "paper"
    if not (paper / "main.tex").exists():
        pytest.skip("paper/ not present")
    issues = ct.run_checks(paper)
    assert issues == [], "\n".join(str(i) for i in issues)
