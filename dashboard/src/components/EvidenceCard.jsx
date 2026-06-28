import { ArrowRight } from "lucide-react";

export default function EvidenceCard({ card, onOpen }) {
  return (
    <button
      type="button"
      onClick={() => onOpen(card)}
      aria-label={`${card.title} evidence details`}
      className="glass flex min-h-48 flex-col rounded-lg p-4 text-left transition hover:-translate-y-0.5 hover:shadow-xl"
    >
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-[#744210]">{card.label}</p>
          <h3 className="mt-2 text-sm font-semibold text-[#4b5563]">{card.title}</h3>
        </div>
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-md border border-[#e7cf9b] bg-[#fff7e6] text-[#744210]">
          <ArrowRight size={17} />
        </span>
      </div>
      <div className="text-3xl font-semibold text-[#172033]">{card.value}</div>
      <p className="mt-3 text-sm leading-6 text-[#4b5563]">{card.short}</p>
      <div className="mt-auto pt-5">
        <span className="rounded-md border border-[#e5ded2] bg-[#fffaf1] px-2.5 py-1 text-xs text-[#6b7280]">
          {card.area}
        </span>
      </div>
    </button>
  );
}
