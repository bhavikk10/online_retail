export default function EvidenceNote({ title, children }) {
  return (
    <div className="editorial-card mt-3 p-4">
      {title ? <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-300/80">{title}</p> : null}
      <p className="mt-2 text-sm leading-6 text-slate-300">{children}</p>
    </div>
  );
}
