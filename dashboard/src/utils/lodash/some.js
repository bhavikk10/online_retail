export default function some(collection, predicate = Boolean) { return Object.values(collection || {}).some(predicate); }
