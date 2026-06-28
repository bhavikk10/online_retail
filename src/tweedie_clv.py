import os
import warnings

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from sklearn.impute import SimpleImputer

from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    root_mean_squared_error,
    median_absolute_error
)

from clv_dataset import build_retention_dataset
from preprocessing import preprocess_online_retail


# HIDING LIGHTGBM FEATURE NAME WARNINGS
warnings.filterwarnings(
    "ignore",
    message="X does not have valid feature names.*"
)


# CREATING OUTPUT DIRECTORIES
PLOT_DIR = "clv_diagnostic_plots"
TABLE_DIR = "clv_diagnostic_tables"

os.makedirs(
    PLOT_DIR,
    exist_ok=True
)

os.makedirs(
    TABLE_DIR,
    exist_ok=True
)


# FUNCTION FOR REGRESSION METRICS
# FUNCTION FOR REGRESSION METRICS
def calculate_regression_metrics(y_true, y_pred):

    y_true_array = np.asarray(y_true)

    y_pred_array = np.asarray(y_pred)

    y_pred_array = np.maximum(
        0,
        y_pred_array
    )

    total_actual = y_true_array.sum()

    total_predicted = y_pred_array.sum()

    mse = mean_squared_error(
        y_true_array,
        y_pred_array
    )

    rmse = root_mean_squared_error(
        y_true_array,
        y_pred_array
    )

    mae = mean_absolute_error(
        y_true_array,
        y_pred_array
    )

    r2 = r2_score(
        y_true_array,
        y_pred_array
    )

    median_ae = median_absolute_error(
        y_true_array,
        y_pred_array
    )

    rmsle = root_mean_squared_error(
        np.log1p(y_true_array),
        np.log1p(y_pred_array)
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

        wmape = (
            np.sum(
                np.abs(y_true_array - y_pred_array)
            ) /
            total_actual
        ) * 100

    else:

        revenue_error_pct = np.nan

        prediction_actual_ratio = np.nan

        wmape = np.nan

    # Spearman is undefined if predictions or actuals are constant
    if (
        np.std(y_true_array) == 0 or
        np.std(y_pred_array) == 0
    ):

        spearman_rank_corr = np.nan

    else:

        spearman_rank_corr = pd.Series(
            y_true_array
        ).corr(
            pd.Series(y_pred_array),
            method='spearman'
        )

    return {
        'MSE': mse,
        'RMSE': rmse,
        'MAE': mae,
        'R2': r2,
        'MEDIAN_AE': median_ae,
        'RMSLE': rmsle,
        'WMAPE_%': wmape,
        'Revenue_Error_%': revenue_error_pct,
        'Prediction_Actual_Ratio': prediction_actual_ratio,
        'Spearman_Rank_Correlation': spearman_rank_corr,
        'Actual_Total_Revenue': total_actual,
        'Predicted_Total_Revenue': total_predicted
    }

# FUNCTION FOR PRINTING METRICS
def print_metrics(metrics, prefix=""):

    print(f"{prefix}MSE: {metrics['MSE']:.4f}")

    print(f"{prefix}RMSE: {metrics['RMSE']:.4f}")

    print(f"{prefix}MAE: {metrics['MAE']:.4f}")

    print(f"{prefix}R2: {metrics['R2']:.4f}")

    print(f"{prefix}MEDIAN_AE: {metrics['MEDIAN_AE']:.4f}")

    print(f"{prefix}RMSLE: {metrics['RMSLE']:.4f}")

    print(f"{prefix}WMAPE %: {metrics['WMAPE_%']:.2f}")

    print(f"{prefix}Revenue Error %: {metrics['Revenue_Error_%']:.2f}")

    print(f"{prefix}Prediction / Actual Ratio: {metrics['Prediction_Actual_Ratio']:.4f}")

    print(f"{prefix}Spearman Rank Correlation: {metrics['Spearman_Rank_Correlation']:.4f}")


# FUNCTION FOR CREATING CLV DIAGNOSTIC DATAFRAME
def create_clv_diagnostic_df(y_true, y_pred):

    y_pred = np.maximum(
        0,
        y_pred
    )

    diagnostic_df = pd.DataFrame({
        'Actual': np.array(y_true),
        'Predicted': np.array(y_pred)
    })

    diagnostic_df['Residual'] = (
        diagnostic_df['Actual'] -
        diagnostic_df['Predicted']
    )

    diagnostic_df['AbsResidual'] = (
        diagnostic_df['Residual']
        .abs()
    )

    diagnostic_df['LogActual'] = np.log1p(
        diagnostic_df['Actual']
    )

    diagnostic_df['LogPredicted'] = np.log1p(
        diagnostic_df['Predicted']
    )

    diagnostic_df['LogResidual'] = (
        diagnostic_df['LogActual'] -
        diagnostic_df['LogPredicted']
    )

    diagnostic_df['ActualZeroFlag'] = (
        diagnostic_df['Actual'] == 0
    ).astype(int)

    return diagnostic_df


# FUNCTION FOR RESIDUAL PLOTS
def plot_clv_residuals(y_true, y_pred, model_name="Calibrated XGBoost Tweedie"):

    diagnostic_df = create_clv_diagnostic_df(
        y_true,
        y_pred
    )

    print("\n--- CLV RESIDUAL SUMMARY ---")

    print(
        diagnostic_df[
            [
                'Actual',
                'Predicted',
                'Residual',
                'AbsResidual',
                'LogResidual'
            ]
        ].describe()
    )

    print("\n--- TOP 10 UNDERPREDICTED CUSTOMERS ---")

    print(
        diagnostic_df
        .sort_values(
            by='Residual',
            ascending=False
        )
        .head(10)
    )

    print("\n--- TOP 10 OVERPREDICTED CUSTOMERS ---")

    print(
        diagnostic_df
        .sort_values(
            by='Residual',
            ascending=True
        )
        .head(10)
    )

    # ACTUAL VS PREDICTED ON ORIGINAL SCALE
    plt.figure(figsize=(8, 6))

    plt.scatter(
        diagnostic_df['Actual'],
        diagnostic_df['Predicted'],
        alpha=0.6
    )

    max_value = max(
        diagnostic_df['Actual'].max(),
        diagnostic_df['Predicted'].max()
    )

    plt.plot(
        [0, max_value],
        [0, max_value],
        linestyle='--'
    )

    plt.title(
        f'Actual vs Predicted CLV - {model_name}'
    )

    plt.xlabel('Actual Future Spend')

    plt.ylabel('Predicted Future Spend')

    plt.tight_layout()

    plt.savefig(
        os.path.join(PLOT_DIR, "01_actual_vs_predicted_clv.png"),
        dpi=300,
        bbox_inches='tight'
    )

    plt.show()

    plt.close()


    # ACTUAL VS PREDICTED ON LOG SCALE
    plt.figure(figsize=(8, 6))

    plt.scatter(
        diagnostic_df['LogActual'],
        diagnostic_df['LogPredicted'],
        alpha=0.6
    )

    max_log_value = max(
        diagnostic_df['LogActual'].max(),
        diagnostic_df['LogPredicted'].max()
    )

    plt.plot(
        [0, max_log_value],
        [0, max_log_value],
        linestyle='--'
    )

    plt.title(
        f'Log Actual vs Log Predicted CLV - {model_name}'
    )

    plt.xlabel('log1p(Actual Future Spend)')

    plt.ylabel('log1p(Predicted Future Spend)')

    plt.tight_layout()

    plt.savefig(
        os.path.join(PLOT_DIR, "02_log_actual_vs_log_predicted_clv.png"),
        dpi=300,
        bbox_inches='tight'
    )

    plt.show()

    plt.close()


    # RESIDUALS VS PREDICTED
    plt.figure(figsize=(8, 6))

    plt.scatter(
        diagnostic_df['Predicted'],
        diagnostic_df['Residual'],
        alpha=0.6
    )

    plt.axhline(
        0,
        linestyle='--'
    )

    plt.title(
        f'Residuals vs Predicted CLV - {model_name}'
    )

    plt.xlabel('Predicted Future Spend')

    plt.ylabel('Residual = Actual - Predicted')

    plt.tight_layout()

    plt.savefig(
        os.path.join(PLOT_DIR, "03_residuals_vs_predicted_clv.png"),
        dpi=300,
        bbox_inches='tight'
    )

    plt.show()

    plt.close()


    # RESIDUAL DISTRIBUTION
    plt.figure(figsize=(8, 6))

    plt.hist(
        diagnostic_df['Residual'],
        bins=80
    )

    plt.axvline(
        0,
        linestyle='--'
    )

    plt.title(
        f'Residual Distribution - {model_name}'
    )

    plt.xlabel('Residual = Actual - Predicted')

    plt.ylabel('Customer Count')

    plt.tight_layout()

    plt.savefig(
        os.path.join(PLOT_DIR, "04_residual_distribution.png"),
        dpi=300,
        bbox_inches='tight'
    )

    plt.show()

    plt.close()


    # LOG RESIDUAL DISTRIBUTION
    plt.figure(figsize=(8, 6))

    plt.hist(
        diagnostic_df['LogResidual'],
        bins=80
    )

    plt.axvline(
        0,
        linestyle='--'
    )

    plt.title(
        f'Log Residual Distribution - {model_name}'
    )

    plt.xlabel('Log Residual = log1p(Actual) - log1p(Predicted)')

    plt.ylabel('Customer Count')

    plt.tight_layout()

    plt.savefig(
        os.path.join(PLOT_DIR, "05_log_residual_distribution.png"),
        dpi=300,
        bbox_inches='tight'
    )

    plt.show()

    plt.close()

    return diagnostic_df


# FUNCTION FOR ERROR BY ACTUAL CLV DECILE
def plot_error_by_actual_decile(diagnostic_df, model_name="Calibrated XGBoost Tweedie"):

    decile_df = diagnostic_df.copy()

    decile_df['ActualDecile'] = pd.qcut(
        decile_df['Actual'].rank(method='first'),
        q=10,
        labels=False
    ) + 1

    decile_error = (
        decile_df
        .groupby('ActualDecile')
        .agg(
            Count=('Actual', 'count'),
            MeanActual=('Actual', 'mean'),
            MeanPredicted=('Predicted', 'mean'),
            ActualRevenue=('Actual', 'sum'),
            PredictedRevenue=('Predicted', 'sum'),
            MAE=('AbsResidual', 'mean'),
            MedianAE=('AbsResidual', 'median')
        )
        .reset_index()
    )

    decile_error['RevenueError_%'] = (
        abs(
            decile_error['ActualRevenue'] -
            decile_error['PredictedRevenue']
        ) /
        decile_error['ActualRevenue'].replace(0, np.nan)
    ) * 100

    print("\n--- ERROR BY ACTUAL CLV DECILE ---")

    print(decile_error)

    plt.figure(figsize=(9, 6))

    plt.bar(
        decile_error['ActualDecile'],
        decile_error['MAE']
    )

    plt.title(
        f'MAE by Actual CLV Decile - {model_name}'
    )

    plt.xlabel('Actual CLV Decile')

    plt.ylabel('Mean Absolute Error')

    plt.tight_layout()

    plt.savefig(
        os.path.join(PLOT_DIR, "06_mae_by_actual_clv_decile.png"),
        dpi=300,
        bbox_inches='tight'
    )

    plt.show()

    plt.close()


    plt.figure(figsize=(9, 6))

    plt.plot(
        decile_error['ActualDecile'],
        decile_error['ActualRevenue'],
        marker='o',
        label='Actual Revenue'
    )

    plt.plot(
        decile_error['ActualDecile'],
        decile_error['PredictedRevenue'],
        marker='o',
        label='Predicted Revenue'
    )

    plt.title(
        f'Actual vs Predicted Revenue by Actual CLV Decile - {model_name}'
    )

    plt.xlabel('Actual CLV Decile')

    plt.ylabel('Revenue')

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        os.path.join(PLOT_DIR, "07_revenue_by_actual_clv_decile.png"),
        dpi=300,
        bbox_inches='tight'
    )

    plt.show()

    plt.close()

    return decile_error


