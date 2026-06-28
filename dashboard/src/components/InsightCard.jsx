import clsx from "clsx";

export default function InsightCard({ title, children, tone = "amber" }) {
  const color = {
    amber: "border-amber-300/25 bg-amber-400/10 text-amber-100",
    blue: "border-sky-300/25 bg-sky-400/10 text-sky-100",
    green: "border-emerald-300/25 bg-emerald-400/10 text-emerald-100",
    red: "border-red-300/25 bg-red-400/10 text-red-100",
  }[tone];
  return (
    <div className={clsx("rounded-lg border p-4", color)}>
      <h3 className="font-semibold">{title}</h3>
      <div className="mt-2 text-sm leading-6 text-slate-200">{children}</div>
    </div>
  );
}
