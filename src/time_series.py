import os
import json
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    root_mean_squared_error,
    r2_score
)

from sklearn.ensemble import RandomForestRegressor

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

from statsmodels.tsa.holtwinters import (
    SimpleExpSmoothing,
    Holt,
    ExponentialSmoothing
)

from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.seasonal import seasonal_decompose

from preprocessing import preprocess_online_retail


warnings.filterwarnings("ignore")


# OUTPUT FOLDERS
OUTPUT_DIR = "time_series_outputs"
PLOT_DIR = "time_series_plots"
FRONTEND_DATA_DIR = "time_series_frontend_data"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PLOT_DIR, exist_ok=True)
os.makedirs(FRONTEND_DATA_DIR, exist_ok=True)


# SETTINGS
TEST_HORIZON = 12
FUTURE_HORIZON = 12
WEEKLY_FREQ = "W-SUN"
MONTHLY_FREQ = "MS"

NON_PRODUCT_CODES = [
    "POST",
    "DOT",
    "BANK CHARGES",
    "AMAZONFEE",
    "MANUAL",
    "CRUK"
]


# BASIC HELPERS
def detect_column(df, possible_names):

    for name in possible_names:

        if name in df.columns:

            return name

    raise ValueError(
        f"None of these columns were found: {possible_names}"
    )


def smape(y_true, y_pred):

    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    denominator = np.abs(y_true) + np.abs(y_pred)

    valid_mask = denominator != 0

    if valid_mask.sum() == 0:

        return np.nan

    return (
        np.mean(
            2 * np.abs(y_pred[valid_mask] - y_true[valid_mask]) /
            denominator[valid_mask]
        ) * 100
    )


def wape(y_true, y_pred):

    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    total_actual = np.sum(
        np.abs(y_true)
    )

    if total_actual == 0:

        return np.nan

    return (
        np.sum(
            np.abs(y_true - y_pred)
        ) / total_actual
    ) * 100


def clean_forecast_array(forecast, horizon=None):

    forecast_array = np.asarray(
        forecast
    ).reshape(-1)

    forecast_array = pd.Series(
        forecast_array
    ).replace(
        [np.inf, -np.inf],
        np.nan
    ).fillna(0).values

    forecast_array = np.maximum(
        0,
        forecast_array
    )

    if horizon is not None:

        forecast_array = forecast_array[:horizon]

        if len(forecast_array) < horizon:

            pad_length = horizon - len(forecast_array)

            forecast_array = np.concatenate(
                [
                    forecast_array,
                    np.repeat(
                        forecast_array[-1] if len(forecast_array) > 0 else 0,
                        pad_length
                    )
                ]
            )

    return forecast_array


def calculate_forecast_metrics(y_true, y_pred):

    y_true = np.asarray(y_true).reshape(-1)
    y_pred = clean_forecast_array(y_pred, horizon=len(y_true))

    return {
        "RMSE": root_mean_squared_error(
            y_true,
            y_pred
        ),
        "MAE": mean_absolute_error(
            y_true,
            y_pred
        ),
        "MSE": mean_squared_error(
            y_true,
            y_pred
        ),
        "R2": r2_score(
            y_true,
            y_pred
        ),
        "WAPE_%": wape(
            y_true,
            y_pred
        ),
        "sMAPE_%": smape(
            y_true,
            y_pred
        ),
        "Actual_Total": y_true.sum(),
        "Predicted_Total": y_pred.sum(),
        "Revenue_Error_%": (
            abs(y_true.sum() - y_pred.sum()) /
            y_true.sum()
        ) * 100
        if y_true.sum() != 0
        else np.nan
    }


def print_metrics(model_name, metrics):

    print(f"\n{model_name}")

    print(f"RMSE: {metrics['RMSE']:.4f}")

    print(f"MAE: {metrics['MAE']:.4f}")

    print(f"R2: {metrics['R2']:.4f}")

    print(f"WAPE %: {metrics['WAPE_%']:.2f}")

    print(f"sMAPE %: {metrics['sMAPE_%']:.2f}")

    print(f"Revenue Error %: {metrics['Revenue_Error_%']:.2f}")


def safe_exp_forecast(log_forecast):

    forecast = np.expm1(
        np.asarray(log_forecast)
    )

    forecast = clean_forecast_array(
        forecast
    )

    return forecast


# TRANSACTION FILTERING
def create_purchase_dataset(df):

    data = df.copy()

    invoice_col = detect_column(
        data,
        [
            "Invoice",
            "InvoiceNo",
            "Invoice_No"
        ]
    )

    date_col = detect_column(
        data,
        [
            "InvoiceDate",
            "Invoice_Date",
            "Date"
        ]
    )

    quantity_col = detect_column(
        data,
        [
            "Quantity"
        ]
    )

    price_col = detect_column(
        data,
        [
            "Price",
            "UnitPrice",
            "Unit_Price"
        ]
    )

    stock_col = detect_column(
        data,
        [
            "StockCode",
            "Stock_Code"
        ]
    )

    customer_col = detect_column(
        data,
        [
            "Customer_ID",
            "CustomerID",
            "Customer ID"
        ]
    )

    data[date_col] = pd.to_datetime(
        data[date_col]
    )

    if "TransactionValue" not in data.columns:

        data["TransactionValue"] = (
            data[quantity_col] *
            data[price_col]
        )

    if "IsCancelled" not in data.columns:

        data["IsCancelled"] = (
            data[invoice_col]
            .astype(str)
            .str.startswith("C")
        )

    if "IsReturn" not in data.columns:

        data["IsReturn"] = (
            data[quantity_col] <= 0
        )

    if "IsNonProduct" not in data.columns:

        data["IsNonProduct"] = (
            data[stock_col]
            .astype(str)
            .isin(NON_PRODUCT_CODES)
        )

    purchase_df = data[
        (~data["IsCancelled"]) &
        (~data["IsReturn"]) &
        (~data["IsNonProduct"]) &
        (data[quantity_col] > 0) &
        (data[price_col] > 0) &
        (data["TransactionValue"] > 0) &
        (data[customer_col].notna())
    ].copy()

    return (
        purchase_df,
        invoice_col,
        date_col,
        customer_col
    )


