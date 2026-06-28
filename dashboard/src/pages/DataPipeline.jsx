import { CheckCircle2 } from "lucide-react";
import CaveatCard from "../components/CaveatCard.jsx";
import SectionHeader from "../components/SectionHeader.jsx";

const stages = [
  {
    name: "Raw Excel workbook",
    script: "data/online_retail_II.xlsx",
    input: "Invoice-line retail records from December 2009 through December 2011.",
    transform: "Preserve the original workbook before applying cleaning, customer filters, target windows, or model-specific feature logic.",
    output: "Auditable source table used to verify that later metrics are derived from historical transactions.",
    reason: "The dashboard is an offline model review, so every later claim must trace back to the same historical dataset.",
  },
  {
    name: "Preprocessing",
    script: "src/preprocessing.py",
    input: "Raw invoice rows with cancellations, missing customer identifiers, operational stock codes, and line-level quantities/prices.",
    transform: "Standardize column names and dates, validate customer identifiers, calculate transaction value, and preserve flags that identify questionable rows.",
    output: "Cleaned transaction foundation used by retention, CLV, segmentation, and revenue aggregation.",
    reason: "Bad cleaning would make cancelled invoices, fees, and missing customers look like ordinary demand.",
  },
  {
    name: "Purchase filtering",
    script: "src/classf_dataset.py",
    input: "Cleaned transaction table with operational noise still present as flags.",
    transform: "Remove cancellations, returns, and non-product stock codes before modelling spend behaviour.",
    output: "Genuine purchase records for customer-level modelling.",
    reason: "Postage, bank charges, manual fees, and cancelled invoices can inflate or distort customer value if treated as ordinary product demand.",
  },
  {
    name: "Customer feature engineering",
    script: "src/classf_dataset.py / src/clv_dataset.py",
    input: "Filtered purchase rows grouped by customer and temporal windows.",
    transform: "Create Frequency, Monetary, Recency, AvgGapDays, PurchasesLast90Days, SpendLast90Days, product diversity, return behaviour, and momentum features.",
    output: "Customer modelling table describing how recently, consistently, broadly, and heavily each customer bought.",
    reason: "The modelling problem moves from invoice rows to customer behaviour; spend alone is not enough.",
  },
  {
    name: "Retention dataset",
    script: "src/classf_pipeline.py",
    input: "Customer features plus the future 90-day outcome window.",
    transform: "Create RetentionLabel as a binary indicator for whether a customer generated future spend.",
    output: "2,778-customer classification table with 1,707 future spenders and 1,071 zero future-spend customers.",
    reason: "Useful for broad return propensity, but it treats a small returner and a high-value returner equally.",
  },
  {
    name: "CLV dataset",
    script: "src/tweedie_clv.py",
    input: "The same customer feature frame with future spend retained as a continuous target.",
    transform: "Model FutureSpend90Days directly using approaches suited to zero-heavy, right-skewed spend.",
    output: "CLV diagnostics, model comparisons, lift tables, and revenue capture checks.",
    reason: "CLV is more useful than retention alone because two returning customers may differ by orders of magnitude in future value.",
  },
  {
    name: "Segmentation dataset",
    script: "src/clustering.py",
    input: "Customer behavioural features and future-value diagnostics.",
    transform: "Compare clustering approaches, then choose KMeans k=4 for complete assignment and interpretable business groups.",
    output: "Segment profiles, PCA coordinates, chart registry, and segment cards.",
    reason: "Campaign strategy needs assigned, explainable groups, not only an abstract clustering score.",
  },
  {
    name: "Time-series aggregation",
    script: "src/time_series.py",
    input: "Valid purchase revenue by transaction date.",
    transform: "Aggregate revenue into 106 weekly observations and 25 monthly observations, then compare forecast models against naive baselines.",
    output: "Weekly model comparison, future 12-week forecast, and trend plots.",
    reason: "Weekly data can support exploratory short-term forecasting; monthly data is too short for confident modelling.",
  },
  {
    name: "Final frontend artifacts",
    script: "scripts/prepare_frontend_assets.py",
    input: "Final CSV, JSON, PNG, model-lab, and SHAP status outputs.",
    transform: "Validate files, record rows/columns/sizes, copy browser-safe artifacts, and report missing optional outputs honestly.",
    output: "Public dashboard assets plus inventory and health reports.",
    reason: "The dashboard remains auditable without silently rerunning or fabricating modelling outputs.",
  },
];

export default function DataPipeline() {
  return (
    <div>
      <SectionHeader eyebrow="Pipeline" title="The Actual Project Spine">
        This page explains how raw invoice records become modelling tables. Cleaning separates genuine purchases from returns, cancellations, and non-product charges so that spend, frequency, product variety, retention labels, CLV targets, segments, and forecasts are traceable to defensible customer definitions.
      </SectionHeader>
      <div className="mb-5 grid gap-3 md:grid-cols-3">
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">What this page answers</p><p className="mt-2 text-sm leading-6 text-slate-300">Which scripts create each dataset, plot, model diagnostic, and frontend artifact.</p></div>
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">Why this matters</p><p className="mt-2 text-sm leading-6 text-slate-300">Bad cleaning would make returns, cancellations, and fees look like normal demand.</p></div>
      </div>
      <div className="grid gap-4">
        {stages.map((stage, index) => (
          <div key={stage.name} className="glass grid gap-4 rounded-lg p-5 lg:grid-cols-[4rem_0.8fr_1fr_1fr_1fr]">
            <div className="flex items-center gap-3 text-amber-200">
              <span className="grid h-10 w-10 place-items-center rounded-md border border-amber-300/20 bg-amber-400/10">{index + 1}</span>
            </div>
            <div>
              <h3 className="font-semibold text-slate-100">{stage.name}</h3>
              <p className="mt-1 text-sm text-slate-400">{stage.script}</p>
            </div>
            <div><p className="text-xs uppercase tracking-[0.18em] text-slate-500">Input</p><p className="mt-2 text-sm leading-6 text-slate-300">{stage.input}</p></div>
            <div><p className="text-xs uppercase tracking-[0.18em] text-slate-500">Transformation</p><p className="mt-2 text-sm leading-6 text-slate-300">{stage.transform}</p></div>
            <div><p className="text-xs uppercase tracking-[0.18em] text-slate-500">Output and reason</p><p className="mt-2 text-sm leading-6 text-slate-300">{stage.output} {stage.reason}</p></div>
          </div>
        ))}
      </div>
      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <CaveatCard title="Cleaning choices that matter">
          Cancellations and returns are flagged, non-product stock codes are excluded from genuine purchases, missing Customer_ID rows are removed, Quantity and Price are checked, and TransactionValue is created. Without those choices, frequency, spend, product variety, and CLV would be distorted.
        </CaveatCard>
        <div className="rounded-lg border border-emerald-300/25 bg-emerald-400/10 p-4">
          <h3 className="flex items-center gap-2 font-semibold text-emerald-100"><CheckCircle2 size={18} /> Why this matters</h3>
          <p className="mt-2 text-sm leading-6 text-slate-200">Bad cleaning would make cancelled invoices look like demand, make internal fees look like products, and inflate or deflate customer spend. The modelling pages depend on this foundation.</p>
        </div>
      </div>
    </div>
  );
}
