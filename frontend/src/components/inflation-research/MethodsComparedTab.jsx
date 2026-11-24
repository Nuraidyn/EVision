import React, { useEffect, useMemo, useState } from "react";
import { Line } from "react-chartjs-2";
import { Chart as ChartJS } from "chart.js/auto";

import { fetchInflationCompare } from "../../api/inflationApi";
import { useI18n } from "../../context/I18nContext";
import { useTheme } from "../../context/ThemeContext";
import {
  CountrySelect,
  ErrorBox,
  HorizonButtons,
  METHOD_COLOR,
  isCanceled,
  pct1,
  useChartColors,
} from "./shared";

ChartJS;

const METHODS = ["split", "rolling", "aci"];

export const buildBandData = (series, labels) => ({
  labels: series.map((s) => s.date),
  datasets: [
    {
      label: labels.lower,
      data: series.map((s) => s.lower),
      borderColor: "rgba(56,189,248,0.4)",
      backgroundColor: "rgba(56,189,248,0.15)",
      pointRadius: 0,
      fill: "+1",
      order: 3,
    },
    {
      label: labels.upper,
      data: series.map((s) => s.upper),
      borderColor: "rgba(56,189,248,0.4)",
      backgroundColor: "transparent",
      pointRadius: 0,
      fill: false,
      order: 4,
    },
    {
      label: labels.actual,
      data: series.map((s) => s.actual),
      borderColor: "rgba(148,163,184,0.6)",
      borderWidth: 1,
      tension: 0.1,
      pointRadius: 4,
      pointHoverRadius: 6,
      pointBackgroundColor: series.map((s) => (s.covered ? "#34d399" : "#f87171")),
      pointBorderColor: series.map((s) => (s.covered ? "#34d399" : "#f87171")),
      pointStyle: series.map((s) => (s.covered ? "circle" : "crossRot")),
      order: 1,
    },
  ],
});

export const buildRunningData = (methods, level, nominalLabel) => {
  const first = methods.aci?.series || [];
  return {
    labels: first.map((s) => s.date),
    datasets: [
      ...METHODS.filter((m) => methods[m]).map((m) => ({
        label: m,
        data: methods[m].series.map((s) => s.running_coverage * 100),
        borderColor: METHOD_COLOR[m],
        backgroundColor: METHOD_COLOR[m],
        pointRadius: 0,
        tension: 0.15,
      })),
      {
        label: nominalLabel,
        data: first.map(() => level * 100),
        borderColor: "rgba(148,163,184,0.8)",
        borderDash: [6, 4],
        pointRadius: 0,
      },
    ],
  };
};

