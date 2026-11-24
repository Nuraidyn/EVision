import { fastapiClient } from "./client";

export const listInflationCountries = async (signal) => {
  const res = await fastapiClient.get("/inflation/countries", { signal });
  return res.data;
};

export const fetchCalibratedForecast = async ({ country, horizon, level }, signal) => {
  const res = await fastapiClient.get("/inflation/calibrated-forecast", {
    params: { country, horizon, level },
    signal,
  });
  return res.data;
};

export const fetchInflationBenchmark = async (signal) => {
  const res = await fastapiClient.get("/inflation/benchmark", { signal });
  return res.data;
};

export const fetchInflationCompare = async ({ country, horizon, level = 0.9, warmup = 48 }, signal) => {
  const res = await fastapiClient.get("/inflation/compare", {
    params: { country, horizon, level, warmup },
    signal,
  });
  return res.data;
};

// The LLM call can take a while (reasoning model behind a proxy): longer timeout than the default.
export const explainInflation = async (body, signal) => {
  const res = await fastapiClient.post("/inflation/explain", body, { signal, timeout: 120000 });
  return res.data;
};
