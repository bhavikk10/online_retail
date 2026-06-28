import React, { useState } from "react";
import { ArrowRight } from "lucide-react";
import EvidenceCard from "../components/EvidenceCard.jsx";
import EvidenceModal from "../components/EvidenceModal.jsx";
import SectionHeader from "../components/SectionHeader.jsx";
import InsightCard from "../components/InsightCard.jsx";
import LoadingState from "../components/LoadingState.jsx";
import { fetchJson, useAsyncResource } from "../utils/fetchJson.js";
import { paths } from "../utils/filePaths.js";
import { num, pct } from "../utils/formatters.js";

const pipeline = ["Raw invoices", "Cleaning", "Customer features", "Retention", "CLV", "Segmentation", "Forecasting"];

const evidenceCards = [
  {
    label: "Data foundation",
    title: "Cleaned purchase rows",
    value: "777,575",
    short: "Valid purchase rows after cleaning.",
    area: "Data & Pipeline",
    relatedPage: "Data & Pipeline",
    tags: ["cleaned rows", "invoice filtering", "feature reliability"],
    detail: "This project starts from transaction-level Online Retail II invoice data. After cleaning and filtering, 777,575 valid purchase rows remain for analysis. This matters because returns, cancellations, fees, and non-product entries can distort customer frequency, monetary value, product variety, and future value modelling.",
  },
  {
    label: "Model table",
    title: "Modelling customers",
    value: "2,778",
    short: "Active customers used for retention and CLV modelling.",
    area: "Customer Value",
    relatedPage: "Customer Value",
    tags: ["customer features", "cutoff date", "retention labels"],
    detail: "The customer-level modelling table contains 2,778 active customers around the selected cutoff date. These rows are not raw invoices; each row summarizes behavioural features such as Recency, Frequency, Monetary value, purchase gaps, recent spend, product variety, returns, and future spend labels.",
  },
  {
    label: "Retention",
    title: "Future spender rate",
    value: "61.45%",
    short: "1,707 of 2,778 customers spent again.",
    area: "Customer Value",
    relatedPage: "Customer Value",
    tags: ["1,707 spenders", "90-day window", "classification"],
    detail: "RetentionLabel is positive when a customer generates future spend in the 90-day prediction window. In this dataset, 1,707 of 2,778 modelling customers returned with future spend, giving a positive rate of about 61.45%. Retention is useful, but it does not measure how valuable the return was.",
  },
  {
    label: "CLV model",
    title: "CLV R2",
    value: "0.833",
    short: "Final calibrated XGBoost Tweedie model.",
    area: "Customer Value",
    relatedPage: "Customer Value",
    tags: ["XGBoost Tweedie", "calibrated", "zero-heavy spend"],
    detail: "The strongest predictive model is the calibrated XGBoost Tweedie CLV model, with R2 around 0.833 on the test set. Future spend is non-negative, zero-heavy, and right-skewed, so Tweedie is a better match than ordinary regression for this customer value task.",
  },
  {
    label: "CLV lift",
    title: "Top 10% revenue capture",
    value: "57.10%",
    short: "Future revenue captured by top predicted CLV customers.",
    area: "Customer Value",
    relatedPage: "Customer Value",
    tags: ["top decile", "ranking", "campaign priority"],
    detail: "When customers are ranked by predicted CLV, the top 10% captured about 57.10% of actual future revenue. This is the strongest business result in the project: the model is useful for prioritizing campaign spend even if exact customer-level prediction remains imperfect.",
  },
  {
    label: "Segmentation",
    title: "High-value revenue share",
    value: "65.35%",
    short: "Future revenue from High-Value Loyalists.",
    area: "Customer Segments",
    relatedPage: "Customer Segments",
    tags: ["High-Value Loyalists", "22.68% customers", "86.98% retention"],
    detail: "High-Value Loyalists represent only 22.68% of customers but contribute about 65.35% of future revenue, with retention near 86.98%. This confirms strong revenue concentration and supports segment-specific treatment rather than equal campaign spend across all customers.",
  },
  {
    label: "Forecasting",
    title: "Forecast WAPE",
    value: "18.29%",
    short: "Best weekly forecasting error from SARIMA.",
    area: "Revenue Forecast",
    relatedPage: "Revenue Forecast",
    tags: ["SARIMA", "weekly forecast", "106 observations"],
    detail: "SARIMA achieved the best weekly forecasting performance with WAPE around 18.29%, improving on the naive baseline. The result is useful for directional short-term planning, but it is not production-grade forecasting because the series has only 106 weekly observations.",
  },
  {
    label: "Clustering",
    title: "DBSCAN noise warning",
    value: "97.52%",
    short: "Earlier DBSCAN run labelled almost all customers as noise.",
    area: "Customer Segments",
    relatedPage: "Customer Segments",
    tags: ["DBSCAN", "noise", "business usability"],
    detail: "DBSCAN produced an attractive silhouette score in an earlier run, but around 97.52% of customers were labelled as noise. This made the metric misleading for business segmentation. A campaign segmentation system needs assigned, interpretable groups, which is why KMeans was selected.",
  },
  {
    label: "CLV target",
    title: "Zero future spend customers",
    value: "1,071",
    short: "Customers with no future spend in the prediction window.",
    area: "Customer Value",
    relatedPage: "Customer Value",
    tags: ["zero-heavy target", "90-day window", "right skew"],
    detail: "1,071 customers had zero future spend in the 90-day prediction window. This is why CLV modelling is harder than simple regression: the target contains many zeros and a small number of very high spenders, creating a zero-heavy and right-skewed prediction problem.",
  },
  {
    label: "CLV lift",
    title: "Top 20% revenue capture",
    value: "72.73%",
    short: "Revenue captured by top 20% predicted CLV customers.",
    area: "Customer Value",
    relatedPage: "Customer Value",
    tags: ["top fifth", "campaign coverage", "revenue concentration"],
    detail: "The top 20% predicted CLV customers captured about 72.73% of actual future revenue. This gives a practical campaign planning option: if the business can afford a broader campaign than the top 10%, the model still concentrates most revenue in the top fifth.",
  },
];