# TIME SERIES AGGREGATION
def build_weekly_monthly_series(purchase_df, invoice_col, date_col, customer_col):

    indexed_df = purchase_df.copy()

    indexed_df = indexed_df.set_index(
        date_col
    )

    weekly_df = (
        indexed_df
        .resample(WEEKLY_FREQ)
        .agg(
            Revenue=("TransactionValue", "sum"),
            OrderCount=(invoice_col, "nunique"),
            UniqueCustomers=(customer_col, "nunique")
        )
        .reset_index()
    )

    weekly_df = weekly_df.rename(
        columns={
            date_col: "Date"
        }
    )

    weekly_df["AvgOrderValue"] = (
        weekly_df["Revenue"] /
        weekly_df["OrderCount"].replace(0, np.nan)
    )

    weekly_df["AvgOrderValue"] = (
        weekly_df["AvgOrderValue"]
        .fillna(0)
    )

    monthly_df = (
        indexed_df
        .resample(MONTHLY_FREQ)
        .agg(
            Revenue=("TransactionValue", "sum"),
            OrderCount=(invoice_col, "nunique"),
            UniqueCustomers=(customer_col, "nunique")
        )
        .reset_index()
    )

    monthly_df = monthly_df.rename(
        columns={
            date_col: "Date"
        }
    )

    monthly_df["AvgOrderValue"] = (
        monthly_df["Revenue"] /
        monthly_df["OrderCount"].replace(0, np.nan)
    )

    monthly_df["AvgOrderValue"] = (
        monthly_df["AvgOrderValue"]
        .fillna(0)
    )

    return weekly_df, monthly_df


# BASELINE FORECASTS
def naive_forecast(train_values, horizon):

    last_value = train_values.iloc[-1]

    return clean_forecast_array(
        np.repeat(
            last_value,
            horizon
        ),
        horizon
    )


def moving_average_forecast(train_values, horizon, window):

    mean_value = (
        train_values
        .tail(window)
        .mean()
    )

    return clean_forecast_array(
        np.repeat(
            mean_value,
            horizon
        ),
        horizon
    )


# EXPONENTIAL SMOOTHING FORECASTS
def ses_forecast(train_values, horizon):

    log_train = np.log1p(
        train_values
    )

    model = SimpleExpSmoothing(
        log_train,
        initialization_method="estimated"
    )

    fitted_model = model.fit(
        optimized=True
    )

    forecast_log = fitted_model.forecast(
        horizon
    )

    return clean_forecast_array(
        safe_exp_forecast(forecast_log),
        horizon
    )


def holt_forecast(train_values, horizon):

    log_train = np.log1p(
        train_values
    )

    model = Holt(
        log_train,
        initialization_method="estimated"
    )

    fitted_model = model.fit(
        optimized=True
    )

    forecast_log = fitted_model.forecast(
        horizon
    )

    return clean_forecast_array(
        safe_exp_forecast(forecast_log),
        horizon
    )


def holt_winters_forecast(train_values, horizon, seasonal_periods=4):

    log_train = np.log1p(
        train_values
    )

    model = ExponentialSmoothing(
        log_train,
        trend="add",
        seasonal="add",
        seasonal_periods=seasonal_periods,
        initialization_method="estimated"
    )

    fitted_model = model.fit(
        optimized=True
    )

    forecast_log = fitted_model.forecast(
        horizon
    )

    return clean_forecast_array(
        safe_exp_forecast(forecast_log),
        horizon
    )


# ARIMA / SARIMA SEARCH
def arima_grid_search(train_values, test_values):

    best_result = None

    log_train = np.log1p(
        np.asarray(train_values)
    )

    orders = [
        (0, 1, 1),
        (1, 1, 0),
        (1, 1, 1),
        (2, 1, 1),
        (1, 1, 2),
        (2, 1, 2),
        (1, 0, 1),
        (2, 0, 2)
    ]

    for order in orders:

        try:

            model = ARIMA(
                log_train,
                order=order
            )

            fitted_model = model.fit()

            forecast_log = fitted_model.forecast(
                steps=len(test_values)
            )

            forecast = clean_forecast_array(
                safe_exp_forecast(forecast_log),
                len(test_values)
            )

            metrics = calculate_forecast_metrics(
                test_values,
                forecast
            )

            result = {
                "order": order,
                "forecast": forecast,
                "metrics": metrics,
                "aic": fitted_model.aic
            }

            if (
                best_result is None or
                metrics["RMSE"] < best_result["metrics"]["RMSE"]
            ):

                best_result = result

        except Exception:

            continue

    return best_result


