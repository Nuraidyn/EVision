import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { fetchInflationBenchmark, listInflationCountries } from "../api/inflationApi";
import ExplainTab from "../components/inflation-research/ExplainTab";
import FindingsTab from "../components/inflation-research/FindingsTab";
import MethodsComparedTab from "../components/inflation-research/MethodsComparedTab";
import { Disclaimer, ErrorBox, isCanceled } from "../components/inflation-research/shared";
import { useI18n } from "../context/I18nContext";
import InflationIntervalsPage from "./InflationIntervalsPage";

const TABS = ["forecast", "methods", "findings", "explain"];

export default function InflationResearchPage() {
  const { t } = useI18n();
  const [tab, setTab] = useState("methods");
  const [countries, setCountries] = useState([]);
  const [benchmark, setBenchmark] = useState(null);
  const [benchmarkError, setBenchmarkError] = useState(false);

  useEffect(() => {
    const ctrl = new AbortController();
    listInflationCountries(ctrl.signal)
      .then((rows) => setCountries(Array.isArray(rows) ? rows : []))
      .catch((err) => {
        if (!isCanceled(err)) setCountries([]);
      });
    fetchInflationBenchmark(ctrl.signal)
      .then((b) => setBenchmark(b))
      .catch((err) => {
        if (!isCanceled(err)) setBenchmarkError(true);
      });
    return () => ctrl.abort();
  }, []);

  /* country code -> UNCTAD record, used for the badge on every country selector */
  const commodity = useMemo(
    () => Object.fromEntries((benchmark?.commodity?.countries || []).map((c) => [c.code, c])),
    [benchmark]
  );

  return (
    <div data-testid="inflation-research-page">
      <div className="px-1">
        <p className="hero-kicker">{t("research.kicker")}</p>
        <h2 className="panel-title text-2xl">{t("research.title")}</h2>
        <p className="text-sm text-muted mt-2 max-w-3xl">{t("research.subtitle")}</p>
      </div>

      <Disclaimer />

      <div className="mt-6 flex gap-1 flex-wrap" role="tablist" aria-label={t("research.title")}>
        {TABS.map((k) => (
          <button
            key={k}
            type="button"
            role="tab"
            id={`rtab-${k}`}
            aria-selected={tab === k}
            className={tab === k ? "tab-active" : "tab"}
            onClick={() => setTab(k)}
          >
            {t(`research.tab.${k}`)}
          </button>
        ))}
      </div>

      <div className="mt-4" role="tabpanel" aria-labelledby={`rtab-${tab}`}>
        {tab === "forecast" && <InflationIntervalsPage />}
        {tab === "methods" && <MethodsComparedTab countries={countries} commodity={commodity} />}
        {tab === "findings" &&
          (benchmark ? (
            <FindingsTab benchmark={benchmark} />
          ) : benchmarkError ? (
            <ErrorBox>{t("research.benchmarkError")}</ErrorBox>
          ) : (
            <p className="text-xs text-muted" role="status">
              {t("inflation.loading")}
            </p>
          ))}
        {tab === "explain" && countries.length > 0 && (
          <ExplainTab countries={countries} commodity={commodity} benchmark={benchmark} />
        )}
      </div>

      <p className="mt-6 text-xs text-faint">
        <Link to="/inflation-intervals" className="underline">
          {t("research.linkForecastPage")}
        </Link>
      </p>
    </div>
  );
}
