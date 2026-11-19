"""Static checker for the LaTeX paper in ``paper/`` (no LaTeX installation needed).

Checks (each reports ``ERROR`` lines; the exit code is 1 if any error exists):

1. every ``\\input`` / ``\\include`` / ``\\includegraphics`` target exists or is in the
   agreed interface list (figures and tables produced by the asset script);
2. every ``\\ref`` / ``\\eqref`` / ``\\Cref`` / ``\\pageref`` label is defined and every
   ``\\label`` is unique;
3. every ``\\cite``-family key exists in ``references.bib`` and every bib entry has the
   fields required for its type;
4. braces, ``$`` delimiters and ``\\begin`` / ``\\end`` environments balance per file;
5. no placeholder strings (TODO, TBD, FIXME, XXX, "[insert", "CITATION NEEDED", "[VERIFY",
   a literal "...");
6. every control sequence used is defined in the paper or belongs to the list of commands
   of LaTeX and of the packages the paper loads;
7. extra hygiene: non-ASCII characters, unescaped ``_`` in text mode, unescaped ``&``
   outside tabular-like environments, unescaped ``#``.

Usage: ``python check_tex.py [paper_dir] [--wordcount]``.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

AGREED_FIGURES = [
    "figures/fig_pipeline.pdf",
    "figures/fig_coverage_h.pdf",
    "figures/fig_ce_bars.pdf",
    "figures/fig_contrasts_forest.pdf",
    "figures/fig_width_winkler.pdf",
    "figures/fig_chronos_accuracy.pdf",
    "figures/fig_country_coverage.pdf",
    "figures/fig_warmup_sensitivity.pdf",
]
AGREED_TABLES = [
    f"tables/{n}.tex"
    for n in [
        "tab_panels", "tab_methods", "tab_ce_exploratory", "tab_ce_holdout1",
        "tab_ce_holdout2", "tab_contrasts_primary", "tab_tost", "tab_winkler_width",
        "tab_ablation_basemodel", "tab_ablation_warmup", "tab_feedback_delay",
        "tab_native_vs_aci", "tab_chronos_mae", "tab_rules",
    ]
]
AGREED_OTHER = ["numbers.tex"]
AGREED = set(AGREED_FIGURES + AGREED_TABLES + AGREED_OTHER)

REQUIRED_BIB_FIELDS = {
    "article": [["author"], ["title"], ["journal"], ["year"]],
    "inproceedings": [["author"], ["title"], ["booktitle"], ["year"]],
    "book": [["author", "editor"], ["title"], ["publisher"], ["year"]],
    "misc": [["author"], ["title"], ["year"]],
    "techreport": [["author"], ["title"], ["institution"], ["year"]],
    "phdthesis": [["author"], ["title"], ["school"], ["year"]],
}

PLACEHOLDER_PATTERNS = [
    r"\bTODO\b", r"\bTBD\b", r"\bFIXME\b", r"\bXXX\b", r"\[insert", r"CITATION NEEDED",
    r"\[VERIFY", r"\.\.\.", r"\\ldots", r"lorem ipsum",
]

REF_CMDS = ["ref", "eqref", "Cref", "cref", "autoref", "pageref", "nameref", "vref"]
CITE_CMDS = [
    "cite", "citep", "citet", "citealp", "citealt", "citeauthor", "citeyear",
    "citeyearpar", "Citep", "Citet", "nocite",
]
# environments whose body may contain a bare '&'
ALIGN_ENVS = {
    "tabular", "tabular*", "array", "align", "align*", "aligned", "alignat", "alignat*",
    "eqnarray", "matrix", "pmatrix", "bmatrix", "cases", "split", "gather", "gathered",
    "tabularx", "longtable",
}
MATH_ENVS = {
    "equation", "equation*", "align", "align*", "aligned", "gather", "gather*", "multline",
    "multline*", "eqnarray", "eqnarray*", "displaymath", "math", "split", "cases", "array",
    "matrix", "pmatrix", "bmatrix",
}

# Control sequences of LaTeX 2e, of the packages loaded in main.tex and of AMS math.
KNOWN_COMMANDS = set("""
documentclass usepackage begin end input include includegraphics IfFileExists
title author date maketitle appendix tableofcontents
section subsection subsubsection paragraph subparagraph chapter part
label ref eqref pageref cite citep citet citealp citealt citeauthor citeyear nocite
bibliography bibliographystyle
textbf textit emph texttt textsc textrm textsf textnormal textup textsl underline
mathrm mathbf mathbb mathcal mathit mathsf mathtt boldsymbol text mbox hbox
item centering raggedright raggedleft noindent par newline linebreak pagebreak newpage
small footnotesize scriptsize tiny large Large LARGE huge Huge normalsize
caption captionof captionsetup resizebox scalebox linewidth textwidth columnwidth
hline toprule midrule bottomrule cmidrule addlinespace multirow multicolumn arraybackslash
newcommand renewcommand providecommand newtheorem newcolumntype DeclareMathOperator
def let setlength addtolength setcounter stepcounter refstepcounter hspace vspace
quad qquad hfill vfill smallskip medskip bigskip thinspace enspace
footnote footnotemark url href texorpdfstring hypersetup
frac dfrac tfrac sum prod int lim ln log exp max min sup inf arg
le ge leq geq ne neq approx sim simeq equiv in notin subset subseteq cup cap
times cdot cdots ldots dots vdots ddots pm mp
alpha beta gamma delta epsilon varepsilon eta theta kappa lambda mu nu pi rho sigma tau phi
varphi chi psi omega Delta Gamma Lambda Sigma Omega Phi Psi Pi Theta
left right big Big bigg Bigg bigl bigr Bigl Bigr biggl biggr
lceil rceil lfloor rfloor langle rangle
mathbf overline underline hat tilde bar widehat widetilde
psi infty partial nabla forall exists
rightarrow leftarrow Rightarrow Leftrightarrow to mapsto
operatorname nonumber notag tag displaystyle textstyle
ensuremath
_ & % $ # { } , ; : ! ' " . = ~ ^ ` - / ( ) [ ] \\ @
hspace* vspace* texttt cdot
`\\`
`"
""".split())
KNOWN_COMMANDS |= {
    # T2A Cyrillic letters used for the author name (main.tex loads fontenc T2A)
    "fontencoding", "selectfont", "CYRN", "CYRS", "cyra", "cyrd", "cyre", "cyrery", "cyrishrt",
    "cyrk", "cyrn", "cyrp", "cyrr", "cyrt", "cyru",
    "\\", "&", "%", "$", "#", "_", "{", "}", ",", ";", ":", "!", "'", '"', ".", "=", "~",
    "^", "`", "-", "/", "(", ")", "[", "]", "@", " ", "|",
    "^", "c", "v", "u", "H", "k", "r", "o", "O", "ae", "AE", "oe", "OE", "ss", "i", "j", "l", "L",
    "textless", "textgreater", "textbar", "textbackslash", "textasciitilde", "textasciicircum",
    "textquotesingle", "textquotedbl", "textendash", "textemdash", "textunderscore",
    "ensuremath", "makeatletter", "makeatother", "relax", "protect", "ignorespaces",
    "detokenize", "string", "sqrt", "binom", "choose", "not", "neg", "land", "lor", "wedge", "vee",
    "mid", "colon", "dagger", "S", "P", "pounds", "copyright", "ell", "Re", "Im", "top", "bot",
    "bm", "bfseries", "itshape", "ttfamily", "rmfamily", "sffamily", "scshape", "mdseries", "upshape",
    "slshape", "normalfont", "tt", "bf", "it", "rm", "sf", "sc", "em", "cal",
    "color", "textcolor", "colorbox", "definecolor", "pagecolor", "rowcolors",
    "citeyearpar", "citenumber", "bibitem", "newblock", "bibpunct", "setcitestyle",
    "theoremstyle", "qedsymbol", "qedhere", "proof", "bibsection",
    "thesection", "thesubsection", "thetable", "thefigure", "theequation", "arabic", "roman", "Roman",
    "alph", "Alph", "value", "the", "z@", "p@", "ifx", "fi", "else", "ifdim", "ifnum", "iftrue", "iffalse",
    "centerline", "rule", "strut", "phantom", "hphantom", "vphantom", "raisebox", "makebox",
    "parbox", "minipage", "fbox", "framebox", "rotatebox", "tabcolsep", "arraystretch",
    "belowrulesep", "aboverulesep", "heavyrulewidth", "lightrulewidth", "extrarowheight",
    "setstretch", "onehalfspacing", "doublespacing", "singlespacing",
    "bigcirc", "circ", "ast", "star", "oplus", "otimes", "varepsilon", "ell", "wp", "emptyset",
    "lesssim", "gtrsim", "ll", "gg", "propto", "perp", "parallel", "angle", "triangle",
    "uparrow", "downarrow", "longrightarrow", "implies", "iff", "Longrightarrow", "xrightarrow",
    "overset", "underset", "stackrel", "substack", "limits", "nolimits", "sideset", "smash",
    "quad", "mathop", "mathrel", "mathbin", "mathord", "mathclose", "mathopen", "mathpunct",
    "ThisURL", "nolinkurl", "autoref", "hyperref", "hypertarget", "hyperlink", "phantomsection",
    "pdfbookmark", "addcontentsline", "contentsline", "numberline",
    "linespread", "frenchspacing", "sloppy", "fussy", "hyphenation", "-", "nobreak", "nolinebreak",
    "sbox", "usebox", "savebox", "newsavebox", "lstinline", "verb", "verbatim",
    "thispagestyle", "pagestyle", "pagenumbering", "clearpage", "cleardoublepage", "FloatBarrier",
    "placeins", "suppressfloats", "listoffigures", "listoftables", "abstractname", "refname",
    "figurename", "tablename", "contentsname", "today", "TeX", "LaTeX", "LaTeXe",
    "tableofcontents", "bibname", "indexname", "appendixname", "partname", "chaptername",
    "dagger", "ddagger", "textdegree", "degree", "textperthousand", "texttimes", "textpm",
    "mathbf", "unitlength", "put", "line", "vector", "circle", "oval", "multiput", "thicklines",
    "thinlines", "linethickness", "makelabel", "labelitemi", "labelenumi", "labelsep", "labelwidth",
    "leftmargin", "itemsep", "parsep", "topsep", "parskip", "parindent", "baselineskip",
    "baselinestretch", "textfloatsep", "floatsep", "intextsep", "abovecaptionskip",
    "belowcaptionskip", "hsize", "vsize", "columnsep", "newif", "if", "ifthenelse", "equal",
    "boolean", "not", "AND", "OR", "NOT", "ifcsname", "csname", "endcsname", "expandafter",
    "noexpand", "edef", "xdef", "gdef", "global", "long", "outer", "futurelet", "afterassignment",
    "ifmmode", "ifvmode", "ifhmode", "unskip", "unkern", "kern", "penalty", "allowbreak",
    "discretionary", "nobreakspace", "ensuremath", "textsuperscript", "textsubscript", "ding",
    "wd", "mathscr", "mathfrak", "operatorname", "varnothing", "uplus", "bigcup", "bigcap", "bigvee",
    "bigwedge", "bigoplus", "bigotimes", "coprod", "oint", "iint", "iiint", "upsilon", "zeta",
    "xi", "iota", "Upsilon", "Xi", "varrho", "varsigma", "vartheta", "varpi", "digamma",
    "nu", "ell", "hbar", "imath", "jmath", "aleph", "beth", "skew", "mkern", "mskip", "hskip",
    "vskip", "vrule", "hrule", "leaders", "hss", "hfil", "hfilll", "vfil", "vss", "cr", "crcr",
    "noalign", "omit", "span", "multispan", "tabularnewline", "endhead", "endfirsthead",
    "endfoot", "endlastfoot", "extracolsep", "tabular", "arraycolsep", "doublerulesep",
    "arrayrulewidth", "cline", "vline", "hdashline", "specialrule", "morecmidrules", "cmidrulewidth",
    "bigstrut", "bigstrutjot", "tnote", "tablenotes", "threeparttable", "adjustbox",
    "Needspace", "needspace", "enlargethispage", "looseness", "emergencystretch", "tolerance",
    "pretolerance", "hbadness", "vbadness", "hfuzz", "vfuzz", "overfullrule", "lefthyphenmin",
    "righthyphenmin", "nonfrenchspacing", "uppercase", "lowercase", "MakeUppercase", "MakeLowercase",
    "makeindex", "printindex", "index", "glossary", "marginpar", "reversemarginpar", "normalmarginpar",
    "oddsidemargin", "evensidemargin", "textheight", "topmargin", "headheight", "headsep",
    "footskip", "marginparwidth", "marginparsep", "paperwidth", "paperheight", "geometry",
    "newgeometry", "restoregeometry", "fancyhead", "fancyfoot", "fancyhf", "headrulewidth",
    "footrulewidth", "leftmark", "rightmark", "markboth", "markright", "thepage", "thechapter",
    "pdfinfo", "pdfstringdef", "pdfstringdefDisableCommands", "pdfoutput", "special",
    "natexlab", "citefield", "Citealp", "Citeauthor", "citetext", "defcitealias", "citetalias",
    "citepalias", "mathllap", "mathrlap", "mathclap", "llap", "rlap", "clap",
}
# Names of environments are handled separately; these are control words that can appear as
# arguments of \begin{...}.
KNOWN_ENVIRONMENTS = {
    "document", "abstract", "equation", "equation*", "align", "align*", "aligned", "gather",
    "gather*", "multline", "multline*", "split", "cases", "array", "matrix", "pmatrix", "bmatrix",
    "itemize", "enumerate", "description", "table", "table*", "figure", "figure*", "tabular",
    "tabular*", "center", "flushleft", "flushright", "quote", "quotation", "verbatim", "minipage",
    "thebibliography", "definition", "theorem", "lemma", "proof", "remark", "proposition",
    "corollary", "displaymath", "math", "eqnarray", "eqnarray*", "tabularx", "longtable",
    "threeparttable", "tablenotes", "appendices",
}