export default function MethodsComparedTab({ countries, commodity }) {
  const { t } = useI18n();
  const { theme } = useTheme();
  const colors = useChartColors(theme);
  const [country, setCountry] = useState("");
  const [horizon, setHorizon] = useState(3);
  const [method, setMethod] = useState("aci");
  const [data, setData] = useState(null);
  const [status, setStatus] = useState({ loading: false, error: false });

  useEffect(() => {
    if (!country && countries.length) setCountry(countries[0].code);
  }, [countries, country]);

  useEffect(() => {
    if (!country) return undefined;
    const ctrl = new AbortController();
    setStatus({ loading: true, error: false });
    fetchInflationCompare({ country, horizon, level: 0.9, warmup: 48 }, ctrl.signal)
      .then((d) => {
        setData(d);
        setStatus({ loading: false, error: false });
      })
      .catch((err) => {
        if (isCanceled(err)) return;
        setData(null);
        setStatus({ loading: false, error: true });
      });
    return () => ctrl.abort();
  }, [country, horizon]);

  const labels = useMemo(
    () => ({
      lower: t("research.methods.lower"),
      upper: t("research.methods.upper"),
      actual: t("research.methods.actual"),
    }),
    [t]
  );
  const band = useMemo(
    () => (data?.methods?.[method] ? buildBandData(data.methods[method].series, labels) : null),
    [data, method, labels]
  );
  const running = useMemo(
    () => (data ? buildRunningData(data.methods, data.level, t("research.methods.nominalLine")) : null),
    [data, t]
  );

  const options = (yTitle) => ({
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    plugins: { legend: { position: "bottom", labels: { color: colors.axis, boxWidth: 12, font: { size: 11 } } } },
    scales: {
      x: { ticks: { color: colors.axis, maxTicksLimit: 8, font: { size: 11 } }, grid: { color: colors.grid } },
      y: {
        ticks: { color: colors.axis, font: { size: 11 } },
        title: { display: true, text: yTitle, color: colors.axis },
        grid: { color: colors.grid },
      },
    },
  });

  return (
    <section className="panel-wide" data-testid="tab-methods">
      <h3 className="panel-title">{t("research.methods.title")}</h3>
      <p className="text-sm text-muted mt-2 max-w-2xl">{t("research.methods.subtitle")}</p>

      <div className="mt-6 surface p-4 grid sm:grid-cols-2 gap-4">
        <CountrySelect id="rm-country" countries={countries} value={country} onChange={setCountry} commodity={commodity} />
        <HorizonButtons value={horizon} onChange={setHorizon} labelId="rm-horizon-label" />
      </div>

      {status.error ? (
        <ErrorBox>{t("research.methods.error")}</ErrorBox>
      ) : status.loading || !data ? (
        <p className="mt-6 text-xs text-muted" role="status">
          {t("inflation.loading")}
        </p>
      ) : (
        <>
          <p className="mt-6 text-sm" data-testid="plain-caption">
            {t("research.methods.caption")}
          </p>
          <div className="mt-3 grid sm:grid-cols-3 gap-4">
            {METHODS.map((m) => {
              const s = data.methods[m];
              const gap = (s.coverage - data.level) * 100;
              return (
                <button
                  key={m}
                  type="button"
                  className="surface p-4 text-left"
                  style={method === m ? { borderColor: METHOD_COLOR[m], borderWidth: 2 } : undefined}
                  aria-pressed={method === m}
                  data-testid={`card-${m}`}
                  onClick={() => setMethod(m)}
                >
                  <p className="label" style={{ color: METHOD_COLOR[m] }}>
                    {t(`research.method.${m}`)}
                  </p>
                  <p className="text-xl font-semibold" data-testid={`coverage-${m}`}>
                    {pct1(s.coverage)}{" "}
                    <span className="text-xs text-muted">
                      {t("research.methods.vsNominal", { nominal: Math.round(data.level * 100) })}
                    </span>
                  </p>
                  <div className="mt-2 text-xs text-muted space-y-1">
                    <div>
                      {t("research.methods.calError")}:{" "}
                      <b data-testid={`calerr-${m}`}>
                        {(s.calibration_error * 100).toFixed(1)} {t("inflation.ppUnit")}
                      </b>{" "}
                      ({gap >= 0 ? "+" : ""}
                      {gap.toFixed(1)})
                    </div>
                    <div>
                      {t("research.methods.meanWidth")}:{" "}
                      <b>
                        {s.mean_width.toFixed(2)} {t("inflation.ppUnit")}
                      </b>
                    </div>
                    <div>
                      {t("inflation.nEval")}: <b>{s.n_eval}</b>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          <div className="mt-6">
            <h4 className="panel-title">
              {t("research.methods.bandTitle", { method: t(`research.method.${method}`) })}
            </h4>
            <p className="text-xs text-faint mt-1">{t("research.methods.bandHelp")}</p>
            <div className="chart-card mt-2" style={{ height: 320 }}>
              {band && <Line data={band} options={options(t("research.methods.yAxis", { h: data.horizon }))} />}
            </div>
          </div>

          <div className="mt-6">
            <h4 className="panel-title">{t("research.methods.runningTitle")}</h4>
            <p className="text-xs text-faint mt-1">{t("research.methods.runningHelp")}</p>
            <div className="chart-card mt-2" style={{ height: 260 }}>
              {running && <Line data={running} options={options(t("research.methods.runningY"))} />}
            </div>
          </div>

          <ul className="mt-4 list-disc pl-5 text-xs text-faint space-y-1">
            <li>{t("research.methods.noteWarmup", { n: data.warmup })}</li>
            <li>{t("research.methods.noteDelay", { h: data.horizon })}</li>
            <li>{t("research.methods.noteDescriptive")}</li>
            <li>{t("research.methods.noteWidth")}</li>
          </ul>
        </>
      )}
    </section>
  );
}
