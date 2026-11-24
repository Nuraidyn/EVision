import React from "react";

import { useI18n } from "../../context/I18nContext";

export const HORIZONS = [1, 3, 6, 12];

/* Colours readable on both themes. */
export const METHOD_COLOR = {
  split: "#94a3b8",
  rolling: "#fbbf24",
  aci: "#38bdf8",
  faci: "#a78bfa",
  pid: "#34d399",
  dracp: "#f87171",
  native: "#f472b6",
};
export const METHOD_ORDER = ["split", "rolling", "aci", "faci", "pid", "dracp", "native"];

/* UI language code -> API language code (the UI uses "kz", the API "kk"). */
export const apiLanguage = (uiLang) => (uiLang === "kz" ? "kk" : uiLang === "ru" ? "ru" : "en");

export const isCanceled = (err) => err?.code === "ERR_CANCELED" || err?.name === "CanceledError";

export const pct1 = (v) => (typeof v === "number" ? `${(v * 100).toFixed(1)}%` : "—");
export const signed = (v, d = 2) => (typeof v === "number" ? `${v > 0 ? "+" : ""}${v.toFixed(d)}` : "—");

export const useChartColors = (theme) => {
  const dark = theme === "dark";
  return {
    axis: dark ? "#94a3b8" : "#475569",
    grid: dark ? "rgba(148,163,184,0.12)" : "rgba(71,85,105,0.12)",
  };
};

/* Honest labelling of the evidence status: shown on every benchmark number. */
export function StatusChip({ status }) {
  const { t } = useI18n();
  const s = String(status || "");
  const key = s.startsWith("pre-specified")
    ? "research.status.pre"
    : s === "post hoc"
      ? "research.status.post"
      : s === "exploratory"
        ? "research.status.expl"
        : null;
  const cls = s === "post hoc" ? "badge badge-warning" : s === "exploratory" ? "badge badge-info" : "badge badge-accent";
  return (
    <span className={cls} data-testid="status-chip" data-status={s}>
      {key ? t(key) : s}
    </span>
  );
}

const VERDICT_CLASS = {
  shown: "badge badge-success",
  "not shown": "badge badge-info",
  inconclusive: "badge badge-warning",
  descriptive: "badge badge-accent",
  "not assessed": "badge",
};

export function VerdictChip({ verdict }) {
  const { t } = useI18n();
  const key = `research.verdict.${String(verdict).replace(" ", "_")}`;
  return (
    <span className={VERDICT_CLASS[verdict] || "badge"} data-testid="verdict-chip" data-verdict={verdict}>
      {t(key)}
    </span>
  );
}

export function CommodityBadge({ info }) {
  const { t } = useI18n();
  if (!info) return null;
  return info.qualifies_60 ? (
    <span className="badge badge-success" data-testid="commodity-badge">
      {t("research.commodity.yes", { share: info.share_2021_2023 })}
    </span>
  ) : (
    <span className="badge badge-info" data-testid="commodity-badge">
      {t("research.commodity.no", { share: info.share_2021_2023 })}
    </span>
  );
}

/* Country select with the UNCTAD commodity-dependence badge for the selected country. */
export function CountrySelect({ id, countries, value, onChange, commodity }) {
  const { t } = useI18n();
  const info = commodity?.[value];
  return (
    <div>
      <label className="label" htmlFor={id}>
        {t("inflation.country")}
      </label>
      <select
        id={id}
        className="input"
        value={value}
        disabled={countries.length === 0}
        onChange={(e) => onChange(e.target.value)}
      >
        {countries.map((c) => {
          const ci = commodity?.[c.code];
          const mark = ci ? (ci.qualifies_60 ? " ●" : " ○") : "";
          return (
            <option key={c.code} value={c.code}>
              {c.name} ({c.code}){mark}
            </option>
          );
        })}
      </select>
      {info && (
        <p className="mt-1 text-[11px]">
          <CommodityBadge info={info} />
        </p>
      )}
    </div>
  );
}

export function HorizonButtons({ value, onChange, labelId }) {
  const { t } = useI18n();
  return (
    <div>
      <span className="label" id={labelId}>
        {t("inflation.horizon")}
      </span>
      <div className="flex gap-1 mt-1 flex-wrap" role="group" aria-labelledby={labelId}>
        {HORIZONS.map((h) => (
          <button
            key={h}
            type="button"
            className={value === h ? "tab-active" : "tab"}
            aria-pressed={value === h}
            onClick={() => onChange(h)}
          >
            {t("inflation.horizonMonths", { n: h })}
          </button>
        ))}
      </div>
    </div>
  );
}

export function Disclaimer() {
  const { t } = useI18n();
  return (
    <aside className="surface p-4 mt-6 text-sm" role="note" data-testid="research-disclaimer">
      <p className="font-semibold">{t("research.disclaimer.title")}</p>
      <ul className="mt-2 list-disc pl-5 space-y-1 text-muted">
        {["a", "b", "c", "d", "e"].map((k) => (
          <li key={k}>{t(`research.disclaimer.${k}`)}</li>
        ))}
      </ul>
    </aside>
  );
}

export function ErrorBox({ children }) {
  return (
    <div className="mt-6 surface p-4 text-sm" role="alert">
      {children}
    </div>
  );
}
