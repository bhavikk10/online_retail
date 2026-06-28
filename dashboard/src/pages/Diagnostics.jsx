import SectionHeader from "../components/SectionHeader.jsx";

const cards = [
  ["DBSCAN looked good but failed business usability.", "DBSCAN was not selected even when it produced attractive silhouette values because the result was not business usable. In the earlier run, it labelled about 97.52% of customers as noise, which made the high silhouette score misleading. A segmentation system for campaigns must assign customers to actionable groups, so KMeans was preferred despite less impressive raw clustering metrics."],
  ["Two-stage CLV underperformed direct Tweedie.", "Two-stage CLV was tested as probability of purchase multiplied by expected spend if the customer buys. The idea is reasonable, but it underperformed the direct Tweedie model. The calibrated two-stage model reached only about 0.585 R2 compared with about 0.833 for final calibrated XGBoost Tweedie. Classification error compounded into spend prediction."],
  ["Tweedie was selected for fit, not perfection.", "The final calibrated XGBoost Tweedie model matched the target shape better than ordinary regression because FutureSpend90Days is non-negative, zero-heavy, and right-skewed. Its R2 of about 0.833 and revenue error near 11.27% are strong for this task, but Tweedie deviance and residual diagnostics still show difficult extreme spenders."],
  ["Most time-series models failed to beat naive.", "Most time-series models performed worse than the naive baseline, which is an important result rather than an embarrassment. The weekly revenue series has only 106 observations and contains noisy demand movement. SARIMA was selected because it performed best overall, but the forecast remains directional rather than production-grade."],
  ["Monthly forecasting was avoided.", "Monthly forecasting was avoided because only 25 monthly observations exist. A model can appear to fit such a short series, but that would overstate certainty. Monthly data is therefore used for trend visualization, while weekly data is used for the short-term forecasting experiment."],
  ["SHAP is explanation, not causality.", "SHAP explains model attribution, not causality. It can show which features pushed predictions upward or downward for a trained model, but it does not prove that changing a feature would cause a business outcome. If SHAP artifacts are unavailable, the dashboard must show a skipped state rather than fake explanations."],
  ["AvgGapDays missingness required special treatment.", "AvgGapDays required special treatment because single-purchase customers have no inter-purchase gap. Missing did not mean zero. Treating missing gap values as zero would falsely imply extremely frequent repeat behaviour. The modelling pipeline therefore needed to handle missing gap information as a behavioural signal rather than a numeric accident."],
];

export default function Diagnostics() {
  return (
    <div>
      <SectionHeader eyebrow="Diagnostics & Lessons" title="What Failed Is Part Of The Evidence">
        This page records modelling decisions that did not become final outputs. DBSCAN, two-stage CLV, monthly forecasting, SHAP availability, and feature missingness all exposed useful constraints. A credible ML project shows why final choices were made, not just what won.
      </SectionHeader>
      <div className="mb-5 grid gap-3 md:grid-cols-3">
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">What this page answers</p><p className="mt-2 text-sm leading-6 text-slate-300">Which attractive modelling paths were rejected, limited, or reframed.</p></div>
        <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">Why this matters</p><p className="mt-2 text-sm leading-6 text-slate-300">Model review is stronger when failures are evidence, not hidden clutter.</p></div>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {cards.map(([title, text], index) => (
          <div key={title} className="glass rounded-lg p-5">
            <span className="grid h-10 w-10 place-items-center rounded-md border border-amber-300/20 bg-amber-400/10 text-amber-200">{index + 1}</span>
            <h3 className="mt-4 text-lg font-semibold text-slate-100">{title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