def sarima_grid_search(train_values, test_values):

    best_result = None

    log_train = np.log1p(
        np.asarray(train_values)
    )

    orders = [
        (0, 1, 1),
        (1, 1, 0),
        (1, 1, 1),
        (2, 1, 1)
    ]

    seasonal_orders = [
        (0, 1, 1, 4),
        (1, 1, 0, 4),
        (1, 1, 1, 4),
        (0, 1, 1, 13),
        (1, 1, 0, 13),
        (1, 1, 1, 13)
    ]

    for order in orders:

        for seasonal_order in seasonal_orders:

            try:

                model = SARIMAX(
                    log_train,
                    order=order,
                    seasonal_order=seasonal_order,
                    enforce_stationarity=False,
                    enforce_invertibility=False
                )

                fitted_model = model.fit(
                    disp=False
                )

                forecast_log = fitted_model.forecast(
                    steps=len(test_values)
                )

                forecast = clean_forecast_array(
                    safe_exp_forecast(forecast_log),
                    len(test_values)
                )

                metrics = calculate_forecast_metrics(
                    test_values,
                    forecast
                )

                result = {
                    "order": order,
                    "seasonal_order": seasonal_order,
                    "forecast": forecast,
                    "metrics": metrics,
                    "aic": fitted_model.aic
                }

                if (
                    best_result is None or
                    metrics["RMSE"] < best_result["metrics"]["RMSE"]
                ):

                    best_result = result

            except Exception:

                continue

    return best_result


# LAG FEATURE MODEL
def create_lag_feature_dataset(weekly_df):

    lag_df = weekly_df.copy()

    lag_df = lag_df.sort_values(
        by="Date"
    )

    lag_df["TimeIndex"] = np.arange(
        len(lag_df)
    )

    lag_df["Month"] = (
        lag_df["Date"]
        .dt.month
    )

    lag_df["Quarter"] = (
        lag_df["Date"]
        .dt.quarter
    )

    lag_df["WeekOfYear"] = (
        lag_df["Date"]
        .dt.isocalendar()
        .week
        .astype(int)
    )

    revenue_lags = [
        1,
        2,
        4,
        8,
        12
    ]

    for lag in revenue_lags:

        lag_df[f"Revenue_Lag_{lag}"] = (
            lag_df["Revenue"]
            .shift(lag)
        )

    for window in [
        4,
        8,
        12
    ]:

        lag_df[f"Revenue_RollingMean_{window}"] = (
            lag_df["Revenue"]
            .shift(1)
            .rolling(window)
            .mean()
        )

        lag_df[f"Revenue_RollingStd_{window}"] = (
            lag_df["Revenue"]
            .shift(1)
            .rolling(window)
            .std()
        )

    for lag in [
        1,
        4
    ]:

        lag_df[f"OrderCount_Lag_{lag}"] = (
            lag_df["OrderCount"]
            .shift(lag)
        )

        lag_df[f"UniqueCustomers_Lag_{lag}"] = (
            lag_df["UniqueCustomers"]
            .shift(lag)
        )

        lag_df[f"AvgOrderValue_Lag_{lag}"] = (
            lag_df["AvgOrderValue"]
            .shift(lag)
        )

    lag_df = lag_df.dropna().reset_index(
        drop=True
    )

    return lag_df


def train_lag_models(lag_feature_df, test_start_date):

    feature_columns = [
        col
        for col in lag_feature_df.columns
        if col not in [
            "Date",
            "Revenue",
            "OrderCount",
            "UniqueCustomers",
            "AvgOrderValue"
        ]
    ]

    train_df = lag_feature_df[
        lag_feature_df["Date"] < test_start_date
    ].copy()

    test_df = lag_feature_df[
        lag_feature_df["Date"] >= test_start_date
    ].copy()

    X_train = train_df[
        feature_columns
    ]

    y_train = np.log1p(
        train_df["Revenue"]
    )

    X_test = test_df[
        feature_columns
    ]

    y_test = test_df[
        "Revenue"
    ]

    ml_results = {}

    rf_model = RandomForestRegressor(
        n_estimators=500,
        max_depth=5,
        min_samples_leaf=3,
        random_state=42,
        n_jobs=-1
    )

    rf_model.fit(
        X_train,
        y_train
    )

    rf_pred_log = rf_model.predict(
        X_test
    )

    rf_pred = clean_forecast_array(
        safe_exp_forecast(rf_pred_log),
        len(y_test)
    )

    ml_results["RandomForest_Lag"] = {
        "model": rf_model,
        "forecast": rf_pred,
        "metrics": calculate_forecast_metrics(
            y_test,
            rf_pred
        ),
        "feature_columns": feature_columns
    }

    if XGBOOST_AVAILABLE:

        xgb_model = XGBRegressor(
            objective="reg:squarederror",
            n_estimators=300,
            max_depth=2,
            learning_rate=0.03,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=5,
            random_state=42,
            n_jobs=-1
        )

        xgb_model.fit(
            X_train,
            y_train
        )

        xgb_pred_log = xgb_model.predict(
            X_test
        )

        xgb_pred = clean_forecast_array(
            safe_exp_forecast(xgb_pred_log),
            len(y_test)
        )

        ml_results["XGBoost_Lag"] = {
            "model": xgb_model,
            "forecast": xgb_pred,
            "metrics": calculate_forecast_metrics(
                y_test,
                xgb_pred
            ),
            "feature_columns": feature_columns
        }

    return ml_results, test_df


