import React from "react";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("react-chartjs-2", () => ({
  Line: ({ data }) => <div data-testid="line-chart" data-datasets={data.datasets.length} data-points={data.labels.length} />,
  Bar: ({ data }) => <div data-testid="bar-chart" data-datasets={data.datasets.length} />,
}));

vi.mock("../../api/inflationApi", () => ({
  listInflationCountries: vi.fn(),
  fetchCalibratedForecast: vi.fn(),
  fetchInflationBenchmark: vi.fn(),
  fetchInflationCompare: vi.fn(),
  explainInflation: vi.fn(),
}));

import InflationResearchPage from "../InflationResearchPage";
import { buildBandData, buildRunningData } from "../../components/inflation-research/MethodsComparedTab";
import { buildCeData } from "../../components/inflation-research/FindingsTab";
import { I18nProvider } from "../../context/I18nContext";
import { ThemeProvider } from "../../context/ThemeContext";
import {
  explainInflation,
  fetchCalibratedForecast,
  fetchInflationBenchmark,
  fetchInflationCompare,
  listInflationCountries,
} from "../../api/inflationApi";

const COUNTRIES = [
  { code: "KZ", name: "Kazakhstan", n_months: 200, first: "2008-01", last: "2025-08" },
  { code: "MX", name: "Mexico", n_months: 300, first: "2000-01", last: "2025-08" },
];

const series = (covered) =>
  [0, 1, 2, 3].map((i) => ({
    origin: `2024-0${i + 1}`,
    date: `2024-0${i + 4}`,
    point: 1,
    lower: 0,
    upper: 2,
    actual: covered[i] ? 1 : 3,
    covered: covered[i],
    running_coverage: 0.9,
  }));

const method = (cov) => ({
  coverage: cov,
  calibration_error: Math.abs(cov - 0.9),
  mean_width: 4.2,
  n_eval: 120,
  series: series([true, true, false, true]),
});

const COMPARE = {
  country: "KZ",
  horizon: 3,
  level: 0.9,
  warmup: 48,
  methods: { split: method(0.8), rolling: method(0.85), aci: method(0.912) },
};

