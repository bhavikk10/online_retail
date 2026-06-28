export default function find(collection, predicate = Boolean) { return Object.values(collection || {}).find(predicate); }
