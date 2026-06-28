import React, { useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import CaveatCard from "../components/CaveatCard.jsx";
import EvidenceNote from "../components/EvidenceNote.jsx";
import LoadingState from "../components/LoadingState.jsx";
import MetricCard from "../components/MetricCard.jsx";
import PlotCard from "../components/PlotCard.jsx";
import SafeChartPanel from "../components/SafeChartPanel.jsx";
import SectionHeader from "../components/SectionHeader.jsx";
import { aggregateDuplicateCategories, sanitizeRows } from "../utils/chartData.js";
import { fetchCsv } from "../utils/fetchCsv.js";
import { fetchJson, useAsyncResource } from "../utils/fetchJson.js";
import { paths } from "../utils/filePaths.js";
import { pct, num } from "../utils/formatters.js";

export default function Forecasting() {
  const [horizon, setHorizon] = useState(12);
  const [model, setModel] = useState("SARIMA");
  const { data, loading } = useAsyncResource(
    async () => ({
      summary: await fetchJson(paths.masterSummary),
      weekly: await fetchCsv(paths.data.weeklyRevenue),
      monthly: await fetchCsv(paths.data.monthlyRevenue),
      comparison: await fetchCsv(paths.data.forecastModels),
      test: await fetchCsv(paths.data.weeklyForecast),
      future: await fetchCsv(paths.data.futureForecast),
    }),
    [],
    React,
  );
  const comparison = aggregateDuplicateCategories(Array.isArray(data?.comparison) ? data.comparison : [], "Model", ["WAPE_%", "RMSE", "MAE"]);
  const test = Array.isArray(data?.test) ? data.test : [];
  const future = Array.isArray(data?.future) ? data.future.slice(0, horizon) : [];
  const modelKeys = useMemo(() => Object.keys(test[0] || {}).filter((key) => key !== "Week" && key !== "Date" && key !== "Actual_Revenue" && key !== "Actual"), [test]);
  const modelOptions = useMemo(() => [...new Set(["SARIMA", ...modelKeys])], [modelKeys]);
  const activeModel = modelOptions.includes(model) ? model : modelOptions[0] || "SARIMA";
  const actualKey = test[0]?.Actual_Revenue !== undefined ? "Actual_Revenue" : "Actual";
  const testRows = sanitizeRows(test, [actualKey, activeModel]);
  const futureKey = Object.keys(future[0] || {}).find((key) => key.toLowerCase().includes("forecast")) || Object.keys(future[0] || {})[1];
  if (loading) return <LoadingState />;
  const forecast = data.summary?.modules?.revenueForecasting || {};
  return (
    <div>
      <SectionHeader eyebrow="Revenue Forecast" title="Short-Term Weekly Direction, Not Production Certainty">
        This page shows exploratory weekly revenue forecasting from 106 weekly observations. SARIMA performed best on RMSE and WAPE, but most models failed to beat the naive baseline, so the forecast is presented as directional short-term planning, not production-grade forecasting.
      </SectionHeader>
      <div className="mb-6 rounded-lg border border-[#e7cf9b] bg-[#fff7e6] p-5">
        <p className="text-xs uppercase tracking-[0.2em] text-[#744210]">Forecasting verdict</p>
        <h2 className="mt-2 text-2xl font-semibold text-[#172033]">SARIMA beat naive, but forecasting remains exploratory.</h2>
        <p className="mt-2 text-sm leading-6 text-[#4b5563]">
          This forecast is intentionally framed as exploratory. SARIMA produced the best weekly accuracy with WAPE around 18.29%, improving on the naive baseline at 22.55%. However, only 106 weekly observations and 25 monthly observations exist, and most models failed to beat naive.
        </p>
      </div>
      <div className="mb-5 grid gap-3 md:grid-cols-3">
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">What this page answers</p><p className="mt-2 text-sm leading-6 text-slate-300">Whether weekly revenue can be forecast over a short test horizon.</p></div>
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">Why this matters</p><p className="mt-2 text-sm leading-6 text-slate-300">Directional forecasts can help planning, staffing, and campaign timing.</p></div>
      </div>
      <div className="grid gap-4 md:grid-cols-5">
        <MetricCard title="Weekly observations" value={num(forecast.weeklyObservations ?? 106)} />
        <MetricCard title="Monthly observations" value={num(forecast.monthlyObservations ?? 25)} />
        <MetricCard title="Best model" value={forecast.finalModel ?? "SARIMA"} tone="green" />
        <MetricCard title="SARIMA WAPE" value={pct(forecast.wapePercent ?? 18.29)} />
        <MetricCard title="Naive WAPE" value={pct(22.55)} description="Naive is a serious baseline here." />
      </div>
      <div className="mt-6 grid gap-5 xl:grid-cols-2">
        <div>
          <SafeChartPanel title="Forecast model comparison" data={comparison} numericFields={["WAPE_%"]} minHeight={380}>
            {(chartRows) => (
          <ResponsiveContainer width="100%" height={380}>
            <BarChart data={chartRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
              <XAxis dataKey="Model" stroke="#94A3B8" tick={{ fontSize: 10 }} />
              <YAxis stroke="#94A3B8" />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(148,163,184,.2)" }} />
              <Bar dataKey="WAPE_%" fill="#F59E0B" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
            )}
          </SafeChartPanel>
          <EvidenceNote title="Model comparison">
            SARIMA achieved the best weekly forecasting performance with WAPE around 18.29%, beating the naive baseline. However, most alternatives performed worse than naive, which signals limited time-series depth rather than a failure to search enough models.
          </EvidenceNote>
        </div>
        <div>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="font-semibold">Actual vs {activeModel} forecast</h3>
            <select aria-label="Forecast model" value={activeModel} onChange={(e) => setModel(e.target.value)} className="rounded-md border border-slate-400/15 bg-slate-950 px-3 py-2 text-sm">{modelOptions.map((key, index) => <option key={`${key}-${index}`} value={key}>{key}</option>)}</select>
          </div>
          <SafeChartPanel data={testRows} numericFields={[actualKey, activeModel]} minHeight={380}>
            {(chartRows) => (
          <ResponsiveContainer width="100%" height={380}>
            <LineChart data={chartRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
              <XAxis dataKey={Object.keys(test[0] || {})[0]} stroke="#94A3B8" tick={{ fontSize: 10 }} />
              <YAxis stroke="#94A3B8" />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(148,163,184,.2)" }} />
              <Line dataKey={actualKey} stroke="#38BDF8" strokeWidth={2} dot={false} />
              <Line dataKey={activeModel} stroke="#F59E0B" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
            )}
          </SafeChartPanel>
          <EvidenceNote title="Actual versus forecast">
            The test-horizon chart compares weekly actual revenue with the selected forecast model. SARIMA follows weekly movement better than most baselines, but the forecast still misses sharp revenue swings, so it should be used for directional planning only.
          </EvidenceNote>
        </div>
      </div>
      <div className="mt-6 grid gap-5 xl:grid-cols-2">
        <div>
          <h3 className="font-semibold">Future 12-week forecast</h3>
          <input
            aria-label="Future forecast horizon"
            type="range"
            min="1"
            max="12"
            value={horizon}
            onInput={(event) => setHorizon(Number(event.currentTarget.value))}
            onChange={(event) => setHorizon(Number(event.currentTarget.value))}
            className="my-4 w-full accent-amber-400"
          />
          <p className="mb-3 text-sm text-slate-400">Showing first {horizon} forecast weeks.</p>
          <SafeChartPanel data={future} numericFields={[futureKey]} minHeight={340}>
            {(chartRows) => (
          <ResponsiveContainer width="100%" height={340}>
            <LineChart data={chartRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
              <XAxis dataKey={Object.keys(future[0] || {})[0]} stroke="#94A3B8" tick={{ fontSize: 10 }} />
              <YAxis stroke="#94A3B8" />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(148,163,184,.2)" }} />
              <Line dataKey={futureKey} stroke="#22C55E" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
            )}
          </SafeChartPanel>
          <EvidenceNote title="Forward view">
            The future horizon slider reveals the first N weeks of the selected 12-week forecast. This is useful for short-term planning scenarios, but the uncertainty is not formally quantified here and should not be treated as a committed revenue target.
          </EvidenceNote>
        </div>
        <CaveatCard title="Forecast caveat">
          Most forecasting models performed worse than naive. That is not a footnote; it is a finding. With only 106 weekly observations and 25 monthly observations, this module is exploratory short-term directional analysis rather than production-grade revenue forecasting.
        </CaveatCard>
      </div>
      <div className="mt-6 grid gap-5 xl:grid-cols-3">
        <PlotCard title="Weekly revenue trend" src={paths.plots.weeklyTrend} />
        <PlotCard title="Best forecast plot" src={paths.plots.bestForecast} />
        <PlotCard title="Future forecast plot" src={paths.plots.futureForecast} />
      </div>
    </div>
  );
}