# FUNCTION FOR PREDICTED DECILE CALIBRATION
def plot_predicted_decile_calibration(diagnostic_df, model_name="Calibrated XGBoost Tweedie"):

    calibration_df = diagnostic_df.copy()

    calibration_df['PredictedDecile'] = pd.qcut(
        calibration_df['Predicted'].rank(method='first'),
        q=10,
        labels=False
    ) + 1

    decile_calibration = (
        calibration_df
        .groupby('PredictedDecile')
        .agg(
            Count=('Actual', 'count'),
            MeanActual=('Actual', 'mean'),
            MeanPredicted=('Predicted', 'mean'),
            ActualRevenue=('Actual', 'sum'),
            PredictedRevenue=('Predicted', 'sum')
        )
        .reset_index()
    )

    decile_calibration['RevenueError_%'] = (
        abs(
            decile_calibration['ActualRevenue'] -
            decile_calibration['PredictedRevenue']
        ) /
        decile_calibration['ActualRevenue'].replace(0, np.nan)
    ) * 100

    print("\n--- PREDICTED DECILE CALIBRATION ---")

    print(decile_calibration)

    plt.figure(figsize=(9, 6))

    plt.plot(
        decile_calibration['PredictedDecile'],
        decile_calibration['MeanActual'],
        marker='o',
        label='Mean Actual CLV'
    )

    plt.plot(
        decile_calibration['PredictedDecile'],
        decile_calibration['MeanPredicted'],
        marker='o',
        label='Mean Predicted CLV'
    )

    plt.title(
        f'Mean Actual vs Predicted CLV by Predicted Decile - {model_name}'
    )

    plt.xlabel('Predicted CLV Decile')

    plt.ylabel('Mean CLV')

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        os.path.join(PLOT_DIR, "08_mean_clv_by_predicted_decile.png"),
        dpi=300,
        bbox_inches='tight'
    )

    plt.show()

    plt.close()


    plt.figure(figsize=(9, 6))

    plt.bar(
        decile_calibration['PredictedDecile'],
        decile_calibration['ActualRevenue']
    )

    plt.title(
        f'Actual Revenue Captured by Predicted CLV Decile - {model_name}'
    )

    plt.xlabel('Predicted CLV Decile')

    plt.ylabel('Actual Revenue')

    plt.tight_layout()

    plt.savefig(
        os.path.join(PLOT_DIR, "09_actual_revenue_by_predicted_decile.png"),
        dpi=300,
        bbox_inches='tight'
    )

    plt.show()

    plt.close()

    return decile_calibration