const BENCH = {
  mde_limit_pp: 7,
  panels: {
    expl: { label: "Design panel (13 countries)", status: "exploratory", note: "n1" },
    hold1: { label: "Hold-out 1 (7 countries)", status: "pre-specified", note: "n2" },
    hold2: { label: "Hold-out 2 (10 countries)", status: "pre-specified", note: "n3" },
  },
  base_models: { lgbm: "LightGBM", arima: "ARIMA", naive_b: "Naive B", chronos: "Chronos" },
  ce: [
    { panel: "hold1", base_model: "lgbm", method: "aci", h: 3, ce_pp: 1.2, status: "pre-specified" },
    { panel: "hold1", base_model: "lgbm", method: "split", h: 3, ce_pp: 4.1, status: "pre-specified" },
    { panel: "hold1", base_model: "lgbm", method: "rolling", h: 3, ce_pp: 2.2, status: "pre-specified" },
    { panel: "expl", base_model: "lgbm", method: "aci", h: 3, ce_pp: 1.0, status: "exploratory" },
    { panel: "hold2", base_model: "arima", method: "aci", h: 3, ce_pp: 1.1, status: "pre-specified" },
  ],
  contrasts: [
    { panel: "hold1", run: "hold48", base_model: "lgbm", h: 3, contrast: "aci-rolling", family: "primary", status: "pre-specified", diff_pp: -1.6, ci_lo_pp: -3.5, ci_hi_pp: 0.2, p: 0.1, p_holm: 0.35, mde_pp: null, verdict: "inconclusive", panel_dependent: true },
    { panel: "hold2", run: "h2_48", base_model: "lgbm", h: 3, contrast: "aci-rolling", family: "primary", status: "pre-specified", diff_pp: -3.7, ci_lo_pp: -5, ci_hi_pp: -1, p: 0.001, p_holm: 0.008, mde_pp: 3.16, verdict: "shown", panel_dependent: true },
    { panel: "hold2", run: "h2_48", base_model: "lgbm", h: 6, contrast: "aci-rolling", family: "primary", status: "pre-specified", diff_pp: -3.5, ci_lo_pp: -8, ci_hi_pp: 1, p: 0.1, p_holm: 0.16, mde_pp: 6.1, verdict: "not shown", panel_dependent: true },
    { panel: "hold1", run: "hold48", base_model: "lgbm", h: 3, contrast: "aci-split", family: "secondary", status: "pre-specified", diff_pp: -3.0, ci_lo_pp: -4, ci_hi_pp: -2, p: 0.001, p_holm: null, mde_pp: null, verdict: "descriptive", panel_dependent: false },
  ],
  chronos_accuracy: {
    rows: [
      { h: 1, comparison: "chronos - lgbm", mae_diff: -0.02, ci_lo: -0.04, ci_hi: -0.007, rel_mae_chronos: 0.774, rel_mae_other: 0.824, status: "pre-specified" },
      { h: 1, comparison: "chronos - arima", mae_diff: -0.03, ci_lo: -0.05, ci_hi: -0.02, rel_mae_chronos: 0.774, rel_mae_other: 0.853, status: "pre-specified" },
    ],
  },
  feedback_delay_h12: [
    { panel: "hold1", method: "aci", cov_delayed: 0.884, cov_instant: 0.908, diff_pp: 2.4, ci_lo_pp: -0.1, ci_hi_pp: 4.8, status: "pre-specified (secondary S3)" },
  ],
  native_vs_aci: { status: "post hoc", aci_minus_native: [{ sample: "exploratory", h: 1, diff_pp: -3.7, ci_lo_pp: -4.6, ci_hi_pp: -0.6, p: 0.004 }] },
  commodity: {
    status: "post hoc",
    n_qualifying: 27,
    n_countries: 30,
    countries: [
      { code: "KZ", name: "Kazakhstan", share_2021_2023: 83.5, qualifies_60: true },
      { code: "MX", name: "Mexico", share_2021_2023: 18.2, qualifies_60: false },
    ],
  },
  llm_eval: {
    v1: { rows: [{ by: "condition", condition: "grounded", n: 468, faithful_rate: 0.906 }] },
    v2: {
      rows: [
        { by: "condition", condition: "grounded", n: 468, faithful_rate: 1.0 },
        { by: "condition", condition: "ungrounded", n: 468, faithful_rate: 0.69 },
      ],
    },
  },
  sources: ["a", "b", "c"],
};

const EXPLAIN = {
  country: "KZ",
  horizon: 3,
  grounded: true,
  question: "What is the inflation forecast for Kazakhstan at 3 months?",
  answer: "The 90% interval is 0.50% to 4.50%.",
  model_saw: { country: "KZ", forecast: { point: 2.5, lower: 0.5, upper: 4.5 } },
  reference: { forecast: { point: 2.5, lower: 0.5, upper: 4.5 }, empirical_coverage: 0.9 },
  check: { checked: true, faithful: true, n_claimed: 2, n_unmatched: 0, guarantee_wording: false },
  model: "test-model",
  seconds: 3.2,
};

const renderPage = () =>
  render(
    <MemoryRouter>
      <I18nProvider>
        <ThemeProvider>
          <InflationResearchPage />
        </ThemeProvider>
      </I18nProvider>
    </MemoryRouter>
  );

