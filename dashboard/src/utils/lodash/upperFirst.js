export default function upperFirst(value) { const text = String(value ?? ""); return text.charAt(0).toUpperCase() + text.slice(1); }