# FUTURE RECURSIVE FORECAST FOR LAG MODEL
def create_future_lag_features(history_df, future_date, feature_columns):

    temp_df = history_df.copy()

    row = {
        "Date": future_date
    }

    row["TimeIndex"] = len(temp_df)

    row["Month"] = future_date.month

    row["Quarter"] = future_date.quarter

    row["WeekOfYear"] = int(
        future_date.isocalendar().week
    )

    for lag in [
        1,
        2,
        4,
        8,
        12
    ]:

        row[f"Revenue_Lag_{lag}"] = (
            temp_df["Revenue"].iloc[-lag]
            if len(temp_df) >= lag
            else np.nan
        )

    for window in [
        4,
        8,
        12
    ]:

        row[f"Revenue_RollingMean_{window}"] = (
            temp_df["Revenue"]
            .tail(window)
            .mean()
        )

        row[f"Revenue_RollingStd_{window}"] = (
            temp_df["Revenue"]
            .tail(window)
            .std()
        )

    for lag in [
        1,
        4
    ]:

        row[f"OrderCount_Lag_{lag}"] = (
            temp_df["OrderCount"].iloc[-lag]
            if len(temp_df) >= lag
            else np.nan
        )

        row[f"UniqueCustomers_Lag_{lag}"] = (
            temp_df["UniqueCustomers"].iloc[-lag]
            if len(temp_df) >= lag
            else np.nan
        )

        row[f"AvgOrderValue_Lag_{lag}"] = (
            temp_df["AvgOrderValue"].iloc[-lag]
            if len(temp_df) >= lag
            else np.nan
        )

    feature_row = pd.DataFrame(
        [row]
    )

    feature_row = feature_row[
        feature_columns
    ]

    feature_row = feature_row.fillna(
        0
    )

    return feature_row


def recursive_future_ml_forecast(model, weekly_df, feature_columns, horizon):

    history_df = weekly_df.copy()

    history_df = history_df.sort_values(
        by="Date"
    ).reset_index(drop=True)

    future_rows = []

    last_date = history_df["Date"].max()

    future_dates = pd.date_range(
        start=last_date + pd.Timedelta(weeks=1),
        periods=horizon,
        freq=WEEKLY_FREQ
    )

    for future_date in future_dates:

        X_future = create_future_lag_features(
            history_df,
            future_date,
            feature_columns
        )

        pred_log = model.predict(
            X_future
        )

        pred_revenue = float(
            clean_forecast_array(
                safe_exp_forecast(pred_log),
                1
            )[0]
        )

        last_order_count = (
            history_df["OrderCount"]
            .tail(4)
            .mean()
        )

        last_unique_customers = (
            history_df["UniqueCustomers"]
            .tail(4)
            .mean()
        )

        if last_order_count > 0:

            avg_order_value = (
                pred_revenue /
                last_order_count
            )

        else:

            avg_order_value = 0

        new_row = {
            "Date": future_date,
            "Revenue": pred_revenue,
            "OrderCount": last_order_count,
            "UniqueCustomers": last_unique_customers,
            "AvgOrderValue": avg_order_value
        }

        future_rows.append(
            new_row
        )

        history_df = pd.concat(
            [
                history_df,
                pd.DataFrame([new_row])
            ],
            ignore_index=True
        )

    return pd.DataFrame(
        future_rows
    )


# PLOTTING FUNCTIONS
def plot_weekly_revenue(weekly_df):

    plt.figure(figsize=(12, 6))

    plt.plot(
        weekly_df["Date"],
        weekly_df["Revenue"]
    )

    plt.title("Weekly Revenue Trend")

    plt.xlabel("Date")

    plt.ylabel("Weekly Revenue")

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            PLOT_DIR,
            "01_weekly_revenue_trend.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


def plot_monthly_revenue(monthly_df):

    plt.figure(figsize=(12, 6))

    plt.plot(
        monthly_df["Date"],
        monthly_df["Revenue"],
        marker="o"
    )

    plt.title("Monthly Revenue Trend")

    plt.xlabel("Date")

    plt.ylabel("Monthly Revenue")

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            PLOT_DIR,
            "02_monthly_revenue_trend.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


def plot_train_test_forecasts(forecast_df):

    plt.figure(figsize=(12, 6))

    plt.plot(
        forecast_df["Date"],
        forecast_df["Actual"],
        marker="o",
        label="Actual"
    )

    model_columns = [
        col
        for col in forecast_df.columns
        if col not in [
            "Date",
            "Actual"
        ]
    ]

    for col in model_columns:

        plot_df = forecast_df[
            [
                "Date",
                col
            ]
        ].dropna()

        if len(plot_df) == 0:

            continue

        plt.plot(
            plot_df["Date"],
            plot_df[col],
            marker="o",
            label=col
        )

    plt.title("Weekly Revenue Forecast Comparison")

    plt.xlabel("Date")

    plt.ylabel("Weekly Revenue")

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            PLOT_DIR,
            "03_train_test_forecast_comparison.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


