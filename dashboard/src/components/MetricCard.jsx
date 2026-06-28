import clsx from "clsx";

export default function MetricCard({ title, value, description, tone = "amber", icon: Icon }) {
  const toneClass = {
    amber: "text-[#744210] bg-[#fff7e6] border-[#e7cf9b]",
    blue: "text-[#1e3a8a] bg-[#eef4ff] border-[#c7d7fe]",
    green: "text-[#166534] bg-[#ecfdf3] border-[#bbebc9]",
    red: "text-[#991b1b] bg-[#fff1f1] border-[#f3c0c0]",
  }[tone];
  return (
    <div className="glass rounded-lg p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-[#4b5563]">{title}</p>
        {Icon ? (
          <span className={clsx("grid h-9 w-9 place-items-center rounded-md border", toneClass)}>
            <Icon size={18} />
          </span>
        ) : null}
      </div>
      <div className="text-2xl font-semibold text-[#172033]">{value}</div>
      {description ? <p className="mt-2 text-sm leading-5 text-[#4b5563]">{description}</p> : null}
    </div>
  );
}
