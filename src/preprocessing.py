# preprocessing.py
# Core preprocessing pipeline for
# UCI Online Retail II Dataset
# Complete preprocessing pipeline for UCI Online Retail II dataset.

import pandas as pd
import numpy as np


 # NON-PRODUCT / INTERNAL STOCK CODES
NON_PRODUCT_CODES = {"POST", "DOT", "BANK CHARGES", "AMAZONFEE", "MANUAL", "CRUK"}


 # MAIN PREPROCESSING FUNCTION
 
def preprocess_online_retail( file_path, verbose=True ): #accepting file path rn but will edit it later
    #Parameters: filepath, verbose: a bool weather to print the logs 
    #Returns: A single cleaned dataset

    #LOAD DATA 
    if verbose:
        print("\nLoading dataset...")

    df_orig = pd.read_excel(r"D:\online_retail\data\online_retail_II.xlsx", sheet_name=None)
    df = pd.concat(df_orig.values(), ignore_index=True)

    if verbose:
        print(f"Initial Shape: {df.shape}")


    # STANDARDIZE COLUMN NAMES 
    df.columns = (
        df.columns
          .str.strip()
          .str.replace(" ", "_")
    )


    # REMOVE MISSING CUSTOMER IDs
    missing_ids = df['Customer_ID'].isna().sum()

    if verbose:
        print(f"\nMissing Customer IDs: {missing_ids}")

    df = df.dropna(subset=['Customer_ID'])


    # FIX DATATYPES
    # Dates to datetime
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    # Customer ID to int then string to avoid floats
    df['Customer_ID'] = (
        df['Customer_ID']
          .astype(int)
          .astype(str)
    )
    # StockCode to a normalised str
    df['StockCode'] = (
        df['StockCode']
          .astype(str)
          .str.strip()
          .str.upper()
    )
    # Country
    df['Country'] = (
        df['Country']
          .astype(str)
          .str.strip()
          .str.title()
    )


    # REMOVE EXACT DUPLICATES  
    duplicate_count = df.duplicated().sum()
    if verbose:
        print(f"\nDuplicate Rows: {duplicate_count}")
    df = df.drop_duplicates()

      
    # REMOVE IMPOSSIBLE PRICES
    invalid_price_count = ((df['Price'] <= 0).sum())

    if verbose:
        print(f"\nRows with Invalid Prices: ", f"{invalid_price_count}")
    df = df[df['Price'] > 0]

    
    # REMOVE NON-PRODUCT STOCK CODES
    non_product_count = (df['StockCode'].isin(NON_PRODUCT_CODES).sum())
    if verbose:
        print(f"\nNon-product rows: ", f"{non_product_count}")
    # NOTE: We DO NOT remove them yet.
    # We preserve them in master dataset.
    # Downstream tasks can filter them.


    # CREATE FLAGS
    # Cancellation invoices
    df['IsCancelled'] = (
        df['Invoice']
          .astype(str)
          .str.startswith('C'))
    # Returns / negative quantities
    df['IsReturn'] = (df['Quantity'] <= 0)
    # Non-product / operational transactions
    df['IsNonProduct'] = (df['StockCode'].isin(NON_PRODUCT_CODES))

    
    # CREATE TRANSACTION VALUE
    df['TransactionValue'] = (df['Quantity'] * df['Price'])


    # SORT CHRONOLOGICALLY
    df = df.sort_values(by=['Customer_ID', 'InvoiceDate'])

    # RESET INDEX
    df = df.reset_index(drop=True)


    # FINAL LOGGING
    if verbose:

        print("\n========== FINAL SUMMARY ==========")

        print(f"\nFinal Dataset Shape: {df.shape}")

        print(f"\nUnique Customers: ", f"{df['Customer_ID'].nunique()}")

        print(f"Unique Invoices: ", f"{df['Invoice'].nunique()}")

        print(f"Date Range: ", f"{df['InvoiceDate'].min()} ", f"to ", f"{df['InvoiceDate'].max()}")

        print(f"\nCancelled Transactions: ", f"{df['IsCancelled'].sum()}")

        print(f"Return Transactions: ", f"{df['IsReturn'].sum()}")
        
        print("\n===================================")

    return df
