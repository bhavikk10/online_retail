import React from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import CaveatCard from "../components/CaveatCard.jsx";
import EvidenceNote from "../components/EvidenceNote.jsx";
import MetricCard from "../components/MetricCard.jsx";
import PlotCard from "../components/PlotCard.jsx";
import SafeChartPanel from "../components/SafeChartPanel.jsx";
import SectionHeader from "../components/SectionHeader.jsx";
import { fetchJson, useAsyncResource } from "../utils/fetchJson.js";
import { paths } from "../utils/filePaths.js";
import { num, pct } from "../utils/formatters.js";

export default function Retention() {
  const { data } = useAsyncResource(async () => fetchJson(paths.modelLab.classificationModels), [], React);
  const rows = data?.data || data?.rows || [];
  return (
    <div>
      <SectionHeader eyebrow="Retention" title="Who Comes Back In The Next 90 Days?">
        This page reviews the 90-day return classification task across 2,778 active modelling customers. RetentionLabel equals 1 when FutureSpend90Days is positive. The task is useful for return propensity, but it deliberately does not estimate how much a returning customer will spend.
      </SectionHeader>
      <div className="mb-5 grid gap-3 md:grid-cols-3">
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">What this page answers</p><p className="mt-2 text-sm leading-6 text-slate-300">Which customers are likely to buy again within the future window.</p></div>
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">Why this matters</p><p className="mt-2 text-sm leading-6 text-slate-300">Retention helps campaign timing, but it is weaker than value ranking.</p></div>
      </div>
      <div className="mb-5 rounded-lg border border-[#e5ded2] bg-white p-4">
        <p className="text-sm leading-6 text-[#4b5563]"><span className="font-semibold text-[#172033]">RetentionLabel definition:</span> 1 means a customer generated positive FutureSpend90Days in the 90-day target window; 0 means zero future spend. This is useful for return propensity, but it treats low-value and high-value returners equally.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-5">
        <MetricCard title="Modelling customers" value={num(2778)} description="Customer-level rows at cutoff." />
        <MetricCard title="Future spenders" value={num(1707)} description="Positive retention labels." tone="green" />
        <MetricCard title="Zero future spenders" value={num(1071)} description="Negative retention labels." tone="red" />
        <MetricCard title="Positive rate" value={pct(61.45)} description="Class balance matters for precision and recall." />
        <MetricCard title="Negative rate" value={pct(38.55)} description="A large non-spender group remains." />
      </div>
      <div className="mt-6 grid gap-5 xl:grid-cols-[1fr_0.8fr]">
        <SafeChartPanel title="Classification CV comparison" data={rows} numericFields={["bestScore"]}>
          {(chartRows) => (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={chartRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
              <XAxis dataKey="model" stroke="#94A3B8" tick={{ fontSize: 11 }} />
              <YAxis stroke="#94A3B8" domain={[0, 1]} />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(148,163,184,.2)" }} />
              <Bar dataKey="bestScore" fill="#F59E0B" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          )}
        </SafeChartPanel>
        <div className="glass rounded-lg p-4">
          <EvidenceNote title="How to read this">
            The comparison shows saved cross-validation scores from the classification experiments. Scores cluster tightly, so the result is not a mandate to chase tiny leaderboard differences. It mainly confirms that retention is learnable, while still leaving spend magnitude unresolved.
          </EvidenceNote>
        </div>
        <div className="glass rounded-lg p-5">
          <h3 className="font-semibold">Threshold analysis unavailable</h3>
          <p className="mt-3 text-sm text-slate-300">Threshold simulation unavailable</p>
          <p className="mt-3 text-sm leading-6 text-slate-400">Threshold simulation requires saved prediction probabilities. They were not found in the current artifacts, so this control is disabled rather than simulated.</p>
        </div>
      </div>
      <div className="mt-6 grid gap-5 xl:grid-cols-2">
        <PlotCard title="F1 / ROC AUC model visual" src="/assets/f1_rocauc_bar.png" caption="Static comparison asset from the project when available." />
        <CaveatCard>
          A customer who returns and spends 30 is not equivalent to a customer who returns and spends 10,000. That is why CLV becomes the central business task after retention.
        </CaveatCard>
      </div>
    </div>
  );
}
