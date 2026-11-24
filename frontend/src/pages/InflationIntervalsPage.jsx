import React, { useEffect, useMemo, useState } from "react";
import { Link, useInRouterContext } from "react-router-dom";
import { Line } from "react-chartjs-2";
import { Chart as ChartJS } from "chart.js/auto";

import { fetchCalibratedForecast, listInflationCountries } from "../api/inflationApi";
import { useI18n } from "../context/I18nContext";
import { useTheme } from "../context/ThemeContext";

ChartJS;

export const HORIZONS = [1, 3, 6, 12];
export const LEVEL = 0.9;

/* Forecast is a cumulative h-month % log growth; convert to a CPI-index level
   so it can share the axis with the CPI history. */
const toLevel = (last, pct) => (typeof pct === "number" ? last * Math.exp(pct / 100) : null);

export const buildChartData = (data, labels) => {
  const history = (data.history || []).filter((r) => typeof r.value === "number");
  const f = data.forecast;
  const lastIdx = history.length - 1;
  const last = lastIdx >= 0 ? history[lastIdx].value : null;
  const dates = [...history.map((r) => r.date), f.date];
  const blank = () => dates.map(() => null);

  const histData = [...history.map((r) => r.value), null];
  const anchored = (pct) => {
    const arr = blank();
    arr[lastIdx] = last;
    arr[dates.length - 1] = toLevel(last, pct);
    return arr;
  };

  return {
    labels: dates,
    datasets: [
      {
        label: labels.history,
        data: histData,
        borderColor: "#38bdf8",
        backgroundColor: "rgba(56,189,248,0.15)",
        tension: 0.2,
        pointRadius: 0,
        pointHoverRadius: 4,
        order: 1,
      },
      {
        label: labels.point,
        data: anchored(f.point),
        borderColor: "#fbbf24",
        backgroundColor: "#fbbf24",
        borderDash: [6, 4],
        pointRadius: dates.map((_, i) => (i === dates.length - 1 ? 5 : 0)),
        spanGaps: true,
        order: 2,
      },
      /* Lower bound — fill toward next dataset (upper), as on the forecast page */
      {
        label: labels.lower,
        data: anchored(f.lower),
        borderColor: "rgba(251,191,36,0.3)",
        backgroundColor: "rgba(251,191,36,0.12)",
        borderDash: [2, 4],
        pointRadius: 0,
        spanGaps: true,
        fill: "+1",
        order: 3,
      },
      {
        label: labels.upper,
        data: anchored(f.upper),
        borderColor: "rgba(251,191,36,0.3)",
        backgroundColor: "transparent",
        borderDash: [2, 4],
        pointRadius: 0,
        spanGaps: true,
        fill: false,
        order: 4,
      },
    ],
  };
};

const fmtPct = (v, digits = 2) => (typeof v === "number" ? `${v > 0 ? "+" : ""}${v.toFixed(digits)}%` : "—");
const isCanceled = (err) => err?.code === "ERR_CANCELED" || err?.name === "CanceledError";

