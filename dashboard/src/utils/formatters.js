export function num(value, digits = 2) {
  const n = Number(value);
  if (!Number.isFinite(n)) return value === undefined || value === null || value === "" ? "Unavailable" : String(value);
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: digits }).format(n);
}

export function money(value, digits = 0) {
  const n = Number(value);
  if (!Number.isFinite(n)) return value === undefined || value === null || value === "" ? "Unavailable" : String(value);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: digits,
  }).format(n);
}

export function pct(value, digits = 2) {
  if (typeof value === "string" && value.includes("%")) return value;
  const n = Number(value);
  if (!Number.isFinite(n)) return value === undefined || value === null || value === "" ? "Unavailable" : String(value);
  return `${num(n, digits)}%`;
}

export function compact(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return value === undefined || value === null || value === "" ? "Unavailable" : String(value);
  return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 2 }).format(n);
}

export function pick(row, candidates, fallback = undefined) {
  for (const key of candidates) {
    if (row && row[key] !== undefined && row[key] !== null && row[key] !== "") return row[key];
  }
  return fallback;
}
