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

print("Extracting trends...")
eda_data = {}

# -------------------------
# ORIGINAL FEATURES TRENDS (from cleaned df to avoid garbage, or raw? Prompt says "original features of the dataset". We will use cleaned df for meaningful trends, but maybe show raw stats too).
# Let's use df (cleaned) for trends.
# -------------------------

# 1. InvoiceDate: Time series of transactions (monthly)
df['MonthYear'] = df['InvoiceDate'].dt.to_period('M').astype(str)
monthly_invoices = df.groupby('MonthYear')['Invoice'].nunique().reset_index()
monthly_invoices.columns = ['Month', 'InvoiceCount']
eda_data['monthly_invoices'] = monthly_invoices

# 2. Country: Top 10
top_countries = df['Country'].value_counts().head(10).reset_index()
top_countries.columns = ['Country', 'Count']
eda_data['top_countries'] = top_countries

# 3. Quantity: Boxplot/Histogram stats (removing extreme outliers for visualization)
quantities = df[df['Quantity'] < df['Quantity'].quantile(0.99)]['Quantity']
eda_data['quantity_dist'] = quantities.sample(n=min(10000, len(quantities)), random_state=42).tolist()

# 4. Price: Dist
prices = df[df['Price'] < df['Price'].quantile(0.99)]['Price']
eda_data['price_dist'] = prices.sample(n=min(10000, len(prices)), random_state=42).tolist()

# 5. StockCode/Description: Top 10
top_products = df['Description'].value_counts().head(10).reset_index()
top_products.columns = ['Product', 'Count']
eda_data['top_products'] = top_products

# -------------------------
# DERIVED FEATURES TRENDS (from retention_df)
# -------------------------
# Derived features: Recency, Frequency, Monetary, AvgBasketValue, AvgQuantity, UniqueProducts, LifetimeDays, PurchaseRate, AvgGapDays, PurchasesLast30Days, SpendLast30Days, CancellationRate, ReturnRate

derived_features = [
    'Recency', 'Frequency', 'Monetary', 'AvgBasketValue', 
    'AvgQuantity', 'UniqueProducts', 'LifetimeDays', 
    'PurchaseRate', 'AvgGapDays', 'PurchasesLast30Days', 
    'SpendLast30Days', 'CancellationRate', 'ReturnRate'
]

derived_dist = {}
for feat in derived_features:
    # Subsample for fast plotting in Streamlit
    data = retention_df[feat].dropna()
    derived_dist[feat] = data.sample(n=min(5000, len(data)), random_state=42).tolist()
    
eda_data['derived_dist'] = derived_dist

with open('eda_data.pkl', 'wb') as f:
    pickle.dump(eda_data, f)

print("EDA extraction complete!")
