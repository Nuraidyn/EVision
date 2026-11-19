"""Regenerate every figure, table and number macro of the paper from the committed results.

    scripts/thesis/.venv/Scripts/python.exe scripts/thesis/paper/build_paper_assets.py [--out DIR]

Deterministic, no network. Writes DIR/figures/*.pdf, DIR/tables/*.tex and DIR/numbers.tex
(default DIR = <repo>/paper).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import DEFAULT_OUT  # noqa: E402


def build(out: Path = DEFAULT_OUT) -> dict[str, list[str]]:
    import paper_figures as figures
    import numbers_tex
    import paper_tables as tables

    out = Path(out)
    (out / "figures").mkdir(parents=True, exist_ok=True)
    (out / "tables").mkdir(parents=True, exist_ok=True)
    made: dict[str, list[str]] = {"tables": [], "figures": [], "numbers": []}
    for name, fn in tables.TABLES.items():
        (out / "tables" / name).write_text(fn(), encoding="utf-8", newline="\n")
        made["tables"].append(name)
    (out / "numbers.tex").write_text(numbers_tex.render(), encoding="utf-8", newline="\n")
    made["numbers"].append("numbers.tex")
    for name, fn in figures.FIGURES.items():
        fn(out / "figures" / name)
        made["figures"].append(name)
    return made


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    a = ap.parse_args()
    made = build(Path(a.out))
    for k, v in made.items():
        print(f"{k}: {len(v)} files")
    print(f"written to {a.out}")


if __name__ == "__main__":
    main()
