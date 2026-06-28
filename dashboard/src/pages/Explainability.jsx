import React from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import CaveatCard from "../components/CaveatCard.jsx";
import LoadingState from "../components/LoadingState.jsx";
import MissingArtifactCard from "../components/MissingArtifactCard.jsx";
import PlotCard from "../components/PlotCard.jsx";
import SafeChartPanel from "../components/SafeChartPanel.jsx";
import SectionHeader from "../components/SectionHeader.jsx";
import { fetchCsv } from "../utils/fetchCsv.js";
import { fetchJson, useAsyncResource } from "../utils/fetchJson.js";
import { paths } from "../utils/filePaths.js";

const generatedShapPlots = [
  ["/raw_outputs/shap_plots/01_retention_shap_summary_beeswarm.png", "Retention SHAP beeswarm", "Shows how engineered customer features push return-propensity predictions higher or lower across the explained sample."],
  ["/raw_outputs/shap_plots/02_retention_shap_summary_bar.png", "Retention SHAP feature importance", "Ranks retention features by mean absolute SHAP value in the rebuilt saved-artifact model."],
  ["/raw_outputs/shap_plots/04_retention_waterfall_example.png", "Retention SHAP waterfall example", "Explains one customer-level retention prediction as feature contributions relative to the model baseline."],
  ["/raw_outputs/shap_plots/01_clv_shap_summary_beeswarm.png", "CLV SHAP beeswarm", "Shows how customer behaviour features push expected future-spend predictions higher or lower."],
  ["/raw_outputs/shap_plots/02_clv_shap_summary_bar.png", "CLV SHAP feature importance", "Ranks CLV model drivers by mean absolute SHAP value using the saved customer-level artifact."],
  ["/raw_outputs/shap_plots/04_clv_waterfall_example.png", "CLV SHAP waterfall example", "Explains one customer-level CLV prediction through positive and negative feature contributions."],
];

export default function Explainability() {
  const { data, loading } = useAsyncResource(
    async () => ({
      retention: await fetchCsv("/raw_outputs/shap_outputs/retention_shap_feature_importance.csv"),
      clv: await fetchCsv("/raw_outputs/shap_outputs/clv_shap_feature_importance.csv"),
      health: await fetchJson(paths.health),
    }),
    [],
    React,
  );
  if (loading) return <LoadingState />;
  const rows = Array.isArray(data.retention) ? data.retention.slice(0, 15) : Array.isArray(data.clv) ? data.clv.slice(0, 15) : [];
  const shapStatus = data.health?.shapStatus || {};
  const retentionStatus = shapStatus.retention || {};
  const clvStatus = shapStatus.clv || {};
  return (
    <div>
      <SectionHeader eyebrow="Explainability" title="Model Attribution Without Causality Theatre">
        This page shows model-attribution artifacts when they are available and keeps skipped SHAP runs visible when they are not. SHAP requires reusable model and test-matrix artifacts; if those files are unavailable, the dashboard reports the skipped state instead of inventing explanations.
      </SectionHeader>
      <div className="mb-5 grid gap-3 md:grid-cols-3">
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">What this page answers</p><p className="mt-2 text-sm leading-6 text-slate-300">Which features influence saved model predictions when SHAP outputs exist.</p></div>
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">Why this matters</p><p className="mt-2 text-sm leading-6 text-slate-300">Attribution helps review model behaviour before turning scores into campaigns.</p></div>
      </div>
      <div className="mb-6 grid gap-4 md:grid-cols-3">
        <CaveatCard title="SHAP status">
          Current status: {shapStatus.status || "unknown"}. The prep script records this status instead of treating missing optional explainability artifacts as a dashboard failure.
        </CaveatCard>
        <CaveatCard title="Retention SHAP">
          {retentionStatus.status === "generated" ? "Retention SHAP artifacts were generated and copied for the dashboard." : retentionStatus.reason || "Retention SHAP has not been generated yet."}
        </CaveatCard>
        <CaveatCard title="CLV SHAP">
          {clvStatus.status === "generated" ? "CLV SHAP artifacts were generated and copied for the dashboard." : clvStatus.reason || "CLV SHAP requires reusable final model artifacts and is skipped when they are absent."}
        </CaveatCard>
      </div>
      {rows.length ? (
        <div className="glass rounded-lg p-4">
          <h3 className="font-semibold">Top SHAP features</h3>
          <SafeChartPanel data={rows} numericFields={["MeanAbsSHAP"]} minHeight={340}>
            {(chartRows) => (
          <ResponsiveContainer width="100%" height={340}>
            <BarChart data={chartRows} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.15)" />
              <XAxis type="number" stroke="#94A3B8" />
              <YAxis type="category" dataKey="Feature" width={160} stroke="#94A3B8" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(148,163,184,.2)" }} />
              <Bar dataKey="MeanAbsSHAP" fill="#F59E0B" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
            )}
          </SafeChartPanel>
          <p className="mt-3 text-sm leading-6 text-slate-400">This bar chart ranks features by mean absolute SHAP value. Large values indicate strong influence inside the fitted model, not a causal intervention. If the chart is absent, reusable model artifacts were not available for this run.</p>
        </div>
      ) : (
        <CaveatCard title="SHAP artifacts skipped">
          SHAP plots were not generated in this run because reusable model/test artifacts were unavailable. The dashboard shows this explicitly rather than fabricating feature attributions. SHAP would explain which features pushed retention or CLV predictions higher or lower, but it requires the trained model and processed test matrix.
        </CaveatCard>
      )}
      {shapStatus.status === "generated" ? (
        <div className="mt-6 grid gap-5 xl:grid-cols-2">
          {generatedShapPlots.map(([src, title, caption]) => (
            <PlotCard key={src} title={title} src={src} caption={caption} />
          ))}
        </div>
      ) : null}
      <div className="mt-6 grid gap-5 xl:grid-cols-2">
        <CaveatCard title="Retention question">For retention, SHAP answers: what pushes a customer toward returning or not returning?</CaveatCard>
        <CaveatCard title="CLV question">For CLV, SHAP answers: what pushes a customer's expected future value higher or lower?</CaveatCard>
      </div>
      {rows.length ? null : (
        <div className="mt-6">
          <MissingArtifactCard
            title="SHAP plots skipped"
            expectedArtifact="Retention and CLV SHAP summary images"
            expectedPath="/raw_outputs/shap_plots/"
            sourceScript="src/shap_analysis.py"
            wouldShow="Feature attribution plots for the saved retention and CLV models, including beeswarm, bar, dependence, and waterfall views when reusable model/test artifacts exist."
            reason="SHAP plots were not generated in this run because reusable model/test artifacts were unavailable. The dashboard keeps this state visible rather than displaying fabricated explanations."
          />
        </div>
      )}
    </div>
  );
}
