from __future__ import annotations

import json
import pickle
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SHAP_OUTPUT_DIR = SRC / "shap_outputs"
SHAP_PLOT_DIR = SRC / "shap_plots"
STATUS_PATH = SHAP_OUTPUT_DIR / "shap_status.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def write_status(payload: dict[str, Any]) -> None:
    SHAP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SHAP_PLOT_DIR.mkdir(parents=True, exist_ok=True)
    payload["generatedAt"] = now_iso()
    STATUS_PATH.write_text(json.dumps(payload, indent=2, default=clean_value), encoding="utf-8")


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "feature"


def first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists() and path.stat().st_size > 0:
            return path
    return None


def load_xgboost_best_params() -> dict[str, Any]:
    source = first_existing([ROOT / "classification_cv_results.pkl", SRC / "pickles" / "classification_cv_results.pkl"])
    if not source:
        return {}
    try:
        with source.open("rb") as handle:
            data = pickle.load(handle)
        result = data.get("XGBoost", {})
        params = result.get("params", [])
        scores = result.get("mean_test_score", [])
        if not params or len(scores) == 0:
            return {}
        best_idx = int(np.nanargmax(scores))
        return {key.replace("model__", ""): clean_value(value) for key, value in dict(params[best_idx]).items()}
    except Exception:
        return {}


def get_feature_names(preprocessor: Any) -> list[str]:
    try:
        names = preprocessor.get_feature_names_out()
        return [str(name).replace("log__", "").replace("scale__", "") for name in names]
    except Exception:
        return []


def as_dense(matrix: Any) -> np.ndarray:
    if hasattr(matrix, "toarray"):
        return matrix.toarray()
    return np.asarray(matrix)


def build_retention_artifacts() -> dict[str, Any]:
    sys.path.insert(0, str(SRC))
    from classf_dataset import build_retention_dataset
    from preprocessing import preprocess_online_retail

    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import FunctionTransformer, StandardScaler
    from xgboost import XGBClassifier

    df = preprocess_online_retail(file_path=str(ROOT / "data" / "online_retail_II.xlsx"), verbose=False)
    retention_df = build_retention_dataset(
        df,
        cutoff_date="2011-09-09",
        prediction_days=90,
        active_days=180,
        verbose=False,
    )
    retention_df["AvgGapDays"] = retention_df["AvgGapDays"].fillna(999)

    X = retention_df.drop(columns=["Customer_ID", "RetentionLabel"])
    y = retention_df["RetentionLabel"]
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    log_features = [
        "Frequency",
        "Monetary",
        "AvgBasketValue",
        "UniqueProducts",
        "SpendLast30Days",
        "SpendLast90Days",
        "SpendPrior90Days",
        "RevenuePerDay",
        "AvgSpendPerProduct",
        "ProductDiversityRate",
    ]
    scale_features = [
        "AvgQuantity",
        "Recency",
        "LifetimeDays",
        "PurchaseRate",
        "AvgGapDays",
        "StdGapDays",
        "PurchasesLast30Days",
        "PurchasesLast90Days",
        "ReturnRate",
        "IsNewCustomer",
        "RecencyFrequency",
        "SpendTrendRatio",
        "FrequencyLast90DaysRatio",
    ]

    log_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("log_transform", FunctionTransformer(np.log1p, feature_names_out="one-to-one")),
        ("scaler", StandardScaler()),
    ])
    scale_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    preprocessor = ColumnTransformer([
        ("log", log_pipeline, [col for col in log_features if col in X.columns]),
        ("scale", scale_pipeline, [col for col in scale_features if col in X.columns]),
    ], remainder="drop")

    best_params = {
        "n_estimators": 200,
        "max_depth": 5,
        "learning_rate": 0.03,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 3,
    }
    best_params.update(load_xgboost_best_params())
    model = XGBClassifier(
        eval_metric="logloss",
        random_state=42,
        n_jobs=1,
        **best_params,
    )
    pipeline = Pipeline([("preprocessing", preprocessor), ("model", model)])
    pipeline.fit(X_train, y_train)

    X_test_processed = as_dense(pipeline.named_steps["preprocessing"].transform(X_test))
    feature_names = get_feature_names(pipeline.named_steps["preprocessing"])
    if not feature_names:
        feature_names = [f"feature_{idx}" for idx in range(X_test_processed.shape[1])]

    return {
        "pipeline": pipeline,
        "model": pipeline.named_steps["model"],
        "X_test": X_test,
        "X_test_processed": X_test_processed,
        "y_test": y_test.reset_index(drop=True),
        "feature_names": feature_names,
        "best_params": best_params,
    }


