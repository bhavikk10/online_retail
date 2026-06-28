import Papa from "papaparse";

export async function fetchCsv(path) {
  try {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    const text = await response.text();
    const parsed = Papa.parse(text, {
      header: true,
      skipEmptyLines: true,
      dynamicTyping: true,
    });
    if (parsed.errors?.length) {
      throw new Error(parsed.errors[0].message);
    }
    return parsed.data;
  } catch (error) {
    return { status: "missing", path, reason: error.message };
  }
}
