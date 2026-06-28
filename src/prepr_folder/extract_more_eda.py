import pandas as pd
import numpy as np
import pickle
import os

from preprocessing import preprocess_online_retail
from classf_dataset import build_retention_dataset

print("Loading raw data...")
df_orig = pd.read_excel(r"D:\online_retail\data\online_retail_II.xlsx", sheet_name=None)
df_raw = pd.concat(df_orig.values(), ignore_index=True)

print("Loading processed data...")
df = preprocess_online_retail(file_path="online_retail_II.xlsx", verbose=False)

print("Building retention dataset...")
retention_df = build_retention_dataset(df, cutoff_date='2011-09-09', prediction_days=90, active_days=180, verbose=False)

# Load existing EDA
with open('eda_data.pkl', 'rb') as f:
    eda_data = pickle.load(f)

print("Extracting more trends...")

# 1. Feature Correlation Matrix
derived_features = [
    'Recency', 'Frequency', 'Monetary', 'AvgBasketValue', 
    'AvgQuantity', 'UniqueProducts', 'LifetimeDays', 
    'PurchaseRate', 'AvgGapDays', 'PurchasesLast30Days', 
    'SpendLast30Days', 'CancellationRate', 'ReturnRate'
]
corr_matrix = retention_df[derived_features].corr().round(2).fillna(0)
eda_data['corr_matrix'] = {
    'z': corr_matrix.values.tolist(),
    'x': corr_matrix.columns.tolist(),
    'y': corr_matrix.index.tolist()
}

# 2. Cohort Data (Monthly active users / revenue)
df['MonthYear'] = df['InvoiceDate'].dt.to_period('M')
revenue_by_month = df.groupby('MonthYear')['TransactionValue'].sum().reset_index()
revenue_by_month['MonthYear'] = revenue_by_month['MonthYear'].astype(str)
eda_data['revenue_by_month'] = revenue_by_month

# 3. Product Treemap Data (Top 50)
top_50_products = df['Description'].value_counts().head(50).reset_index()
top_50_products.columns = ['Product', 'Count']
eda_data['treemap_products'] = top_50_products

# 4. Hourly/Daily Trends
df['Hour'] = df['InvoiceDate'].dt.hour
df['DayOfWeek'] = df['InvoiceDate'].dt.day_name()
hourly_trend = df['Hour'].value_counts().sort_index().reset_index()
hourly_trend.columns = ['Hour', 'Count']
eda_data['hourly_trend'] = hourly_trend

daily_trend = df['DayOfWeek'].value_counts().reset_index()
daily_trend.columns = ['Day', 'Count']
# Sorting days
days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
daily_trend['Day'] = pd.Categorical(daily_trend['Day'], categories=days_order, ordered=True)
daily_trend = daily_trend.sort_values('Day')
eda_data['daily_trend'] = daily_trend


with open('eda_data.pkl', 'wb') as f:
    pickle.dump(eda_data, f)

print("More EDA extraction complete!")