@dataclass
class Issue:
    check: str
    file: str
    message: str

    def __str__(self) -> str:
        return f"ERROR [{self.check}] {self.file}: {self.message}"


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def strip_comments(text: str) -> str:
    """Remove ``%`` comments (an unescaped ``%`` up to the end of the line)."""
    out = []
    for line in text.split("\n"):
        i = 0
        cut = None
        while i < len(line):
            c = line[i]
            if c == "\\":
                i += 2
                continue
            if c == "%":
                cut = i
                break
            i += 1
        out.append(line if cut is None else line[:cut])
    return "\n".join(out)


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def find_tex_files(paper_dir: Path) -> list[Path]:
    """main.tex plus every file reachable through \\input / \\include."""
    main = paper_dir / "main.tex"
    seen: list[Path] = []
    stack = [main] if main.exists() else []
    while stack:
        f = stack.pop(0)
        if f in seen or not f.exists():
            continue
        seen.append(f)
        for target in input_targets(strip_comments(f.read_text(encoding="utf-8"))):
            p = resolve_target(paper_dir, target, add_tex=True)
            if p.exists() and p.suffix == ".tex" and not _is_generated(paper_dir, p):
                stack.append(p)
    return seen


def _is_generated(paper_dir: Path, p: Path) -> bool:
    """Generated interface files (tables/, numbers.tex) are written by another script."""
    rel = p.relative_to(paper_dir).as_posix()
    return rel in AGREED