def plot_best_model_forecast(forecast_df, best_model_name):

    plot_df = forecast_df[
        [
            "Date",
            "Actual",
            best_model_name
        ]
    ].dropna()

    if len(plot_df) == 0:

        print(
            f"\nSkipping best forecast plot for {best_model_name}: no valid values."
        )

        return

    plt.figure(figsize=(12, 6))

    plt.plot(
        plot_df["Date"],
        plot_df["Actual"],
        marker="o",
        label="Actual"
    )

    plt.plot(
        plot_df["Date"],
        plot_df[best_model_name],
        marker="o",
        label=f"Forecast - {best_model_name}"
    )

    plt.title(f"Best Model Forecast: {best_model_name}")

    plt.xlabel("Date")

    plt.ylabel("Weekly Revenue")

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            PLOT_DIR,
            "04_best_model_test_forecast.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


def plot_model_comparison(metrics_df):

    plot_df = metrics_df.sort_values(
        by="RMSE",
        ascending=True
    )

    plt.figure(figsize=(10, 6))

    plt.barh(
        plot_df["Model"],
        plot_df["RMSE"]
    )

    plt.title("Forecast Model Comparison by RMSE")

    plt.xlabel("RMSE")

    plt.ylabel("Model")

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            PLOT_DIR,
            "05_forecast_model_comparison_rmse.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


def plot_residuals(forecast_df, best_model_name):

    residual_df = forecast_df[
        [
            "Actual",
            best_model_name
        ]
    ].copy()

    residual_df = residual_df.dropna()

    residuals = (
        residual_df["Actual"] -
        residual_df[best_model_name]
    )

    residuals = residuals[
        np.isfinite(residuals)
    ]

    if len(residuals) == 0:

        print(
            f"\nSkipping residual plot for {best_model_name}: no finite residuals found."
        )

        return

    plt.figure(figsize=(8, 6))

    plt.hist(
        residuals,
        bins=20
    )

    plt.axvline(
        0,
        linestyle="--"
    )

    plt.title(f"Forecast Residual Distribution - {best_model_name}")

    plt.xlabel("Residual = Actual - Forecast")

    plt.ylabel("Count")

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            PLOT_DIR,
            "06_forecast_residual_distribution.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


def plot_future_forecast(weekly_df, future_forecast_df, best_model_name):

    recent_history = weekly_df.tail(
        40
    )

    plt.figure(figsize=(12, 6))

    plt.plot(
        recent_history["Date"],
        recent_history["Revenue"],
        marker="o",
        label="Historical Revenue"
    )

    plt.plot(
        future_forecast_df["Date"],
        future_forecast_df["ForecastRevenue"],
        marker="o",
        label=f"Future Forecast - {best_model_name}"
    )

    plt.title("Future 12-Week Revenue Forecast")

    plt.xlabel("Date")

    plt.ylabel("Weekly Revenue")

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            PLOT_DIR,
            "07_future_12_week_forecast.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


def plot_seasonal_decomposition(weekly_df):

    series = weekly_df.set_index(
        "Date"
    )["Revenue"]

    if len(series) >= 104:

        period = 52

    elif len(series) >= 26:

        period = 13

    else:

        print("\nSkipping seasonal decomposition: not enough data.")

        return

    decomposition = seasonal_decompose(
        series,
        model="additive",
        period=period
    )

    fig = decomposition.plot()

    fig.set_size_inches(
        12,
        8
    )

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            PLOT_DIR,
            "08_seasonal_decomposition.png"
        ),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


# MAIN SCRIPT
print("\nLoading cleaned dataset...")

df = preprocess_online_retail(
    file_path="online_retail_II.xlsx",
    verbose=False
)

purchase_df, invoice_col, date_col, customer_col = create_purchase_dataset(
    df
)

print("\nPurchase dataset created.")

print("Purchase rows:", len(purchase_df))

print("Date range:", purchase_df[date_col].min(), "to", purchase_df[date_col].max())

print("Total revenue:", purchase_df["TransactionValue"].sum())


weekly_df, monthly_df = build_weekly_monthly_series(
    purchase_df,
    invoice_col,
    date_col,
    customer_col
)

weekly_df.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "weekly_revenue_series.csv"
    ),
    index=False
)

monthly_df.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "monthly_revenue_series.csv"
    ),
    index=False
)

weekly_df.to_json(
    os.path.join(
        FRONTEND_DATA_DIR,
        "weekly_revenue_series.json"
    ),
    orient="records",
    indent=2,
    date_format="iso"
)

monthly_df.to_json(
    os.path.join(
        FRONTEND_DATA_DIR,
        "monthly_revenue_series.json"
    ),
    orient="records",
    indent=2,
    date_format="iso"
)

print("\nWeekly series shape:", weekly_df.shape)

print("Monthly series shape:", monthly_df.shape)


if len(weekly_df) <= TEST_HORIZON + 20:

    raise ValueError(
        "Not enough weekly data for a 12-week test horizon."
    )


# TRAIN TEST SPLIT
weekly_df = weekly_df.sort_values(
    by="Date"
).reset_index(drop=True)

train_df = weekly_df.iloc[
    :-TEST_HORIZON
].copy()

