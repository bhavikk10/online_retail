import React, { useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from "recharts";
import CaveatCard from "../components/CaveatCard.jsx";
import DataTable from "../components/DataTable.jsx";
import LoadingState from "../components/LoadingState.jsx";
import MetricCard from "../components/MetricCard.jsx";
import SafeChartPanel from "../components/SafeChartPanel.jsx";
import SectionHeader from "../components/SectionHeader.jsx";
import { fetchCsv } from "../utils/fetchCsv.js";
import { fetchJson, useAsyncResource } from "../utils/fetchJson.js";
import { paths } from "../utils/filePaths.js";
import { num, pct } from "../utils/formatters.js";
import { aggregateDuplicateCategories, sanitizeRows } from "../utils/chartData.js";

function payloadRows(payload) {
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.rows)) return payload.rows;
  return [];
}

function numeric(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function uniqueNumeric(rows, key) {
  return [...new Set(rows.map((row) => row[key]).filter((value) => value !== undefined && value !== ""))]
    .sort((a, b) => Number(a) - Number(b));
}

function firstMetric(columns, candidates) {
  return candidates.find((candidate) => columns.includes(candidate)) || candidates[0];
}

export default function ModelLab() {
  const [selectedClassModel, setSelectedClassModel] = useState("All");
  const [classHyperparameter, setClassHyperparameter] = useState("");
  const [clvMetric, setClvMetric] = useState("RMSE");
  const [selectedLiftIndex, setSelectedLiftIndex] = useState(1);
  const [selectedK, setSelectedK] = useState(4);
  const [eps, setEps] = useState("");
  const [minSamples, setMinSamples] = useState("");
  const [forecastMetric, setForecastMetric] = useState("WAPE_%");
  const [forecastModel, setForecastModel] = useState("SARIMA");
  const [horizon, setHorizon] = useState(12);

  const { data, loading } = useAsyncResource(
    async () => ({
      classModels: await fetchJson(paths.modelLab.classificationModels),
      classTrials: await fetchJson(paths.modelLab.classificationTrials),
      clvModels: await fetchJson(paths.modelLab.clvModels),
      clvTrials: await fetchJson(paths.modelLab.clvTrials),
      kmeans: await fetchJson(paths.modelLab.kmeans),
      dbscan: await fetchJson(paths.modelLab.dbscan),
      clusterModels: await fetchJson(paths.modelLab.clusteringModels),
      forecastModels: await fetchJson(paths.modelLab.forecastModels),
      forecastResults: await fetchJson(paths.modelLab.forecastResults),
      futureForecast: await fetchCsv(paths.modelLab.futureForecast),
      lift: await fetchJson(paths.modelLab.clvLift),
    }),
    [],
    React,
  );

  const classModels = payloadRows(data?.classModels);
  const classTrials = payloadRows(data?.classTrials);
  const clvModels = payloadRows(data?.clvModels);
  const clvParams = data?.clvTrials?.finalSelectedParameters || payloadRows(data?.clvTrials)[0] || {};
  const kRows = payloadRows(data?.kmeans);
  const dbRows = payloadRows(data?.dbscan);
  const clusterModels = payloadRows(data?.clusterModels);
  const forecastModels = aggregateDuplicateCategories(payloadRows(data?.forecastModels), "Model", ["RMSE", "MAE", "WAPE_%", "sMAPE_%", "Revenue_Error_%", "R2"]);
  const forecastResults = payloadRows(data?.forecastResults);
  const futureForecast = Array.isArray(data?.futureForecast) ? data.futureForecast.slice(0, horizon) : [];
  const liftRows = payloadRows(data?.lift);

  const classMetric = "bestScore";
  const classTrialMetric = "meanScore";
  const classModelOptions = ["All", ...new Set(classTrials.map((row) => row.model).filter(Boolean))];
  const filteredClassTrials = classTrials.filter((row) => selectedClassModel === "All" || row.model === selectedClassModel);
  const classColumns = [...new Set(filteredClassTrials.flatMap((row) => Object.keys(row)))];
  const hyperparameterOptions = classColumns.filter((key) => !["model", "metric", "meanScore", "stdScore"].includes(key));
  const selectedHyperparameter = classHyperparameter || hyperparameterOptions[0] || "";
  const topClassTrials = [...filteredClassTrials].sort((a, b) => Number(b[classTrialMetric] || 0) - Number(a[classTrialMetric] || 0)).slice(0, 10);
  const classModelChartRows = sanitizeRows(classModels, [classMetric]);
  const classScatterRows = selectedHyperparameter ? sanitizeRows(filteredClassTrials.filter((row) => numeric(row[selectedHyperparameter]) !== null), [selectedHyperparameter, classTrialMetric]) : [];

  const liftOptions = liftRows.map((row) => Number(row["TopCustomer_%"] ?? row.TopPercent ?? row.Customer_Percent)).filter(Number.isFinite);
  const selectedLift = liftRows[Math.min(selectedLiftIndex, Math.max(liftRows.length - 1, 0))] || {};

  const kValues = uniqueNumeric(kRows, "K");
  const selectedKValue = kValues.includes(String(selectedK)) ? selectedK : Number(kValues[0] || 4);
  const chosenK = kRows.find((row) => Number(row.K) === Number(selectedKValue)) || kRows[0] || {};
  const kChartRows = sanitizeRows(kRows, ["K", "Silhouette_Score", "Davies_Bouldin_Score", "Calinski_Harabasz_Score"]);
  const epsValues = uniqueNumeric(dbRows, "eps");
  const activeEps = eps || epsValues[0] || "";
  const minSampleValues = uniqueNumeric(dbRows.filter((row) => String(row.eps) === String(activeEps)), "min_samples");
  const activeMinSamples = minSamples && minSampleValues.includes(minSamples) ? minSamples : minSampleValues[0] || "";
  const chosenDb = dbRows.find((row) => String(row.eps) === String(activeEps) && String(row.min_samples) === String(activeMinSamples)) || dbRows[0] || {};

  const forecastColumns = Object.keys(forecastResults[0] || {});
  const forecastModelOptions = [...new Set(forecastColumns.filter((key) => !["Date", "Week", "Actual", "Actual_Revenue"].includes(key)))];
  const activeForecastModel = forecastModelOptions.includes(forecastModel) ? forecastModel : forecastModelOptions[0] || "SARIMA";
  const activeForecastRow = forecastModels.find((row) => row.Model === activeForecastModel) || forecastModels[0] || {};
  const futureForecastKey = Object.keys(futureForecast[0] || {}).find((key) => key.toLowerCase().includes("forecast")) || Object.keys(futureForecast[0] || {})[1];

  if (loading) return <LoadingState />;

  return (
    <div>
      <SectionHeader eyebrow="Experiment Review" title="Precomputed Experiments, Not Fake Browser Retraining">
        This page reviews how model choices and tested settings affected performance. Controls are based on saved experiment artifacts rather than browser-side retraining, so unavailable trials and probability files are shown as disabled or partial states instead of simulated results.
      </SectionHeader>
      <div className="mb-5 grid gap-3 md:grid-cols-3">
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">What this page answers</p><p className="mt-2 text-sm leading-6 text-slate-300">Which tested models and settings performed best across project modules.</p></div>
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">Why this matters</p><p className="mt-2 text-sm leading-6 text-slate-300">Model selection should be auditable, not a single unexplained final score.</p></div>
      </div>

      <section className="glass rounded-lg p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h3 className="text-xl font-semibold">Retention Classification Model Explorer</h3>
            <p className="mt-2 text-sm leading-6 text-slate-400">The saved classification CV artifact contains F1-oriented grid-search scores. It does not include probability predictions, so threshold simulation is intentionally disabled.</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="text-xs uppercase tracking-[0.2em] text-slate-500">Model<select value={selectedClassModel} onChange={(event) => { setSelectedClassModel(event.target.value); setClassHyperparameter(""); }} className="mt-2 w-full rounded-md border border-slate-400/15 bg-slate-950 px-3 py-2 text-sm normal-case tracking-normal text-slate-200">{classModelOptions.map((option) => <option key={option}>{option}</option>)}</select></label>
            <label className="text-xs uppercase tracking-[0.2em] text-slate-500">Hyperparameter<select value={selectedHyperparameter} onChange={(event) => setClassHyperparameter(event.target.value)} className="mt-2 w-full rounded-md border border-slate-400/15 bg-slate-950 px-3 py-2 text-sm normal-case tracking-normal text-slate-200">{hyperparameterOptions.map((option) => <option key={option}>{option}</option>)}</select></label>
          </div>
        </div>
        <div className="mt-5 grid gap-5 xl:grid-cols-[1fr_0.9fr]">
          <SafeChartPanel data={classModelChartRows} numericFields={[classMetric]}>
            {(chartRows) => (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={chartRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
              <XAxis dataKey="model" stroke="#94A3B8" tick={{ fontSize: 11 }} />
              <YAxis stroke="#94A3B8" domain={[0, 1]} />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(148,163,184,.2)" }} />
              <Bar dataKey={classMetric} fill="#F59E0B" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
            )}
          </SafeChartPanel>
          <SafeChartPanel data={classScatterRows} numericFields={[selectedHyperparameter, classTrialMetric]}>
            {(chartRows) => (
          <ResponsiveContainer width="100%" height={320}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
              <XAxis dataKey={selectedHyperparameter} name={selectedHyperparameter} stroke="#94A3B8" />
              <YAxis dataKey={classTrialMetric} name={classTrialMetric} stroke="#94A3B8" domain={[0.6, 0.82]} />
              <ZAxis range={[80, 180]} />
              <Tooltip cursor={{ strokeDasharray: "3 3" }} contentStyle={{ background: "#111827", border: "1px solid rgba(148,163,184,.2)" }} />
              <Scatter name="Trials" data={chartRows} fill="#38BDF8" />
            </ScatterChart>
          </ResponsiveContainer>
            )}
          </SafeChartPanel>
        </div>
        <div className="mt-5 grid gap-5 xl:grid-cols-[1fr_0.75fr]">
          <DataTable title="Top classification configurations" rows={topClassTrials} recordLabel="Top saved hyperparameter configurations" />
          <CaveatCard title="Threshold simulation disabled">
            Threshold simulation requires saved prediction probabilities. They were not found in the current artifacts, so this control is disabled rather than simulated.
          </CaveatCard>
        </div>
      </section>

      <section className="mt-6 glass rounded-lg p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h3 className="text-xl font-semibold">CLV Regression Model Explorer</h3>
            <p className="mt-2 text-sm leading-6 text-slate-400">This section compares saved CLV model diagnostics and highlights why calibrated XGBoost Tweedie became the final business model.</p>
          </div>
          <label className="text-xs uppercase tracking-[0.2em] text-slate-500">Metric<select value={clvMetric} onChange={(event) => setClvMetric(event.target.value)} className="mt-2 w-full rounded-md border border-slate-400/15 bg-slate-950 px-3 py-2 text-sm normal-case tracking-normal text-slate-200">{["RMSE", "MAE", "R2", "Revenue_Error_%", "Spearman_Rank_Correlation"].map((metric) => <option key={metric}>{metric}</option>)}</select></label>
        </div>
        <div className="mt-4 grid gap-4 md:grid-cols-4">
          {clvModels.slice(0, 4).map((row) => <MetricCard key={`${row.Model}-${row.Version}`} title={`${row.Model} ${row.Version || ""}`} value={num(row[clvMetric], clvMetric === "R2" ? 3 : 1)} description={`RMSE ${num(row.RMSE)} | Revenue error ${pct(row["Revenue_Error_%"])}`} />)}
        </div>
        <div className="mt-5 grid gap-5 xl:grid-cols-2">
          <SafeChartPanel data={clvModels} numericFields={[clvMetric]}>
            {(chartRows) => (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={chartRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
              <XAxis dataKey="Version" stroke="#94A3B8" tick={{ fontSize: 11 }} />
              <YAxis stroke="#94A3B8" />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(148,163,184,.2)" }} />
              <Bar dataKey={clvMetric} fill="#F59E0B" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
            )}
          </SafeChartPanel>
          <div className="grid gap-4">
            <CaveatCard title="Why direct calibrated Tweedie won">
              Direct Tweedie models the zero-heavy, right-skewed spend distribution without compounding classifier mistakes. Calibration improves aggregate revenue alignment while keeping the model useful for ranking.
            </CaveatCard>
            <div className="glass rounded-lg p-4">
              <h4 className="font-semibold">CLV lift selector</h4>
              <input aria-label="CLV lift cutoff" type="range" min="0" max={Math.max(liftRows.length - 1, 0)} step="1" value={Math.min(selectedLiftIndex, Math.max(liftRows.length - 1, 0))} onInput={(event) => setSelectedLiftIndex(Number(event.currentTarget.value))} onChange={(event) => setSelectedLiftIndex(Number(event.currentTarget.value))} disabled={liftRows.length < 2} className="mt-4 w-full accent-amber-400 disabled:opacity-40" />
              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <MetricCard title="Top customers" value={`${num(selectedLift["TopCustomer_%"], 0)}%`} />
                <MetricCard title="Revenue capture" value={pct(selectedLift["RevenueCapture_%"])} tone="green" />
                <MetricCard title="Lift vs random" value={num(selectedLift.LiftVsRandom, 2)} />
              </div>
            </div>
          </div>
        </div>
        <DataTable title="Final selected CLV hyperparameters" rows={[clvParams]} sampleOnly={false} />
      </section>

      <section className="mt-6 glass rounded-lg p-5">
        <h3 className="text-xl font-semibold">Clustering Hyperparameter Explorer</h3>
        <div className="mt-4 grid gap-4 md:grid-cols-4">
          <label className="text-sm text-slate-300">KMeans k: {selectedKValue}<input type="range" min="0" max={Math.max(kValues.length - 1, 0)} step="1" value={Math.max(0, kValues.findIndex((value) => Number(value) === Number(selectedKValue)))} onInput={(event) => setSelectedK(Number(kValues[Number(event.currentTarget.value)]))} onChange={(event) => setSelectedK(Number(kValues[Number(event.currentTarget.value)]))} disabled={kValues.length < 2} className="mt-3 w-full accent-amber-400 disabled:opacity-40" /></label>
          <MetricCard title="Silhouette" value={num(chosenK.Silhouette_Score, 3)} />
          <MetricCard title="Davies-Bouldin" value={num(chosenK.Davies_Bouldin_Score, 3)} />
          <MetricCard title="Calinski-Harabasz" value={num(chosenK.Calinski_Harabasz_Score, 1)} />
        </div>
        <SafeChartPanel data={kChartRows} numericFields={["K", "Silhouette_Score", "Davies_Bouldin_Score", "Calinski_Harabasz_Score"]} minHeight={300}>
          {(chartRows) => (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartRows}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
            <XAxis dataKey="K" stroke="#94A3B8" />
            <YAxis stroke="#94A3B8" />
            <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(148,163,184,.2)" }} />
            <Line dataKey="Silhouette_Score" stroke="#F59E0B" />
            <Line dataKey="Davies_Bouldin_Score" stroke="#38BDF8" />
            <Line dataKey="Calinski_Harabasz_Score" stroke="#22C55E" />
          </LineChart>
        </ResponsiveContainer>
          )}
        </SafeChartPanel>
        <div className="mt-5 grid gap-4 md:grid-cols-5">
          <label className="text-sm text-slate-300">DBSCAN eps<select value={activeEps} onChange={(event) => { setEps(event.target.value); setMinSamples(""); }} className="mt-2 w-full rounded-md border border-slate-400/15 bg-slate-950 px-3 py-2">{epsValues.map((value) => <option key={value}>{value}</option>)}</select></label>
          <label className="text-sm text-slate-300">min_samples<select value={activeMinSamples} onChange={(event) => setMinSamples(event.target.value)} className="mt-2 w-full rounded-md border border-slate-400/15 bg-slate-950 px-3 py-2">{minSampleValues.map((value) => <option key={value}>{value}</option>)}</select></label>
          <MetricCard title="Noise percentage" value={pct(chosenDb["Noise_%"])} tone="red" />
          <MetricCard title="Clusters" value={num(chosenDb.Clusters, 0)} />
          <MetricCard title="Silhouette" value={num(chosenDb.Silhouette_Score, 3)} />
        </div>
        <div className="mt-5 grid gap-5 xl:grid-cols-[1fr_0.75fr]">
          <DataTable title="Clustering model comparison" rows={clusterModels} sampleOnly={false} maxHeight="18rem" />
          <CaveatCard title="Why KMeans k = 4">
            k = 2 had stronger raw silhouette, but k = 4 created actionable groups. DBSCAN's best-looking scores often came with very high noise, which is a business-usability failure.
          </CaveatCard>
        </div>
      </section>

      <section className="mt-6 glass rounded-lg p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h3 className="text-xl font-semibold">Time-Series Forecasting Model Explorer</h3>
            <p className="mt-2 text-sm leading-6 text-slate-400">The saved comparison shows SARIMA winning week-by-week accuracy, while XGBoost lag is competitive on aggregate revenue error.</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="text-xs uppercase tracking-[0.2em] text-slate-500">Model<select value={activeForecastModel} onChange={(event) => setForecastModel(event.target.value)} className="mt-2 w-full rounded-md border border-slate-400/15 bg-slate-950 px-3 py-2 text-sm normal-case tracking-normal text-slate-200">{forecastModelOptions.map((option) => <option key={option}>{option}</option>)}</select></label>
            <label className="text-xs uppercase tracking-[0.2em] text-slate-500">Metric<select value={forecastMetric} onChange={(event) => setForecastMetric(event.target.value)} className="mt-2 w-full rounded-md border border-slate-400/15 bg-slate-950 px-3 py-2 text-sm normal-case tracking-normal text-slate-200">{["RMSE", "MAE", "WAPE_%", "sMAPE_%", "Revenue_Error_%", "R2"].map((metric) => <option key={metric}>{metric}</option>)}</select></label>
          </div>
        </div>
        <div className="mt-4 grid gap-4 md:grid-cols-4">
          <MetricCard title="Selected model" value={activeForecastModel} />
          <MetricCard title={forecastMetric} value={forecastMetric.includes("%") ? pct(activeForecastRow[forecastMetric]) : num(activeForecastRow[forecastMetric])} />
          <MetricCard title="Revenue error" value={pct(activeForecastRow["Revenue_Error_%"])} />
          <MetricCard title="Test horizon" value={`${forecastResults.length} weeks`} />
        </div>
        <div className="mt-5 grid gap-5 xl:grid-cols-2">
          <SafeChartPanel data={forecastModels} numericFields={[forecastMetric]}>
            {(chartRows) => (
          <ResponsiveContainer width="100%" height={330}>
            <BarChart data={chartRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
              <XAxis dataKey="Model" stroke="#94A3B8" tick={{ fontSize: 10 }} />
              <YAxis stroke="#94A3B8" />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(148,163,184,.2)" }} />
              <Bar dataKey={forecastMetric} fill="#F59E0B" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
            )}
          </SafeChartPanel>
          <SafeChartPanel data={forecastResults} numericFields={["Actual", activeForecastModel]}>
            {(chartRows) => (
          <ResponsiveContainer width="100%" height={330}>
            <LineChart data={chartRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
              <XAxis dataKey="Date" stroke="#94A3B8" tick={{ fontSize: 10 }} />
              <YAxis stroke="#94A3B8" />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(148,163,184,.2)" }} />
              <Line dataKey="Actual" stroke="#38BDF8" strokeWidth={2} dot={false} />
              <Line dataKey={activeForecastModel} stroke="#F59E0B" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
            )}
          </SafeChartPanel>
        </div>
        <div className="mt-5 grid gap-5 xl:grid-cols-[1fr_0.75fr]">
          <div className="glass rounded-lg p-4">
            <h4 className="font-semibold">Future forecast horizon: {horizon} weeks</h4>
            <input aria-label="Model Lab forecast horizon" type="range" min="1" max="12" value={horizon} onInput={(event) => setHorizon(Number(event.currentTarget.value))} onChange={(event) => setHorizon(Number(event.currentTarget.value))} className="mt-4 w-full accent-amber-400" />
            <SafeChartPanel data={futureForecast} numericFields={[futureForecastKey]} minHeight={250}>
              {(chartRows) => (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={chartRows}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
                <XAxis dataKey={Object.keys(futureForecast[0] || {})[0]} stroke="#94A3B8" tick={{ fontSize: 10 }} />
                <YAxis stroke="#94A3B8" />
                <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(148,163,184,.2)" }} />
                <Line dataKey={futureForecastKey} stroke="#22C55E" strokeWidth={3} />
              </LineChart>
            </ResponsiveContainer>
              )}
            </SafeChartPanel>
          </div>
          <CaveatCard title="Naive is not a strawman">
            Most time-series models performing worse than naive is a real finding. With only 106 weekly observations, the module is useful for exploratory short-term direction, not production certainty.
          </CaveatCard>
        </div>
      </section>
    </div>
  );
}
