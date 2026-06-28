export function plotCandidates(src = "") {
  const filename = src.split("/").pop();
  if (!filename) return [src].filter(Boolean);
  return [
    src,
    `/final_outputs/plots/${filename}`,
    `/raw_outputs/clv_diagnostic_plots/${filename}`,
    `/raw_outputs/clustering_frontend_plots/${filename}`,
    `/raw_outputs/time_series_plots/${filename}`,
    `/raw_outputs/shap_plots/${filename}`,
  ].filter((value, index, arr) => value && arr.indexOf(value) === index);
}

export function resolveImage(candidates) {
  const paths = Array.isArray(candidates) ? candidates : plotCandidates(candidates);
  return new Promise((resolve) => {
    let index = 0;
    function tryNext() {
      const candidate = paths[index];
      if (!candidate) {
        resolve({ status: "missing", candidates: paths });
        return;
      }
      const image = new Image();
      image.onload = () => resolve({ status: "available", path: candidate, candidates: paths });
      image.onerror = () => {
        index += 1;
        tryNext();
      };
      image.src = candidate;
    }
    tryNext();
  });
}
