export function toRows(payload) {
  if (Array.isArray(payload)) return payload;
  if (payload?.rows && Array.isArray(payload.rows)) return payload.rows;
  if (payload?.records && Array.isArray(payload.records)) return payload.records;
  if (payload?.files && Array.isArray(payload.files)) return payload.files;
  return [];
}

export function numericKeys(rows) {
  const first = rows.find(Boolean) || {};
  return Object.keys(first).filter((key) => rows.some((row) => Number.isFinite(Number(row[key]))));
}

export function stringKeys(rows) {
  const first = rows.find(Boolean) || {};
  return Object.keys(first).filter((key) => !Number.isFinite(Number(first[key])));
}

export function sampleRows(rows, limit = 3000) {
  if (!Array.isArray(rows) || rows.length <= limit) return rows || [];
  const step = Math.ceil(rows.length / limit);
  return rows.filter((_, index) => index % step === 0).slice(0, limit);
}
