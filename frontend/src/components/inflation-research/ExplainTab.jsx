import React, { useState } from "react";

import { explainInflation } from "../../api/inflationApi";
import { useI18n } from "../../context/I18nContext";
import { CountrySelect, HorizonButtons, StatusChip, apiLanguage, pct1 } from "./shared";

const QUESTIONS = ["T1", "T2", "T3"];
const LANGS = ["en", "ru", "kk"];

const errorKey = (err) => {
  const code = err?.response?.status;
  if (code === 503) return "research.explain.err503";
  if (code === 429) return "research.explain.err429";
  return "research.explain.errGeneric";
};

function CheckBadge({ check }) {
  const { t } = useI18n();
  if (!check?.checked) return <span className="badge">{t("research.explain.checkNone")}</span>;
  return check.faithful ? (
    <span className="badge badge-success" data-testid="check-badge" data-faithful="true">
      {t("research.explain.checkOk", { n: check.n_claimed })}
    </span>
  ) : (
    <span className="badge badge-danger" data-testid="check-badge" data-faithful="false">
      {t("research.explain.checkBad", { bad: check.n_unmatched, n: check.n_claimed })}
    </span>
  );
}

function AnswerCard({ res, title }) {
  const { t } = useI18n();
  const f = res.reference?.forecast;
  return (
    <div className="surface p-4" data-testid={res.grounded ? "answer-grounded" : "answer-ungrounded"}>
      <div className="flex flex-wrap items-center gap-2">
        <h4 className="panel-title">{title}</h4>
        <CheckBadge check={res.check} />
        {res.check?.guarantee_wording && <span className="badge badge-warning">{t("research.explain.guarantee")}</span>}
      </div>
      <p className="text-xs text-faint mt-1">{res.question}</p>
      <p className="mt-3 text-sm whitespace-pre-wrap" data-testid="answer-text">
        {res.answer}
      </p>

      <details className="mt-3" open={res.grounded}>
        <summary className="text-xs font-semibold cursor-pointer">{t("research.explain.sawTitle")}</summary>
        {res.model_saw ? (
          <pre className="mt-2 text-[11px] overflow-x-auto surface p-2" data-testid="model-saw">
            {JSON.stringify(res.model_saw, null, 2)}
          </pre>
        ) : (
          <div className="mt-2 text-xs text-muted" data-testid="model-saw-none">
            <p>{t("research.explain.sawNone")}</p>
            {f && (
              <p className="mt-1">
                {t("research.explain.trueValues", {
                  lower: f.lower.toFixed(2),
                  upper: f.upper.toFixed(2),
                  cov: pct1(res.reference.empirical_coverage),
                })}
              </p>
            )}
          </div>
        )}
      </details>
      <p className="mt-2 text-[11px] text-faint">
        {res.model} · {res.seconds}s · {t("research.explain.checkScope")}
      </p>
    </div>
  );
}