# FUNCTION FOR CLV LIFT TABLE AND PLOT
def plot_clv_lift(diagnostic_df, model_name="Calibrated XGBoost Tweedie"):

    lift_df = diagnostic_df.copy()

    lift_df = lift_df.sort_values(
        by='Predicted',
        ascending=False
    )

    total_revenue = lift_df['Actual'].sum()

    rows = []

    for pct in [0.05, 0.10, 0.20, 0.30, 0.50]:

        customer_count = int(
            len(lift_df) * pct
        )

        top_customers = lift_df.head(
            customer_count
        )

        captured_revenue = top_customers['Actual'].sum()

        revenue_capture_pct = (
            captured_revenue /
            total_revenue
        ) * 100

        lift_vs_random = (
            revenue_capture_pct /
            (pct * 100)
        )

        rows.append({
            'TopCustomer_%': pct * 100,
            'CustomerCount': customer_count,
            'ActualRevenueCaptured': captured_revenue,
            'RevenueCapture_%': revenue_capture_pct,
            'LiftVsRandom': lift_vs_random
        })

    lift_table = pd.DataFrame(rows)

    print("\n--- CLV LIFT TABLE ---")

    print(lift_table)

    plt.figure(figsize=(8, 6))

    plt.plot(
        lift_table['TopCustomer_%'],
        lift_table['RevenueCapture_%'],
        marker='o',
        label='Model'
    )

    plt.plot(
        [0, 50],
        [0, 50],
        linestyle='--',
        label='Random Baseline'
    )

    plt.title(
        f'Revenue Capture by Top Predicted Customers - {model_name}'
    )

    plt.xlabel('Top Predicted Customers (%)')

    plt.ylabel('Actual Revenue Captured (%)')

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        os.path.join(PLOT_DIR, "10_revenue_capture_by_top_customers.png"),
        dpi=300,
        bbox_inches='tight'
    )

    plt.show()

    plt.close()


    plt.figure(figsize=(8, 6))

    plt.bar(
        lift_table['TopCustomer_%'].astype(str),
        lift_table['LiftVsRandom']
    )

    plt.title(
        f'CLV Lift vs Random Selection - {model_name}'
    )

    plt.xlabel('Top Predicted Customer Group (%)')

    plt.ylabel('Lift vs Random')

    plt.tight_layout()

    plt.savefig(
        os.path.join(PLOT_DIR, "11_clv_lift_vs_random.png"),
        dpi=300,
        bbox_inches='tight'
    )

    plt.show()

    plt.close()

    return lift_table