test_df = weekly_df.iloc[
    -TEST_HORIZON:
].copy()

y_train = train_df["Revenue"]

y_test = test_df["Revenue"]

test_dates = test_df["Date"]


print("\nTime-based split:")

print("Train start:", train_df["Date"].min())

print("Train end:", train_df["Date"].max())

print("Test start:", test_df["Date"].min())

print("Test end:", test_df["Date"].max())


# MODEL FORECASTS
forecast_results = pd.DataFrame({
    "Date": test_dates.values,
    "Actual": y_test.values
})

metrics_rows = []


# NAIVE
naive_pred = naive_forecast(
    y_train,
    TEST_HORIZON
)

forecast_results["Naive"] = clean_forecast_array(
    naive_pred,
    TEST_HORIZON
)

metrics = calculate_forecast_metrics(
    y_test,
    naive_pred
)

metrics["Model"] = "Naive"

metrics_rows.append(
    metrics
)

print_metrics(
    "Naive",
    metrics
)


# MOVING AVERAGES
for window in [
    4,
    8,
    12
]:

    model_name = f"MovingAverage_{window}"

    ma_pred = moving_average_forecast(
        y_train,
        TEST_HORIZON,
        window
    )

    forecast_results[model_name] = clean_forecast_array(
        ma_pred,
        TEST_HORIZON
    )

    metrics = calculate_forecast_metrics(
        y_test,
        ma_pred
    )

    metrics["Model"] = model_name

    metrics_rows.append(
        metrics
    )

    print_metrics(
        model_name,
        metrics
    )


# SIMPLE EXPONENTIAL SMOOTHING
try:

    ses_pred = ses_forecast(
        y_train,
        TEST_HORIZON
    )

    forecast_results["SES"] = clean_forecast_array(
        ses_pred,
        TEST_HORIZON
    )

    metrics = calculate_forecast_metrics(
        y_test,
        ses_pred
    )

    metrics["Model"] = "SES"

    metrics_rows.append(
        metrics
    )

    print_metrics(
        "SES",
        metrics
    )

except Exception as e:

    print("\nSES failed:", e)


# HOLT
try:

    holt_pred = holt_forecast(
        y_train,
        TEST_HORIZON
    )

    forecast_results["Holt"] = clean_forecast_array(
        holt_pred,
        TEST_HORIZON
    )

    metrics = calculate_forecast_metrics(
        y_test,
        holt_pred
    )

    metrics["Model"] = "Holt"

    metrics_rows.append(
        metrics
    )

    print_metrics(
        "Holt",
        metrics
    )

except Exception as e:

    print("\nHolt failed:", e)


# HOLT-WINTERS
for seasonal_period in [
    4,
    13
]:

    try:

        model_name = f"HoltWinters_s{seasonal_period}"

        hw_pred = holt_winters_forecast(
            y_train,
            TEST_HORIZON,
            seasonal_periods=seasonal_period
        )

        forecast_results[model_name] = clean_forecast_array(
            hw_pred,
            TEST_HORIZON
        )

        metrics = calculate_forecast_metrics(
            y_test,
            hw_pred
        )

        metrics["Model"] = model_name

        metrics_rows.append(
            metrics
        )

        print_metrics(
            model_name,
            metrics
        )

    except Exception as e:

        print(f"\nHolt-Winters s={seasonal_period} failed:", e)


# ARIMA
arima_result = arima_grid_search(
    y_train,
    y_test
)

if arima_result is not None:

    forecast_results["ARIMA"] = clean_forecast_array(
        arima_result["forecast"],
        TEST_HORIZON
    )

    metrics = arima_result["metrics"]

    metrics["Model"] = "ARIMA"

    metrics["Order"] = str(
        arima_result["order"]
    )

    metrics["AIC"] = arima_result["aic"]

    metrics_rows.append(
        metrics
    )

    print("\nBest ARIMA order:", arima_result["order"])

    print_metrics(
        "ARIMA",
        metrics
    )

else:

    print("\nARIMA failed for all tested orders.")


# SARIMA
sarima_result = sarima_grid_search(
    y_train,
    y_test
)

if sarima_result is not None:

    forecast_results["SARIMA"] = clean_forecast_array(
        sarima_result["forecast"],
        TEST_HORIZON
    )

    metrics = sarima_result["metrics"]

    metrics["Model"] = "SARIMA"

    metrics["Order"] = str(
        sarima_result["order"]
    )

    metrics["Seasonal_Order"] = str(
        sarima_result["seasonal_order"]
    )

    metrics["AIC"] = sarima_result["aic"]

    metrics_rows.append(
        metrics
    )

    print("\nBest SARIMA order:", sarima_result["order"])

    print("Best SARIMA seasonal order:", sarima_result["seasonal_order"])

    print_metrics(
        "SARIMA",
        metrics
    )

else:

    print("\nSARIMA failed for all tested orders.")


# LAG FEATURE ML MODELS
lag_feature_df = create_lag_feature_dataset(
    weekly_df
)

test_start_date = test_df["Date"].min()

ml_results, ml_test_df = train_lag_models(
    lag_feature_df,
    test_start_date
)