export default function Overview() {
  const [selectedEvidence, setSelectedEvidence] = useState(null);
  const { data, loading } = useAsyncResource(
    async () => ({
      summary: await fetchJson(paths.masterSummary),
      health: await fetchJson(paths.health),
    }),
    [],
    React,
  );
  if (loading) return <LoadingState />;
  const clv = data.summary?.modules?.clvPrediction || {};
  const seg = data.summary?.modules?.customerSegmentation || {};
  const forecast = data.summary?.modules?.revenueForecasting || {};
  const cards = evidenceCards.map((card) => {
    if (card.title === "CLV R2") return { ...card, value: num(clv.r2 ?? 0.833, 3) };
    if (card.title === "Top 10% revenue capture") return { ...card, value: pct(clv.top10PercentRevenueCapture ?? 57.1) };
    if (card.title === "High-value revenue share") return { ...card, value: pct(seg.highValueFutureRevenueSharePercent ?? 65.35) };
    if (card.title === "Forecast WAPE") return { ...card, value: pct(forecast.wapePercent ?? 18.29) };
    return card;
  });
  const heroEvidence = [
    ["Top 10% CLV capture", pct(clv.top10PercentRevenueCapture ?? 57.1), "Highest predicted customers captured most future revenue."],
    ["High-Value revenue share", pct(seg.highValueFutureRevenueSharePercent ?? 65.35), "Loyalists concentrate the segment-level opportunity."],
    ["Final CLV R2", num(clv.r2 ?? 0.833, 3), "Calibrated XGBoost Tweedie fit on customer-level spend."],
    ["Forecast WAPE", pct(forecast.wapePercent ?? 18.29), "Useful directional signal, not production certainty."],
  ];

  return (
    <div>
      <section className="grid gap-6 rounded-lg border border-[#e5ded2] bg-white p-6 shadow-2xl shadow-slate-900/5 lg:grid-cols-[1.15fr_0.85fr] lg:p-8">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[#744210]">Online Retail II Analytics</p>
          <h1 className="mt-4 max-w-3xl text-4xl font-semibold leading-tight text-[#172033] sm:text-5xl">Customer Intelligence Lab</h1>
          <h2 className="mt-6 max-w-3xl text-2xl font-semibold leading-9 text-[#172033]">
            A small group of customers drives most future revenue, and CLV ranking identifies that group better than simple retention modelling.
          </h2>
          <p className="mt-5 max-w-3xl text-base leading-8 text-[#4b5563]">
            This case study traces 777,575 cleaned purchase rows into retention, CLV, segmentation, forecasting, SHAP, and reproducibility artifacts. The reviewer takeaway is evidence hierarchy: customer value ranking and segment concentration are strong; forecasting is useful but deliberately exploratory.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
          {heroEvidence.map(([label, value, description]) => (
            <div key={label} className="rounded-lg border border-[#e5ded2] bg-[#fffaf1] p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-[#744210]">{label}</p>
              <p className="mt-3 text-3xl font-semibold text-[#172033]">{value}</p>
              <p className="mt-2 text-sm leading-6 text-[#4b5563]">{description}</p>
            </div>
          ))}
        </div>
      </section>

      <div className="mt-5 grid gap-3 md:grid-cols-2">
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">What this page answers</p><p className="mt-2 text-sm leading-6 text-slate-300">Where the strongest customer value and forecasting evidence sits.</p></div>
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">Why this matters</p><p className="mt-2 text-sm leading-6 text-slate-300">A small share of customers drives a large share of future revenue.</p></div>
      </div>

      <section className="mt-8">
        <SectionHeader eyebrow="Major Trends" title="Evidence summary">
          Each card opens the numerical reasoning behind the result.
        </SectionHeader>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          {cards.map((card) => <EvidenceCard key={card.title} card={card} onOpen={setSelectedEvidence} />)}
        </div>
      </section>

      <EvidenceModal card={selectedEvidence} onClose={() => setSelectedEvidence(null)} />

      <div className="mt-8 grid gap-5 xl:grid-cols-[1.4fr_0.9fr]">
        <div className="glass rounded-lg p-5">
          <SectionHeader eyebrow="Architecture" title="From Invoices To Decisions">
            The dashboard follows the actual project spine: cleaning produces reliable customer features; CLV and segmentation become the strongest business modules; forecasting stays explicitly exploratory.
          </SectionHeader>
          <div className="flex flex-wrap items-center gap-2">
            {pipeline.map((stage, index) => (
              <div key={stage} className="flex animate-[fadeIn_0.35s_ease-out] items-center gap-2" style={{ animationDelay: `${index * 40}ms` }}>
                <span className="rounded-md border border-slate-400/15 bg-slate-900/70 px-3 py-2 text-sm text-slate-200">{stage}</span>
                {index < pipeline.length - 1 ? <ArrowRight size={16} className="text-amber-300" /> : null}
              </div>
            ))}
          </div>
        </div>
        <InsightCard title="Project verdict" tone="green">
          CLV and segmentation are the most actionable parts of the system. The CLV model is strongest as a prioritization model, while KMeans turns customer value patterns into campaign groups. The time-series module is useful for short-term directional planning, but the dataset has only 106 weekly observations.
        </InsightCard>
      </div>
      {data.health?.status ? (
        <div className="mt-6 rounded-lg border border-slate-400/15 bg-slate-900/70 p-4 text-sm text-slate-300">
          Asset health: <span className="font-semibold text-amber-200">{data.health.status}</span>. Missing/empty artifacts are handled as visible notes rather than silent failures.
        </div>
      ) : null}
    </div>
  );
}
