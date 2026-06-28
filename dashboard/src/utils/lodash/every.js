export default function every(collection, predicate = Boolean) { return Object.values(collection || {}).every(predicate); }
