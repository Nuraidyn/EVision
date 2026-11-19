import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("react-chartjs-2", () => ({
  Line: ({ data }) => <div data-testid="line-chart" data-datasets={data.datasets.length} />,
}));

vi.mock("../../api/inflationApi", () => ({
  listInflationCountries: vi.fn(),
  fetchCalibratedForecast: vi.fn(),
}));

import InflationIntervalsPage, { buildChartData } from "../InflationIntervalsPage";
import { I18nProvider } from "../../context/I18nContext";
import { ThemeProvider } from "../../context/ThemeContext";
import { fetchCalibratedForecast, listInflationCountries } from "../../api/inflationApi";

const COUNTRIES = [
  { code: "KZ", name: "Kazakhstan", n_months: 200, first: "2008-01", last: "2025-08" },
  { code: "BR", name: "Brazil", n_months: 300, first: "2000-01", last: "2025-08" },
];

const makeResponse = (over = {}) => ({
  country: "KZ",
  horizon: 3,
  level: 0.9,
  method: "aci",
  as_of: "2025-08",
  history: [
    { date: "2025-06", value: 100 },
    { date: "2025-07", value: 101 },
    { date: "2025-08", value: 102 },
  ],
  forecast: { date: "2025-11", point: 2.5, lower: 0.5, upper: 4.5 },
  calibration: { empirical_coverage: 0.874, nominal: 0.9, n_eval: 120, mean_width: 4.2 },
  notes: ["test note"],
  ...over,
});

const renderPage = () =>
  render(
    <I18nProvider>
      <ThemeProvider>
        <InflationIntervalsPage />
      </ThemeProvider>
    </I18nProvider>
  );

describe("InflationIntervalsPage", () => {
  beforeEach(() => {
    window.localStorage.setItem("ewp_language", "en");
    listInflationCountries.mockResolvedValue(COUNTRIES);
    fetchCalibratedForecast.mockResolvedValue(makeResponse());
  });

  it("renders chart, forecast values and calibration panel", async () => {
    renderPage();
    expect(await screen.findByTestId("line-chart")).toBeInTheDocument();
    expect(screen.getByTestId("point-value")).toHaveTextContent("+2.50%");
    expect(screen.getByTestId("interval-value")).toHaveTextContent("+0.50%");

    const panel = screen.getByTestId("calibration-panel");
    expect(panel).toHaveTextContent("90.0%");
    expect(panel).toHaveTextContent("87.4%");
    expect(panel).toHaveTextContent("120");
    expect(panel).toHaveTextContent("4.20");
    expect(panel).toHaveTextContent(/below the nominal level/i);
    expect(panel).toHaveTextContent("test note");
  });

  it("requests the first country with default horizon 3 and level 0.9", async () => {
    renderPage();
    await screen.findByTestId("line-chart");
    expect(fetchCalibratedForecast).toHaveBeenCalledWith(
      { country: "KZ", horizon: 3, level: 0.9 },
      expect.anything()
    );
  });

  it("re-requests when the horizon or country changes", async () => {
    renderPage();
    await screen.findByTestId("line-chart");

    await userEvent.click(screen.getByRole("button", { name: /12 mo/i }));
    await waitFor(() =>
      expect(fetchCalibratedForecast).toHaveBeenLastCalledWith(
        { country: "KZ", horizon: 12, level: 0.9 },
        expect.anything()
      )
    );

    await userEvent.selectOptions(screen.getByLabelText(/country/i), "BR");
    await waitFor(() =>
      expect(fetchCalibratedForecast).toHaveBeenLastCalledWith(
        { country: "BR", horizon: 12, level: 0.9 },
        expect.anything()
      )
    );
  });

  it("shows an error state when the forecast request fails", async () => {
    fetchCalibratedForecast.mockRejectedValue(new Error("boom"));
    renderPage();
    expect(await screen.findByRole("alert")).toHaveTextContent(/unable to load the forecast/i);
    expect(screen.queryByTestId("line-chart")).not.toBeInTheDocument();
  });

  it("shows an error state when the country list fails", async () => {
    listInflationCountries.mockRejectedValue(new Error("boom"));
    renderPage();
    expect(await screen.findByRole("alert")).toHaveTextContent(/list of countries/i);
    expect(fetchCalibratedForecast).not.toHaveBeenCalled();
  });

  it("shows an empty state when no countries are available", async () => {
    listInflationCountries.mockResolvedValue([]);
    renderPage();
    expect(await screen.findByText(/no countries are available/i)).toBeInTheDocument();
    expect(fetchCalibratedForecast).not.toHaveBeenCalled();
  });
});

describe("buildChartData", () => {
  it("anchors the interval at the last observation and converts log growth to levels", () => {
    const data = buildChartData(makeResponse(), { history: "h", point: "p", lower: "l", upper: "u" });
    expect(data.labels).toEqual(["2025-06", "2025-07", "2025-08", "2025-11"]);
    const [, point, lower, upper] = data.datasets;
    expect(point.data[2]).toBe(102);
    expect(point.data[3]).toBeCloseTo(102 * Math.exp(0.025), 6);
    expect(lower.data[3]).toBeLessThan(point.data[3]);
    expect(upper.data[3]).toBeGreaterThan(point.data[3]);
    expect(lower.fill).toBe("+1");
  });
});
