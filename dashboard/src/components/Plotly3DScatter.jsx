import { useEffect, useMemo, useRef } from "react";
import { sampleRows } from "../utils/chartTransforms.js";
import { pick } from "../utils/formatters.js";

const palette = ["#F59E0B", "#38BDF8", "#22C55E", "#EF4444", "#A78BFA", "#FB7185"];

export default function Plotly3DScatter({ title, rows, xKeys, yKeys, zKeys, colorKeys, sizeKeys, hoverKeys = [], maxPoints = 3000 }) {
  const plotRef = useRef(null);
  const plotlyRef = useRef(null);
  const dataRows = sampleRows(rows || [], maxPoints);
  const xKey = xKeys.find((key) => dataRows.some((row) => row[key] !== undefined));
  const yKey = yKeys.find((key) => dataRows.some((row) => row[key] !== undefined));
  const zKey = zKeys.find((key) => dataRows.some((row) => row[key] !== undefined));
  const colorKey = colorKeys.find((key) => dataRows.some((row) => row[key] !== undefined));
  const sizeKey = sizeKeys.find((key) => dataRows.some((row) => row[key] !== undefined));
  const groups = xKey && yKey && zKey ? [...new Set(dataRows.map((row) => String(pick(row, [colorKey], "value"))))] : [];
  const traces = useMemo(() => groups.map((group, idx) => {
    const groupRows = dataRows.filter((row) => String(pick(row, [colorKey], "value")) === group);
    return {
      type: "scatter3d",
      mode: "markers",
      name: group,
      x: groupRows.map((row) => Number(row[xKey])),
      y: groupRows.map((row) => Number(row[yKey])),
      z: groupRows.map((row) => Number(row[zKey])),
      text: groupRows.map((row) => hoverKeys.map((key) => `${key}: ${row[key] ?? ""}`).join("<br>")),
      hovertemplate: "%{text}<extra></extra>",
      marker: {
        color: palette[idx % palette.length],
        size: groupRows.map((row) => Math.max(3, Math.min(14, Math.sqrt(Math.abs(Number(row[sizeKey] || 25))) / 4))),
        opacity: 0.78,
      },
    };
  }), [dataRows, groups, colorKey, xKey, yKey, zKey, sizeKey, hoverKeys]);
  useEffect(() => {
    if (!plotRef.current || !xKey || !yKey || !zKey || traces.length === 0) return;
    let cancelled = false;
    async function renderPlot() {
      const module = await import("plotly.js-dist-min");
      const Plotly = module.default || module;
      plotlyRef.current = Plotly;
      if (cancelled || !plotRef.current) return;
      Plotly.react(
        plotRef.current,
        traces,
        {
          autosize: true,
          height: 520,
          paper_bgcolor: "rgba(0,0,0,0)",
          plot_bgcolor: "rgba(0,0,0,0)",
          font: { color: "#334155" },
          margin: { l: 0, r: 0, t: 10, b: 0 },
          scene: {
            xaxis: { title: xKey, gridcolor: "rgba(100,116,139,0.2)" },
            yaxis: { title: yKey, gridcolor: "rgba(100,116,139,0.2)" },
            zaxis: { title: zKey, gridcolor: "rgba(100,116,139,0.2)" },
          },
          legend: { orientation: "h", y: -0.1 },
        },
        { displaylogo: false, responsive: true },
      );
    }
    renderPlot();
    return () => {
      cancelled = true;
      if (plotRef.current && plotlyRef.current) plotlyRef.current.purge(plotRef.current);
    };
  }, [traces, xKey, yKey, zKey]);
  if (!xKey || !yKey || !zKey || dataRows.length === 0) {
    return <div className="glass rounded-lg p-5 text-slate-400">3D chart needs usable x/y/z columns.</div>;
  }
  return (
    <div className="glass rounded-lg p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <h3 className="font-semibold text-slate-100">{title}</h3>
          <p className="text-sm text-slate-400">{dataRows.length} points sampled for browser performance. Axes: {xKey}, {yKey}, {zKey}.</p>
        </div>
      </div>
      <div ref={plotRef} className="min-h-[520px] w-full" />
    </div>
  );
}
