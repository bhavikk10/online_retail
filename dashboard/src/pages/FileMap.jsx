import React from "react";
import DataTable from "../components/DataTable.jsx";
import LoadingState from "../components/LoadingState.jsx";
import SectionHeader from "../components/SectionHeader.jsx";
import { fetchJson, useAsyncResource } from "../utils/fetchJson.js";
import { paths } from "../utils/filePaths.js";

export default function FileMap() {
  const { data, loading } = useAsyncResource(
    async () => ({
      map: await fetchJson(paths.fileMap),
      inventory: await fetchJson(paths.inventory),
      health: await fetchJson(paths.health),
    }),
    [],
    React,
  );
  if (loading) return <LoadingState />;
  const rows = data.map?.rows || data.inventory?.files || [];
  return (
    <div>
      <SectionHeader eyebrow="Artifact Map" title="A Reviewer-Friendly Map Of The Repository">
        This page is included for reproducibility. It explains which generated CSVs, JSON files, and plots support each dashboard page, so the review remains auditable rather than becoming a static visual presentation detached from project artifacts.
      </SectionHeader>
      <div className="mb-5 grid gap-3 md:grid-cols-3">
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">What this page answers</p><p className="mt-2 text-sm leading-6 text-slate-300">Which files back each metric, chart, table, and model review page.</p></div>
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">Why this matters</p><p className="mt-2 text-sm leading-6 text-slate-300">Artifact validation keeps visible claims traceable to real outputs.</p></div>
      </div>
      <div className="mb-5 grid gap-4 md:grid-cols-3">
        <div className="glass rounded-lg p-4"><p className="text-sm text-slate-400">Asset status</p><p className="mt-1 text-2xl font-semibold text-amber-200">{data.health?.status || "unknown"}</p></div>
        <div className="glass rounded-lg p-4"><p className="text-sm text-slate-400">Missing</p><p className="mt-1 text-2xl font-semibold text-red-200">{data.health?.missingFiles?.length || 0}</p></div>
        <div className="glass rounded-lg p-4"><p className="text-sm text-slate-400">Inventory entries</p><p className="mt-1 text-2xl font-semibold text-sky-200">{rows.length}</p></div>
      </div>
      <DataTable
        title="Searchable artifact inventory"
        rows={rows}
        columns={["name", "file", "type", "purpose", "usedOnPage", "sourceScript", "status", "rows", "fileSize"]}
        description="Each row links a generated file to its human-readable purpose, where it is used in the dashboard, its source script when known, validation status, and row count or file size when available."
        importantColumns={["file", "purpose", "usedOnPage", "sourceScript", "status", "rows", "fileSize"]}
        sampleOnly={false}
        maxHeight="34rem"
      />
    </div>
  );
}