export default function ExplainTab({ countries, commodity, benchmark }) {
  const { t, language } = useI18n();
  const [country, setCountry] = useState(countries[0]?.code || "");
  const [horizon, setHorizon] = useState(3);
  const [question, setQuestion] = useState("T1");
  const [lang, setLang] = useState(apiLanguage(language));
  const [grounded, setGrounded] = useState(true);
  const [results, setResults] = useState({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const selected = country || countries[0]?.code || "";

  const ask = async (modes) => {
    setBusy(true);
    setError(null);
    setResults({});
    try {
      for (const g of modes) {
        const res = await explainInflation({ country: selected, horizon, question_type: question, language: lang, grounded: g });
        setResults((prev) => ({ ...prev, [g ? "grounded" : "ungrounded"]: res }));
      }
    } catch (err) {
      setError(errorKey(err));
    } finally {
      setBusy(false);
    }
  };

  const llm = benchmark?.llm_eval;
  const row = (ver, cond) => llm?.[ver]?.rows?.find((r) => r.by === "condition" && r.condition === cond);
  const g1 = row("v1", "grounded");
  const g2 = row("v2", "grounded");
  const u2 = row("v2", "ungrounded");
  const shown = ["grounded", "ungrounded"].filter((k) => results[k]);

  return (
    <section className="panel-wide" data-testid="tab-explain">
      <h3 className="panel-title">{t("research.explain.title")}</h3>
      <p className="text-sm text-muted mt-2 max-w-2xl">{t("research.explain.subtitle")}</p>

      <div className="mt-6 surface p-4 grid sm:grid-cols-2 gap-4">
        <CountrySelect id="rx-country" countries={countries} value={selected} onChange={setCountry} commodity={commodity} />
        <HorizonButtons value={horizon} onChange={setHorizon} labelId="rx-horizon-label" />
        <div>
          <span className="label">{t("research.explain.question")}</span>
          <div className="flex gap-1 mt-1 flex-wrap" role="group" aria-label={t("research.explain.question")}>
            {QUESTIONS.map((q) => (
              <button key={q} type="button" className={question === q ? "tab-active" : "tab"} aria-pressed={question === q} onClick={() => setQuestion(q)}>
                {t(`research.explain.q.${q}`)}
              </button>
            ))}
          </div>
        </div>
        <div>
          <span className="label">{t("research.explain.language")}</span>
          <div className="flex gap-1 mt-1" role="group" aria-label={t("research.explain.language")}>
            {LANGS.map((l) => (
              <button key={l} type="button" className={lang === l ? "tab-active" : "tab"} aria-pressed={lang === l} onClick={() => setLang(l)}>
                {l.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
        <div className="sm:col-span-2">
          <span className="label">{t("research.explain.mode")}</span>
          <div className="flex gap-1 mt-1 flex-wrap" role="group" aria-label={t("research.explain.mode")}>
            <button type="button" className={grounded ? "tab-active" : "tab"} aria-pressed={grounded} onClick={() => setGrounded(true)}>
              {t("research.explain.grounded")}
            </button>
            <button type="button" className={!grounded ? "tab-active" : "tab"} aria-pressed={!grounded} onClick={() => setGrounded(false)}>
              {t("research.explain.ungrounded")}
            </button>
          </div>
          <p className="text-xs text-faint mt-1">{grounded ? t("research.explain.groundedHelp") : t("research.explain.ungroundedHelp")}</p>
        </div>
        <div className="sm:col-span-2 flex flex-wrap gap-2">
          <button type="button" className="btn-primary" disabled={busy || !selected} onClick={() => ask([grounded])}>
            {busy ? t("research.explain.asking") : t("research.explain.ask")}
          </button>
          <button type="button" className="btn-secondary" disabled={busy || !selected} onClick={() => ask([true, false])}>
            {t("research.explain.askBoth")}
          </button>
        </div>
      </div>

      {error && (
        <div className="mt-6 surface p-4 text-sm" role="alert" data-testid="explain-error">
          {t(error)}
        </div>
      )}

      {shown.length > 0 && (
        <div className={`mt-6 grid gap-4 ${shown.length > 1 ? "lg:grid-cols-2" : ""}`}>
          {shown.map((k) => (
            <AnswerCard key={k} res={results[k]} title={t(`research.explain.${k}`)} />
          ))}
        </div>
      )}

      <div className="surface p-4 mt-6" data-testid="eval-note">
        <div className="flex flex-wrap items-center gap-2">
          <h4 className="panel-title">{t("research.explain.evalTitle")}</h4>
          <StatusChip status="post hoc" />
        </div>
        <p className="text-sm text-muted mt-2">{t("research.explain.evalBody")}</p>
        {g2 && u2 && (
          <ul className="mt-2 text-sm space-y-1" data-testid="eval-numbers">
            <li>{t("research.explain.evalGrounded", { v2: pct1(g2.faithful_rate), v1: pct1(g1?.faithful_rate), n: g2.n })}</li>
            <li>{t("research.explain.evalUngrounded", { v2: pct1(u2.faithful_rate), n: u2.n })}</li>
          </ul>
        )}
        <p className="text-xs text-faint mt-2">{t("research.explain.evalCaveat")}</p>
      </div>
    </section>
  );
}
