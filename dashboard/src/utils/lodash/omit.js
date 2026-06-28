export default function omit(object, keys = []) { const remove = new Set(keys); return Object.fromEntries(Object.entries(object || {}).filter(([key]) => !remove.has(key))); }
