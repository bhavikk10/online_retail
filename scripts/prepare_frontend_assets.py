from __future__ import annotations

import csv
import json
import pickle
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from PIL import Image
except Exception:  # pragma: no cover - optional dependency
    Image = None


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DASHBOARD_PUBLIC = ROOT / "dashboard" / "public"
GENERATED = DASHBOARD_PUBLIC / "generated"
TABLES = GENERATED / "tables"
META = GENERATED / "metadata"
MODEL_LAB = GENERATED / "model_lab"
SHAP_STATUS = SRC / "shap_outputs" / "shap_status.json"

IMPORTANT_FOLDERS = [
    SRC / "final_outputs" / "data",
    SRC / "final_outputs" / "frontend",
    SRC / "final_outputs" / "plots",
    SRC / "clv_diagnostic_tables",
    SRC / "clv_diagnostic_plots",
    SRC / "clustering_outputs",
    SRC / "clustering_plots",
    SRC / "clustering_frontend_data",
    SRC / "clustering_frontend_plots",
    SRC / "time_series_outputs",
    SRC / "time_series_frontend_data",
    SRC / "time_series_plots",
    SRC / "shap_outputs",
    SRC / "shap_plots",
]

COPY_JOBS = [
    (ROOT / "assets", DASHBOARD_PUBLIC / "assets"),
    (SRC / "final_outputs", DASHBOARD_PUBLIC / "final_outputs"),
    (SRC / "clustering_frontend_data", DASHBOARD_PUBLIC / "raw_outputs" / "clustering_frontend_data"),
    (SRC / "clustering_frontend_plots", DASHBOARD_PUBLIC / "raw_outputs" / "clustering_frontend_plots"),
    (SRC / "clustering_plots", DASHBOARD_PUBLIC / "raw_outputs" / "clustering_plots"),
    (SRC / "clv_diagnostic_tables", DASHBOARD_PUBLIC / "raw_outputs" / "clv_diagnostic_tables"),
    (SRC / "clv_diagnostic_plots", DASHBOARD_PUBLIC / "raw_outputs" / "clv_diagnostic_plots"),
    (SRC / "time_series_outputs", DASHBOARD_PUBLIC / "raw_outputs" / "time_series_outputs"),
    (SRC / "time_series_plots", DASHBOARD_PUBLIC / "raw_outputs" / "time_series_plots"),
    (SRC / "shap_outputs", DASHBOARD_PUBLIC / "raw_outputs" / "shap_outputs"),
    (SRC / "shap_plots", DASHBOARD_PUBLIC / "raw_outputs" / "shap_plots"),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): clean_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_value(item) for item in value]
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        return clean_value(value.item())
    return value


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean_value(payload), indent=2, allow_nan=False), encoding="utf-8")


