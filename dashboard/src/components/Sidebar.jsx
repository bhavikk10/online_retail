import clsx from "clsx";
import { X } from "lucide-react";
import { navItems } from "../App.jsx";

export default function Sidebar({ activePage, setActivePage, open, setOpen }) {
  return (
    <>
      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-40 w-80 border-r border-slate-400/10 bg-slate-950/95 p-5 backdrop-blur-xl transition-transform lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="mb-8 flex items-start justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-amber-300">Online Retail II</p>
            <h2 className="mt-2 text-2xl font-semibold leading-tight text-slate-50">Customer Intelligence Lab</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">A model review dashboard for retention, CLV, segmentation, forecasting, and reproducible project artifacts.</p>
          </div>
          <button className="lg:hidden" onClick={() => setOpen(false)} aria-label="Close navigation">
            <X />
          </button>
        </div>
        <nav className="space-y-1">
          {navItems.map((item, index) => (
            <button
              key={item.id}
              onClick={() => {
                setActivePage(item.id);
                setOpen(false);
              }}
              className={clsx(
                "flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-left text-sm transition",
                activePage === item.id
                  ? "border border-amber-300/30 bg-amber-400/10 text-amber-100"
                  : "text-slate-400 hover:bg-slate-800/70 hover:text-slate-100",
              )}
            >
              <span className="w-6 text-xs text-slate-500">{String(index + 1).padStart(2, "0")}</span>
              <item.icon size={17} />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
      </aside>
      {open ? <div className="fixed inset-0 z-30 bg-black/50 lg:hidden" onClick={() => setOpen(false)} /> : null}
    </>
  );
}
