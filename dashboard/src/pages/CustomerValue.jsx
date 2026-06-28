import { useState } from "react";
import CLV from "./CLV.jsx";
import CLVDiagnostics from "./CLVDiagnostics.jsx";
import Explainability from "./Explainability.jsx";
import Retention from "./Retention.jsx";
import SectionHeader from "../components/SectionHeader.jsx";

const tabs = [
  ["retention", "Retention"],
  ["clv", "CLV Prediction"],
  ["diagnostics", "CLV Diagnostics"],
  ["explainability", "Explainability Status"],
];

export default function CustomerValue() {
  const [active, setActive] = useState("retention");
  return (
    <div>
      <SectionHeader eyebrow="Customer Value" title="Retention Signals And 90-Day Value Ranking">
        This section combines retention and CLV analysis. Retention predicts whether a customer returns, while CLV estimates future value. The calibrated XGBoost Tweedie model achieved about 0.833 R2 and captured 57.10% of future revenue in the top 10% predicted customers.
      </SectionHeader>
      <div className="mb-6 grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-[#e5ded2] bg-white p-5">
          <p className="text-xs uppercase tracking-[0.18em] text-[#744210]">Retention asks</p>
          <h3 className="mt-2 text-xl font-semibold text-[#172033]">Will the customer return?</h3>
          <p className="mt-2 text-sm leading-6 text-[#4b5563]">RetentionLabel is positive when FutureSpend90Days is greater than zero. It is useful for campaign timing across 2,778 customers, including 1,707 future spenders and 1,071 zero future-spend customers.</p>
        </div>
        <div className="rounded-lg border border-[#e5ded2] bg-[#fffaf1] p-5">
          <p className="text-xs uppercase tracking-[0.18em] text-[#744210]">CLV asks</p>
          <h3 className="mt-2 text-xl font-semibold text-[#172033]">How much value might the customer generate?</h3>
          <p className="mt-2 text-sm leading-6 text-[#4b5563]">CLV is the stronger business layer because retention treats a low-value returner and a high-value returner equally. The final model ranks customers so budget can focus on high expected value.</p>
        </div>
      </div>
      <div className="mb-6 flex flex-wrap gap-2">
        {tabs.map(([id, label]) => (
          <button
            key={id}
            type="button"
            onClick={() => setActive(id)}
            className={`rounded-md border px-4 py-2 text-sm transition ${
              active === id
                ? "border-amber-300/40 bg-amber-300/15 text-amber-100"
                : "border-[#e5ded2] bg-white text-[#334155] hover:border-[#c9bda9]"
            }`}
          >
            {label}
          </button>
        ))}
      </div>
      {active === "retention" ? <Retention /> : null}
      {active === "clv" ? <CLV /> : null}
      {active === "diagnostics" ? <CLVDiagnostics /> : null}
      {active === "explainability" ? <Explainability /> : null}
    </div>
  );
}