# FUNCTION FOR ZERO-SPENDER DIAGNOSTICS
def plot_zero_spender_diagnostics(diagnostic_df, model_name="Calibrated XGBoost Tweedie"):

    zero_customers = diagnostic_df[
        diagnostic_df['Actual'] == 0
    ]

    positive_customers = diagnostic_df[
        diagnostic_df['Actual'] > 0
    ]

    total_predicted_revenue = diagnostic_df['Predicted'].sum()

    zero_predicted_revenue = zero_customers['Predicted'].sum()

    if total_predicted_revenue != 0:

        zero_predicted_share = (
            zero_predicted_revenue /
            total_predicted_revenue
        ) * 100

    else:

        zero_predicted_share = np.nan

    print("\n--- ZERO-SPENDER DIAGNOSTICS ---")

    print("Zero-spender count:", len(zero_customers))

    print("Positive-spender count:", len(positive_customers))

    print(
        "Average predicted CLV for zero-spenders:",
        zero_customers['Predicted'].mean()
    )

    print(
        "Median predicted CLV for zero-spenders:",
        zero_customers['Predicted'].median()
    )

    print(
        "Total predicted revenue assigned to zero-spenders:",
        zero_predicted_revenue
    )

    print(
        "Share of predicted revenue assigned to zero-spenders:",
        f"{zero_predicted_share:.2f}%"
    )

    plt.figure(figsize=(8, 6))

    plt.hist(
        zero_customers['Predicted'],
        bins=50
    )

    plt.title(
        f'Predicted CLV Distribution for Actual Zero-Spenders - {model_name}'
    )

    plt.xlabel('Predicted CLV')

    plt.ylabel('Zero-Spender Count')

    plt.tight_layout()

    plt.savefig(
        os.path.join(PLOT_DIR, "12_zero_spender_predicted_clv_distribution.png"),
        dpi=300,
        bbox_inches='tight'
    )

    plt.show()

    plt.close()

    return zero_customers


