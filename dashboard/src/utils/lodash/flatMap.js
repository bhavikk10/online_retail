export default function flatMap(array, iteratee) { return (array || []).flatMap(iteratee || ((x) => x)); }
