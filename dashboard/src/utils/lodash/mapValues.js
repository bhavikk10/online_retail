export default function mapValues(object, iteratee) { return Object.fromEntries(Object.entries(object || {}).map(([key, value]) => [key, iteratee(value, key)])); }