for model_name, result in ml_results.items():

    forecast_values = clean_forecast_array(
        result["forecast"],
        TEST_HORIZON
    )

    if len(forecast_values) == len(forecast_results):

        forecast_results[model_name] = forecast_values

        metrics = result["metrics"]

        metrics["Model"] = model_name

        metrics_rows.append(
            metrics
        )

        print_metrics(
            model_name,
            metrics
        )

    else:

        print(
            f"\nSkipping {model_name}: forecast length mismatch."
        )


# FINAL METRICS TABLE
metrics_df = pd.DataFrame(
    metrics_rows
)

front_cols = [
    "Model",
    "RMSE",
    "MAE",
    "MSE",
    "R2",
    "WAPE_%",
    "sMAPE_%",
    "Revenue_Error_%",
    "Actual_Total",
    "Predicted_Total",
    "Order",
    "Seasonal_Order",
    "AIC"
]

front_cols = [
    col
    for col in front_cols
    if col in metrics_df.columns
]

metrics_df = metrics_df[
    front_cols
]

metrics_df = metrics_df.sort_values(
    by="RMSE",
    ascending=True
)

print("\nFinal Forecast Model Comparison:\n")

print(metrics_df)

best_model_name = metrics_df.iloc[0]["Model"]

print("\nBest forecasting model:", best_model_name)


# SAVE FORECAST RESULTS
forecast_results.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "weekly_forecast_results.csv"
    ),
    index=False
)

metrics_df.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "forecast_model_comparison.csv"
    ),
    index=False
)

forecast_results.to_json(
    os.path.join(
        FRONTEND_DATA_DIR,
        "weekly_forecast_results.json"
    ),
    orient="records",
    indent=2,
    date_format="iso"
)

metrics_df.to_json(
    os.path.join(
        FRONTEND_DATA_DIR,
        "forecast_model_comparison.json"
    ),
    orient="records",
    indent=2
)


# FUTURE 12-WEEK FORECAST USING BEST MODEL
future_forecast_df = None

future_dates = pd.date_range(
    start=weekly_df["Date"].max() + pd.Timedelta(weeks=1),
    periods=FUTURE_HORIZON,
    freq=WEEKLY_FREQ
)

if best_model_name in [
    "Naive",
    "MovingAverage_4",
    "MovingAverage_8",
    "MovingAverage_12"
]:

    if best_model_name == "Naive":

        future_values = naive_forecast(
            weekly_df["Revenue"],
            FUTURE_HORIZON
        )

    else:

        window = int(
            best_model_name.split("_")[-1]
        )

        future_values = moving_average_forecast(
            weekly_df["Revenue"],
            FUTURE_HORIZON,
            window
        )

    future_forecast_df = pd.DataFrame({
        "Date": future_dates,
        "ForecastRevenue": clean_forecast_array(
            future_values,
            FUTURE_HORIZON
        )
    })


elif best_model_name == "SES":

    future_values = ses_forecast(
        weekly_df["Revenue"],
        FUTURE_HORIZON
    )

    future_forecast_df = pd.DataFrame({
        "Date": future_dates,
        "ForecastRevenue": clean_forecast_array(
            future_values,
            FUTURE_HORIZON
        )
    })


elif best_model_name == "Holt":

    future_values = holt_forecast(
        weekly_df["Revenue"],
        FUTURE_HORIZON
    )

    future_forecast_df = pd.DataFrame({
        "Date": future_dates,
        "ForecastRevenue": clean_forecast_array(
            future_values,
            FUTURE_HORIZON
        )
    })


elif best_model_name.startswith("HoltWinters"):

    seasonal_period = int(
        best_model_name.split("s")[-1]
    )

    future_values = holt_winters_forecast(
        weekly_df["Revenue"],
        FUTURE_HORIZON,
        seasonal_periods=seasonal_period
    )

    future_forecast_df = pd.DataFrame({
        "Date": future_dates,
        "ForecastRevenue": clean_forecast_array(
            future_values,
            FUTURE_HORIZON
        )
    })


elif best_model_name in [
    "ARIMA",
    "SARIMA"
]:

    combined_train = np.log1p(
        np.asarray(weekly_df["Revenue"])
    )

    if best_model_name == "ARIMA" and arima_result is not None:

        model = ARIMA(
            combined_train,
            order=arima_result["order"]
        )

        fitted_model = model.fit()

        future_log = fitted_model.forecast(
            steps=FUTURE_HORIZON
        )

        future_values = safe_exp_forecast(
            future_log
        )

        future_forecast_df = pd.DataFrame({
            "Date": future_dates,
            "ForecastRevenue": clean_forecast_array(
                future_values,
                FUTURE_HORIZON
            )
        })

    elif best_model_name == "SARIMA" and sarima_result is not None:

        model = SARIMAX(
            combined_train,
            order=sarima_result["order"],
            seasonal_order=sarima_result["seasonal_order"],
            enforce_stationarity=False,
            enforce_invertibility=False
        )

        fitted_model = model.fit(
            disp=False
        )

        future_log = fitted_model.forecast(
            steps=FUTURE_HORIZON
        )

        future_values = safe_exp_forecast(
            future_log
        )

        future_forecast_df = pd.DataFrame({
            "Date": future_dates,
            "ForecastRevenue": clean_forecast_array(
                future_values,
                FUTURE_HORIZON
            )
        })


