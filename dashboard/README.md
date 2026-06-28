# Customer Intelligence Lab

Premium Vite + React dashboard for the Online Retail II customer analytics project.

## Purpose

This dashboard tells the full project story: raw invoice transactions to preprocessing, retention modelling, CLV prediction, segmentation, forecasting, SHAP readiness, model diagnostics, and business recommendations.

It is intentionally project-specific. Pages use the generated CSV, JSON, and PNG artifacts under `src/final_outputs`, `src/clustering_outputs`, `src/clv_diagnostic_tables`, `src/time_series_outputs`, and related folders.

## Generate Frontend Assets

From the repository root:

```powershell
python scripts\prepare_frontend_assets.py
```

The prep script:

- validates important CSV, JSON, and PNG artifacts
- copies analysis outputs into `dashboard/public`
- creates `generated/project_data_inventory.json`
- creates `generated/project_health_report.json`
- creates sample table heads under `generated/tables`
- creates Model Lab JSON under `generated/model_lab`
- records missing artifacts without fabricating model results

## Run The Frontend

```powershell
cd dashboard
npm install
npm run dev
```

Build for deployment:

```powershell
npm run build
```

## Dashboard Pages

1. Executive Overview
2. Data Pipeline
3. Dataset Explorer
4. Retention Modelling
5. CLV Prediction
6. Customer Segmentation
7. Revenue Forecasting
8. SHAP / Model Explainability
9. Model Lab
10. Failures, Diagnostics, and Lessons
11. Business Recommendations
12. File and Artifact Map

## Model Lab

Model Lab sliders and selectors are based on precomputed experiment results, not fake browser-side retraining. This is intentional: retraining models in the browser would be slow and misleading.

When a full trial history is unavailable, the page shows a clear partial or missing state and, where safe, the final selected parameters only.

## Known Limitations

- SHAP artifacts are shown only if reusable model/test artifacts exist and SHAP outputs have been generated.
- CLV is strongest as a prioritization model, not an exact customer-level spend oracle.
- Forecasting is exploratory because there are only 106 weekly observations and 25 monthly observations.
- DBSCAN is documented as a failure case because high silhouette can be misleading when many customers are marked as noise.

## Regenerating Outputs

Use the project scripts from `src` only when artifacts are missing or stale:

- clustering: `python src\clustering.py`
- forecasting: `python src\time_series.py`
- CLV: `python src\tweedie_clv.py` or `python src\clv_regression.py`
- classification experiments: `python src\run_experiments.py`

After regenerating outputs, rerun:

```powershell
python scripts\prepare_frontend_assets.py
```