def generate_retention_shap(max_rows: int = 500) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import shap

    artifacts = build_retention_artifacts()
    X_test = artifacts["X_test"]
    y_test = artifacts["y_test"]
    pipeline = artifacts["pipeline"]
    xgb_classifier = artifacts["model"]
    X_processed_full = artifacts["X_test_processed"]
    feature_names = artifacts["feature_names"]

    sample_size = min(max_rows, X_processed_full.shape[0])
    X_processed = X_processed_full[:sample_size]
    X_test_sample = X_test.iloc[:sample_size]
    y_test_sample = y_test.iloc[:sample_size].reset_index(drop=True)

    explainer = shap.TreeExplainer(xgb_classifier)
    shap_values = explainer.shap_values(X_processed)
    if isinstance(shap_values, list):
        shap_values = shap_values[1]

    expected_value = explainer.expected_value
    if isinstance(expected_value, list):
        expected_value = expected_value[1]

    shap.summary_plot(shap_values, X_processed, feature_names=feature_names, show=False)
    plt.tight_layout()
    plt.savefig(SHAP_PLOT_DIR / "01_retention_shap_summary_beeswarm.png", dpi=220, bbox_inches="tight")
    plt.close()

    shap.summary_plot(shap_values, X_processed, feature_names=feature_names, plot_type="bar", show=False)
    plt.tight_layout()
    plt.savefig(SHAP_PLOT_DIR / "02_retention_shap_summary_bar.png", dpi=220, bbox_inches="tight")
    plt.close()

    importance = pd.DataFrame({
        "Feature": feature_names,
        "MeanAbsSHAP": np.abs(shap_values).mean(axis=0),
    }).sort_values("MeanAbsSHAP", ascending=False)
    importance.to_csv(SHAP_OUTPUT_DIR / "retention_shap_feature_importance.csv", index=False)

    for feature in importance.head(5)["Feature"].tolist():
        try:
            shap.dependence_plot(feature, shap_values, X_processed, feature_names=feature_names, show=False)
            plt.tight_layout()
            plt.savefig(SHAP_PLOT_DIR / f"03_retention_dependence_{safe_name(feature)}.png", dpi=220, bbox_inches="tight")
            plt.close()
        except Exception:
            plt.close()

    probabilities = pipeline.predict_proba(X_test_sample)[:, 1]
    predictions = pipeline.predict(X_test_sample)
    case_indices: dict[str, int] = {
        "highest_retention_probability": int(np.argmax(probabilities)),
        "lowest_retention_probability": int(np.argmin(probabilities)),
    }
    fp = np.where((predictions == 1) & (y_test_sample.values == 0))[0]
    fn = np.where((predictions == 0) & (y_test_sample.values == 1))[0]
    if len(fp):
        case_indices["false_positive"] = int(fp[0])
    if len(fn):
        case_indices["false_negative"] = int(fn[0])

    for case_name, idx in case_indices.items():
        explanation = shap.Explanation(
            values=shap_values[idx],
            base_values=expected_value,
            data=X_processed[idx],
            feature_names=feature_names,
        )
        shap.plots.waterfall(explanation, show=False)
        plt.tight_layout()
        plt.savefig(SHAP_PLOT_DIR / f"04_retention_waterfall_{case_name}.png", dpi=220, bbox_inches="tight")
        plt.close()

    return {
        "status": "generated",
        "sampleRowsExplained": sample_size,
        "outputs": [
            "src/shap_outputs/retention_shap_feature_importance.csv",
            "src/shap_plots/01_retention_shap_summary_beeswarm.png",
            "src/shap_plots/02_retention_shap_summary_bar.png",
        ],
        "bestParams": artifacts["best_params"],
    }


