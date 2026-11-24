import React, { useMemo, useState } from "react";
import { Bar } from "react-chartjs-2";
import { Chart as ChartJS } from "chart.js/auto";

import { useI18n } from "../../context/I18nContext";
import { useTheme } from "../../context/ThemeContext";
import {
  CommodityBadge,
  HORIZONS,
  METHOD_COLOR,
  METHOD_ORDER,
  StatusChip,
  VerdictChip,
  signed,
  useChartColors,
} from "./shared";

ChartJS;

const MODELS = ["lgbm", "arima", "naive_b", "chronos"];
const PANELS = ["expl", "hold1", "hold2"];
const num = (v, d = 1) => (typeof v === "number" ? v.toFixed(d) : "—");

export const buildCeData = (rows, panel, model, methodLabel) => {
  const sel = rows.filter((r) => r.panel === panel && r.base_model === model);
  const methods = METHOD_ORDER.filter((m) => sel.some((r) => r.method === m));
  return {
    labels: HORIZONS.map(String),
    datasets: methods.map((m) => ({
      label: methodLabel(m),
      data: HORIZONS.map((h) => sel.find((r) => r.method === m && r.h === h)?.ce_pp ?? null),
      backgroundColor: METHOD_COLOR[m],
      borderRadius: 3,
    })),
  };
};

function Section({ title, status, children, id }) {
  return (
    <div className="surface p-4 mt-6" data-testid={id}>
      <div className="flex flex-wrap items-center gap-2">
        <h4 className="panel-title">{title}</h4>
        {status && <StatusChip status={status} />}
      </div>
      {children}
    </div>
  );
}

function Segmented({ options, value, onChange, labelOf, name }) {
  return (
    <div className="flex gap-1 flex-wrap" role="group" aria-label={name}>
      {options.map((o) => (
        <button key={o} type="button" className={value === o ? "tab-active" : "tab"} aria-pressed={value === o} onClick={() => onChange(o)}>
          {labelOf(o)}
        </button>
      ))}
    </div>
  );
}