# LOADING CLEANED MASTER DATASET
df = preprocess_online_retail(
    file_path="online_retail_II.xlsx",
    verbose=False
)

# BUILDING CUSTOMER CLV DATASET
clv_df = build_retention_dataset(
    df,
    cutoff_date='2011-09-09',
    prediction_days=90,
    active_days=180,
    verbose=True
)

# HANDLING AvgGapDays MISSING VALUES
clv_df['AvgGapDays'] = (
    clv_df['AvgGapDays']
    .fillna(999)
)

# CORRECT CLV TARGET SUMMARY
print("\nCorrect CLV Target Summary:")

print(
    "Total customers:",
    len(clv_df)
)

print(
    "Customers with future spend > 0:",
    (clv_df['FutureSpend90Days'] > 0).sum()
)

print(
    "Customers with future spend = 0:",
    (clv_df['FutureSpend90Days'] == 0).sum()
)

print(
    "Average future spend:",
    f"{clv_df['FutureSpend90Days'].mean():.2f}"
)

# SPLITTING FEATURES AND TARGET
X = clv_df.drop(
    columns=[
        'Customer_ID',
        'FutureSpend90Days'
    ],
    errors='ignore'
)

# TARGET LABELS WITHOUT LOG TRANSFORM FOR TWEEDIE
y = clv_df['FutureSpend90Days']

