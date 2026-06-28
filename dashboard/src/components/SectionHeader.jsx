export default function SectionHeader({ eyebrow, title, children, answers, matters, caveat }) {
  return (
    <div className="mb-6 max-w-5xl animate-[fadeIn_0.35s_ease-out]">
      {eyebrow ? <p className="mb-2 text-xs font-semibold uppercase tracking-[0.25em] text-[#744210]">{eyebrow}</p> : null}
      <h2 className="text-3xl font-semibold tracking-normal text-[#172033] sm:text-4xl">{title}</h2>
      {children ? <p className="mt-3 text-base leading-7 text-[#4b5563]">{children}</p> : null}
      {(answers || matters || caveat) ? (
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {answers ? <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">What this page answers</p><p className="mt-2 text-sm leading-6 text-slate-300">{answers}</p></div> : null}
          {matters ? <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">Why this matters</p><p className="mt-2 text-sm leading-6 text-slate-300">{matters}</p></div> : null}
          {caveat ? <div className="editorial-card p-3"><p className="text-xs uppercase tracking-[0.18em] text-slate-500">Caveat</p><p className="mt-2 text-sm leading-6 text-slate-300">{caveat}</p></div> : null}
        </div>
      ) : null}
    </div>
  );
}
