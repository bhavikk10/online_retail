export default function ErrorState({ title = "Artifact unavailable", children }) {
  return (
    <div className="rounded-lg border border-red-300/25 bg-red-400/10 p-4 text-red-100">
      <h3 className="font-semibold">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-slate-200">{children || "The expected optional artifact was not available in the generated dashboard bundle. The page can continue without it, and the missing state is shown rather than hidden."}</p>
    </div>
  );
}
