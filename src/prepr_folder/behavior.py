def analyze_customer_behavior(df, verbose=True):

    invoice_df = (
        df[(~df['IsCancelled']) & (~df['IsReturn']) & (~df['IsNonProduct'])]
        .groupby(['Customer_ID', 'Invoice'])
        .agg({
            'InvoiceDate': 'min',
            'TransactionValue': 'sum'
        })
        .reset_index()
    )

    invoice_df = invoice_df.sort_values(
        ['Customer_ID', 'InvoiceDate']
    )

    purchase_counts = (
        invoice_df.groupby('Customer_ID')['Invoice']
        .nunique()
    )

    repeat_rate = (purchase_counts > 1).mean()

    invoice_df['PrevInvoiceDate'] = (
        invoice_df.groupby('Customer_ID')['InvoiceDate']
        .shift(1)
    )

    invoice_df['GapDays'] = (
        invoice_df['InvoiceDate']
        - invoice_df['PrevInvoiceDate']
    ).dt.days

    gaps = invoice_df['GapDays'].dropna()

    gap_stats = gaps.describe()

    within_30 = (gaps <= 30).mean()
    within_60 = (gaps <= 60).mean()
    within_90 = (gaps <= 90).mean()
    within_75 = (gaps <= 75).mean()

    if verbose:

        print(f"Invoice-level shape: {invoice_df.shape}")

        print(f"Unique customers: {invoice_df['Customer_ID'].nunique()}")

        print(f"Repeat customer rate: {repeat_rate:.2%}")

        print(f"Median inter-purchase gap: {gaps.median():.2f} days")

        print(f"Mean inter-purchase gap: {gaps.mean():.2f} days")

        print(f"90th percentile gap: {gaps.quantile(0.9):.2f} days")

        print(f"Returned within 30 days: {within_30:.2%}")

        print(f"Returned within 60 days: {within_60:.2%}")

        print(f"Returned within 90 days: {within_90:.2%}")

        print(f"Returned within 75 days: {within_75:.2%}")

    return {
        'invoice_df': invoice_df,
        'gap_stats': gap_stats,
        'repeat_rate': repeat_rate,
        'within_30': within_30,
        'within_60': within_60,
        'within_90': within_90
    }