def clv_shap_status() -> dict[str, Any]:
    reusable = first_existing([
        SRC / "pickles" / "clv_model_artifact.pkl",
        SRC / "pickles" / "clv_shap_artifacts.pkl",
        SRC / "clv_model_artifact.pkl",
    ])
    if reusable:
        return {
            "status": "skipped",
            "reason": f"Reusable CLV artifact candidate exists at {reusable.relative_to(ROOT).as_posix()}, but this hardening pass does not infer its schema automatically.",
            "suggestedScriptToRun": "Update src/shap_analysis.py with the artifact schema, then run python src/shap_analysis.py.",
        }
    return {
        "status": "skipped",
        "reason": "Reusable CLV model/test artifacts were not available, so CLV SHAP was not generated.",
        "suggestedScriptToRun": "Modify src/tweedie_clv.py to save the final trained pipeline, X_test, y_test, predictions, and feature names, then rerun SHAP.",
    }


def saved_customer_artifact() -> Path | None:
    return first_existing([
        SRC / "final_outputs" / "data" / "clustered_customers.csv",
        SRC / "clustering_outputs" / "clustered_customers.csv",
    ])


def artifact_feature_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    excluded = {
        "Customer_ID",
        "KMeans_Cluster",
        "KMeans_SegmentName",
        "Agglomerative_Cluster",
        "GaussianMixture_Cluster",
        "DBSCAN_Cluster",
        "FutureSpend90Days",
        "RetentionLabel",
    }
    feature_cols = [col for col in df.columns if col not in excluded and pd.api.types.is_numeric_dtype(df[col])]
    X = df[feature_cols].copy()
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median(numeric_only=True)).fillna(0)
    return X, feature_cols


def plot_artifact_shap(
    model: Any,
    X_sample: pd.DataFrame,
    prefix: str,
    label: str,
    max_dependence: int = 5,
) -> dict[str, Any]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import shap

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)
    if isinstance(shap_values, list):
        shap_values = shap_values[1]

    expected_value = explainer.expected_value
    if isinstance(expected_value, list):
        expected_value = expected_value[1]

    feature_names = list(X_sample.columns)
    shap.summary_plot(shap_values, X_sample, feature_names=feature_names, show=False)
    plt.tight_layout()
    beeswarm = SHAP_PLOT_DIR / f"01_{prefix}_shap_summary_beeswarm.png"
    plt.savefig(beeswarm, dpi=220, bbox_inches="tight")
    plt.close()

    shap.summary_plot(shap_values, X_sample, feature_names=feature_names, plot_type="bar", show=False)
    plt.tight_layout()
    bar = SHAP_PLOT_DIR / f"02_{prefix}_shap_summary_bar.png"
    plt.savefig(bar, dpi=220, bbox_inches="tight")
    plt.close()

    importance = pd.DataFrame({
        "Feature": feature_names,
        "MeanAbsSHAP": np.abs(shap_values).mean(axis=0),
    }).sort_values("MeanAbsSHAP", ascending=False)
    importance_path = SHAP_OUTPUT_DIR / f"{prefix}_shap_feature_importance.csv"
    importance.to_csv(importance_path, index=False)

    for feature in importance.head(max_dependence)["Feature"].tolist():
        try:
            shap.dependence_plot(feature, shap_values, X_sample, feature_names=feature_names, show=False)
            plt.tight_layout()
            plt.savefig(SHAP_PLOT_DIR / f"03_{prefix}_dependence_{safe_name(feature)}.png", dpi=220, bbox_inches="tight")
            plt.close()
        except Exception:
            plt.close()

    if len(X_sample):
        explanation = shap.Explanation(
            values=shap_values[0],
            base_values=expected_value,
            data=X_sample.iloc[0].to_numpy(),
            feature_names=feature_names,
        )
        shap.plots.waterfall(explanation, show=False)
        plt.tight_layout()
        waterfall = SHAP_PLOT_DIR / f"04_{prefix}_waterfall_example.png"
        plt.savefig(waterfall, dpi=220, bbox_inches="tight")
        plt.close()
    else:
        waterfall = None

    outputs = [
        beeswarm.relative_to(ROOT).as_posix(),
        bar.relative_to(ROOT).as_posix(),
        importance_path.relative_to(ROOT).as_posix(),
    ]
    if waterfall:
        outputs.append(waterfall.relative_to(ROOT).as_posix())
    return {
        "status": "generated",
        "source": "src/final_outputs/data/clustered_customers.csv",
        "modelSource": f"Rebuilt {label} model from saved customer-level artifact; no synthetic data used.",
        "sampleRowsExplained": int(len(X_sample)),
        "topFeatures": importance.head(10).where(pd.notnull(importance), None).to_dict(orient="records"),
        "outputs": outputs,
    }