describe("InflationResearchPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.setItem("ewp_language", "en");
    listInflationCountries.mockResolvedValue(COUNTRIES);
    fetchInflationBenchmark.mockResolvedValue(BENCH);
    fetchInflationCompare.mockResolvedValue(COMPARE);
    fetchCalibratedForecast.mockResolvedValue({
      country: "KZ", horizon: 3, level: 0.9, as_of: "2025-08",
      history: [{ date: "2025-08", value: 100 }],
      forecast: { date: "2025-11", point: 1, lower: 0, upper: 2 },
      calibration: { empirical_coverage: 0.9, nominal: 0.9, n_eval: 10, mean_width: 2 },
      notes: [],
    });
    explainInflation.mockResolvedValue(EXPLAIN);
  });

  it("shows the honest disclaimer and the four tabs on every tab", async () => {
    renderPage();
    const disclaimer = screen.getByTestId("research-disclaimer");
    expect(disclaimer).toHaveTextContent(/not financial or policy advice/i);
    expect(disclaimer).toHaveTextContent(/better calibrated than one-shot/i);
    expect(disclaimer).toHaveTextContent(/DRACP versus ACI is inconclusive/i);
    expect(disclaimer).toHaveTextContent(/post hoc/i);
    expect(screen.getAllByRole("tab")).toHaveLength(4);
    await userEvent.click(screen.getByRole("tab", { name: /what we found/i }));
    expect(screen.getByTestId("research-disclaimer")).toBeInTheDocument();
  });

  it("methods tab: three method cards, plain caption and commodity badge", async () => {
    renderPage();
    expect(await screen.findByTestId("coverage-aci")).toHaveTextContent("91.2%");
    expect(screen.getByTestId("coverage-split")).toHaveTextContent("80.0%");
    expect(screen.getByTestId("calerr-rolling")).toHaveTextContent("5.0");
    expect(screen.getByTestId("plain-caption")).toHaveTextContent("9 times in 10");
    expect(fetchInflationCompare).toHaveBeenCalledWith(
      { country: "KZ", horizon: 3, level: 0.9, warmup: 48 },
      expect.anything()
    );
    expect(await screen.findByTestId("commodity-badge")).toHaveTextContent(/commodity-dependent \(83.5%\)/);
    expect(screen.getAllByTestId("line-chart")).toHaveLength(2);
  });

  it("methods tab: changing the horizon refetches", async () => {
    renderPage();
    await screen.findByTestId("coverage-aci");
    await userEvent.click(screen.getByRole("button", { name: "12 mo" }));
    await waitFor(() =>
      expect(fetchInflationCompare).toHaveBeenLastCalledWith(
        { country: "KZ", horizon: 12, level: 0.9, warmup: 48 },
        expect.anything()
      )
    );
  });

  it("methods tab: shows an error box when the API fails", async () => {
    fetchInflationCompare.mockRejectedValue(new Error("boom"));
    renderPage();
    expect(await screen.findByRole("alert")).toHaveTextContent(/unable to run the comparison/i);
  });

  it("findings tab: verdict chips follow the benchmark and flag panel dependence", async () => {
    renderPage();
    await userEvent.click(screen.getByRole("tab", { name: /what we found/i }));
    const rows = await screen.findAllByTestId("contrast-row");
    expect(rows).toHaveLength(4);
    const verdicts = rows.map((r) => within(r).getByTestId("verdict-chip").getAttribute("data-verdict"));
    expect(verdicts).toEqual(["inconclusive", "shown", "not shown", "descriptive"]);
    expect(screen.getAllByTestId("panel-dependent").length).toBe(3);
    expect(screen.getByTestId("commodity-summary")).toHaveTextContent("27 of 30");
    expect(screen.getByTestId("headline")).toHaveTextContent(/DRACP versus ACI is inconclusive/);
    expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
    // status tags on benchmark numbers
    expect(within(screen.getByTestId("native-section")).getByTestId("status-chip")).toHaveAttribute("data-status", "post hoc");
  });

  it("findings tab: shows an error when the benchmark cannot be loaded", async () => {
    fetchInflationBenchmark.mockRejectedValue(new Error("down"));
    renderPage();
    await userEvent.click(screen.getByRole("tab", { name: /what we found/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/could not be loaded/i);
  });

  it("explain tab: grounded answer shows the data the model saw, the check badge and the evaluation numbers", async () => {
    renderPage();
    await userEvent.click(screen.getByRole("tab", { name: /explain it/i }));
    await userEvent.click(await screen.findByRole("button", { name: "Explain" }));
    expect(await screen.findByTestId("answer-text")).toHaveTextContent("0.50% to 4.50%");
    expect(explainInflation).toHaveBeenCalledWith({
      country: "KZ", horizon: 3, question_type: "T1", language: "en", grounded: true,
    });
    expect(screen.getByTestId("model-saw")).toHaveTextContent('"upper": 4.5');
    expect(screen.getByTestId("check-badge")).toHaveAttribute("data-faithful", "true");
    const ev = screen.getByTestId("eval-numbers");
    expect(ev).toHaveTextContent("100.0%");
    expect(ev).toHaveTextContent("90.6%");
    expect(screen.getByTestId("eval-note")).toHaveTextContent(/one model/i);
    expect(within(screen.getByTestId("eval-note")).getByTestId("status-chip")).toHaveAttribute("data-status", "post hoc");
  });

  it("explain tab: compare both modes and ungrounded shows nothing was seen", async () => {
    explainInflation.mockImplementation(async (body) =>
      body.grounded
        ? EXPLAIN
        : { ...EXPLAIN, grounded: false, model_saw: null, answer: "Probably around 7%.", check: { checked: true, faithful: false, n_claimed: 1, n_unmatched: 1, guarantee_wording: false } }
    );
    renderPage();
    await userEvent.click(screen.getByRole("tab", { name: /explain it/i }));
    await userEvent.click(await screen.findByRole("button", { name: /compare grounded and ungrounded/i }));
    expect(await screen.findByTestId("answer-ungrounded")).toHaveTextContent("Probably around 7%.");
    expect(screen.getByTestId("answer-grounded")).toBeInTheDocument();
    expect(screen.getByTestId("model-saw-none")).toHaveTextContent(/received no forecast data/i);
    const badges = screen.getAllByTestId("check-badge").map((b) => b.getAttribute("data-faithful"));
    expect(badges).toEqual(["true", "false"]);
  });

  it("explain tab: 503 shows a clear message without details", async () => {
    explainInflation.mockRejectedValue({ response: { status: 503, data: { detail: "x" } } });
    renderPage();
    await userEvent.click(screen.getByRole("tab", { name: /explain it/i }));
    await userEvent.click(await screen.findByRole("button", { name: "Explain" }));
    expect(await screen.findByTestId("explain-error")).toHaveTextContent(/not available right now/i);
  });

  it("forecast tab embeds the existing forecast page", async () => {
    renderPage();
    await userEvent.click(screen.getByRole("tab", { name: /^forecast$/i }));
    expect(await screen.findByTestId("point-value")).toBeInTheDocument();
  });
});

describe("chart data builders", () => {
  it("buildBandData colours covered points green and missed red", () => {
    const d = buildBandData(series([true, false, true, true]), { lower: "l", upper: "u", actual: "a" });
    expect(d.datasets).toHaveLength(3);
    expect(d.datasets[2].pointBackgroundColor[1]).toBe("#f87171");
    expect(d.datasets[2].pointBackgroundColor[0]).toBe("#34d399");
    expect(d.labels).toHaveLength(4);
  });

  it("buildRunningData adds a nominal line", () => {
    const d = buildRunningData(COMPARE.methods, 0.9, "nominal");
    expect(d.datasets).toHaveLength(4);
    expect(d.datasets[3].data.every((v) => v === 90)).toBe(true);
  });

  it("buildCeData selects panel and model", () => {
    const d = buildCeData(BENCH.ce, "hold1", "lgbm", (m) => m);
    expect(d.datasets.map((x) => x.label)).toEqual(["split", "rolling", "aci"]);
    expect(d.datasets[2].data).toEqual([null, 1.2, null, null]);
  });
});
