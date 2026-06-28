import React, { useMemo, useState } from "react";
import DataTable from "../components/DataTable.jsx";
import EvidenceNote from "../components/EvidenceNote.jsx";
import LoadingState from "../components/LoadingState.jsx";
import MetricCard from "../components/MetricCard.jsx";
import PlotCard from "../components/PlotCard.jsx";
import Plotly3DScatter from "../components/Plotly3DScatter.jsx";
import SectionHeader from "../components/SectionHeader.jsx";
import CaveatCard from "../components/CaveatCard.jsx";
import { fetchCsv } from "../utils/fetchCsv.js";
import { fetchJson, useAsyncResource } from "../utils/fetchJson.js";
import { paths } from "../utils/filePaths.js";
import { money, num, pct } from "../utils/formatters.js";

function field(row, keys, fallback = undefined) {
  for (const key of keys) {
    if (row?.[key] !== undefined && row[key] !== null && row[key] !== "") return row[key];
  }
  return fallback;
}

function segmentRole(name = "") {
  if (name.includes("High-Value")) return "Protect";
  if (name.includes("Regular")) return "Grow";
  if (name.includes("At-Risk")) return "Reactivate";
  return "Nurture";
}

const fallbackSegments = [
  { name: "High-Value Loyalists", customers: 630, customerShare: 22.68, futureRevenueShare: 65.35, retention: 86.98, zeroSpend: 13.02, recency: 15.66, frequency: 21.7, monetary: 12542.67, futureSpend: 2592.06, recommendation: "Recommended use: protect with loyalty, service recovery, and early access." },
  { name: "Regular Mid-Value Customers", customers: 1031, customerShare: 37.11, futureRevenueShare: 18.51, retention: 62.46, zeroSpend: 37.54, recency: 45.53, frequency: 5.8, monetary: 1913.95, futureSpend: 448.7, recommendation: "Recommended use: grow with cross-sell bundles and timed reminders." },
  { name: "At-Risk Inactive Customers", customers: 697, customerShare: 25.09, futureRevenueShare: 10.65, retention: 52.22, zeroSpend: 47.78, recency: 127.04, frequency: 5.24, monetary: 1945.49, futureSpend: 381.92, recommendation: "Recommended use: reactivate selectively using CLV rank." },
  { name: "New / One-Time Customers", customers: 420, customerShare: 15.12, futureRevenueShare: 5.48, retention: 35.95, zeroSpend: 64.05, recency: 84.19, frequency: 1.07, monetary: 471.3, futureSpend: 326.2, recommendation: "Recommended use: nurture cheaply with welcome journeys." },
];