export default function InflationIntervalsPage() {
  const { t } = useI18n();
  const { theme } = useTheme();
  const inRouter = useInRouterContext();
  const isDark = theme === "dark";
  const axisColor = isDark ? "#94a3b8" : "#475569";
  const gridColor = isDark ? "rgba(148,163,184,0.12)" : "rgba(71,85,105,0.12)";

  const [countries, setCountries] = useState([]);
  const [countriesState, setCountriesState] = useState({ loading: true, error: false });
  const [country, setCountry] = useState("");
  const [horizon, setHorizon] = useState(3);
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState({ loading: false, error: false });

  useEffect(() => {
    const ctrl = new AbortController();
    listInflationCountries(ctrl.signal)
      .then((rows) => {
        const list = Array.isArray(rows) ? rows : [];
        setCountries(list);
        setCountriesState({ loading: false, error: false });
        if (list.length) setCountry((c) => c || list[0].code);
      })
      .catch((err) => {
        if (isCanceled(err)) return;
        setCountriesState({ loading: false, error: true });
      });
    return () => ctrl.abort();
  }, []);

  useEffect(() => {
    if (!country) return undefined;
    const ctrl = new AbortController();
    setStatus({ loading: true, error: false });
    fetchCalibratedForecast({ country, horizon, level: LEVEL }, ctrl.signal)
      .then((data) => {
        setResult(data);
        setStatus({ loading: false, error: false });
      })
      .catch((err) => {
        if (isCanceled(err)) return;
        setResult(null);
        setStatus({ loading: false, error: true });
      });
    return () => ctrl.abort();
  }, [country, horizon]);

  const chartData = useMemo(() => {
    if (!result?.forecast || !result.history?.length) return null;
    return buildChartData(result, {
      history: t("inflation.chartHistory"),
      point: t("inflation.chartPoint"),
      lower: t("inflation.chartLower"),
      upper: t("inflation.chartUpper"),
    });
  }, [result, t]);

  const chartOptions = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { position: "bottom", labels: { color: axisColor, boxWidth: 12, padding: 16, font: { size: 11 } } },
      },
      scales: {
        x: {
          ticks: { color: axisColor, maxTicksLimit: 8, font: { size: 11 } },
          grid: { color: gridColor },
        },
        y: {
          ticks: { color: axisColor, font: { size: 11 } },
          title: { display: true, text: t("inflation.cpiIndex"), color: axisColor },
          grid: { color: gridColor },
        },
      },
    }),
    [axisColor, gridColor, t]
  );

  const cal = result?.calibration;
  const gap =
    cal && typeof cal.empirical_coverage === "number" && typeof cal.nominal === "number"
      ? cal.empirical_coverage - cal.nominal
      : null;
  const hasData = Boolean(chartData && result?.forecast);

  return (
    <section className="panel-wide">
      <div>
        <p className="hero-kicker">{t("inflation.kicker")}</p>
        <h3 className="panel-title">{t("inflation.title")}</h3>
        <p className="text-sm text-muted mt-2 max-w-2xl">{t("inflation.subtitle")}</p>
        <p className="text-xs mt-2" data-testid="research-link">
          {inRouter ? (
            <Link to="/inflation-research" className="underline">
              {t("inflation.researchLink")}
            </Link>
          ) : (
            <a href="/inflation-research" className="underline">
              {t("inflation.researchLink")}
            </a>
          )}
        </p>
      </div>

      <div className="mt-6 surface p-4 grid sm:grid-cols-2 gap-4">
        <div>
          <label className="label" htmlFor="infl-country">
            {t("inflation.country")}
          </label>
          <select
            id="infl-country"
            className="input"
            value={country}
            disabled={countriesState.loading || countries.length === 0}
            onChange={(e) => setCountry(e.target.value)}
          >
            {countries.map((c) => (
              <option key={c.code} value={c.code}>
                {c.name} ({c.code})
              </option>
            ))}
          </select>
        </div>
        <div>
          <span className="label" id="infl-horizon-label">
            {t("inflation.horizon")}
          </span>
          <div className="flex gap-1 mt-1" role="group" aria-labelledby="infl-horizon-label">
            {HORIZONS.map((h) => (
              <button
                key={h}
                type="button"
                className={horizon === h ? "tab-active" : "tab"}
                aria-pressed={horizon === h}
                onClick={() => setHorizon(h)}
              >
                {t("inflation.horizonMonths", { n: h })}
              </button>
            ))}
          </div>
        </div>
      </div>

      {countriesState.error ? (
        <div className="mt-6 surface p-4 text-sm" role="alert">
          {t("inflation.errorCountries")}
        </div>
      ) : countriesState.loading ? (
        <p className="mt-6 text-xs text-muted">{t("inflation.loading")}</p>
      ) : countries.length === 0 ? (
        <div className="mt-6 surface p-4 text-sm text-muted">{t("inflation.emptyCountries")}</div>
      ) : status.error ? (
        <div className="mt-6 surface p-4 text-sm" role="alert">
          {t("inflation.errorForecast")}
        </div>
      ) : status.loading ? (
        <p className="mt-6 text-xs text-muted" role="status">
          {t("inflation.loading")}
        </p>
      ) : !hasData ? (
        <div className="mt-6 surface p-4 text-sm text-muted">{t("inflation.emptyForecast")}</div>
      ) : (
        <>
          <div className="mt-6 grid sm:grid-cols-3 gap-4">
            <div className="surface p-4">
              <p className="label">{t("inflation.pointLabel", { h: result.horizon })}</p>
              <p className="text-xl font-semibold" data-testid="point-value">
                {fmtPct(result.forecast.point)}
              </p>
            </div>
            <div className="surface p-4">
              <p className="label">{t("inflation.intervalLabel", { level: Math.round(result.level * 100) })}</p>
              <p className="text-xl font-semibold" data-testid="interval-value">
                {fmtPct(result.forecast.lower)} … {fmtPct(result.forecast.upper)}
              </p>
            </div>
            <div className="surface p-4">
              <p className="label">{t("inflation.asOf")}</p>
              <p className="text-xl font-semibold">{result.as_of}</p>
            </div>
          </div>
          <p className="mt-2 text-[11px] text-faint">{t("inflation.growthNote")}</p>

          <div className="chart-card chart-card-appear mt-4">
            <Line data={chartData} options={chartOptions} />
          </div>

          <div className="surface p-4 mt-6" data-testid="calibration-panel">
            <h4 className="panel-title">{t("inflation.calibrationTitle")}</h4>
            {cal ? (
              <dl className="mt-3 grid sm:grid-cols-4 gap-4">
                <div>
                  <dt className="label">{t("inflation.nominal")}</dt>
                  <dd className="text-lg font-semibold">{(cal.nominal * 100).toFixed(1)}%</dd>
                </div>
                <div>
                  <dt className="label">{t("inflation.empirical")}</dt>
                  <dd className="text-lg font-semibold">
                    {(cal.empirical_coverage * 100).toFixed(1)}%
                    {gap != null && (
                      <span className="ml-2 text-xs text-muted">
                        ({gap >= 0 ? "+" : ""}
                        {(gap * 100).toFixed(1)} {t("inflation.ppUnit")})
                      </span>
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="label">{t("inflation.nEval")}</dt>
                  <dd className="text-lg font-semibold">{cal.n_eval}</dd>
                </div>
                <div>
                  <dt className="label">{t("inflation.meanWidth")}</dt>
                  <dd className="text-lg font-semibold">
                    {Number(cal.mean_width).toFixed(2)} {t("inflation.ppUnit")}
                  </dd>
                </div>
              </dl>
            ) : (
              <p className="mt-3 text-sm text-muted">{t("inflation.noCalibration")}</p>
            )}
            <p className="mt-4 text-sm text-muted">{t("inflation.explain")}</p>
            <p className="mt-2 text-sm text-muted">{t("inflation.caveat")}</p>
            {Array.isArray(result.notes) && result.notes.length > 0 && (
              <ul className="mt-3 list-disc pl-5 text-xs text-faint space-y-1">
                {result.notes.map((n, i) => (
                  <li key={i}>{n}</li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </section>
  );
}
