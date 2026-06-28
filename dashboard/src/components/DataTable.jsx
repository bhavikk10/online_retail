import { Download, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { num } from "../utils/formatters.js";

function isPublicSource(source = "") {
  return ["final_outputs/", "raw_outputs/", "generated/", "assets/"].some((prefix) => source.startsWith(prefix));
}

export default function DataTable({
  title,
  rows = [],
  columns,
  source,
  description,
  importantColumns = [],
  sampleOnly = true,
  recordLabel = "Representative records",
  totalRows,
  searchable,
  maxHeight = "28rem",
}) {
  const [query, setQuery] = useState("");
  const [column, setColumn] = useState("all");
  const cols = columns?.length ? columns : [...new Set(rows.flatMap((row) => Object.keys(row || {})))];
  const canSearch = (searchable ?? rows.length >= 8) && rows.length > 0 && cols.length > 0;

  useEffect(() => {
    setQuery("");
    setColumn("all");
  }, [title]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((row) => {
      const keys = column === "all" ? cols : [column];
      return keys.some((key) => String(row[key] ?? "").toLowerCase().includes(q));
    });
  }, [rows, query, column, cols]);
  const rowSummary = query.trim()
    ? `${filtered.length} matching records from ${rows.length} displayed`
    : Number(totalRows) > rows.length
      ? `${rows.length} displayed records from ${num(totalRows, 0)} source rows`
      : `${rows.length} displayed records`;

  return (
    <div className="glass rounded-lg">
      <div className="border-b border-slate-400/10 p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h3 className="font-semibold text-slate-100">{title}</h3>
            {description ? <p className="mt-1 text-sm leading-6 text-slate-400">{description}</p> : null}
            <p className="mt-1 text-xs text-slate-500">{rowSummary}</p>
            {sampleOnly ? <p className="mt-2 inline-flex rounded-md border border-amber-300/25 bg-amber-400/10 px-2 py-1 text-xs font-medium text-amber-200">{recordLabel}</p> : null}
            {importantColumns.length ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {importantColumns.map((item) => (
                  <span key={item} className="rounded-md border border-slate-400/15 bg-slate-950/40 px-2.5 py-1 text-xs text-slate-400">
                    {item}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
          <div className="flex flex-wrap gap-2">
            {canSearch ? (
              <>
                <label className="flex items-center gap-2 rounded-md border border-slate-400/15 bg-slate-950/40 px-3 py-2 text-sm text-slate-300">
                  <Search size={15} />
                  <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={`Search ${title.toLowerCase()}`} className="w-48 bg-transparent outline-none" />
                </label>
                <select aria-label={`Search column for ${title}`} value={column} onChange={(event) => setColumn(event.target.value)} className="max-w-56 rounded-md border border-slate-400/15 bg-slate-950/70 px-3 py-2 text-sm">
                  <option value="all">All columns</option>
                  {cols.map((col) => <option key={col} value={col}>{col}</option>)}
                </select>
              </>
            ) : null}
            {source && isPublicSource(source) ? (
              <a href={`/${source}`} className="inline-flex items-center gap-2 rounded-md border border-amber-300/25 bg-amber-400/10 px-3 py-2 text-sm text-amber-100">
                <Download size={15} />
                Source
              </a>
            ) : null}
          </div>
        </div>
      </div>
      <div className="overflow-auto" style={{ maxHeight }}>
        {filtered.length ? (
          <table className="min-w-full border-separate border-spacing-0 text-left text-sm">
            <thead className="sticky top-0 z-10 bg-slate-950">
              <tr>
                {cols.map((col) => (
                  <th key={col} className="whitespace-nowrap border-b border-slate-400/10 px-4 py-3 font-medium text-slate-300">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((row, index) => (
                <tr key={index} className="odd:bg-slate-900/30">
                  {cols.map((col) => {
                    const value = row[col];
                    const formatted = typeof value === "number" ? num(value) : String(value ?? "");
                    return <td key={col} className="whitespace-nowrap border-b border-slate-400/5 px-4 py-3 text-slate-300">{formatted}</td>;
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-6 text-sm leading-6 text-slate-400">
            {rows.length
              ? "No displayed records match the current search."
              : "No records are available for this table. If this is an optional artifact, the dashboard keeps the missing state visible rather than inventing records."}
          </div>
        )}
      </div>
      {source && !isPublicSource(source) ? (
        <div className="border-t border-slate-400/10 px-4 py-3 text-xs leading-5 text-slate-500">
          Source file recorded in generated metadata. It is not linked here because it is not copied to the public dashboard bundle.
        </div>
      ) : null}
    </div>
  );
}
