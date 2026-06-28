# Dashboard QA Checklist

## Routes Checked

- Overview
- Data & Pipeline
- Customer Value
- Customer Segments
- Revenue Forecast
- Model Review & Appendix

## Interactions Checked

- Overview `Evidence summary` cards open the evidence modal and close from the close button in the live smoke test; Escape and backdrop close handlers are present in `EvidenceModal.jsx`.
- Customer Value tabs: Retention, CLV Prediction, CLV Diagnostics, Explainability Status.
- Revenue Forecast model selector and 1-12 week horizon control.
- Customer Segments filters plus PCA/3D plot sections.
- Model Review & Appendix tabs: Model Lab, Diagnostics, Recommendations, Explainability, Artifacts & Reproducibility.
- File Map / artifact search behavior through the appendix artifact section.

## Reviewer-Grade Pass

- Overview first fold now leads with one thesis, four strongest evidence tiles, and a shorter framing paragraph.
- Evidence cards are unified under `Evidence summary`; no visible flashcard language remains.
- Data & Pipeline stages use human-readable methodology labels with input, transformation, output, and why-it-matters copy.
- Customer Value separates Retention, CLV Prediction, CLV Diagnostics, and Explainability instead of hiding CLV behind one long page.
- Customer Segments leads with the High-Value Loyalist revenue-share result before lower-level tables.
- Revenue Forecast is framed as exploratory, with SARIMA vs naive evidence and observation-count limitations.
- Model Review & Appendix is internally tabbed and includes Model Lab, Diagnostics, Recommendations, Explainability, and artifact reproducibility.

## Runtime Errors Before

- Recharts unmount crash: `this.throttleTriggeredAfterMouseMove.cancel is not a function`.
- Duplicate React key warning for repeated `SARIMA`.
- Route-level crashes on Customer Value, Revenue Forecast, and Model Review & Appendix subtabs.

## Runtime Errors After

- Final production build passed on 2026-06-26.
- Static path audit passed with 69 valid public paths, 0 broken required paths, and 0 optional missing paths.
- Final in-app browser smoke test started at `2026-06-26T18:07:29.457Z`.
- All six routes changed via the visible navigation menu in the mobile viewport.
- Route render failure text was absent on all checked routes.
- Chart error-boundary fallback text was absent on checked routes.
- Broken images were 0 on checked routes.
- `undefined`, `NaN`, visible `null`, visible `n/a`, and absolute Windows paths were absent from visible dashboard copy.
- New console warnings/errors since the smoke-test timestamp: 0.

## Recharts Crash Status

- Fixed for the dev app by replacing the local `lodash/throttle` shim with lodash-compatible `cancel` and `flush` methods.
- `dashboard/vite.config.js` now aliases exact `lodash/throttle` and forces Vite dependency optimization so Recharts does not reuse stale optimized code.
- Rebuilt `node_modules/.vite/deps/recharts.js` contains `throttled.cancel`.

## Duplicate Key Status

- Forecast model options are deduplicated before rendering.
- Repeated model names are handled as display values rather than React keys where needed.

## Homepage Modal Status

- Evidence modal includes title, value, detailed evidence text, evidence type, related page, close button, Escape support, and backdrop close.
- The modal content uses verified project constants and generated artifacts only.
- Live smoke verified modal open and close-button close; the in-app browser keypress helper could not deliver Escape reliably, so Escape support was verified by inspecting the installed keydown handler.

## SHAP Status

- Status: generated.
- `src/shap_outputs/shap_status.json` is copied to `/raw_outputs/shap_outputs/shap_status.json`.
- Retention and CLV SHAP feature-importance CSVs and plot PNGs are available under `/raw_outputs/shap_outputs/` and `/raw_outputs/shap_plots/`.
- SHAP copy is framed as attribution, not causality.

## Build And Asset Checks

- `python scripts\prepare_frontend_assets.py` passed.
- `npm run build` passed.
- `node scripts\static_path_audit.mjs` passed.
- `node scripts\visual_smoke_test.mjs` still requires Playwright if screenshot automation is desired.

## Remaining Limitations

- Vite still warns that the async Plotly chunk is larger than 500 kB; Plotly is split from the main app bundle and loaded on demand for the 3D component.
- Forecasting remains exploratory because the weekly series has 106 observations, monthly aggregation has 25 observations, and several models underperform the naive baseline.
- Some appendix controls depend on saved experiment artifacts; unavailable probability files remain disabled instead of simulated.