def input_targets(text: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"\\(?:input|include)\{([^}]*)\}", text)]


def resolve_target(paper_dir: Path, target: str, add_tex: bool) -> Path:
    p = paper_dir / target
    if add_tex and not p.suffix:
        p = p.with_suffix(".tex")
    return p


def _args(text: str, cmd: str) -> list[tuple[int, str]]:
    """All mandatory arguments of ``\\cmd`` (optional ``[..]`` skipped), with positions."""
    res = []
    pat = re.compile(r"\\" + cmd + r"\*?\s*((?:\[[^\]]*\]\s*)*)\{([^}]*)\}")
    for m in pat.finditer(text):
        res.append((m.start(), m.group(2)))
    return res


# ---------------------------------------------------------------------------
# Bibliography
# ---------------------------------------------------------------------------

def parse_bib(text: str) -> dict[str, dict]:
    """Minimal BibTeX parser: ``{key: {"type": t, "fields": {name: value}}}``."""
    entries: dict[str, dict] = {}
    i = 0
    n = len(text)
    while True:
        i = text.find("@", i)
        if i < 0:
            break
        m = re.match(r"@(\w+)\s*\{", text[i:])
        if not m:
            i += 1
            continue
        etype = m.group(1).lower()
        j = i + m.end()
        depth = 1
        k = j
        while k < n and depth:
            if text[k] == "{":
                depth += 1
            elif text[k] == "}":
                depth -= 1
            k += 1
        body = text[j:k - 1]
        i = k
        if etype in {"comment", "string", "preamble"}:
            continue
        km = re.match(r"\s*([^,\s]+)\s*,", body)
        if not km:
            continue
        key = km.group(1)
        rest = body[km.end():]
        fields: dict[str, str] = {}
        for fm in re.finditer(r"(\w+)\s*=\s*", rest):
            name = fm.group(1).lower()
            p = fm.end()
            if p >= len(rest):
                continue
            if rest[p] == "{":
                d = 0
                q = p
                while q < len(rest):
                    if rest[q] == "{":
                        d += 1
                    elif rest[q] == "}":
                        d -= 1
                        if d == 0:
                            break
                    q += 1
                value = rest[p + 1:q]
            elif rest[p] == '"':
                q = rest.find('"', p + 1)
                value = rest[p + 1:q]
            else:
                q = re.compile(r"[,\s}]").search(rest, p)
                value = rest[p:q.start() if q else len(rest)]
            fields.setdefault(name, value.strip())
        entries[key] = {"type": etype, "fields": fields}
    return entries


