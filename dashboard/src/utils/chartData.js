export function toNumber(value, fallback = null) {
  if (value === null || value === undefined || value === "") return fallback;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

export function sanitizeRows(rows, numericFields = []) {
  const fields = numericFields.filter(Boolean);
  if (!Array.isArray(rows)) return [];
  return rows
    .map((row) => {
      const next = { ...row };
      for (const field of fields) {
        const value = toNumber(next[field], null);
        if (value === null) return null;
        next[field] = value;
      }
      return next;
    })
    .filter(Boolean);
}

export function uniqueByKey(rows, keyField) {
  const seen = new Set();
  return (Array.isArray(rows) ? rows : []).filter((row) => {
    const key = row?.[keyField];
    if (key === undefined || key === null || key === "" || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export function aggregateDuplicateCategories(rows, categoryField, numericFields = []) {
  const fields = numericFields.filter(Boolean);
  const buckets = new Map();
  for (const row of Array.isArray(rows) ? rows : []) {
    const category = row?.[categoryField];
    if (category === undefined || category === null || category === "") continue;
    if (!buckets.has(category)) {
      buckets.set(category, { ...row, __count: 0 });
      for (const field of fields) buckets.get(category)[field] = 0;
    }
    const target = buckets.get(category);
    target.__count += 1;
    for (const field of fields) target[field] += toNumber(row[field], 0);
  }
  return [...buckets.values()].map((row) => {
    const next = { ...row };
    for (const field of fields) next[field] = row.__count ? row[field] / row.__count : row[field];
    delete next.__count;
    return next;
  });
}

export function makeStableKey(prefix, value, index) {
  return `${prefix}-${String(value ?? "missing").replace(/[^A-Za-z0-9_-]+/g, "-")}-${index}`;
}
