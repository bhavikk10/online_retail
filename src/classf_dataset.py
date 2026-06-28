# classification_dataset.py

import pandas as pd
import numpy as np
 
# MAIN FUNCTION FOR BUILDING RETENTION CLASSIFICATION DATASET
def build_retention_dataset(df, cutoff_date='2011-09-09', prediction_days=90, active_days=180, verbose=True):

    # CONVERTING INPUT CUTOFF DATE INTO PANDAS TIMESTAMP
    # This becomes the boundary separating historical feature generation and Future retention label generation
    cutoff_date = pd.Timestamp(cutoff_date)

  
    # DEFINING FUTURE PREDICTION WINDOW END DATE
    # Customers purchasing between:
    # cutoff_date -> prediction_end
    # receive retention label = 1
    prediction_end = (cutoff_date + pd.Timedelta(days=prediction_days))

  
    # DEFINING RECENT ACTIVITY WINDOW
    # Customers inactive for too long before cutoff
    # are excluded to avoid trivial dead-user predictions
    active_start = (cutoff_date - pd.Timedelta(days=active_days))

  
    # FILTERING ONLY GENUINE PURCHASE TRANSACTIONS
    # Removing:
    # 1. Cancelled invoices
    # 2. Product returns
    # 3. Operational/non-product transactions
    purchase_df = df[
        (~df['IsCancelled']) &
        (~df['IsReturn']) &
        (~df['IsNonProduct'])].copy()

  
    # SORTING PURCHASES CHRONOLOGICALLY 
    # Sorting by customer then time is essential for:
    # 1. Gap calculations
    # 2. Recency features
    # 3. Temporal behavior modeling
    purchase_df = purchase_df.sort_values(['Customer_ID', 'InvoiceDate'])

  
    # SPLITTING HISTORICAL AND FUTURE DATA
    # Historical data:
    # Used ONLY for feature engineering
    history_df = purchase_df[purchase_df['InvoiceDate'] < cutoff_date].copy()
    # Future data:
    # Used ONLY for retention label creation
    future_df = purchase_df[
        (purchase_df['InvoiceDate'] >= cutoff_date) &
        (purchase_df['InvoiceDate'] < prediction_end)
    ].copy()

  
    # IDENTIFYING RECENTLY ACTIVE CUSTOMERS
    # Keeping only customers active within recent window
    # avoids learning from ancient dormant customers
    recent_active_customers = (
        history_df[
            history_df['InvoiceDate'] >= active_start
        ]['Customer_ID']
        .unique()
    )

  
    # FILTERING HISTORY TO ACTIVE CUSTOMERS ONLY
    # This ensures:
    # every customer had at least some recent activity
    history_df = history_df[history_df['Customer_ID'].isin(recent_active_customers)]

  
    # FILTERING FUTURE DATA TO SAME CUSTOMER SET
    # Future labels must only exist for valid customers
    future_df = future_df[future_df['Customer_ID'].isin(recent_active_customers)]

  
    # CREATING INVOICE-LEVEL AGGREGATION
    # Raw dataset is transaction-line level:
    # one row per purchased item

    # Here we aggregate into one row per invoice/order
    # This captures cleaner order-level behavior
    invoice_df = (
        history_df
        .groupby(['Customer_ID', 'Invoice'])
        .agg({
            # First timestamp of invoice
            'InvoiceDate': 'min',
            # Total spend within invoice
            'TransactionValue': 'sum',
            # Total quantity purchased in invoice
            'Quantity': 'sum',
            # Number of unique products in invoice
            'StockCode': 'nunique'
        })
        .reset_index()
    )

  
    # SORTING INVOICE-LEVEL DATA CHRONOLOGICALLY
    # Required for temporal customer calculations
    invoice_df = invoice_df.sort_values(['Customer_ID', 'InvoiceDate'])

  
    # CREATING CUSTOMER-LEVEL AGGREGATED FEATURES
    # Final dataset requires none row per customer
    # So invoice-level behavior is aggregated upward
    customer_features = (
        invoice_df
        .groupby('Customer_ID')
        .agg(
            # Most recent purchase timestamp
            LastPurchaseDate=('InvoiceDate', 'max'),
            # First ever purchase timestamp
            FirstPurchaseDate=('InvoiceDate', 'min'),
            # Total number of orders placed
            Frequency=('Invoice', 'nunique'),
            # Total customer spending
            Monetary=('TransactionValue', 'sum'),
            # Average spend per order
            AvgBasketValue=('TransactionValue', 'mean'),
            # Average quantity purchased per order
            AvgQuantity=('Quantity', 'mean'),
            # Total unique products purchased
            UniqueProducts=('StockCode', 'sum')
        )
        .reset_index()
    )

  
    # DERIVING RECENCY FEATURE
    # Measures: days since customer's last purchase
    # Lower recency usually means:
    # higher probability of returning
    customer_features['Recency'] = (cutoff_date - customer_features['LastPurchaseDate']).dt.days

  
    # DERIVING CUSTOMER LIFETIME FEATURE
    # Measures: duration between first and latest purchase
    # Helps distinguish new customers vs mature loyal customers
    customer_features['LifetimeDays'] = (customer_features['LastPurchaseDate'] - customer_features['FirstPurchaseDate']).dt.days

  
    # PREVENTING DIVISION BY ZERO
    # Customers with single-day activity
    # would otherwise create divide-by-zero errors
    customer_features['LifetimeDays'] = (customer_features['LifetimeDays'].replace(0, 1))

    # FLAGGING RECENTLY ACQUIRED CUSTOMERS
    # New customers often behave differently from mature customers
    customer_features['IsNewCustomer'] = (
        customer_features['LifetimeDays'] <= 60
    ).astype(int)
  
    # DERIVING PURCHASE VELOCITY FEATURE
    # Measures: average order frequency per lifetime day
    # Captures long-term customer engagement intensity
    customer_features['PurchaseRate'] = (customer_features['Frequency']/customer_features['LifetimeDays'])

    # DERIVING RECENCY-FREQUENCY INTERACTION
    # Combines freshness and loyalty into one signal
    customer_features['RecencyFrequency'] = (customer_features['Recency'] / customer_features['Frequency'])

    # DERIVING REVENUE INTENSITY FEATURE
    # Measures average spending generated per day
    customer_features['RevenuePerDay'] = (
        customer_features['Monetary'] /
        customer_features['LifetimeDays']
    )

    # DERIVING PRODUCT SPEND INTENSITY FEATURE
    # Measures average spend per unique product purchased
    customer_features['AvgSpendPerProduct'] = (
        customer_features['Monetary'] /
        customer_features['UniqueProducts']
    )

    # DERIVING PRODUCT DIVERSITY FEATURE
    # Measures product variety purchased per order
    customer_features['ProductDiversityRate'] = (
        customer_features['UniqueProducts'] /
        customer_features['Frequency']
    )

    # CREATING PREVIOUS PURCHASE TIMESTAMPS
    # Previous invoice timestamps are needed
    # for inter-purchase gap calculations
    invoice_df['PrevInvoiceDate'] = (invoice_df.groupby('Customer_ID')['InvoiceDate'].shift(1))

  
    # CALCULATING INTER-PURCHASE GAPS
    # Measures: time gap between consecutive purchases
    # Highly informative behavioral feature
    invoice_df['GapDays'] = (invoice_df['InvoiceDate']-invoice_df['PrevInvoiceDate']).dt.days

  
    # DERIVING AVERAGE INTER-PURCHASE GAP
    # Customers with lower average gaps
    # often show stronger retention tendencies
    # DERIVING INTER-PURCHASE GAP STATISTICS
    gap_features = (
        invoice_df
        .groupby('Customer_ID')
        .agg(
            AvgGapDays=('GapDays', 'mean'),
            StdGapDays=('GapDays', 'std')
        )
        .reset_index()
    )


    # MERGING GAP FEATURES
    customer_features = customer_features.merge(
        gap_features,
        on='Customer_ID',
        how='left'
    )


    # SINGLE-PURCHASE CUSTOMERS HAVE NO GAP VARIANCE
    customer_features['StdGapDays'] = (
        customer_features['StdGapDays']
        .fillna(0)
    )


  
    # DEFINING RECENT 30-DAY ACTIVITY WINDOW
    # Recent activity often predicts
    # short-term retention strongly
    last_30_start = (cutoff_date - pd.Timedelta(days=30))

  
    # EXTRACTING RECENT CUSTOMER ACTIVITY
    # Captures customer momentum immediately
    # before prediction cutoff
    last_30_df = history_df[history_df['InvoiceDate'] >= last_30_start]

  
    # CREATING RECENT MOMENTUM FEATURES
    # These features capture:
    # recent engagement intensity
    recent_features = (
        last_30_df
        .groupby('Customer_ID')
        .agg(
            # Number of recent orders
            PurchasesLast30Days=('Invoice', 'nunique'),
            # Recent spending volume
            SpendLast30Days=('TransactionValue', 'sum')
        )
        .reset_index()
    )

  
    # MERGING RECENT MOMENTUM FEATURES
    customer_features = customer_features.merge(recent_features, on='Customer_ID', how='left')

  
    # FILLING MISSING RECENT ACTIVITY VALUES
    # Customers without recent purchases
    # should receive zeros instead of NaNs
    customer_features[['PurchasesLast30Days', 'SpendLast30Days']] = customer_features[['PurchasesLast30Days', 'SpendLast30Days']].fillna(0)



    # NEW
    # DEFINING RECENT 90-DAY ACTIVITY WINDOW
    # Captures medium-term customer engagement before cutoff
    last_90_start = (
        cutoff_date -
        pd.Timedelta(days=90)
    )


    # EXTRACTING LAST 90-DAY CUSTOMER ACTIVITY
    last_90_df = history_df[
        history_df['InvoiceDate'] >= last_90_start
    ]

    # CREATING MEDIUM-TERM MOMENTUM FEATURES
    recent_90_features = (
        last_90_df
        .groupby('Customer_ID')
        .agg(
            PurchasesLast90Days=('Invoice', 'nunique'),
            SpendLast90Days=('TransactionValue', 'sum')
        )
        .reset_index()
    )

    # MERGING MEDIUM-TERM MOMENTUM FEATURES
    customer_features = customer_features.merge(
        recent_90_features,
        on='Customer_ID',
        how='left'
    )

    # FILLING MISSING VALUES
    customer_features[
        ['PurchasesLast90Days', 'SpendLast90Days']
    ] = customer_features[
        ['PurchasesLast90Days', 'SpendLast90Days']
    ].fillna(0)



    # DEFINING PRIOR 90-DAY WINDOW
    # Window from cutoff-180 to cutoff-90
    prior_90_start = (
        cutoff_date -
        pd.Timedelta(days=180)
    )

    prior_90_end = (
        cutoff_date -
        pd.Timedelta(days=90)
    )

    # EXTRACTING PRIOR WINDOW ACTIVITY
    prior_90_df = history_df[
        (history_df['InvoiceDate'] >= prior_90_start) &
        (history_df['InvoiceDate'] < prior_90_end)
    ]

    # CALCULATING PRIOR WINDOW ACTIVITY
    prior_90_features = (
        prior_90_df
        .groupby('Customer_ID')
        .agg(
            SpendPrior90Days=('TransactionValue', 'sum'),
            PurchasesPrior90Days=('Invoice', 'nunique')
        )
        .reset_index()
    )

    # MERGING PRIOR WINDOW FEATURES
    customer_features = customer_features.merge(
        prior_90_features,
        on='Customer_ID',
        how='left'
    )

    customer_features[
        ['SpendPrior90Days','PurchasesPrior90Days']
    ] = customer_features[
        ['SpendPrior90Days','PurchasesPrior90Days']
    ].fillna(0)



    # DERIVING SPENDING MOMENTUM FEATURE
    # Ratio > 1 means accelerating spend
    # Ratio < 1 means declining spend
    customer_features['SpendTrendRatio'] = (
        customer_features['SpendLast90Days'] /
        (
            customer_features['SpendPrior90Days']
            + 1
        )
    )


    # DERIVING PURCHASE MOMENTUM FEATURE
    # Ratio > 1 means increasing purchase frequency
    # Ratio < 1 means declining purchase frequency
    customer_features['FrequencyLast90DaysRatio'] = (
        customer_features['PurchasesLast90Days'] /
        (
            customer_features['PurchasesPrior90Days']
            + 1
        )
    )


    # COLLECTING HISTORICAL RETURN/CANCELLATION DATA
    # Behavioral instability signals
    # may help predict retention
    cancellation_df = df[(df['InvoiceDate'] < cutoff_date)]

  
    # CREATING RETURN/CANCELLATION FEATURES
    cancellation_features = (
        cancellation_df
        .groupby('Customer_ID')
        .agg(
            # Total historical transaction count
            TotalTransactions=('Invoice', 'count'),
            # Number of cancelled transactions
            CancelledTransactions=('IsCancelled', 'sum'),
            # Number of returned transactions
            ReturnedTransactions=('IsReturn', 'sum')
        ).reset_index())

  
    '''# DERIVING CANCELLATION RATE
    # Measures: proportion of customer cancellations
    cancellation_features['CancellationRate'] = (cancellation_features['CancelledTransactions']/cancellation_features['TotalTransactions'])
    '''
  
    # DERIVING RETURN RATE
    # Measures: proportion of customer returns
    # Found out that cancellation rate and return rate are same, correlation = 1.0
    cancellation_features['ReturnRate'] = (cancellation_features['ReturnedTransactions']/cancellation_features['TotalTransactions'])

  
    # MERGING CANCELLATION FEATURES
    customer_features = customer_features.merge(cancellation_features[
            [
                'Customer_ID',
                'ReturnRate'
            ]
        ],
        on='Customer_ID',
        how='left')

  
    # IDENTIFYING FUTURE RETURNING CUSTOMERS
    # Customers purchasing during future window
    # become positive retention examples
    future_labels = (
        future_df
        .groupby('Customer_ID')['Invoice']
        .nunique()
        .reset_index()
    )

  
    # ASSIGNING POSITIVE RETENTION LABELS
    future_labels['RetentionLabel'] = 1

  
    # MERGING LABELS INTO FINAL FEATURE TABLE
    customer_features = customer_features.merge(
        future_labels[
            ['Customer_ID', 'RetentionLabel']
        ],
        on='Customer_ID',
        how='left'
    )

  
    # ASSIGNING NEGATIVE LABELS TO NON-RETURNERS
    # Customers absent in future purchases
    # are labeled as non-retained
    customer_features['RetentionLabel'] = (
        customer_features['RetentionLabel']
        .fillna(0)
        .astype(int)
    )

  
    # REMOVING RAW TIMESTAMP COLUMNS
    # Derived features already contain needed information
    customer_features = customer_features.drop(columns=['LastPurchaseDate','FirstPurchaseDate'])

  
    # PRINTING FINAL DATASET STATISTICS
    if verbose:

        print(f"Cutoff date: {cutoff_date.date()}")

        print(f"Prediction end: {prediction_end.date()}")

        print(f"Active customer window: {active_days} days")

        print(f"Final dataset shape: {customer_features.shape}")

        print(f"Customers retained: ", f"{customer_features['RetentionLabel'].mean():.2%}")

        print(f"Positive labels: ", f"{customer_features['RetentionLabel'].sum()}")

        print(f"Negative labels: ", f"{(customer_features['RetentionLabel'] == 0).sum()}")

    return customer_features


 
# TEST EXECUTION
 

if __name__ == "__main__":

    # Importing preprocessing pipeline
    from preprocessing import preprocess_online_retail

    # Loading cleaned master transaction dataset
    df = preprocess_online_retail(
        file_path="online_retail_II.xlsx",
        verbose=False
    )

    # Building customer-level retention dataset
    retention_df = build_retention_dataset(
        df,
        cutoff_date='2011-09-09',
        prediction_days=90,
        active_days=180,
        verbose=True
    )

    # Printing sample rows from final dataset
    print(retention_df.head())