def standard_payload(
    status: str,
    source: Path | str | None = None,
    reason: str = "",
    suggested: str = "",
    data: list[dict[str, Any]] | None = None,
    columns: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rows = data or []
    if isinstance(source, Path):
        source_value = source.relative_to(ROOT).as_posix()
    else:
        source_value = source or ""
    payload: dict[str, Any] = {
        "status": status,
        "source": source_value,
        "reason": reason,
        "suggestedScriptToRun": suggested,
        "rows": len(rows),
        "columns": columns or (list(rows[0].keys()) if rows else []),
        "data": rows,
    }
    if extra:
        payload.update(extra)
    return payload


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def csv_profile(path: Path) -> dict[str, Any]:
    try:
        df = pd.read_csv(path)
        return {
            "rows": int(len(df)),
            "columns": list(df.columns),
            "sample": df.head(3).where(pd.notnull(df), None).to_dict(orient="records"),
        }
    except Exception as exc:
        return {"error": str(exc)}


def json_profile(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            keys = list(data.keys())
            count = len(data)
        elif isinstance(data, list):
            keys = list(data[0].keys()) if data and isinstance(data[0], dict) else []
            count = len(data)
        else:
            keys = []
            count = None
        return {"keys": keys, "itemCount": count}
    except Exception as exc:
        return {"error": str(exc)}


def png_profile(path: Path) -> dict[str, Any]:
    info: dict[str, Any] = {}
    if Image is not None:
        try:
            with Image.open(path) as image:
                info["width"] = image.width
                info["height"] = image.height
        except Exception as exc:
            info["imageError"] = str(exc)
    return info


def inventory_file(path: Path) -> dict[str, Any]:
    rel = path.relative_to(ROOT).as_posix()
    item = {
        "file": rel,
        "extension": path.suffix.lower().lstrip("."),
        "sizeBytes": path.stat().st_size,
        "status": "empty" if path.stat().st_size == 0 else "ok",
    }
    if path.suffix.lower() == ".csv":
        item.update(csv_profile(path))
    elif path.suffix.lower() == ".json":
        item.update(json_profile(path))
    elif path.suffix.lower() == ".png":
        item.update(png_profile(path))
    return item


def copy_outputs() -> list[str]:
    copied: list[str] = []
    for source, destination in COPY_JOBS:
        if not source.exists() or not any(source.rglob("*")):
            continue
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
        copied.append(f"{source.relative_to(ROOT).as_posix()} -> {destination.relative_to(ROOT).as_posix()}")
    return copied


def ensure_shap_status() -> dict[str, Any]:
    if SHAP_STATUS.exists() and SHAP_STATUS.stat().st_size > 0:
        try:
            return json.loads(SHAP_STATUS.read_text(encoding="utf-8"))
        except Exception:
            pass
    status = {
        "status": "skipped",
        "retention": {
            "status": "skipped",
            "reason": "Retention SHAP has not been generated in this workspace yet.",
            "suggestedScriptToRun": "python src/shap_analysis.py",
        },
        "clv": {
            "status": "skipped",
            "reason": "Reusable CLV model/test artifacts were not available, so CLV SHAP was not generated.",
            "suggestedScriptToRun": "Modify src/tweedie_clv.py to save reusable final-model artifacts, then run python src/shap_analysis.py.",
        },
        "notes": [
            "No SHAP outputs were fabricated.",
            "The dashboard will show SHAP plots only when generated files exist.",
        ],
        "generatedAt": now_iso(),
    }
    write_json(SHAP_STATUS, status)
    return status


def collect_inventory() -> tuple[list[dict[str, Any]], list[str], list[str]]:
    inventory: list[dict[str, Any]] = []
    missing: list[str] = []
    empty: list[str] = []
    for folder in IMPORTANT_FOLDERS:
        if not folder.exists():
            missing.append(folder.relative_to(ROOT).as_posix())
            continue
        files = [p for p in folder.rglob("*") if p.is_file()]
        if not files:
            empty.append(folder.relative_to(ROOT).as_posix())
            continue
        for file_path in files:
            item = inventory_file(file_path)
            inventory.append(item)
            if item["status"] == "empty":
                empty.append(item["file"])
    return inventory, missing, empty


def save_head_json(name: str, source: Path | None, df: pd.DataFrame | None, description: str, rows: int = 20) -> None:
    if df is None:
        payload = {
            "status": "missing",
            "source": source.relative_to(ROOT).as_posix() if source else None,
            "description": description,
            "rowsShown": 0,
            "columns": [],
            "records": [],
        }
    else:
        sample = df.head(rows).copy()
        sample = sample.where(pd.notnull(sample), None)
        payload = {
            "status": "ok",
            "source": source.relative_to(ROOT).as_posix() if source else "generated in prep script",
            "description": description,
            "rowsShown": int(len(sample)),
            "totalRowsAvailable": int(len(df)),
            "columns": list(sample.columns),
            "records": sample.to_dict(orient="records"),
        }
    write_json(TABLES / name, payload)


def generate_table_heads() -> None:
    excel_path = ROOT / "data" / "online_retail_II.xlsx"
    try:
        book = pd.ExcelFile(excel_path)
        raw_df = pd.read_excel(excel_path, sheet_name=book.sheet_names[0], nrows=20)
        payload = {
            "status": "ok",
            "source": excel_path.relative_to(ROOT).as_posix(),
            "description": "First rows from the first Online Retail II workbook sheet.",
            "sheetNames": book.sheet_names,
            "rowsShown": int(len(raw_df)),
            "columns": list(raw_df.columns),
            "records": raw_df.where(pd.notnull(raw_df), None).to_dict(orient="records"),
        }
        write_json(TABLES / "original_dataset_head.json", payload)
    except Exception as exc:
        write_json(TABLES / "original_dataset_head.json", {"status": "missing", "reason": str(exc), "records": []})

    clustered = first_existing([
        SRC / "final_outputs" / "data" / "clustered_customers.csv",
        SRC / "clustering_outputs" / "clustered_customers.csv",
    ])
    weekly = first_existing([
        SRC / "final_outputs" / "data" / "weekly_revenue_series.csv",
        SRC / "time_series_outputs" / "weekly_revenue_series.csv",
    ])
    monthly = first_existing([
        SRC / "final_outputs" / "data" / "monthly_revenue_series.csv",
        SRC / "time_series_outputs" / "monthly_revenue_series.csv",
    ])
    forecast = first_existing([
        SRC / "final_outputs" / "data" / "weekly_forecast_results.csv",
        SRC / "time_series_outputs" / "weekly_forecast_results.csv",
    ])

    if clustered:
        clustered_df = pd.read_csv(clustered)
        save_head_json("clustered_customers_head.json", clustered, clustered_df, "Customer-level segmentation and modelling features.")
        save_head_json("retention_dataset_head.json", clustered, clustered_df, "Preview of the generated retention modelling table.")
        save_head_json("clv_dataset_head.json", clustered, clustered_df, "Customer-level CLV modelling artifact.")
    else:
        for name in ["clustered_customers_head.json", "retention_dataset_head.json", "clv_dataset_head.json"]:
            save_head_json(name, None, None, "Source customer feature table was unavailable.")

    try:
        if clustered:
            clean_cols = [
                "Customer_ID",
                "Frequency",
                "Monetary",
                "AvgBasketValue",
                "Recency",
                "FutureSpend90Days",
                "RetentionLabel",
            ]
            clean_df = pd.read_csv(clustered, usecols=lambda col: col in clean_cols)
            save_head_json("cleaned_purchase_head.json", clustered, clean_df, "Preview of cleaned purchase-derived customer features.")
        else:
            save_head_json("cleaned_purchase_head.json", None, None, "Cleaned customer feature preview unavailable.")
    except Exception as exc:
        write_json(TABLES / "cleaned_purchase_head.json", {"status": "missing", "reason": str(exc), "records": []})

    for name, path, description in [
        ("weekly_revenue_head.json", weekly, "Weekly revenue series used for forecasting."),
        ("monthly_revenue_head.json", monthly, "Monthly revenue series used for trend context."),
        ("forecast_results_head.json", forecast, "Forecast test-period actuals and model predictions."),
    ]:
        if path:
            save_head_json(name, path, pd.read_csv(path), description)
        else:
            save_head_json(name, None, None, description)


def first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists() and path.stat().st_size > 0:
            return path
    return None


def csv_to_json_file(source: Path, target: Path, missing_reason: str, suggested: str = "") -> None:
    if not source.exists() or source.stat().st_size == 0:
        write_json(target, standard_payload("missing", source, missing_reason, suggested))
        return
    rows = read_csv_rows(source)
    write_json(target, standard_payload("available", source, data=rows))


def extract_classification_results() -> None:
    source = first_existing([ROOT / "classification_cv_results.pkl", SRC / "pickles" / "classification_cv_results.pkl"])
    if not source:
        payload = standard_payload(
            "missing",
            "classification_cv_results.pkl",
            "classification_cv_results.pkl was not found.",
            "python src/run_experiments.py",
        )
        write_json(MODEL_LAB / "classification_model_results.json", payload)
        write_json(MODEL_LAB / "classification_hyperparameter_trials.json", payload)
        return

    try:
        with source.open("rb") as handle:
            data = pickle.load(handle)
        trials: list[dict[str, Any]] = []
        summaries: list[dict[str, Any]] = []
        for model_name, result in data.items():
            params = result.get("params", [])
            means = result.get("mean_test_score", [])
            stds = result.get("std_test_score", [])
            best_score = None
            best_params: dict[str, Any] = {}
            for idx, params_item in enumerate(params):
                score = clean_value(means[idx]) if idx < len(means) else None
                std = clean_value(stds[idx]) if idx < len(stds) else None
                flat_params = {key.replace("model__", ""): clean_value(value) for key, value in dict(params_item).items()}
                trials.append({"model": model_name, "metric": "mean_cv_score", "meanScore": score, "stdScore": std, **flat_params})
                if score is not None and (best_score is None or score > best_score):
                    best_score = score
                    best_params = flat_params
            summaries.append({"model": model_name, "metric": "mean_cv_score", "bestScore": best_score, "bestParams": best_params})
        write_json(MODEL_LAB / "classification_model_results.json", standard_payload("available", source, data=summaries))
        write_json(MODEL_LAB / "classification_hyperparameter_trials.json", standard_payload("available", source, data=trials))
    except Exception as exc:
        payload = standard_payload("missing", source, str(exc), "python src/run_experiments.py")
        write_json(MODEL_LAB / "classification_model_results.json", payload)
        write_json(MODEL_LAB / "classification_hyperparameter_trials.json", payload)


def extract_model_lab() -> None:
    extract_classification_results()
    csv_to_json_file(
        SRC / "final_outputs" / "data" / "clv_model_comparison.csv",
        MODEL_LAB / "clv_model_results.json",
        "CLV model comparison CSV was unavailable.",
        "python src/tweedie_clv.py",
    )
    final_params = {
        "tweedie_variance_power": 1.1,
        "subsample": 0.8,
        "reg_lambda": 5,
        "reg_alpha": 0.1,
        "n_estimators": 1000,
        "min_child_weight": 5,
        "max_depth": 2,
        "learning_rate": 0.03,
        "colsample_bytree": 0.8,
    }
    write_json(
        MODEL_LAB / "clv_hyperparameter_trials.json",
        standard_payload(
            "partial",
            "src/tweedie_clv.py",
            "Full CLV hyperparameter trial history was not saved as a reusable artifact. Showing selected final parameters only.",
            "python src/tweedie_clv.py",
            data=[final_params],
            extra={"finalSelectedParameters": final_params},
        ),
    )
    csv_to_json_file(SRC / "clustering_outputs" / "kmeans_k_search_results.csv", MODEL_LAB / "kmeans_k_search.json", "KMeans search results were unavailable.", "python src/clustering.py")
    csv_to_json_file(SRC / "clustering_outputs" / "dbscan_parameter_search_results.csv", MODEL_LAB / "dbscan_parameter_search.json", "DBSCAN search results were unavailable.", "python src/clustering.py")
    csv_to_json_file(SRC / "clustering_outputs" / "clustering_model_comparison.csv", MODEL_LAB / "clustering_model_comparison.json", "Clustering comparison was unavailable.", "python src/clustering.py")
    csv_to_json_file(SRC / "final_outputs" / "data" / "forecast_model_comparison.csv", MODEL_LAB / "forecast_model_comparison.json", "Forecast comparison was unavailable.", "python src/time_series.py")
    csv_to_json_file(SRC / "final_outputs" / "data" / "weekly_forecast_results.csv", MODEL_LAB / "forecast_model_results.json", "Weekly forecast results were unavailable.", "python src/time_series.py")
    csv_to_json_file(SRC / "final_outputs" / "data" / "clv_lift_table.csv", MODEL_LAB / "clv_lift_slider_data.json", "CLV lift table was unavailable.", "python src/tweedie_clv.py")


def generate_file_map(inventory: list[dict[str, Any]]) -> None:
    script_lookup = {
        "clv": "src/tweedie_clv.py",
        "cluster": "src/clustering.py",
        "forecast": "src/time_series.py",
        "weekly": "src/time_series.py",
        "monthly": "src/time_series.py",
        "shap": "src/shap_analysis.py",
        "segment": "src/clustering.py",
        "kmeans": "src/clustering.py",
        "dbscan": "src/clustering.py",
    }
    purpose_lookup = {
        "online_retail_II.xlsx": "Raw UCI Online Retail II workbook before cleaning. Contains invoice records, stock codes, quantities, dates, prices, customer IDs, and countries.",
        "weekly_revenue_series.csv": "Weekly aggregation of valid purchase revenue. Used by forecasting pages to visualize revenue trends and evaluate models over 106 weekly observations.",
        "monthly_revenue_series.csv": "Monthly aggregation of valid purchase revenue. Used mainly for trend context because only 25 monthly observations are available.",
        "clv_model_comparison.csv": "Comparison of CLV regression models and metrics including RMSE, MAE, R2, revenue error, and ranking usefulness.",
        "clv_lift_table.csv": "Revenue capture by top-ranked predicted CLV customers. Used to show capture at the top 5%, 10%, 20%, 30%, and 50% cutoffs.",
        "clv_zero_spender_diagnostics.csv": "Diagnostic table showing predicted CLV assigned to actual zero-spend customers. Used to explain uncertainty around non-returners.",
        "clustered_customers.csv": "Customer-level dataset with final cluster assignments. Used for segment tables, filtering, customer maps, and 3D visualizations.",
        "kmeans_cluster_profiles.csv": "Segment-level customer profiles from the final KMeans model, including size, revenue share, retention, recency, frequency, and monetary statistics.",
        "pca_cluster_coordinates.csv": "Low-dimensional coordinates for visualizing customer clusters and inspecting separation between behavioural groups.",
        "segment_cards.json": "Frontend-ready summary of the four customer segments with business labels, metrics, and recommended actions.",
        "segment_cards_json.json": "Frontend-ready summary of the four customer segments with business labels, metrics, and recommended actions.",
        "weekly_forecast_results.csv": "Actual versus forecasted weekly revenue for the 12-week test horizon across SARIMA, XGBoost lag, naive, and smoothing baselines.",
        "future_12_week_forecast.csv": "Future weekly revenue forecast generated by the selected model. Used for directional short-term revenue planning.",
        "forecast_model_comparison.csv": "Weekly revenue forecasting model comparison with RMSE, MAE, WAPE, sMAPE, revenue error, and selected model metadata.",
        "project_master_summary.json": "Consolidated project summary used by the overview page. Contains module status, selected models, recommendations, and frontend references.",
        "project_health_report.json": "Generated validation report showing which artifacts are available, missing, empty, skipped, or optional.",
        "shap_status.json": "SHAP generation status file. Explains whether retention and CLV SHAP were generated or skipped and why.",
    }
    rows = []
    for item in inventory:
        file_name = item["file"]
        lower = file_name.lower()
        basename = Path(file_name).name
        source_script = "manual or source artifact"
        for token, script in script_lookup.items():
            if token in lower:
                source_script = script
                break
        artifact_type = "plot" if lower.endswith(".png") else "generated table" if lower.endswith(".csv") else "frontend manifest" if lower.endswith(".json") else "model output"
        used_on = []
        if "clv" in lower:
            used_on.append("CLV Prediction")
        if "cluster" in lower or "segment" in lower or "kmeans" in lower or "dbscan" in lower:
            used_on.append("Customer Segmentation")
        if "forecast" in lower or "weekly" in lower or "monthly" in lower:
            used_on.append("Revenue Forecasting")
        if "shap" in lower:
            used_on.append("SHAP / Model Explainability")
        rows.append({
            "name": basename,
            "file": file_name,
            "type": artifact_type,
            "sourceScript": source_script,
            "purpose": purpose_lookup.get(basename, "Project artifact copied or referenced by the dashboard. Its filename, folder, type, and source script indicate which page or model module uses it."),
            "usedOnPage": ", ".join(sorted(set(used_on))) or "File and Artifact Map",
            "status": item["status"],
            "rows": item.get("rows"),
            "columns": item.get("columns", []),
            "sizeBytes": item["sizeBytes"],
            "fileSize": f"{item['sizeBytes']} bytes",
        })
    write_json(META / "pipeline_file_map.json", {"status": "ok", "rows": rows})


def main() -> None:
    DASHBOARD_PUBLIC.mkdir(parents=True, exist_ok=True)
    GENERATED.mkdir(parents=True, exist_ok=True)
    shap_status = ensure_shap_status()
    copied = copy_outputs()
    inventory, missing, empty = collect_inventory()
    generate_table_heads()
    extract_model_lab()
    generate_file_map(inventory)

    shap_plots_empty = not any((SRC / "shap_plots").glob("*"))
    shap_generated = shap_status.get("status") in {"generated", "partial"}
    rerun = []
    if any("clustering" in item for item in missing + empty):
        rerun.append("Run python src/clustering.py for missing clustering artifacts.")
    if any("time_series" in item for item in missing + empty):
        rerun.append("Run python src/time_series.py for missing forecasting artifacts.")
    if any("clv" in item for item in missing + empty):
        rerun.append("Run python src/tweedie_clv.py or python src/clv_regression.py for missing CLV artifacts.")
    if not shap_generated:
        rerun.append("SHAP artifacts are skipped or incomplete. Run python src/shap_analysis.py to attempt safe generation.")

    health = {
        "status": "healthy" if not missing and not empty and shap_generated and not shap_plots_empty else "partial",
        "missingFiles": missing,
        "emptyFiles": empty,
        "rerunSuggestions": rerun,
        "shapStatus": shap_status,
        "generatedAt": now_iso(),
        "copied": copied,
        "notes": [
            "No synthetic model results were created.",
            "Model Lab sliders/selectors use precomputed artifacts only.",
            "SHAP status is read from src/shap_outputs/shap_status.json and may be generated, partial, or skipped depending on available artifacts.",
        ],
    }
    write_json(GENERATED / "project_data_inventory.json", {"generatedAt": now_iso(), "files": inventory})
    write_json(GENERATED / "project_health_report.json", health)

    print("Frontend asset prep complete.")
    print(f"Inventory files: {len(inventory)}")
    print(f"Missing folders/files: {len(missing)}")
    print(f"Empty folders/files: {len(empty)}")
    print(f"SHAP status: {shap_status.get('status', 'unknown')}")
    for item in inventory:
        descriptor = item["file"]
        if item.get("rows") is not None:
            descriptor += f" | rows={item.get('rows')} columns={len(item.get('columns', []))}"
        if item.get("width") and item.get("height"):
            descriptor += f" | image={item['width']}x{item['height']}"
        descriptor += f" | size={item['sizeBytes']} bytes"
        print(descriptor)
    if rerun:
        print("Rerun suggestions:")
        for item in rerun:
            print(f"- {item}")


if __name__ == "__main__":
    main()
