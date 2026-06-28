import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split, RandomizedSearchCV

# Preprocessing utilities
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

# Missing value handling
from sklearn.impute import SimpleImputer

# XGBoost models
from xgboost import XGBClassifier, XGBRegressor

# Classification metrics
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix
)

# Regression metrics
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    root_mean_squared_error,
    median_absolute_error
)

# Dataset creation pipeline
from clv_dataset import build_retention_dataset

# Preprocessing pipeline
from preprocessing import preprocess_online_retail


# FUNCTION FOR REGRESSION METRICS
def calculate_regression_metrics(y_true, y_pred):

    y_pred = np.maximum(0, y_pred)

    total_actual = y_true.sum()

    total_predicted = y_pred.sum()

    mse = mean_squared_error(y_true, y_pred)

    rmse = root_mean_squared_error(y_true, y_pred)

    mae = mean_absolute_error(y_true, y_pred)

    r2 = r2_score(y_true, y_pred)

    median_ae = median_absolute_error(y_true, y_pred)

    rmsle = root_mean_squared_error(
        np.log1p(y_true),
        np.log1p(y_pred)
    )

    if total_actual != 0:

        revenue_error_pct = (
            abs(total_actual - total_predicted) /
            total_actual
        ) * 100

        prediction_actual_ratio = (
            total_predicted /
            total_actual
        )

    else:

        revenue_error_pct = np.nan

        prediction_actual_ratio = np.nan

    return {
        'MSE': mse,
        'RMSE': rmse,
        'MAE': mae,
        'R2': r2,
        'MEDIAN_AE': median_ae,
        'RMSLE': rmsle,
        'Revenue_Error_%': revenue_error_pct,
        'Prediction_Actual_Ratio': prediction_actual_ratio,
        'Actual_Total_Revenue': total_actual,
        'Predicted_Total_Revenue': total_predicted
    }


# LOADING CLEANED MASTER DATASET
df = preprocess_online_retail(
    file_path="online_retail_II.xlsx",
    verbose=False
)

# BUILDING CUSTOMER CLV DATASET
retention_df = build_retention_dataset(
    df,
    cutoff_date='2011-09-09',
    prediction_days=90,
    active_days=180,
    verbose=True
)

# HANDLING AvgGapDays MISSING VALUES
retention_df['AvgGapDays'] = (
    retention_df['AvgGapDays']
    .fillna(999)
)

# CREATING RETENTION LABEL FOR CLASSIFICATION STAGE
retention_df['RetentionLabel'] = (
    retention_df['FutureSpend90Days'] > 0
).astype(int)

print("\nCorrect CLV Target Summary:")

print(
    "Total customers:",
    len(retention_df)
)

print(
    "Customers with future spend > 0:",
    (retention_df['FutureSpend90Days'] > 0).sum()
)

print(
    "Customers with future spend = 0:",
    (retention_df['FutureSpend90Days'] == 0).sum()
)

print(
    "Average future spend:",
    f"{retention_df['FutureSpend90Days'].mean():.2f}"
)

# SPLITTING FEATURES AND TARGETS
X = retention_df.drop(
    columns=[
        'Customer_ID',
        'FutureSpend90Days',
        'RetentionLabel'
    ],
    errors='ignore'
)

y_class = retention_df['RetentionLabel']

y_reg = retention_df['FutureSpend90Days']

# TRAIN TEST SPLIT
X_train, X_test, y_class_train, y_class_test, y_reg_train, y_reg_test = train_test_split(
    X,
    y_class,
    y_reg,
    test_size=0.2,
    random_state=42,
    stratify=y_class
)

# FEATURES NEEDING LOG TRANSFORMATION
log_features = [
    'Frequency',
    'Monetary',
    'AvgBasketValue',
    'UniqueProducts',
    'SpendLast30Days',
    'SpendLast90Days',
    'SpendPrior90Days',
    'RevenuePerDay',
    'AvgSpendPerProduct',
    'ProductDiversityRate'
]

# FEATURES NEEDING NORMAL SCALING ONLY
scale_features = [
    'AvgQuantity',
    'Recency',
    'LifetimeDays',
    'PurchaseRate',
    'AvgGapDays',
    'StdGapDays',
    'PurchasesLast30Days',
    'PurchasesLast90Days',
    'ReturnRate',
    'IsNewCustomer',
    'RecencyFrequency',
    'SpendTrendRatio',
    'FrequencyLast90DaysRatio'
]

# PIPELINE FOR LOG-TRANSFORMED FEATURES
log_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('log_transform', FunctionTransformer(np.log1p)),
    ('scaler', StandardScaler())
])

# PIPELINE FOR STANDARD-SCALED FEATURES
scale_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

# COMBINING PREPROCESSING PIPELINES
preprocessor = ColumnTransformer([
    ('log', log_pipeline, log_features),
    ('scale', scale_pipeline, scale_features)
],
    remainder='drop'
)


# BASELINE MODEL
baseline_pred = np.repeat(
    y_reg_train.mean(),
    len(y_reg_test)
)

