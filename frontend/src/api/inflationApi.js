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