# CREATING CLASSIFICATION LABEL ONLY FOR STRATIFICATION
y_class = (
    y > 0
).astype(int)

# TRAIN TEST SPLIT
X_train, X_test, y_train, y_test, y_class_train, y_class_test = train_test_split(
    X,
    y,
    y_class,
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

# DEFINING MODELS WITH TWEEDIE OBJECTIVE
models = {
    'XGBoost_Tweedie': XGBRegressor(
        objective='reg:tweedie',
        eval_metric='tweedie-nloglik@1.5',
        tweedie_variance_power=1.5,
        tree_method='hist',
        random_state=42,
        n_jobs=1
    ),
    'LGBM_Tweedie': LGBMRegressor(
        objective='tweedie',
        tweedie_variance_power=1.5,
        random_state=42,
        verbose=-1
    )
}

# DEFINING RANDOM SEARCH PARAMETER GRIDS
param_grids = {
    'XGBoost_Tweedie': {
        'model__n_estimators': [100, 200, 500, 1000],
        'model__max_depth': [2, 3, 4, 5],
        'model__learning_rate': [0.01, 0.03, 0.05, 0.1],
        'model__subsample': [0.6, 0.8, 1.0],
        'model__colsample_bytree': [0.6, 0.8, 1.0],
        'model__min_child_weight': [1, 3, 5, 7],
        'model__reg_alpha': [0, 0.01, 0.1],
        'model__reg_lambda': [1, 2, 5, 10],
        'model__tweedie_variance_power': [1.1, 1.3, 1.5, 1.7, 1.9]
    },
    'LGBM_Tweedie': {
        'model__n_estimators': [100, 200, 500, 1000],
        'model__learning_rate': [0.01, 0.03, 0.05, 0.1],
        'model__max_depth': [3, 5, 7, -1],
        'model__num_leaves': [15, 31, 63],
        'model__subsample': [0.6, 0.8, 1.0],
        'model__colsample_bytree': [0.6, 0.8, 1.0],
        'model__min_child_samples': [10, 20, 50],
        'model__reg_alpha': [0, 0.01, 0.1, 1],
        'model__reg_lambda': [0.1, 1, 5, 10],
        'model__tweedie_variance_power': [1.1, 1.3, 1.5, 1.7, 1.9]
    }
}

# BASELINE MODEL
baseline_pred = np.repeat(
    y_train.mean(),
    len(y_test)
)

baseline_metrics = calculate_regression_metrics(
    y_test,
    baseline_pred
)

print("\n--- BASELINE MODEL ---")

print_metrics(
    baseline_metrics,
    prefix="Baseline "
)


# STORING MODEL RESULTS
results = []
trained_models = {}
final_model_predictions = {}

# ADDING BASELINE TO RESULTS
baseline_result = baseline_metrics.copy()

baseline_result['Model'] = 'Baseline_Mean'

baseline_result['Version'] = 'Baseline'

baseline_result['Calibration_Factor'] = 1.0

results.append(
    baseline_result
)


# TRAINING AND EVALUATING MODELS
for model_name, model in models.items():

    print(f"\nTraining {model_name}...")

    pipeline = Pipeline([
        ('preprocessing', preprocessor),
        ('model', model)
    ])

    random_search = RandomizedSearchCV(
        estimator=pipeline,
        param_distributions=param_grids[model_name],
        n_iter=100,
        cv=5,
        scoring='neg_root_mean_squared_error',
        random_state=42,
        n_jobs=-1
    )

    random_search.fit(
        X_train,
        y_train
    )

    best_model = random_search.best_estimator_

    trained_models[model_name] = best_model

    # PREDICTING RAW FUTURE SPEND
    y_train_pred = best_model.predict(
        X_train
    )

    y_pred = best_model.predict(
        X_test
    )

    # CLIPPING NEGATIVE PREDICTIONS
    y_train_pred = np.maximum(
        0,
        y_train_pred
    )

    y_pred = np.maximum(
        0,
        y_pred
    )

    # CALIBRATION FACTOR USING TRAINING DATA ONLY
    if y_train_pred.sum() != 0:

        calibration_factor = (
            y_train.sum() /
            y_train_pred.sum()
        )

    else:

        calibration_factor = 1.0

    # CALIBRATED TEST PREDICTIONS
    y_pred_calibrated = (
        y_pred *
        calibration_factor
    )

    y_pred_calibrated = np.maximum(
        0,
        y_pred_calibrated
    )

    # UNCALIBRATED METRICS
    uncalibrated_metrics = calculate_regression_metrics(
        y_test,
        y_pred
    )

    # CALIBRATED METRICS
    calibrated_metrics = calculate_regression_metrics(
        y_test,
        y_pred_calibrated
    )

    print(f"Best Params: {random_search.best_params_}")

    print("\nUncalibrated:")

    print_metrics(
        uncalibrated_metrics
    )

    print("\nCalibrated:")

    print(f"Calibration Factor: {calibration_factor:.4f}")

    print_metrics(
        calibrated_metrics
    )

    print("\nRevenue Totals:")

    print(f"Actual test revenue: {y_test.sum():.2f}")

    print(f"Predicted test revenue: {y_pred.sum():.2f}")

    print(f"Calibrated predicted test revenue: {y_pred_calibrated.sum():.2f}")

    print(f"Prediction / Actual ratio: {y_pred.sum() / y_test.sum():.4f}")

    print(f"Calibrated Prediction / Actual ratio: {y_pred_calibrated.sum() / y_test.sum():.4f}")

    # STORING XGBOOST TWEEDIE PREDICTIONS FOR FINAL DIAGNOSTIC PLOTS
    if model_name == 'XGBoost_Tweedie':

        final_model_predictions['model_name'] = model_name

        final_model_predictions['y_test'] = y_test.copy()

        final_model_predictions['y_pred_uncalibrated'] = y_pred.copy()

        final_model_predictions['y_pred_calibrated'] = y_pred_calibrated.copy()

        final_model_predictions['best_model'] = best_model

        final_model_predictions['best_params'] = random_search.best_params_

        final_model_predictions['calibration_factor'] = calibration_factor

    # APPENDING UNCALIBRATED RESULTS
    uncalibrated_result = uncalibrated_metrics.copy()

    uncalibrated_result['Model'] = model_name

    uncalibrated_result['Version'] = 'Uncalibrated'

    uncalibrated_result['Calibration_Factor'] = 1.0

    results.append(
        uncalibrated_result
    )

    # APPENDING CALIBRATED RESULTS
    calibrated_result = calibrated_metrics.copy()

    calibrated_result['Model'] = model_name

    calibrated_result['Version'] = 'Calibrated'

    calibrated_result['Calibration_Factor'] = calibration_factor

    results.append(
        calibrated_result
    )


# FINAL MODEL COMPARISON TABLE
results_df = pd.DataFrame(
    results
)

results_df = results_df[
    [
        'Model',
        'Version',
        'MSE',
        'RMSE',
        'MAE',
        'R2',
        'MEDIAN_AE',
        'RMSLE',
        'WMAPE_%',
        'Revenue_Error_%',
        'Prediction_Actual_Ratio',
        'Spearman_Rank_Correlation',
        'Actual_Total_Revenue',
        'Predicted_Total_Revenue',
        'Calibration_Factor'
    ]
]

results_df = results_df.sort_values(
    by='RMSE',
    ascending=True
)

print("\nFinal Model Comparison:\n")

print(results_df)

results_df.to_csv(
    os.path.join(TABLE_DIR, "clv_model_comparison.csv"),
    index=False
)


# CHECKING FINAL MODEL STORAGE
if len(final_model_predictions) == 0:

    raise ValueError(
        "XGBoost_Tweedie predictions were not stored. Check model_name inside models dictionary."
    )


# RUNNING ALL FINAL CLV DIAGNOSTIC PLOTS FOR XGBOOST TWEEDIE
print("\n--- RUNNING FINAL CLV DIAGNOSTIC PLOTS ---")

print("\n--- FINAL MODEL USED FOR PLOTS ---")

print("Model:", final_model_predictions['model_name'])

print("Best Params:", final_model_predictions['best_params'])

print("Calibration Factor:", final_model_predictions['calibration_factor'])


final_y_test = final_model_predictions['y_test']

final_y_pred = final_model_predictions['y_pred_calibrated']

diagnostic_df = plot_clv_residuals(
    final_y_test,
    final_y_pred,
    model_name="Calibrated XGBoost Tweedie"
)

decile_error = plot_error_by_actual_decile(
    diagnostic_df,
    model_name="Calibrated XGBoost Tweedie"
)

decile_calibration = plot_predicted_decile_calibration(
    diagnostic_df,
    model_name="Calibrated XGBoost Tweedie"
)

lift_table = plot_clv_lift(
    diagnostic_df,
    model_name="Calibrated XGBoost Tweedie"
)

zero_customers = plot_zero_spender_diagnostics(
    diagnostic_df,
    model_name="Calibrated XGBoost Tweedie"
)


# SAVING DIAGNOSTIC TABLES FOR FRONTEND
diagnostic_df.to_csv(
    os.path.join(TABLE_DIR, "clv_residual_diagnostics.csv"),
    index=False
)

decile_error.to_csv(
    os.path.join(TABLE_DIR, "clv_error_by_actual_decile.csv"),
    index=False
)

decile_calibration.to_csv(
    os.path.join(TABLE_DIR, "clv_predicted_decile_calibration.csv"),
    index=False
)

lift_table.to_csv(
    os.path.join(TABLE_DIR, "clv_lift_table.csv"),
    index=False
)

zero_customers.to_csv(
    os.path.join(TABLE_DIR, "clv_zero_spender_diagnostics.csv"),
    index=False
)

print("\nSaved CLV diagnostic tables:")

print(os.path.join(TABLE_DIR, "clv_model_comparison.csv"))

print(os.path.join(TABLE_DIR, "clv_residual_diagnostics.csv"))

print(os.path.join(TABLE_DIR, "clv_error_by_actual_decile.csv"))

print(os.path.join(TABLE_DIR, "clv_predicted_decile_calibration.csv"))

print(os.path.join(TABLE_DIR, "clv_lift_table.csv"))

print(os.path.join(TABLE_DIR, "clv_zero_spender_diagnostics.csv"))

print("\nSaved CLV diagnostic plots in folder:")

print(PLOT_DIR)