def check_bib(entries: dict[str, dict], bib_name: str = "references.bib") -> list[Issue]:
    issues = []
    for key, e in entries.items():
        req = REQUIRED_BIB_FIELDS.get(e["type"])
        if req is None:
            issues.append(Issue("bib", bib_name, f"entry {key}: unsupported type @{e['type']}"))
            continue
        for alternatives in req:
            if not any(e["fields"].get(a) for a in alternatives):
                issues.append(Issue("bib", bib_name, f"entry {key}: missing field {'/'.join(alternatives)}"))
    return issues


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_inputs(paper_dir: Path, files: list[Path]) -> list[Issue]:
    issues = []
    for f in files:
        text = strip_comments(f.read_text(encoding="utf-8"))
        rel = f.relative_to(paper_dir).as_posix()
        for t in input_targets(text):
            p = resolve_target(paper_dir, t, add_tex=True)
            key = p.relative_to(paper_dir).as_posix() if p.is_relative_to(paper_dir) else t
            if not p.exists() and key not in AGREED:
                issues.append(Issue("input", rel, f"\\input target not found and not in the interface list: {t}"))
        for _, t in _args(text, "includegraphics"):
            p = paper_dir / t.strip()
            if not p.exists() and t.strip() not in AGREED:
                issues.append(Issue("input", rel, f"\\includegraphics target not found and not in the interface list: {t}"))
    return issues


