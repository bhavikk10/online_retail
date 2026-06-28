import { useState } from "react";
import Diagnostics from "./Diagnostics.jsx";
import Explainability from "./Explainability.jsx";
import FileMap from "./FileMap.jsx";
import ModelLab from "./ModelLab.jsx";
import Recommendations from "./Recommendations.jsx";
import SectionHeader from "../components/SectionHeader.jsx";

const sections = [
  { id: "model-lab", label: "Model Lab", component: ModelLab },
  { id: "diagnostics", label: "Diagnostics", component: Diagnostics },
  { id: "recommendations", label: "Recommendations", component: Recommendations },
  { id: "explainability", label: "Explainability", component: Explainability },
  { id: "file-map", label: "Artifacts & Reproducibility", component: FileMap },
];

export default function ModelReviewAppendix() {
  const [active, setActive] = useState("model-lab");
  const Active = sections.find((section) => section.id === active)?.component || Explainability;
  return (
    <div>
      <SectionHeader eyebrow="Model Review & Appendix" title="Experiment Evidence, SHAP Status, And Reproducibility">
        This appendix keeps the modelling review auditable. It brings together saved experiment controls, diagnostics, evidence-based recommendations, SHAP status, and the artifact map so every visible claim can be traced back to generated project outputs.
      </SectionHeader>
      <div className="mb-6 flex flex-wrap gap-2">
        {sections.map((section) => (
          <button
            key={section.id}
            type="button"
            onClick={() => setActive(section.id)}
            className={`rounded-md border px-4 py-2 text-sm transition ${
              active === section.id
                ? "border-amber-300/40 bg-amber-300/15 text-amber-100"
                : "border-slate-400/15 bg-slate-950/40 text-slate-300 hover:border-slate-300/30"
            }`}
          >
            {section.label}
          </button>
        ))}
      </div>
      <Active />
    </div>
  );
}
