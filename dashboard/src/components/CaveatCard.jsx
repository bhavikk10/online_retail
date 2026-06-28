export default function CaveatCard({ title = "Caveat", children }) {
  return (
    <div className="rounded-lg border border-[#e5ded2] bg-[#fff7e6] p-4">
      <p className="font-semibold text-[#744210]">{title}</p>
      <p className="mt-2 text-sm leading-6 text-[#4b5563]">{children}</p>
    </div>
  );
}