def check_labels(files: list[Path], paper_dir: Path) -> list[Issue]:
    issues = []
    defined: dict[str, str] = {}
    refs: list[tuple[str, str, int]] = []
    for f in files:
        text = strip_comments(f.read_text(encoding="utf-8"))
        rel = f.relative_to(paper_dir).as_posix()
        for pos, lab in _args(text, "label"):
            lab = lab.strip()
            if lab in defined:
                issues.append(Issue("label", rel, f"duplicate label '{lab}' (first in {defined[lab]})"))
            else:
                defined[lab] = rel
        for cmd in REF_CMDS:
            for pos, arg in _args(text, cmd):
                for lab in arg.split(","):
                    refs.append((lab.strip(), rel, _line_of(text, pos)))
    for lab, rel, line in refs:
        if lab not in defined:
            issues.append(Issue("ref", rel, f"line {line}: reference to undefined label '{lab}'"))
    return issues


def check_cites(files: list[Path], paper_dir: Path, bib_keys: set[str]) -> list[Issue]:
    issues = []
    for f in files:
        text = strip_comments(f.read_text(encoding="utf-8"))
        rel = f.relative_to(paper_dir).as_posix()
        for cmd in CITE_CMDS:
            for pos, arg in _args(text, cmd):
                for key in arg.split(","):
                    key = key.strip()
                    if key and key != "*" and key not in bib_keys:
                        issues.append(Issue("cite", rel, f"line {_line_of(text, pos)}: citation key '{key}' not in references.bib"))
    return issues


