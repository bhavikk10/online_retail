import { useEffect } from "react";
import { X } from "lucide-react";

export default function EvidenceModal({ card, onClose }) {
  useEffect(() => {
    if (!card) return undefined;
    const handleKey = (event) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [card, onClose]);

  if (!card) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4"
      role="dialog"
      aria-modal="true"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="w-full max-w-2xl rounded-lg border border-[#e5ded2] bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.22em] text-[#744210]">Numerical evidence</p>
            <h3 className="mt-2 text-2xl font-semibold text-[#172033]">{card.title}</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="grid h-10 w-10 place-items-center rounded-md border border-[#e5ded2] bg-[#fffaf1] text-[#4b5563]"
            aria-label="Close evidence note"
          >
            <X size={18} />
          </button>
        </div>
        <div className="mt-5 rounded-md border border-[#e7cf9b] bg-[#fff7e6] p-4 text-4xl font-semibold text-[#744210]">
          {card.value}
        </div>
        <p className="mt-5 text-base leading-7 text-[#4b5563]">{card.detail}</p>
        <div className="mt-5 flex flex-wrap gap-2">
          <span className="rounded-md border border-[#e7cf9b] bg-[#fff7e6] px-2.5 py-1 text-xs font-medium text-[#744210]">
            Evidence type: {card.evidenceType || card.label}
          </span>
          {card.tags.map((tag) => (
            <span key={tag} className="rounded-md border border-[#e5ded2] bg-[#fffaf1] px-2.5 py-1 text-xs text-[#6b7280]">
              {tag}
            </span>
          ))}
        </div>
        <p className="mt-5 text-sm font-medium text-[#172033]">Related page: {card.relatedPage}</p>
      </div>
    </div>
  );
}
