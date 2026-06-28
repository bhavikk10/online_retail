import { ImageOff } from "lucide-react";

export default function MissingArtifactCard({
  title = "Artifact unavailable",
  expectedArtifact = "Optional project artifact",
  expectedPath,
  wouldShow,
  sourceScript,
  required = false,
  reason,
}) {
  return (
    <div className="rounded-lg border border-amber-300/15 bg-slate-950/70 p-5">
      <div className="flex items-start gap-3">
        <div className="rounded-md border border-amber-300/20 bg-amber-300/10 p-2 text-amber-200">
          <ImageOff size={18} />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-100">{title}</p>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            {expectedArtifact} is {required ? "required for this view" : "optional for this review"} and was not available in the public dashboard bundle.
          </p>
        </div>
      </div>
      <dl className="mt-4 grid gap-3 text-sm md:grid-cols-2">
        {expectedPath ? (
          <div>
            <dt className="text-xs uppercase tracking-[0.18em] text-slate-500">Expected path</dt>
            <dd className="mt-1 break-all text-slate-300">{expectedPath}</dd>
          </div>
        ) : null}
        {sourceScript ? (
          <div>
            <dt className="text-xs uppercase tracking-[0.18em] text-slate-500">Likely source</dt>
            <dd className="mt-1 text-slate-300">{sourceScript}</dd>
          </div>
        ) : null}
        {wouldShow ? (
          <div>
            <dt className="text-xs uppercase tracking-[0.18em] text-slate-500">What it would show</dt>
            <dd className="mt-1 text-slate-300">{wouldShow}</dd>
          </div>
        ) : null}
        {reason ? (
          <div>
            <dt className="text-xs uppercase tracking-[0.18em] text-slate-500">Reason</dt>
            <dd className="mt-1 text-slate-300">{reason}</dd>
          </div>
        ) : null}
      </dl>
    </div>
  );
}
