"""Vector figures (PDF) from the committed CSV results. Light theme, Okabe-Ito palette."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402

import paper_tables as T  # noqa: E402
from common import (  # noqa: E402
    COUNTRIES, HORIZONS, METHOD_COLOR, METHOD_LABEL, METHOD_MARKER, METHODS, MODEL_LABEL, NOMINAL,
    PANEL_LABEL, PANEL_UNITS, RUNS, apply_style, ce_table, contrasts, load, per_unit, pooled, save_pdf,
    CONTRAST_SETS, is_inconclusive,
)

W1, W2 = 3.4, 7.0  # single / double column width, inches
PANEL_RUN = {"expl": "expl48", "hold1": "hold48", "hold2": "h2_48"}
HPOS = {h: i for i, h in enumerate(HORIZONS)}
BLUE, ORANGE, GREEN, VERM, SKY, PURPLE, GREY = "#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9", "#CC79A7", "#7f7f7f"


def _hlabels(ax):
    ax.set_xticks(range(len(HORIZONS)))
    ax.set_xticklabels([str(h) for h in HORIZONS])
    ax.set_xlabel("Horizon $h$ (months)")


# --------------------------------------------------------------------------------------------
def fig_pipeline(path: Path):
    apply_style()
    fig, ax = plt.subplots(figsize=(W2, 4.3))
    ax.set_xlim(0, 100)
    ax.set_ylim(-8, 56)
    ax.axis("off")

    def box(x, y, w, h, text, fc="#f2f2f2", ec="#444444", fs=7.2, bold=False, ha="center"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=0.8", fc=fc, ec=ec, lw=0.8))
        ax.text(x + (w / 2 if ha == "center" else 1.0), y + h / 2, text, ha=ha, va="center", fontsize=fs,
                fontweight="bold" if bold else "normal", linespacing=1.25)

    def arrow(x0, y0, x1, y1):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=8, lw=0.9, color="#333333", shrinkA=1, shrinkB=1))

    # column headers
    for x, w, t in ((1, 22, "1 Panels"), (28, 20, "2 Base forecasters"),
                    (53, 21, "3 Intervals"), (79, 20, "4 Evaluation")):
        ax.text(x + w / 2, 54.2, t, ha="center", va="center", fontsize=8, fontweight="bold")

    # panels
    box(1, 38, 22, 11, "Design panel\n13 countries\nexploratory, to 2025-06", fc="#dfeaf5", fs=7)
    box(1, 24, 22, 11, "Hold-out panel 1\n7 countries\nrule fixed first", fc="#fbeed6", fs=7)
    box(1, 10, 22, 11, "Hold-out panel 2\n10 countries, from 2010\nrule fixed first", fc="#d9f0e8", fs=7)
    # forecasters
    for i, (t, sub) in enumerate((("Naive B", "last $h$-month growth"), ("ARIMA", "AICc, harmonics"),
                                  ("LightGBM", "direct, per $h$"), ("Chronos", "zero-shot, leakage flag"))):
        box(28, 41 - i * 9.5, 20, 7.5, f"{t}\n{sub}", fs=6.8)
    arrow(23.8, 43, 27.6, 43)
    arrow(23.8, 29.5, 27.6, 29.5)
    arrow(23.8, 15.5, 27.6, 15.5)
    # interval methods
    meths = [("Split", METHOD_COLOR["split"]), ("Rolling (120)", METHOD_COLOR["rolling"]), ("ACI (step 0.02)", METHOD_COLOR["aci"]),
             ("FACI", METHOD_COLOR["faci"]), ("Conformal PID", METHOD_COLOR["pid"]), ("DRACP", METHOD_COLOR["dracp"]),
             ("Native (ARIMA, ETS)", METHOD_COLOR["native"])]
    for i, (t, col) in enumerate(meths):
        y = 44.5 - i * 6.2
        ax.add_patch(Rectangle((53, y), 1.2, 4.6, fc=col, ec="none"))
        box(54.4, y, 19.6, 4.6, t, fs=6.8, fc="white")
    arrow(48.8, 33, 52.6, 33)
    # evaluation
    box(79, 38, 20, 11, "Rolling origin\n1 origin per month\nwarm-up $n_{cal}$ = 48 / 96", fs=6.9)
    box(79, 24.5, 20, 11, "Delayed feedback\noutcome released at\norigin + $h$ (h = 1, 3, 6, 12)", fs=6.9)
    box(79, 6, 20, 15.5, "Coverage, CE, Winkler\nblock bootstrap, Holm\nTOST (2 pp), MDE\nrules R1-R5, E1-E5", fs=6.9, fc="#eaeaea")
    arrow(74.6, 33, 78.6, 40)
    arrow(89, 37.6, 89, 36.2)
    arrow(89, 24.2, 89, 22.2)

    # rolling-origin timeline (bottom, left)
    y0 = -4.2
    ax.text(1, 0.6, "Rolling origin for one country (30 countries in total)", fontsize=7.2, fontweight="bold", va="center")
    segs = [(1, 20, "#c9c9c9", "training (min. 60)", "-"), (21, 12, "#fbeed6", "warm-up", "-"),
            (33, 32, "#dfeaf5", "evaluated origins (interval, then score)", "-"), (65, 10, "white", "+ h", "--")]
    for x, w, fc, t, ls in segs:
        ax.add_patch(Rectangle((x, y0), w, 3.0, fc=fc, ec="#444444", lw=0.6, ls=ls))
        ax.text(x + w / 2, y0 + 1.5, t, ha="center", va="center", fontsize=5.8)
    arrow(1, y0 - 0.7, 75, y0 - 0.7)
    ax.text(75.8, y0 - 0.7, "time", fontsize=6, va="center")
    save_pdf(fig, path)
    plt.close(fig)


# --------------------------------------------------------------------------------------------
def fig_coverage_h(path: Path):
    apply_style()
    fig, axes = plt.subplots(1, 3, figsize=(W2, 2.6), sharey=True)
    for ax, panel in zip(axes, ("expl", "hold1", "hold2")):
        p = pooled(PANEL_RUN[panel])
        p = p[p.model == "lgbm"]
        for me in METHODS:
            d = p[p.method == me].sort_values("h")
            x = [HPOS[h] for h in d.h]
            ax.plot(x, d.coverage, color=METHOD_COLOR[me], marker=METHOD_MARKER[me], ms=3.6, lw=1.1,
                    label=METHOD_LABEL[me], zorder=3 if me == "aci" else 2)
            if me == "aci":
                ax.fill_between(x, d.cov_lo, d.cov_hi, color=METHOD_COLOR[me], alpha=0.15, lw=0, zorder=1)
        ax.axhline(NOMINAL, color="black", ls="--", lw=0.8, zorder=0)
        ax.set_title(PANEL_LABEL[panel])
        _hlabels(ax)
        ax.grid(axis="y")
        ax.set_ylim(0.78, 0.99)
    axes[0].set_ylabel("Pooled coverage (LightGBM base)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=6, bbox_to_anchor=(0.5, -0.07), columnspacing=1.2, handletextpad=0.4)
    fig.text(0.5, -0.12, "Dashed line: nominal 0.90. Band: 95% bootstrap interval of ACI. Warm-up 48.", ha="center", fontsize=6.8)
    fig.tight_layout()
    save_pdf(fig, path)
    plt.close(fig)


# --------------------------------------------------------------------------------------------
def fig_ce_bars(path: Path):
    apply_style()
    fig, axes = plt.subplots(1, 3, figsize=(W2, 2.9), sharey=True)
    nm = len(METHODS)
    bw = 0.8 / nm
    for ax, panel in zip(axes, ("expl", "hold1", "hold2")):
        ct = ce_table(PANEL_RUN[panel])
        ct = ct[ct.model == "lgbm"]
        for j, me in enumerate(METHODS):
            d = ct[ct.method == me].set_index("h")
            x = np.array([HPOS[h] for h in HORIZONS]) - 0.4 + bw * (j + 0.5)
            y = np.array([d.loc[h, "ce"] for h in HORIZONS])
            se = np.array([d.loc[h, "se"] for h in HORIZONS])
            ax.bar(x, y, width=bw * 0.92, color=METHOD_COLOR[me], label=METHOD_LABEL[me], zorder=2)
            ax.errorbar(x, y, yerr=se, fmt="none", ecolor="black", elinewidth=0.6, capsize=0.8, zorder=3)
        ax.set_title(f"{PANEL_LABEL[panel]}")
        _hlabels(ax)
        ax.grid(axis="y", zorder=0)
    axes[0].set_ylabel("Calibration error (LightGBM base)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=6, bbox_to_anchor=(0.5, -0.07), columnspacing=1.2, handletextpad=0.4)
    fig.text(0.5, -0.12, "CE = mean over countries of |coverage - 0.90|; whiskers: one standard error across countries. Warm-up 48.",
             ha="center", fontsize=6.8)
    fig.tight_layout()
    save_pdf(fig, path)
    plt.close(fig)


# --------------------------------------------------------------------------------------------
def fig_contrasts_forest(path: Path):
    apply_style()
    rows = T.contrast_rows()
    keys = []
    for r in rows:
        k = (r["run"], r["model"])
        if k not in keys:
            keys.append(k)
    short = {"expl": "Design (13)", "hold1": "Hold-out 1 (7)", "hold2": "Hold-out 2 (10)",
             "d13r": "Design, from 2010", "h1r": "Hold-out 1, from 2010"}
    labels = [f"{short[RUNS[r]['panel']]}, {MODEL_LABEL[m]}" for r, m in keys]
    fig, axes = plt.subplots(1, 2, figsize=(W2, 4.0), sharey=True)
    ypos = {k: len(keys) - 1 - i for i, k in enumerate(keys)}
    for ax, contrast, title in zip(axes, ("aci-rolling", "dracp-aci"), ("ACI $-$ rolling", "DRACP $-$ ACI")):
        for r in rows:
            if r["contrast"] != contrast:
                continue
            y = ypos[(r["run"], r["model"])] + (0.17 if r["h"] == 3 else -0.17)
            col = BLUE if r["h"] == 3 else VERM
            mk = "o" if r["h"] == 3 else "s"
            hollow = (not r["mde_computed"]) or is_inconclusive(r["mde"])
            ax.plot([r["lo"], r["hi"]], [y, y], color=col, lw=1.1, zorder=2)
            ax.plot([r["T"]], [y], marker=mk, ms=4.6, mfc="white" if hollow else col, mec=col, mew=1.0, ls="none", zorder=3)
        ax.axvline(0, color="black", lw=0.7)
        ax.set_title(title)
        ax.set_xlabel("Change in calibration error (pp)")
        ax.grid(axis="x")
        ax.set_yticks([ypos[k] for k in keys])
        ax.set_yticklabels(labels)
        ax.set_ylim(-0.7, len(keys) - 0.3)
    handles = [
        Line2D([], [], marker="o", color=BLUE, ls="-", ms=4.6, label="$h=3$"),
        Line2D([], [], marker="s", color=VERM, ls="-", ms=4.6, label="$h=6$"),
        Line2D([], [], marker="o", color="#444444", mfc="#444444", ls="none", ms=4.6, label="MDE defined and $\\leq$ 7 pp"),
        Line2D([], [], marker="o", color="#444444", mfc="white", ls="none", ms=4.6, label="inconclusive (MDE undefined or $>$ 7 pp)"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.05), columnspacing=1.4)
    fig.tight_layout()
    save_pdf(fig, path)
    plt.close(fig)


# --------------------------------------------------------------------------------------------
def fig_width_winkler(path: Path):
    apply_style()
    fig, axes = plt.subplots(2, 2, figsize=(W2, 4.3), sharex=True)
    srcs = (("Design (13)", "explore_v1"), ("Hold-out 1 (7)", "holdout_ncal48"))
    for ci_, (title, rel) in enumerate(srcs):
        s4 = load(f"{rel}/robust/s4_compact.csv")
        s4 = s4[s4.n_cal == 48].set_index("method")
        for ri, (stat, lab) in enumerate((("winkler_ratio", "Winkler score ratio to rolling"), ("width_ratio", "Median width ratio to rolling"))):
            ax = axes[ri, ci_]
            for me in ("split", "aci", "faci", "pid", "dracp"):
                y = [s4.loc[me, f"{stat}_h{h}"] for h in HORIZONS]
                ax.plot(range(len(HORIZONS)), y, color=METHOD_COLOR[me], marker=METHOD_MARKER[me], ms=3.6, label=METHOD_LABEL[me])
            ax.axhline(1, color="black", ls="--", lw=0.8)
            ax.grid(axis="y")
            if ri == 0:
                ax.set_title(f"{title}, warm-up 48")
            if ci_ == 0:
                ax.set_ylabel(lab)
            if ri == 1:
                _hlabels(ax)
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=5, bbox_to_anchor=(0.5, -0.04), columnspacing=1.2)
    fig.text(0.5, -0.08, "LightGBM base. Ratio below 1: better than rolling conformal (dashed line).", ha="center", fontsize=6.8)
    fig.tight_layout()
    save_pdf(fig, path)
    plt.close(fig)


# --------------------------------------------------------------------------------------------
def fig_chronos_accuracy(path: Path):
    apply_style()
    a = T.accuracy_frame()
    fig, ax = plt.subplots(figsize=(W1, 3.3))
    comps = [("chronos - lgbm", "vs LightGBM", BLUE, "o"), ("chronos - arima", "vs ARIMA", GREEN, "s"), ("chronos - naive_b", "vs naive B", VERM, "D")]
    off = {0: 0.24, 1: 0.0, 2: -0.24}
    for k, (cmp, lab, col, mk) in enumerate(comps):
        d = a[a.comparison == cmp].set_index("h")
        for h in HORIZONS:
            y = (len(HORIZONS) - 1 - HPOS[h]) + off[k]
            r = d.loc[h]
            ax.plot([r.ci_lo, r.ci_hi], [y, y], color=col, lw=1.1)
            ax.plot([r.mean_abs_error_diff], [y], marker=mk, color=col, ms=4.2, ls="none", label=lab if h == 1 else None)
    ax.axvline(0, color="black", lw=0.7)
    ax.set_yticks(range(len(HORIZONS)))
    ax.set_yticklabels([f"$h={h}$" for h in HORIZONS[::-1]])
    ax.set_xlabel("MAE difference, Chronos $-$ other (pp)\n(negative favours Chronos)")
    ax.grid(axis="x")
    ax.legend(loc="lower left", fontsize=6.8)
    n_m = int(a["months"].iloc[0])
    ax.set_title(f"Clean months from 2025-01 ({n_m} months)", fontsize=8)
    fig.tight_layout()
    save_pdf(fig, path)
    plt.close(fig)


# --------------------------------------------------------------------------------------------
def fig_country_coverage(path: Path):
    apply_style()
    fig, axes = plt.subplots(1, 3, figsize=(W2, 4.3), sharex=True)
    for ax, panel in zip(axes, ("expl", "hold1", "hold2")):
        u = per_unit(PANEL_RUN[panel])
        u = u[(u.model == "lgbm") & (u.method == "aci")]
        c3 = u[u.h == 3].set_index("unit")["coverage"]
        c12 = u[u.h == 12].set_index("unit")["coverage"]
        order = list(c3.sort_values().index)
        y = np.arange(len(order))
        for yi, unit in zip(y, order):
            lo, hi = min(c3[unit], c12.get(unit, c3[unit])), max(c3[unit], c12.get(unit, c3[unit]))
            ax.plot([lo, hi], [yi, yi], color="#bbbbbb", lw=0.8, zorder=1)
        ax.scatter([c3[x] for x in order], y, color=BLUE, marker="o", s=16, zorder=3, label="$h=3$")
        ax.scatter([c12.get(x, np.nan) for x in order], y, color=VERM, marker="s", s=16, zorder=3, label="$h=12$")
        ax.axvline(NOMINAL, color="black", ls="--", lw=0.8)
        ax.set_yticks(y)
        ax.set_yticklabels([f"{COUNTRIES[x]}" for x in order])
        ax.set_title(PANEL_LABEL[panel])
        ax.set_xlabel("Coverage of ACI")
        ax.grid(axis="x")
        ax.set_ylim(-0.7, 12.7)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout()
    save_pdf(fig, path)
    plt.close(fig)


# --------------------------------------------------------------------------------------------
def fig_warmup_sensitivity(path: Path):
    apply_style()
    cfgs = T.warmup_configs()
    short = {"expl": "Design", "hold1": "Hold-out 1", "hold2": "Hold-out 2"}
    labels = [f"{short[RUNS[a]['panel']]}\n{MODEL_LABEL[m]}" for a, b, m in cfgs]
    fig, axes = plt.subplots(1, 2, figsize=(W2, 2.9), sharey=True)
    for ax, h in zip(axes, (3, 6)):
        for me, col, dx in (("aci", BLUE, -0.09), ("rolling", ORANGE, 0.09)):
            for i, (r48, r96, m) in enumerate(cfgs):
                v48 = T.ce_table_val(r48, m, me, h)
                v96 = T.ce_table_val(r96, m, me, h)
                ax.plot([i + dx, i + dx], [v48, v96], color=col, lw=0.9, zorder=1)
                ax.plot([i + dx], [v48], marker="o", color=col, ms=4.6, ls="none", zorder=3)
                ax.plot([i + dx], [v96], marker="o", mfc="white", mec=col, ms=4.6, mew=1.1, ls="none", zorder=3)
        ax.set_xticks(range(len(cfgs)))
        ax.set_xticklabels(labels, fontsize=6.4)
        ax.set_title(f"$h={h}$")
        ax.grid(axis="y")
    axes[0].set_ylabel("Calibration error")
    handles = [
        Line2D([], [], marker="o", color=BLUE, ls="-", ms=4.6, label="ACI"),
        Line2D([], [], marker="o", color=ORANGE, ls="-", ms=4.6, label="Rolling"),
        Line2D([], [], marker="o", color="#444444", ls="none", ms=4.6, label="warm-up 48 (filled)"),
        Line2D([], [], marker="o", mfc="white", mec="#444444", color="#444444", ls="none", ms=4.6, label="warm-up 96 (hollow)"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.05), columnspacing=1.4)
    fig.tight_layout()
    save_pdf(fig, path)
    plt.close(fig)


FIGURES = {
    "fig_pipeline.pdf": fig_pipeline,
    "fig_coverage_h.pdf": fig_coverage_h,
    "fig_ce_bars.pdf": fig_ce_bars,
    "fig_contrasts_forest.pdf": fig_contrasts_forest,
    "fig_width_winkler.pdf": fig_width_winkler,
    "fig_chronos_accuracy.pdf": fig_chronos_accuracy,
    "fig_country_coverage.pdf": fig_country_coverage,
    "fig_warmup_sensitivity.pdf": fig_warmup_sensitivity,
}
