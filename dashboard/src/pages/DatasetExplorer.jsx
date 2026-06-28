import React, { useMemo, useState } from "react";
import DataTable from "../components/DataTable.jsx";
import LoadingState from "../components/LoadingState.jsx";
import SectionHeader from "../components/SectionHeader.jsx";
import { fetchJson, useAsyncResource } from "../utils/fetchJson.js";
import { paths } from "../utils/filePaths.js";

const tabs = [
  ["original", "Original raw invoices"],
  ["cleaned", "Cleaned purchases"],
  ["retention", "Retention dataset"],
  ["clv", "CLV dataset"],
  ["clustered", "Clustered customers"],
  ["weekly", "Weekly revenue"],
  ["monthly", "Monthly revenue"],
  ["forecast", "Forecast results"],
];

const importantColumns = {
  original: ["Invoice", "StockCode", "Quantity", "InvoiceDate", "Customer_ID"],
  cleaned: ["Customer_ID", "InvoiceDate", "Quantity", "Price", "TransactionValue"],
  retention: ["RetentionLabel", "FutureSpend90Days", "Recency", "Frequency", "Monetary"],
  clv: ["FutureSpend90Days", "PredictedCLV", "Recency", "Frequency", "Monetary"],
  clustered: ["KMeans_SegmentName", "Recency", "Frequency", "Monetary", "FutureSpend90Days"],
  weekly: ["Week", "Revenue", "Transactions", "Customers"],
  monthly: ["Month", "Revenue", "Transactions", "Customers"],
  forecast: ["Actual", "SARIMA", "Naive", "XGBoost_Lag"],
};

const recordLabels = {
  original: "Representative invoice records",
  cleaned: "Preview of cleaned customer features",
  retention: "Preview of generated retention table",
  clv: "Customer-level modelling artifact",
  clustered: "Customer-level segmentation artifact",
  weekly: "Representative weekly observations",
  monthly: "Representative monthly observations",
  forecast: "Forecast evaluation preview",
};

export default function DatasetExplorer() {
  const [active, setActive] = useState("original");
  const { data, loading } = useAsyncResource(
    async () => Object.fromEntries(await Promise.all(tabs.map(async ([key]) => [key, await fetchJson(paths.tables[key])]))),
    [],
    React,
  );
  const payload = useMemo(() => data?.[active] || {}, [data, active]);
  if (loading) return <LoadingState />;
  return (
    <div>
      <SectionHeader eyebrow="Data Artifacts" title="Representative Records Across The Pipeline">
        This page shows focused record previews from the raw workbook, cleaned purchases, customer modelling tables, clustered customers, revenue series, and forecast evaluation. The goal is inspection and reproducibility without loading hundreds of thousands of transaction rows into the browser.
      </SectionHeader>
      <div className="mb-5 grid gap-3 md:grid-cols-3">
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">What this page answers</p><p className="mt-2 text-sm leading-6 text-slate-300">What records look like at each stage of the pipeline.</p></div>
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">Why this matters</p><p className="mt-2 text-sm leading-6 text-slate-300">Representative records make feature definitions auditable without overwhelming the page.</p></div>
      </div>
      <div className="mb-5 flex flex-wrap gap-2">
        {tabs.map(([key, label]) => (
          <button key={key} onClick={() => setActive(key)} className={`rounded-md border px-3 py-2 text-sm ${active === key ? "border-amber-300/30 bg-amber-400/10 text-amber-100" : "border-slate-400/15 bg-slate-900/60 text-slate-300"}`}>
            {label}
          </button>
        ))}
      </div>
      <DataTable
        title={tabs.find(([key]) => key === active)?.[1]}
        rows={payload.records || []}
        columns={payload.columns}
        source={payload.source}
        description={payload.description || payload.reason || "A focused preview of the selected project artifact. Use search to inspect feature definitions without loading the full file into the browser."}
        importantColumns={importantColumns[active] || []}
        recordLabel={recordLabels[active]}
        totalRows={payload.totalRowsAvailable}
      />
    </div>
  );
}