baseline_metrics = calculate_regression_metrics(
    y_reg_test,
    baseline_pred
)

print("\n--- BASELINE MODEL ---")

print(f"Baseline RMSE: {baseline_metrics['RMSE']:.4f}")

print(f"Baseline MAE: {baseline_metrics['MAE']:.4f}")

print(f"Baseline R2: {baseline_metrics['R2']:.4f}")

print(f"Baseline RMSLE: {baseline_metrics['RMSLE']:.4f}")

print(f"Baseline Revenue Error %: {baseline_metrics['Revenue_Error_%']:.2f}")


# STAGE 1: CLASSIFICATION
print("\n--- STAGE 1: CLASSIFICATION ---")

neg_count = (y_class_train == 0).sum()

pos_count = (y_class_train == 1).sum()

scale_pos_weight_value = neg_count / pos_count

classifier = XGBClassifier(
    objective='binary:logistic',
    eval_metric='logloss',
    tree_method='hist',
    random_state=42,
    n_jobs=1
)

clf_pipeline = Pipeline([
    ('preprocessing', preprocessor),
    ('model', classifier)
])

clf_param_grid = {
    'model__n_estimators': [100, 200, 500, 1000],
    'model__max_depth': [2, 3, 4, 5, 6],
    'model__learning_rate': [0.01, 0.03, 0.05, 0.1],
    'model__subsample': [0.6, 0.8, 1.0],
    'model__colsample_bytree': [0.6, 0.8, 1.0],
    'model__min_child_weight': [1, 3, 5, 7],
    'model__gamma': [0, 0.1, 0.3, 0.5],
    'model__reg_alpha': [0, 0.01, 0.1],
    'model__reg_lambda': [1, 2, 5, 10],
    'model__scale_pos_weight': [1, scale_pos_weight_value]
}

clf_search = RandomizedSearchCV(
    estimator=clf_pipeline,
    param_distributions=clf_param_grid,
    n_iter=80,
    cv=5,
    scoring='roc_auc',
    random_state=42,
    n_jobs=-1
)

clf_search.fit(
    X_train,
    y_class_train
)

best_classifier = clf_search.best_estimator_

print(f"Best Classifier Params: {clf_search.best_params_}")

# PREDICTING CLASS PROBABILITIES
prob_buy_train = best_classifier.predict_proba(X_train)[:, 1]

prob_buy_test = best_classifier.predict_proba(X_test)[:, 1]

# DEFAULT THRESHOLD CLASS PREDICTIONS
class_pred_test = (
    prob_buy_test >= 0.5
).astype(int)

# CLASSIFICATION METRICS
accuracy = accuracy_score(
    y_class_test,
    class_pred_test
)

precision = precision_score(
    y_class_test,
    class_pred_test,
    zero_division=0
)

recall = recall_score(
    y_class_test,
    class_pred_test,
    zero_division=0
)

f1 = f1_score(
    y_class_test,
    class_pred_test,
    zero_division=0
)

roc_auc = roc_auc_score(
    y_class_test,
    prob_buy_test
)

pr_auc = average_precision_score(
    y_class_test,
    prob_buy_test
)

brier = brier_score_loss(
    y_class_test,
    prob_buy_test
)

cm = confusion_matrix(
    y_class_test,
    class_pred_test
)

print("\nClassification Metrics:")

print(f"Accuracy: {accuracy:.4f}")

print(f"Precision: {precision:.4f}")

print(f"Recall: {recall:.4f}")

print(f"F1: {f1:.4f}")

print(f"ROC AUC: {roc_auc:.4f}")

print(f"PR AUC: {pr_auc:.4f}")

print(f"Brier Score: {brier:.4f}")

print("Confusion Matrix:")

print(cm)


# STAGE 2: TWEEDIE REGRESSION ON POSITIVE SPENDERS ONLY
print("\n--- STAGE 2: TWEEDIE REGRESSION ON POSITIVE SPENDERS ---")

X_train_pos = X_train[
    y_class_train == 1
]

y_reg_train_pos = y_reg_train[
    y_class_train == 1
]

X_test_pos = X_test[
    y_class_test == 1
]

y_reg_test_pos = y_reg_test[
    y_class_test == 1
]

regressor = XGBRegressor(
    objective='reg:tweedie',
    eval_metric='tweedie-nloglik@1.5',
    tweedie_variance_power=1.5,
    tree_method='hist',
    random_state=42,
    n_jobs=1
)

reg_pipeline = Pipeline([
    ('preprocessing', preprocessor),
    ('model', regressor)
])

reg_param_grid = {
    'model__n_estimators': [100, 200, 500, 1000],
    'model__max_depth': [2, 3, 4, 5],
    'model__learning_rate': [0.01, 0.03, 0.05, 0.1],
    'model__subsample': [0.6, 0.8, 1.0],
    'model__colsample_bytree': [0.6, 0.8, 1.0],
    'model__min_child_weight': [1, 3, 5, 7],
    'model__gamma': [0, 0.1, 0.3, 0.5],
    'model__reg_alpha': [0, 0.01, 0.1],
    'model__reg_lambda': [1, 2, 5, 10],
    'model__tweedie_variance_power': [1.1, 1.3, 1.5, 1.7, 1.9]
}

