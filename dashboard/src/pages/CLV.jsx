import React, { useMemo, useState } from "react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";
import CaveatCard from "../components/CaveatCard.jsx";
import DataTable from "../components/DataTable.jsx";
import EvidenceNote from "../components/EvidenceNote.jsx";
import LoadingState from "../components/LoadingState.jsx";
import MetricCard from "../components/MetricCard.jsx";
import PlotCard from "../components/PlotCard.jsx";
import Plotly3DScatter from "../components/Plotly3DScatter.jsx";
import SafeChartPanel from "../components/SafeChartPanel.jsx";
import SectionHeader from "../components/SectionHeader.jsx";
import { fetchCsv } from "../utils/fetchCsv.js";
import { fetchJson, useAsyncResource } from "../utils/fetchJson.js";
import { paths } from "../utils/filePaths.js";
import { money, num, pct, pick } from "../utils/formatters.js";
import { sanitizeRows } from "../utils/chartData.js";

export default function CLV() {
  const [topPct, setTopPct] = useState(10);
  const { data, loading } = useAsyncResource(
    async () => ({
      summary: await fetchJson(paths.masterSummary),
      lift: await fetchCsv(paths.data.clvLift),
      models: await fetchCsv(paths.data.clvModels),
      calibration: await fetchCsv(paths.data.clvCalibration),
      errors: await fetchCsv(paths.data.clvErrorDecile),
      clusters: await fetchCsv(paths.data.clusters),
    }),
    [],
    React,
  );
  const liftRows = Array.isArray(data?.lift) ? data.lift : [];
  const liftXKey = Object.keys(liftRows[0] || {})[0];
  const liftYKey = Object.keys(liftRows[0] || {}).find((key) => key.toLowerCase().includes("capture")) || Object.keys(liftRows[0] || {})[1];
  const liftChartRows = sanitizeRows(liftRows, [liftYKey]);
  const selectedLift = useMemo(() => liftRows.find((row) => Number(pick(row, ["Top_%", "TopPercent", "top_percent", "Customer_Percent"])) === topPct) || liftRows[Math.max(0, Math.round((topPct / 100) * liftRows.length) - 1)] || {}, [liftRows, topPct]);
  if (loading) return <LoadingState />;
  const clv = data.summary?.modules?.clvPrediction || {};
  return (
    <div>
      <SectionHeader eyebrow="Customer Lifetime Value" title="The Main Business Model">
        This page evaluates the 90-day customer future-spend model. The final calibrated XGBoost Tweedie model achieved about 0.833 R2 and ranked customers effectively: the top 10% predicted customers captured around 57.10% of actual future revenue.
      </SectionHeader>
      <div className="mb-5 grid gap-3 md:grid-cols-3">
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">What this page answers</p><p className="mt-2 text-sm leading-6 text-slate-300">Which customers should receive priority when campaign budget is limited.</p></div>
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">Why this matters</p><p className="mt-2 text-sm leading-6 text-slate-300">CLV separates small returners from customers likely to generate material revenue.</p></div>
      </div>
      <div className="grid gap-4 md:grid-cols-5">
        <MetricCard title="Final model" value="Calibrated XGBoost Tweedie" description="Handles skewed spend and many zero outcomes." />
        <MetricCard title="RMSE" value={num(clv.rmse ?? 1976.27)} description="Large-error scale." />
        <MetricCard title="MAE" value={num(clv.mae ?? 529.88)} description="Typical absolute error." />
        <MetricCard title="R²" value={num(clv.r2 ?? 0.833, 3)} description="Customer-level explained variance." tone="green" />
        <MetricCard title="Revenue error" value={pct(clv.revenueErrorPercent ?? 11.27)} description="Aggregate prediction gap." />
      </div>
      <div className="mt-6 grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="glass rounded-lg p-4">
          <h3 className="font-semibold">Revenue capture by top predicted CLV customers</h3>
          <SafeChartPanel data={liftChartRows} numericFields={[liftYKey]} minHeight={420}>
            {(chartRows) => (
          <ResponsiveContainer width="100%" height={420}>
            <LineChart data={chartRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
              <XAxis dataKey={liftXKey} stroke="#94A3B8" />
              <YAxis stroke="#94A3B8" />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(148,163,184,.2)" }} />
              <Line type="monotone" dataKey={liftYKey} stroke="#F59E0B" strokeWidth={3} dot />
            </LineChart>
          </ResponsiveContainer>
            )}
          </SafeChartPanel>
          <EvidenceNote title="Main reading">
            The lift curve is the main business result. The top 5% predicted customers captured 47.88% of future revenue, the top 10% captured 57.10%, and the top 20% captured 72.73%. This supports CLV as a ranking model for campaign prioritization, not a claim of perfect individual spend prediction.
          </EvidenceNote>
        </div>
        <div className="glass rounded-lg p-5">
          <h3 className="font-semibold">Top customer percentage</h3>
          <input
            aria-label="Top customer percentage"
            className="mt-5 w-full accent-amber-400"
            type="range"
            min="5"
            max="50"
            step="5"
            value={topPct}
            onInput={(event) => setTopPct(Number(event.currentTarget.value))}
            onChange={(event) => setTopPct(Number(event.currentTarget.value))}
          />
          <MetricCard title={`Top ${topPct}% selected`} value={pct(pick(selectedLift, ["Actual_Revenue_Captured_%", "Revenue_Capture_%", "ActualRevenueCapturedPercent"], topPct === 10 ? 57.1 : ""))} description="Actual future revenue captured by selected high-priority customers." tone="green" />
          <p className="mt-4 text-sm leading-6 text-slate-400">At the 10% cutoff, the model captures about 57.10% of actual future revenue, making it highly useful for campaign prioritization even when exact rupee-level predictions are imperfect.</p>
        </div>
      </div>
      <div className="mt-6 grid gap-5 xl:grid-cols-3">
        <PlotCard title="Actual vs predicted CLV" src={paths.plots.clvActual} caption="The extreme high-spend customers remain the hardest cases." />
        <PlotCard title="Log actual vs predicted" src={paths.plots.clvLogActual} caption="Log scale makes the ordinary customer range visible." />
        <PlotCard title="Zero-spender diagnostics" src={paths.plots.zeroDistribution} caption="Some predicted revenue is assigned to actual zero-spenders." />
      </div>
      <div className="mt-6 grid gap-5 xl:grid-cols-2">
        <div className="glass rounded-lg p-4">
          <h3 className="font-semibold">Predicted decile calibration</h3>
          <SafeChartPanel data={Array.isArray(data.calibration) ? data.calibration : []} numericFields={[Object.keys(data.calibration?.[0] || {}).find((key) => key.toLowerCase().includes("actual")) || Object.keys(data.calibration?.[0] || {})[1]]} minHeight={300}>
            {(chartRows) => (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
              <XAxis dataKey={Object.keys(data.calibration?.[0] || {})[0]} stroke="#94A3B8" />
              <YAxis stroke="#94A3B8" />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(148,163,184,.2)" }} />
              <Area dataKey={Object.keys(data.calibration?.[0] || {}).find((key) => key.toLowerCase().includes("actual")) || Object.keys(data.calibration?.[0] || {})[1]} fill="#F59E0B55" stroke="#F59E0B" />
            </AreaChart>
          </ResponsiveContainer>
            )}
          </SafeChartPanel>
          <EvidenceNote title="Calibration reading">
            The decile chart compares predicted CLV groups with actual future spend. Strong separation across predicted deciles supports using the model for ranking. Calibration is still imperfect, especially near zero-spenders and extreme high-spend customers, so campaign rules should include monitoring.
          </EvidenceNote>
        </div>
        <div className="glass rounded-lg p-4">
          <h3 className="font-semibold">Error by actual CLV decile</h3>
          <SafeChartPanel data={Array.isArray(data.errors) ? data.errors : []} numericFields={[Object.keys(data.errors?.[0] || {}).find((key) => key.toLowerCase().includes("mae")) || Object.keys(data.errors?.[0] || {})[1]]} minHeight={300}>
            {(chartRows) => (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
              <XAxis dataKey={Object.keys(data.errors?.[0] || {})[0]} stroke="#94A3B8" />
              <YAxis stroke="#94A3B8" />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(148,163,184,.2)" }} />
              <Bar dataKey={Object.keys(data.errors?.[0] || {}).find((key) => key.toLowerCase().includes("mae")) || Object.keys(data.errors?.[0] || {})[1]} fill="#38BDF8" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
            )}
          </SafeChartPanel>
          <EvidenceNote title="Error reading">
            Error by actual decile shows where spend prediction is hardest. High-value customers create much larger absolute errors, which is expected in a right-skewed retail dataset. This is why lift and revenue capture are more useful business checks than RMSE alone.
          </EvidenceNote>
        </div>
      </div>
      <div className="mt-6">
        <Plotly3DScatter
          title="3D CLV relationship"
          rows={Array.isArray(data.clusters) ? data.clusters : []}
          xKeys={["Recency"]}
          yKeys={["Frequency"]}
          zKeys={["FutureSpend90Days", "PredictedCLV", "Monetary"]}
          colorKeys={["KMeans_SegmentName", "RetentionLabel"]}
          sizeKeys={["Monetary", "FutureSpend90Days"]}
          hoverKeys={["Customer_ID", "KMeans_SegmentName", "Recency", "Frequency", "Monetary", "FutureSpend90Days"]}
        />
      </div>
      <div className="mt-6 grid gap-5 xl:grid-cols-2">
        <DataTable title="CLV model comparison" rows={Array.isArray(data.models) ? data.models : []} sampleOnly={false} />
        <CaveatCard title="Known CLV weakness">
          The model underpredicts extreme whale customers and assigns some predicted revenue to actual zero-spenders. That weakness is visible, not hidden, and is why the project emphasizes ranking, lift, and campaign allocation rather than pretending exact individual spend is solved.
        </CaveatCard>
      </div>
    </div>
  );
}
