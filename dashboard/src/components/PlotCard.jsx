import { useEffect, useState } from "react";
import MissingArtifactCard from "./MissingArtifactCard.jsx";
import { plotCandidates, resolveImage } from "../utils/assetResolver.js";

function artifactContext(src = "") {
  if (src.includes("shap")) return ["SHAP attribution plot", "Feature-level attribution for saved model predictions.", "src/shap_analysis.py"];
  if (src.includes("clv")) return ["CLV diagnostic plot", "How calibrated CLV predictions compare with actual future spend or revenue capture.", "src/tweedie_clv.py"];
  if (src.includes("cluster")) return ["Segmentation plot", "How selected customer segments differ by revenue, retention, or behavioural profiles.", "src/clustering.py"];
  if (src.includes("forecast") || src.includes("weekly") || src.includes("monthly")) return ["Forecasting plot", "Weekly or monthly revenue trend, model comparison, or future forecast output.", "src/time_series.py"];
  return ["Project plot", "A generated visual from the modelling pipeline.", "scripts/prepare_frontend_assets.py"];
}

export default function PlotCard({ title, src, caption, expected }) {
  const [asset, setAsset] = useState({ status: "checking", path: null, candidates: plotCandidates(src) });
  const [expectedArtifact, wouldShow, sourceScript] = artifactContext(src);
  useEffect(() => {
    let mounted = true;
    setAsset({ status: "checking", path: null, candidates: plotCandidates(src) });
    resolveImage(plotCandidates(src)).then((result) => {
      if (mounted) setAsset(result);
    });
    return () => {
      mounted = false;
    };
  }, [src]);
  return (
    <div className="glass overflow-hidden rounded-lg">
      <div className="border-b border-slate-400/10 px-4 py-3">
        <h3 className="font-semibold text-slate-100">{title}</h3>
        {caption ? <p className="mt-1 text-sm text-slate-400">{caption}</p> : null}
      </div>
      {asset.status === "checking" ? (
        <div className="flex min-h-64 items-center justify-center p-6 text-sm text-slate-400">Checking plot artifact...</div>
      ) : asset.status === "missing" ? (
        <div className="p-4">
          <MissingArtifactCard
            title="Plot unavailable"
            expectedArtifact={expectedArtifact}
            expectedPath={src}
            sourceScript={sourceScript}
            wouldShow={expected || wouldShow}
            reason={`No candidate public path loaded. Checked ${asset.candidates.length} browser-accessible location(s), then replaced the plot with this controlled missing-artifact state.`}
          />
        </div>
      ) : (
        <img src={asset.path} alt={title} className="w-full bg-slate-950/40 object-contain" />
      )}
    </div>
  );
}