def check_balance(files: list[Path], paper_dir: Path) -> list[Issue]:
    issues = []
    for f in files:
        raw = f.read_text(encoding="utf-8")
        text = strip_comments(raw)
        rel = f.relative_to(paper_dir).as_posix()
        # braces
        depth = 0
        i = 0
        while i < len(text):
            c = text[i]
            if c == "\\":
                i += 2
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth < 0:
                    issues.append(Issue("balance", rel, f"line {_line_of(text, i)}: unmatched closing brace"))
                    depth = 0
            i += 1
        if depth:
            issues.append(Issue("balance", rel, f"{depth} unclosed opening brace(s)"))
        # environments
        stack: list[tuple[str, int]] = []
        for m in re.finditer(r"\\(begin|end)\{([^}]*)\}", text):
            kind, name = m.group(1), m.group(2)
            line = _line_of(text, m.start())
            if kind == "begin":
                stack.append((name, line))
            else:
                if not stack:
                    issues.append(Issue("balance", rel, f"line {line}: \\end{{{name}}} without \\begin"))
                elif stack[-1][0] != name:
                    issues.append(Issue("balance", rel, f"line {line}: \\end{{{name}}} closes \\begin{{{stack[-1][0]}}} (line {stack[-1][1]})"))
                    stack.pop()
                else:
                    stack.pop()
        for name, line in stack:
            issues.append(Issue("balance", rel, f"line {line}: \\begin{{{name}}} never closed"))
        # dollar signs per paragraph
        for para in re.split(r"\n\s*\n", text):
            clean = para.replace("\\$", "")
            if clean.count("$") % 2:
                snippet = para.strip()[:60].replace("\n", " ")
                issues.append(Issue("balance", rel, f"odd number of $ in paragraph starting '{snippet}'"))
    return issues


def check_placeholders(files: list[Path], paper_dir: Path, extra_files: list[Path] | None = None) -> list[Issue]:
    issues = []
    for f in list(files) + list(extra_files or []):
        text = strip_comments(f.read_text(encoding="utf-8"))
        rel = f.relative_to(paper_dir).as_posix()
        for pat in PLACEHOLDER_PATTERNS:
            for m in re.finditer(pat, text, flags=re.IGNORECASE if pat == "lorem ipsum" else 0):
                issues.append(Issue("placeholder", rel, f"line {_line_of(text, m.start())}: placeholder '{m.group(0)}'"))
    return issues


def collect_defined_macros(files: list[Path]) -> set[str]:
    defined: set[str] = set()
    for f in files:
        text = strip_comments(f.read_text(encoding="utf-8"))
        for m in re.finditer(r"\\(?:re)?newcommand\*?\s*\{?\\([A-Za-z@]+)\}?", text):
            defined.add(m.group(1))
        for m in re.finditer(r"\\providecommand\*?\s*\{?\\([A-Za-z@]+)\}?", text):
            defined.add(m.group(1))
        for m in re.finditer(r"\\newsavebox\s*\{\\([A-Za-z@]+)\}", text):
            defined.add(m.group(1))
        for m in re.finditer(r"\\DeclareMathOperator\*?\s*\{\\([A-Za-z@]+)\}", text):
            defined.add(m.group(1))
        for m in re.finditer(r"\\def\s*\\([A-Za-z@]+)", text):
            defined.add(m.group(1))
    return defined


def check_macros(files: list[Path], paper_dir: Path, defined: set[str] | None = None) -> list[Issue]:
    issues = []
    if defined is None:
        defined = collect_defined_macros(files)
    for f in files:
        text = strip_comments(f.read_text(encoding="utf-8"))
        rel = f.relative_to(paper_dir).as_posix()
        for m in re.finditer(r"\\([A-Za-z@]+)", text):
            name = m.group(1)
            if name in defined or name in KNOWN_COMMANDS:
                continue
            issues.append(Issue("macro", rel, f"line {_line_of(text, m.start())}: undefined control sequence \\{name}"))
        for m in re.finditer(r"\\begin\{([^}]*)\}", text):
            if m.group(1) not in KNOWN_ENVIRONMENTS:
                issues.append(Issue("macro", rel, f"line {_line_of(text, m.start())}: unknown environment '{m.group(1)}'"))
    return issues


def _strip_math_and_args(text: str) -> str:
    """Remove math and arguments that legitimately hold '_' or '&' and similar."""
    for env in MATH_ENVS:
        text = re.sub(r"\\begin\{" + re.escape(env) + r"\}.*?\\end\{" + re.escape(env) + r"\}", " ", text, flags=re.S)
    text = re.sub(r"\\\$", " ", text)
    text = re.sub(r"\$[^$]*\$", " ", text)
    for cmd in ["label", "input", "include", "includegraphics", "bibliography", "bibliographystyle", "url", "href"] + REF_CMDS + CITE_CMDS:
        text = re.sub(r"\\" + cmd + r"\*?\s*(?:\[[^\]]*\]\s*)*\{[^}]*\}", " ", text)
    return text