export default function Segmentation() {
  const [segment, setSegment] = useState("All");
  const [minMonetary, setMinMonetary] = useState(0);
  const [maxRecency, setMaxRecency] = useState(180);
  const { data, loading } = useAsyncResource(
    async () => ({
      cards: await fetchJson(paths.segmentCards, []),
      clusters: await fetchCsv(paths.data.clusters),
      profiles: await fetchCsv(paths.data.clusterProfiles),
    }),
    [],
    React,
  );
  const cardRows = Array.isArray(data?.cards) ? data.cards : data?.cards?.segments || [];
  const customers = Array.isArray(data?.clusters) ? data.clusters : [];
  const segments = ["All", ...new Set(customers.map((row) => row.KMeans_SegmentName).filter(Boolean))];
  const filtered = useMemo(() => customers.filter((row) => (segment === "All" || row.KMeans_SegmentName === segment) && Number(row.Monetary ?? 0) >= minMonetary && Number(row.Recency ?? 9999) <= maxRecency), [customers, segment, minMonetary, maxRecency]);
  const normalizedCards = (cardRows.length ? cardRows : fallbackSegments).map((card) => {
    const name = field(card, ["name", "segmentName", "SegmentName", "Segment", "BusinessSegment"], "Segment");
    return {
      name,
      customers: field(card, ["customers", "clusterSize", "ClusterSize", "Customer_Count", "Customers"]),
      customerShare: field(card, ["customerShare", "customerSharePercent", "CustomerShare_%", "CustomerSharePct", "CustomerShare"]),
      futureRevenueShare: field(card, ["futureRevenueShare", "futureRevenueSharePercent", "FutureRevenueShare_%", "FutureRevenueSharePct", "FutureRevenueShare"]),
      retention: field(card, ["retention", "retentionRatePercent", "RetentionRate_%", "RetentionRate", "retention_rate"]),
      zeroSpend: field(card, ["zeroSpend", "zeroFutureSpendRatePercent", "ZeroFutureSpendRate_%", "ZeroFutureSpendRate"]),
      recency: field(card, ["recency", "avgRecency", "AvgRecency", "AverageRecency"]),
      frequency: field(card, ["frequency", "avgFrequency", "AvgFrequency", "AverageFrequency"]),
      monetary: field(card, ["monetary", "avgMonetary", "AvgMonetary", "AverageMonetary"]),
      futureSpend: field(card, ["futureSpend", "avgFutureSpend90Days", "AvgFutureSpend90Days", "AvgFutureSpend", "AverageFutureSpend"]),
      insight: field(card, ["Insight", "insight"], ""),
      recommendation: field(card, ["Recommendation", "recommendation"], ""),
    };
  });
  if (loading) return <LoadingState />;
  return (
    <div>
      <SectionHeader eyebrow="Customer Segments" title="Four Segments Built For Action">
        This page translates customer behaviour into four business-readable segments. KMeans with four clusters was selected because it produced balanced, assigned, and interpretable groups. The High-Value Loyalists segment alone contributes about 65.35% of future revenue.
      </SectionHeader>
      <div className="mb-6 rounded-lg border border-[#e7cf9b] bg-[#fff7e6] p-5">
        <p className="text-xs uppercase tracking-[0.2em] text-[#744210]">Core segmentation result</p>
        <h2 className="mt-2 text-2xl font-semibold leading-9 text-[#172033]">High-Value Loyalists are 22.68% of customers but 65.35% of future revenue.</h2>
        <p className="mt-2 text-sm leading-6 text-[#4b5563]">The segment page is organized around strategic profiles first, then supporting charts and tables. The raw customer table stays lower on the page so the revenue concentration result is not buried.</p>
      </div>
      <div className="mb-5 grid gap-3 md:grid-cols-3">
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">What this page answers</p><p className="mt-2 text-sm leading-6 text-slate-300">Which customer groups differ enough to deserve different treatment.</p></div>
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">Why this matters</p><p className="mt-2 text-sm leading-6 text-slate-300">Revenue is concentrated, so one campaign rule for all customers is wasteful.</p></div>
      </div>
      <div className="grid gap-5 xl:grid-cols-2">
        {normalizedCards.map((card) => (
          <div key={card.name} className="glass rounded-lg p-5">
            <div className="flex flex-col gap-3 border-b border-slate-400/10 pb-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-amber-300">{segmentRole(card.name)}</p>
                <h3 className="mt-1 text-2xl font-semibold text-slate-100">{card.name}</h3>
              </div>
              <div className="rounded-md bg-amber-400/10 px-3 py-2 text-sm font-semibold text-amber-100">
                {pct(card.futureRevenueShare)} future revenue
              </div>
            </div>
            <p className="mt-4 text-sm leading-6 text-slate-400">
              {card.insight || `${card.name} represents ${pct(card.customerShare)} of customers and ${pct(card.futureRevenueShare)} of future revenue.`} {card.recommendation}
            </p>
            <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <MetricCard title="Customers" value={num(card.customers, 0)} description={`${pct(card.customerShare)} of modelling customers`} />
              <MetricCard title="Retention" value={pct(card.retention)} description={`${pct(card.zeroSpend)} zero future spend`} tone="green" />
              <MetricCard title="Avg recency" value={`${num(card.recency, 2)} days`} description={`Avg frequency ${num(card.frequency, 2)}`} />
              <MetricCard title="Avg value" value={money(card.futureSpend)} description={`Historical ${money(card.monetary)}`} />
            </div>
          </div>
        ))}
      </div>
      <div className="mt-6 glass rounded-lg p-4">
        <div className="grid gap-4 lg:grid-cols-3">
          <label className="text-sm text-slate-300">Segment<select value={segment} onChange={(e) => setSegment(e.target.value)} className="mt-2 w-full rounded-md border border-slate-400/15 bg-slate-950 px-3 py-2">{segments.map((item) => <option key={item}>{item}</option>)}</select></label>
          <label className="text-sm text-slate-300">Minimum monetary: {money(minMonetary)}<input type="range" min="0" max="20000" step="500" value={minMonetary} onInput={(event) => setMinMonetary(Number(event.currentTarget.value))} onChange={(event) => setMinMonetary(Number(event.currentTarget.value))} className="mt-3 w-full accent-amber-400" /></label>
          <label className="text-sm text-slate-300">Maximum recency: {maxRecency} days<input type="range" min="10" max="180" step="5" value={maxRecency} onInput={(event) => setMaxRecency(Number(event.currentTarget.value))} onChange={(event) => setMaxRecency(Number(event.currentTarget.value))} className="mt-3 w-full accent-amber-400" /></label>
        </div>
        <p className="mt-4 text-sm text-slate-400">Showing {num(filtered.length, 0)} of {num(customers.length, 0)} customer records in the 3D view.</p>
      </div>
      <div className="mt-6">
        <Plotly3DScatter title="3D customer segments" rows={filtered} xKeys={["Recency"]} yKeys={["Frequency"]} zKeys={["Monetary", "FutureSpend90Days"]} colorKeys={["KMeans_SegmentName"]} sizeKeys={["FutureSpend90Days", "Monetary"]} hoverKeys={["Customer_ID", "KMeans_SegmentName", "Recency", "Frequency", "Monetary", "FutureSpend90Days"]} />
        <EvidenceNote title="3D segment view">
          The 3D view uses customer recency, frequency, and monetary or future-spend fields to inspect how segment labels sit in behavioural space. It is sampled for browser performance, so it should support interpretation rather than replace the segment profile tables.
        </EvidenceNote>
      </div>
      <div className="mt-6 grid gap-5 xl:grid-cols-3">
        <PlotCard title="Customer share vs revenue share" src={paths.plots.clusterShare} caption="High-Value Loyalists are 22.68% of customers but about 65.35% of future revenue." />
        <PlotCard title="PCA cluster view" src={paths.plots.clusterPca} caption="PCA compresses behavioural features so the final KMeans assignment can be inspected visually." />
        <PlotCard title="Segment profile heatmap" src={paths.plots.clusterHeatmap} caption="The heatmap compares segment-level recency, frequency, monetary, retention, and future-spend profiles." />
      </div>
      <div className="mt-6 grid gap-5 xl:grid-cols-3">
        <PlotCard title="DBSCAN noise vs silhouette" src={paths.plots.dbscanNoise} caption="DBSCAN is useful diagnostically, but high noise makes it weaker for campaign assignment than KMeans." />
        <PlotCard title="Gaussian mixture PCA view" src={paths.plots.gaussianPca} caption="Gaussian mixture clustering is shown as a comparator, not the final segmentation choice." />
        <PlotCard title="Agglomerative PCA view" src={paths.plots.agglomerativePca} caption="Agglomerative clustering provides another reference point for how customer groups separate in PCA space." />
      </div>
      <EvidenceNote title="Revenue concentration">
        The segment share chart compares customer share with future revenue share across groups. High-Value Loyalists represent only 22.68% of customers but contribute about 65.35% of future revenue, confirming that retention investment should not be distributed evenly.
      </EvidenceNote>
      <EvidenceNote title="Model choice">
        KMeans with four clusters was selected because it produced fully assigned, interpretable groups. DBSCAN was useful diagnostically but less suitable for business segmentation because earlier runs labelled too many customers as noise, making the higher silhouette score misleading.
      </EvidenceNote>
      <div className="mt-6 grid gap-5 xl:grid-cols-[1fr_0.8fr]">
        <DataTable title="Cluster profiles" rows={Array.isArray(data.profiles) ? data.profiles : []} sampleOnly={false} />
        <CaveatCard title="Why k = 4">
          k = 2 can look stronger by silhouette, but k = 4 produces useful business groups: High-Value Loyalists, Regular Mid-Value Customers, At-Risk Inactive Customers, and New / One-Time Customers. Interpretability beat a small raw metric advantage.
        </CaveatCard>
      </div>
    </div>
  );
}