elif best_model_name in [
    "RandomForest_Lag",
    "XGBoost_Lag"
]:

    best_ml_result = ml_results[
        best_model_name
    ]

    future_forecast_df = recursive_future_ml_forecast(
        best_ml_result["model"],
        weekly_df,
        best_ml_result["feature_columns"],
        FUTURE_HORIZON
    )

    future_forecast_df = future_forecast_df.rename(
        columns={
            "Revenue": "ForecastRevenue"
        }
    )

    future_forecast_df = future_forecast_df[
        [
            "Date",
            "ForecastRevenue"
        ]
    ]

    future_forecast_df["ForecastRevenue"] = clean_forecast_array(
        future_forecast_df["ForecastRevenue"],
        FUTURE_HORIZON
    )


if future_forecast_df is not None:

    future_forecast_df["ForecastRevenue"] = clean_forecast_array(
        future_forecast_df["ForecastRevenue"],
        FUTURE_HORIZON
    )

    future_forecast_df.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "future_12_week_forecast.csv"
        ),
        index=False
    )

    future_forecast_df.to_json(
        os.path.join(
            FRONTEND_DATA_DIR,
            "future_12_week_forecast.json"
        ),
        orient="records",
        indent=2,
        date_format="iso"
    )


# PLOTS
plot_weekly_revenue(
    weekly_df
)

plot_monthly_revenue(
    monthly_df
)

plot_train_test_forecasts(
    forecast_results
)

plot_best_model_forecast(
    forecast_results,
    best_model_name
)

plot_model_comparison(
    metrics_df
)

plot_residuals(
    forecast_results,
    best_model_name
)

if future_forecast_df is not None:

    plot_future_forecast(
        weekly_df,
        future_forecast_df,
        best_model_name
    )

plot_seasonal_decomposition(
    weekly_df
)


# SUMMARY JSON
summary = {
    "timeSeriesStatus": "complete",
    "target": "Weekly Revenue",
    "interpretation": "Exploratory short-term weekly revenue forecasting. Monthly data has only 25 points, so monthly output is used mainly for trend visualization rather than serious forecasting.",
    "testHorizonWeeks": TEST_HORIZON,
    "futureForecastWeeks": FUTURE_HORIZON,
    "bestModel": best_model_name,
    "bestModelMetrics": metrics_df.iloc[0].to_dict(),
    "trainStart": str(train_df["Date"].min()),
    "trainEnd": str(train_df["Date"].max()),
    "testStart": str(test_df["Date"].min()),
    "testEnd": str(test_df["Date"].max()),
    "weeklyObservations": int(len(weekly_df)),
    "monthlyObservations": int(len(monthly_df)),
    "totalHistoricalRevenue": float(weekly_df["Revenue"].sum()),
    "averageWeeklyRevenue": float(weekly_df["Revenue"].mean()),
    "latestWeeklyRevenue": float(weekly_df["Revenue"].iloc[-1]),
    "latestMonthlyRevenue": float(monthly_df["Revenue"].iloc[-1]),
    "frontendFiles": {
        "weeklyRevenueSeries": "time_series_frontend_data/weekly_revenue_series.json",
        "monthlyRevenueSeries": "time_series_frontend_data/monthly_revenue_series.json",
        "weeklyForecastResults": "time_series_frontend_data/weekly_forecast_results.json",
        "forecastModelComparison": "time_series_frontend_data/forecast_model_comparison.json",
        "futureForecast": "time_series_frontend_data/future_12_week_forecast.json"
    },
    "plots": {
        "weeklyRevenueTrend": "time_series_plots/01_weekly_revenue_trend.png",
        "monthlyRevenueTrend": "time_series_plots/02_monthly_revenue_trend.png",
        "forecastComparison": "time_series_plots/03_train_test_forecast_comparison.png",
        "bestModelForecast": "time_series_plots/04_best_model_test_forecast.png",
        "modelComparison": "time_series_plots/05_forecast_model_comparison_rmse.png",
        "residualDistribution": "time_series_plots/06_forecast_residual_distribution.png",
        "futureForecast": "time_series_plots/07_future_12_week_forecast.png",
        "seasonalDecomposition": "time_series_plots/08_seasonal_decomposition.png"
    }
}

with open(
    os.path.join(
        OUTPUT_DIR,
        "time_series_summary.json"
    ),
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        summary,
        f,
        indent=2
    )

with open(
    os.path.join(
        FRONTEND_DATA_DIR,
        "time_series_summary.json"
    ),
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        summary,
        f,
        indent=2
    )


print("\nSaved time-series outputs in:")

print(OUTPUT_DIR)

print("\nSaved time-series plots in:")

print(PLOT_DIR)

print("\nSaved frontend time-series data in:")

print(FRONTEND_DATA_DIR)

print("\nImportant output files:")

print(os.path.join(OUTPUT_DIR, "weekly_revenue_series.csv"))

print(os.path.join(OUTPUT_DIR, "monthly_revenue_series.csv"))

print(os.path.join(OUTPUT_DIR, "forecast_model_comparison.csv"))

print(os.path.join(OUTPUT_DIR, "weekly_forecast_results.csv"))

print(os.path.join(OUTPUT_DIR, "future_12_week_forecast.csv"))

print(os.path.join(OUTPUT_DIR, "time_series_summary.json"))

print("\nBest forecasting model:")

print(best_model_name)

print("\nTime-series forecasting complete.")