reg_search = RandomizedSearchCV(
    estimator=reg_pipeline,
    param_distributions=reg_param_grid,
    n_iter=100,
    cv=5,
    scoring='neg_root_mean_squared_error',
    random_state=42,
    n_jobs=-1
)

reg_search.fit(
    X_train_pos,
    y_reg_train_pos
)

best_regressor = reg_search.best_estimator_

print(f"Best Regressor Params: {reg_search.best_params_}")

# CONDITIONAL SPEND PREDICTIONS ON TRUE BUYERS
positive_pred = best_regressor.predict(
    X_test_pos
)

positive_pred = np.maximum(
    0,
    positive_pred
)

positive_metrics = calculate_regression_metrics(
    y_reg_test_pos,
    positive_pred
)

print("\nConditional Regression Metrics On Actual Buyers:")

print(f"Positive RMSE: {positive_metrics['RMSE']:.4f}")

print(f"Positive MAE: {positive_metrics['MAE']:.4f}")

print(f"Positive R2: {positive_metrics['R2']:.4f}")

print(f"Positive RMSLE: {positive_metrics['RMSLE']:.4f}")

print(f"Positive Revenue Error %: {positive_metrics['Revenue_Error_%']:.2f}")

print(f"Positive Prediction / Actual Ratio: {positive_metrics['Prediction_Actual_Ratio']:.4f}")


# FINAL TWO-STAGE CLV PREDICTIONS
print("\n--- FINAL EVALUATION: TWO-STAGE CLV MODEL ---")

# EXPECTED SPEND IF BUY FOR TRAIN SET
expected_spend_train = best_regressor.predict(
    X_train
)

expected_spend_train = np.maximum(
    0,
    expected_spend_train
)

# EXPECTED SPEND IF BUY FOR TEST SET
expected_spend_test = best_regressor.predict(
    X_test
)

expected_spend_test = np.maximum(
    0,
    expected_spend_test
)

# FINAL CLV = PROBABILITY OF BUYING * EXPECTED SPEND IF BUY
final_pred_train = (
    prob_buy_train *
    expected_spend_train
)

final_pred_test = (
    prob_buy_test *
    expected_spend_test
)

final_pred_train = np.maximum(
    0,
    final_pred_train
)

final_pred_test = np.maximum(
    0,
    final_pred_test
)

# TRAIN-SET REVENUE CALIBRATION FACTOR
if final_pred_train.sum() != 0:

    calibration_factor = (
        y_reg_train.sum() /
        final_pred_train.sum()
    )

else:

    calibration_factor = 1

# CALIBRATED FINAL TEST PREDICTION
final_pred_calibrated = (
    final_pred_test *
    calibration_factor
)

final_pred_calibrated = np.maximum(
    0,
    final_pred_calibrated
)

# FINAL METRICS
results = []

model_predictions = {
    'Baseline_Mean': baseline_pred,
    'TwoStage_Tweedie_Uncalibrated': final_pred_test,
    'TwoStage_Tweedie_Calibrated': final_pred_calibrated
}

for model_name, prediction in model_predictions.items():

    metrics = calculate_regression_metrics(
        y_reg_test,
        prediction
    )

    metrics['Model'] = model_name

    if model_name == 'TwoStage_Tweedie_Calibrated':

        metrics['Calibration_Factor'] = calibration_factor

    else:

        metrics['Calibration_Factor'] = 1

    results.append(metrics)

results_df = pd.DataFrame(results)

results_df = results_df[
    [
        'Model',
        'MSE',
        'RMSE',
        'MAE',
        'R2',
        'MEDIAN_AE',
        'RMSLE',
        'Revenue_Error_%',
        'Prediction_Actual_Ratio',
        'Actual_Total_Revenue',
        'Predicted_Total_Revenue',
        'Calibration_Factor'
    ]
]

results_df = results_df.sort_values(
    by='RMSE',
    ascending=True
)

print("\nFinal Two-Stage Model Comparison:\n")

print(results_df)


# SHORT FINAL SUMMARY
best_row = results_df.iloc[0]

print("\nBest Two-Stage Model:")

print(f"Model: {best_row['Model']}")

print(f"RMSE: {best_row['RMSE']:.4f}")

print(f"MAE: {best_row['MAE']:.4f}")

print(f"R2: {best_row['R2']:.4f}")

print(f"RMSLE: {best_row['RMSLE']:.4f}")

print(f"Revenue Error %: {best_row['Revenue_Error_%']:.2f}")

print(f"Prediction / Actual Ratio: {best_row['Prediction_Actual_Ratio']:.4f}")

print(f"Calibration Factor: {best_row['Calibration_Factor']:.4f}")