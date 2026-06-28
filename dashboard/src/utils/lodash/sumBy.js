export default function sumBy(array, iteratee) { return (array || []).reduce((sum, item) => sum + Number(typeof iteratee === "function" ? iteratee(item) : item?.[iteratee] || 0), 0); }
