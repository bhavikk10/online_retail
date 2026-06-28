import ChartErrorBoundary from "./ChartErrorBoundary.jsx";
import { sanitizeRows } from "../utils/chartData.js";

export default function SafeChartPanel({
  title,
  description,
  data,
  requiredFields = [],
  numericFields = [],
  minHeight = 320,
  children,
}) {
  const fields = requiredFields.filter(Boolean);
  const rows = sanitizeRows(data, numericFields).filter((row) =>
    fields.every((field) => row[field] !== undefined && row[field] !== null && row[field] !== ""),
  );
  return (
    <div className="glass rounded-lg p-4">
      {title ? <h3 className="font-semibold">{title}</h3> : null}
      {description ? <p className="mt-1 text-sm leading-6 text-slate-400">{description}</p> : null}
      {!rows.length ? (
        <div className="mt-4 rounded-lg border border-amber-300/20 bg-amber-400/10 p-5 text-sm leading-6 text-slate-400" style={{ minHeight }}>
          Chart data is unavailable or incomplete. The dashboard keeps this controlled empty state rather than rendering an unstable chart with missing values.
        </div>
      ) : (
        <div className="mt-3" style={{ minHeight }}>
          <ChartErrorBoundary resetKey={`${title}-${rows.length}-${numericFields.join(",")}`}>
            {typeof children === "function" ? children(rows) : children}
          </ChartErrorBoundary>
        </div>
      )}
    </div>
  );
}