export default function FindingsTab({ benchmark }) {
  const { t } = useI18n();
  const { theme } = useTheme();
  const colors = useChartColors(theme);
  const [panel, setPanel] = useState("hold1");
  const [model, setModel] = useState("lgbm");
  const [cModel, setCModel] = useState("lgbm");

  const methodLabel = (m) => t(`research.method.${m}`);
  const modelsInPanel = MODELS.filter((m) => benchmark.ce.some((r) => r.panel === panel && r.base_model === m));
  const activeModel = modelsInPanel.includes(model) ? model : modelsInPanel[0];
  const ceData = useMemo(
    () => buildCeData(benchmark.ce, panel, activeModel, (m) => t(`research.method.${m}`)),
    [benchmark, panel, activeModel, t]
  );

  const contrasts = benchmark.contrasts.filter((c) => c.base_model === cModel);
  const contrastModels = MODELS.filter((m) => benchmark.contrasts.some((c) => c.base_model === m));

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: "bottom", labels: { color: colors.axis, boxWidth: 12, font: { size: 11 } } } },
    scales: {
      x: { title: { display: true, text: t("research.findings.hAxis"), color: colors.axis }, ticks: { color: colors.axis }, grid: { color: colors.grid } },
      y: { beginAtZero: true, title: { display: true, text: t("research.findings.ceAxis"), color: colors.axis }, ticks: { color: colors.axis }, grid: { color: colors.grid } },
    },
  };

  const commodity = benchmark.commodity;
  const chronos = benchmark.chronos_accuracy.rows;
  const chronosByH = HORIZONS.map((h) => {
    const rows = chronos.filter((r) => r.h === h);
    const get = (cmp) => rows.find((r) => r.comparison === cmp);
    return { h, lgbm: get("chronos - lgbm"), arima: get("chronos - arima"), naive: get("chronos - naive_b") };
  });
  const fb = benchmark.feedback_delay_h12;
  const fbMethods = ["split", "rolling", "aci", "faci", "pid", "dracp"];
  const nva = benchmark.native_vs_aci;

  return (
    <section className="panel-wide" data-testid="tab-findings">
      <h3 className="panel-title">{t("research.findings.title")}</h3>
      <p className="text-sm text-muted mt-2 max-w-2xl">{t("research.findings.subtitle")}</p>

      <ul className="mt-4 space-y-2 text-sm" data-testid="headline">
        {["h1", "h2", "h3"].map((k) => (
          <li key={k} className="surface p-3">
            {t(`research.findings.${k}`)}
          </li>
        ))}
      </ul>

      <Section id="ce-section" title={t("research.findings.ceTitle")} status={benchmark.panels[panel]?.status}>
        <p className="text-xs text-faint mt-1">{t("research.findings.ceHelp")}</p>
        <div className="mt-3 flex flex-wrap gap-4">
          <Segmented name="panel" options={PANELS} value={panel} onChange={setPanel} labelOf={(p) => benchmark.panels[p]?.label || p} />
          <Segmented name="model" options={modelsInPanel} value={activeModel} onChange={setModel} labelOf={(m) => benchmark.base_models[m] || m} />
        </div>
        <div className="chart-card mt-3" style={{ height: 300 }}>
          <Bar data={ceData} options={options} />
        </div>
        <p className="text-[11px] text-faint mt-2">{benchmark.panels[panel]?.note}</p>
      </Section>

      <Section id="contrast-section" title={t("research.findings.contrastTitle")}>
        <p className="text-xs text-faint mt-1">{t("research.findings.contrastHelp", { limit: benchmark.mde_limit_pp })}</p>
        <div className="mt-3">
          <Segmented name="contrast-model" options={contrastModels} value={cModel} onChange={setCModel} labelOf={(m) => benchmark.base_models[m] || m} />
        </div>
        <div className="overflow-x-auto mt-3">
          <table className="w-full text-xs" data-testid="contrast-table">
            <thead>
              <tr className="text-left text-faint">
                <th className="py-1 pr-3">{t("research.findings.colPanel")}</th>
                <th className="pr-3">{t("research.findings.colContrast")}</th>
                <th className="pr-3">h</th>
                <th className="pr-3">{t("research.findings.colDiff")}</th>
                <th className="pr-3">{t("research.findings.colHolm")}</th>
                <th className="pr-3">{t("research.findings.colMde")}</th>
                <th>{t("research.findings.colVerdict")}</th>
              </tr>
            </thead>
            <tbody>
              {contrasts.map((c) => (
                <tr key={`${c.run}-${c.contrast}-${c.h}`} className="border-t border-[var(--panel-border)]" data-testid="contrast-row">
                  <td className="py-1 pr-3">
                    {benchmark.panels[c.panel]?.label || c.panel} <StatusChip status={c.status} />
                  </td>
                  <td className="pr-3">{t(`research.contrast.${c.contrast}`)}</td>
                  <td className="pr-3">{c.h}</td>
                  <td className="pr-3 whitespace-nowrap">
                    {signed(c.diff_pp, 1)} [{signed(c.ci_lo_pp, 1)}, {signed(c.ci_hi_pp, 1)}]
                  </td>
                  <td className="pr-3">{c.p_holm == null ? `p=${num(c.p, 3)}*` : num(c.p_holm, 3)}</td>
                  <td className="pr-3">{c.mde_pp == null ? t("research.findings.undefined") : num(c.mde_pp, 1)}</td>
                  <td>
                    <VerdictChip verdict={c.verdict} />
                    {c.panel_dependent && (
                      <span className="ml-1 text-[11px] text-faint" data-testid="panel-dependent">
                        {t("research.findings.panelDependent")}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-[11px] text-faint mt-2">{t("research.findings.contrastFoot")}</p>
      </Section>

      <Section id="commodity-section" title={t("research.findings.commodityTitle")} status={commodity.status}>
        <p className="text-sm mt-2" data-testid="commodity-summary">
          {t("research.findings.commoditySummary", { n: commodity.n_qualifying, total: commodity.n_countries })}
        </p>
        <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-4 gap-y-1 text-xs">
          {commodity.countries.map((c) => (
            <div key={c.code} className="flex items-center justify-between gap-2">
              <span>
                {c.name} ({c.code})
              </span>
              <CommodityBadge info={c} />
            </div>
          ))}
        </div>
        <p className="text-[11px] text-faint mt-2">{t("research.findings.commodityFoot")}</p>
      </Section>

      <Section id="chronos-section" title={t("research.findings.chronosTitle")} status={benchmark.chronos_accuracy.rows[0]?.status}>
        <p className="text-xs text-faint mt-1">{t("research.findings.chronosHelp")}</p>
        <div className="overflow-x-auto mt-3">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-faint">
                <th className="py-1 pr-3">h</th>
                <th className="pr-3">{t("research.findings.relMaeChronos")}</th>
                <th className="pr-3">LightGBM</th>
                <th className="pr-3">ARIMA</th>
                <th>{t("research.findings.chronosVsLgbm")}</th>
              </tr>
            </thead>
            <tbody>
              {chronosByH.map((r) => (
                <tr key={r.h} className="border-t border-[var(--panel-border)]">
                  <td className="py-1 pr-3">{r.h}</td>
                  <td className="pr-3">{num(r.lgbm?.rel_mae_chronos, 3)}</td>
                  <td className="pr-3">{num(r.lgbm?.rel_mae_other, 3)}</td>
                  <td className="pr-3">{num(r.arima?.rel_mae_other, 3)}</td>
                  <td className="whitespace-nowrap">
                    {signed(r.lgbm?.mae_diff, 3)} [{signed(r.lgbm?.ci_lo, 3)}, {signed(r.lgbm?.ci_hi, 3)}]
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-[11px] text-faint mt-2">{t("research.findings.chronosFoot")}</p>
      </Section>

      <Section id="feedback-section" title={t("research.findings.feedbackTitle")} status={fb[0]?.status}>
        <p className="text-xs text-faint mt-1">{t("research.findings.feedbackHelp")}</p>
        <div className="overflow-x-auto mt-3">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-faint">
                <th className="py-1 pr-3">{t("research.findings.colPanel")}</th>
                <th className="pr-3">{t("research.findings.colMethod")}</th>
                <th className="pr-3">{t("research.findings.delayed")}</th>
                <th className="pr-3">{t("research.findings.instant")}</th>
                <th>{t("research.findings.colDiff")}</th>
              </tr>
            </thead>
            <tbody>
              {["expl", "hold1"].flatMap((p) =>
                fbMethods
                  .map((m) => fb.find((r) => r.panel === p && r.method === m))
                  .filter(Boolean)
                  .map((r) => (
                    <tr key={`${p}-${r.method}`} className="border-t border-[var(--panel-border)]">
                      <td className="py-1 pr-3">{benchmark.panels[p]?.label}</td>
                      <td className="pr-3">{methodLabel(r.method)}</td>
                      <td className="pr-3">{num(r.cov_delayed * 100, 1)}%</td>
                      <td className="pr-3">{num(r.cov_instant * 100, 1)}%</td>
                      <td className="whitespace-nowrap">
                        {signed(r.diff_pp, 1)} [{signed(r.ci_lo_pp, 1)}, {signed(r.ci_hi_pp, 1)}]
                      </td>
                    </tr>
                  ))
              )}
            </tbody>
          </table>
        </div>
        <p className="text-[11px] text-faint mt-2">{t("research.findings.feedbackFoot")}</p>
      </Section>

      <Section id="native-section" title={t("research.findings.nativeTitle")} status={nva.status}>
        <p className="text-xs text-faint mt-1">{t("research.findings.nativeHelp")}</p>
        <div className="overflow-x-auto mt-3">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-faint">
                <th className="py-1 pr-3">{t("research.findings.colPanel")}</th>
                <th className="pr-3">h</th>
                <th>{t("research.findings.nativeDiff")}</th>
              </tr>
            </thead>
            <tbody>
              {nva.aci_minus_native.map((r) => (
                <tr key={`${r.sample}-${r.h}`} className="border-t border-[var(--panel-border)]">
                  <td className="py-1 pr-3">{r.sample}</td>
                  <td className="pr-3">{r.h}</td>
                  <td className="whitespace-nowrap">
                    {signed(r.diff_pp, 1)} [{signed(r.ci_lo_pp, 1)}, {signed(r.ci_hi_pp, 1)}]
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <p className="mt-4 text-[11px] text-faint" data-testid="sources-note">
        {t("research.findings.sources", { n: benchmark.sources.length })}
      </p>
    </section>
  );
}