def generate_shap_from_saved_customer_artifact(max_rows: int = 800) -> dict[str, Any]:
    from sklearn.model_selection import train_test_split
    from xgboost import XGBClassifier, XGBRegressor

    source = saved_customer_artifact()
    if not source:
        raise FileNotFoundError("No saved customer-level artifact found for SHAP generation.")

    df = pd.read_csv(source)
    required = {"RetentionLabel", "FutureSpend90Days"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Saved customer artifact is missing required target column(s): {missing}")

    X, feature_cols = artifact_feature_frame(df)
    if not feature_cols:
        raise ValueError("Saved customer artifact did not contain numeric engineered feature columns.")

    retention_y = df["RetentionLabel"].astype(int)
    clv_y = pd.to_numeric(df["FutureSpend90Days"], errors="coerce").fillna(0).clip(lower=0)

    X_train, X_test, y_train, _ = train_test_split(
        X,
        retention_y,
        test_size=0.25,
        random_state=42,
        stratify=retention_y,
    )
    retention_model = XGBClassifier(
        n_estimators=180,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=2,
        eval_metric="logloss",
        random_state=42,
        n_jobs=1,
    )
    retention_model.fit(X_train, y_train)
    retention_sample = X_test.head(min(max_rows, len(X_test)))
    retention_status = plot_artifact_shap(retention_model, retention_sample, "retention", "retention classifier")

    X_train, X_test, y_train, _ = train_test_split(
        X,
        clv_y,
        test_size=0.25,
        random_state=42,
    )
    clv_model = XGBRegressor(
        objective="reg:tweedie",
        tweedie_variance_power=1.5,
        n_estimators=220,
        max_depth=4,
        learning_rate=0.04,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=2,
        random_state=42,
        n_jobs=1,
    )
    clv_model.fit(X_train, y_train)
    clv_sample = X_test.head(min(max_rows, len(X_test)))
    clv_status = plot_artifact_shap(clv_model, clv_sample, "clv", "CLV Tweedie regressor")

    return {
        "status": "generated",
        "retention": retention_status,
        "clv": clv_status,
        "notes": [
            "Generated from saved customer-level artifact, not fabricated.",
            "Models were rebuilt from existing engineered features because reusable final model objects were not saved.",
        ],
    }


def main() -> int:
    SHAP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SHAP_PLOT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        status = generate_shap_from_saved_customer_artifact()
    except Exception as exc:
        status = {
            "status": "skipped",
            "retention": {
                "status": "skipped",
                "reason": str(exc),
                "suggestedScriptToRun": "Confirm saved customer-level artifacts or workbook rebuild dependencies are available, then run python src/shap_analysis.py.",
            },
            "clv": clv_shap_status(),
            "notes": ["No SHAP output is fabricated. Generation happens only when required artifacts can be built or loaded safely."],
        }
    write_status(status)

    print("SHAP analysis complete.")
    print(f"Overall status: {status['status']}")
    print(f"Retention SHAP: {status['retention'].get('status')}")
    if status["retention"].get("reason"):
        print(f"Retention reason: {status['retention']['reason']}")
    print(f"CLV SHAP: {status['clv'].get('status')}")
    if status["clv"].get("reason"):
        print(f"CLV reason: {status['clv']['reason']}")
    print(f"Status file: {STATUS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