def check_hygiene(files: list[Path], paper_dir: Path) -> list[Issue]:
    issues = []
    for f in files:
        raw = f.read_text(encoding="utf-8")
        rel = f.relative_to(paper_dir).as_posix()
        for lineno, line in enumerate(raw.split("\n"), 1):
            for ch in line:
                if ord(ch) > 127:
                    issues.append(Issue("hygiene", rel, f"line {lineno}: non-ASCII character {ch!r}"))
                    break
        text = strip_comments(raw)
        body = _strip_math_and_args(text)
        for m in re.finditer(r"(?<!\\)_", body):
            issues.append(Issue("hygiene", rel, f"line {_line_of(body, m.start())}: unescaped '_' in text mode"))
        for m in re.finditer(r"(?<!\\)#(?![1-9])", body):
            ctx = body[max(0, m.start() - 30):m.start()]
            if "\\newcommand" in ctx or "\\renewcommand" in ctx:
                continue
            issues.append(Issue("hygiene", rel, f"line {_line_of(body, m.start())}: unescaped '#'"))
        # '&' outside tabular-like environments
        no_tab = body
        for env in ALIGN_ENVS:
            no_tab = re.sub(r"\\begin\{" + re.escape(env) + r"\}.*?\\end\{" + re.escape(env) + r"\}", " ", no_tab, flags=re.S)
        for m in re.finditer(r"(?<!\\)&", no_tab):
            issues.append(Issue("hygiene", rel, f"line {_line_of(no_tab, m.start())}: unescaped '&' outside a tabular-like environment"))
    return issues


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def run_checks(paper_dir: Path | str) -> list[Issue]:
    paper_dir = Path(paper_dir)
    issues: list[Issue] = []
    files = find_tex_files(paper_dir)
    if not files:
        return [Issue("input", str(paper_dir), "main.tex not found")]
    bib_path = paper_dir / "references.bib"
    if bib_path.exists():
        entries = parse_bib(bib_path.read_text(encoding="utf-8"))
        issues += check_bib(entries)
        bib_keys = set(entries)
    else:
        issues.append(Issue("bib", "references.bib", "file not found"))
        bib_keys = set()
    issues += check_inputs(paper_dir, files)
    issues += check_labels(files, paper_dir)
    issues += check_cites(files, paper_dir, bib_keys)
    issues += check_balance(files, paper_dir)
    extra = [bib_path] if bib_path.exists() else []
    issues += check_placeholders(files, paper_dir, extra)
    issues += check_macros(files, paper_dir)
    issues += check_hygiene(files, paper_dir)
    # Generated table bodies (if already present) must at least be balanced and use known macros.
    gen = [paper_dir / t for t in AGREED_TABLES if (paper_dir / t).exists()]
    if gen:
        issues += check_balance(gen, paper_dir)
        issues += check_macros(gen, paper_dir, collect_defined_macros(files + gen))
    return issues


def body_word_count(paper_dir: Path | str, exclude=("appendix.tex", "abstract.tex")) -> int:
    """Approximate word count of the running text in sections/*.tex (math, tables,
    commands and appendix excluded)."""
    paper_dir = Path(paper_dir)
    total = 0
    for f in sorted((paper_dir / "sections").glob("*.tex")):
        if f.name in exclude:
            continue
        text = strip_comments(f.read_text(encoding="utf-8"))
        for env in ["tabular", "equation", "align", "figure", "table"]:
            text = re.sub(r"\\begin\{" + env + r"\*?\}.*?\\end\{" + env + r"\*?\}", " ", text, flags=re.S)
        text = re.sub(r"\$[^$]*\$", " ", text)
        text = re.sub(r"\\(?:cite[a-z]*|ref|eqref|label|input)\*?(?:\[[^\]]*\])*\{[^}]*\}", " ", text)
        text = re.sub(r"\\[A-Za-z]+\*?", " ", text)
        words = re.findall(r"[A-Za-z][A-Za-z'\-]*|\d+(?:\.\d+)?", text)
        total += len(words)
    return total


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    paper_dir = Path(args[0]) if args else Path(__file__).resolve().parents[3] / "paper"
    issues = run_checks(paper_dir)
    for i in issues:
        print(i)
    if "--wordcount" in argv:
        print(f"body word count (sections without abstract/appendix): {body_word_count(paper_dir)}")
    if issues:
        print(f"{len(issues)} problem(s) found")
        return 1
    print("OK: no problems found")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
