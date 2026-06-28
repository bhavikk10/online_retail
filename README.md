# Customer Intelligence Lab — Online Retail II Customer Analytics

An end-to-end customer analytics and machine learning project built on the **Online Retail II** dataset. The project converts raw invoice-level transaction data into customer-level behavioural features, retention labels, future value predictions, customer segments, revenue forecasts, explainability outputs, and an interactive dashboard for reviewing the complete modelling pipeline.

The central objective is not only to train models, but to answer a practical business question:

> Which customers are most likely to generate future value, how should they be segmented, and how reliable are the model outputs for campaign prioritization?

---

## Project Summary

This project analyses historical retail transaction data and builds a complete customer intelligence workflow covering:

* Transaction cleaning and purchase filtering
* Customer-level feature engineering
* 90-day retention prediction
* 90-day Customer Lifetime Value-style future spend prediction
* Behaviour-based customer segmentation
* Short-term weekly revenue forecasting
* SHAP-based model explainability
* Model diagnostics, failure analysis, and limitations
* A React dashboard for presenting results, evidence, artifacts, and reproducibility

The strongest result of the project is that **future revenue is highly concentrated among a small group of customers**. The final CLV model is most useful as a **prioritization model**, not merely as an exact rupee-level forecaster.

---

## Key Results

### Customer Modelling Dataset

| Metric                         |         Value |
| ------------------------------ | ------------: |
| Cleaned valid purchase rows    |       777,575 |
| Total cleaned purchase revenue | 17,237,799.87 |
| Modelling customers            |         2,778 |
| Future spenders                |         1,707 |
| Zero future spend customers    |         1,071 |
| Future spender rate            |        61.45% |
| Prediction window              |       90 days |
| Active customer window         |      180 days |

---

### Final CLV Model

The final selected model was a **Calibrated XGBoost Tweedie Regressor**.

| Metric                    |    Value |
| ------------------------- | -------: |
| RMSE                      | 1,976.27 |
| MAE                       |   529.88 |
| R²                        |    0.833 |
| Revenue Error             |   11.27% |
| Spearman Rank Correlation |   0.6172 |

The model performed especially well as a ranking model:

| Targeted Customer Group         | Actual Future Revenue Captured |
| ------------------------------- | -----------------------------: |
| Top 5% predicted CLV customers  |                         47.88% |
| Top 10% predicted CLV customers |                         57.10% |
| Top 20% predicted CLV customers |                         72.73% |
| Top 30% predicted CLV customers |                         80.21% |
| Top 50% predicted CLV customers |                         90.40% |

This means that the model can help prioritize marketing and retention resources toward customers expected to generate the most future value, to a great extent.

---

### Customer Segmentation

The final segmentation model uses **KMeans with 4 clusters**. KMeans was selected because it produced assigned, interpretable, and business-actionable customer groups.

| Segment                     | Customers | Customer Share | Future Revenue Share | Retention Rate | Avg Future Spend |
| --------------------------- | --------: | -------------: | -------------------: | -------------: | ---------------: |
| High-Value Loyalists        |       630 |         22.68% |               65.35% |         86.98% |         2,592.06 |
| Regular Mid-Value Customers |     1,031 |         37.11% |               18.51% |         62.46% |           448.70 |
| At-Risk Inactive Customers  |       697 |         25.09% |               10.65% |         52.22% |           381.92 |
| New / One-Time Customers    |       420 |         15.12% |                5.48% |         35.95% |           326.20 |

The most important segmentation finding:

> High-Value Loyalists are only **22.68%** of customers but contribute **65.35%** of future revenue.

---

### Revenue Forecasting

The project also includes an exploratory short-term revenue forecasting module.

| Metric               |     Value |
| -------------------- | --------: |
| Weekly observations  |       106 |
| Monthly observations |        25 |
| Best model           |    SARIMA |
| SARIMA RMSE          | 57,057.61 |
| SARIMA MAE           | 48,227.71 |
| SARIMA WAPE          |    18.29% |
| Naive WAPE           |    22.55% |

Forecasting is intentionally presented as **exploratory**. The weekly series is short and noisy, and most models failed to beat the naive baseline. SARIMA performed best overall, but the results should be interpreted as directional planning evidence rather than production-grade forecasting.

---

## What this project does differently

Many customer analytics projects stop at basic RFM segmentation or simple churn prediction. This project goes further by combining:

1. **Retention modelling** — whether the customer returns.
2. **CLV-style future spend prediction** — how much value the customer may generate.
3. **Customer segmentation** — how different customer groups behave.
4. **Forecasting** — how aggregate revenue may move in the short term.
5. **Explainability and diagnostics** — why models behave the way they do and where they fail.

The project also shows modelling judgement. It does not only present successful results; it includes failed experiments, misleading metrics, and limitations.

---

## Dataset

The project uses the **Online Retail II** dataset, which contains invoice-level transactions from a UK-based online retail business.

The original columns in the dataset include:

* Invoice number
* Stock code
* Product description
* Quantity
* Invoice date
* Unit price
* Customer ID
* Country

The raw dataset is transaction-level. The modelling pipeline transforms it into customer-level datasets for retention, CLV, clustering, and forecasting.

---

## Project Architecture

```text
Raw Online Retail II Excel file
        |
        v
Preprocessing and cleaning
        |
        v
Purchase filtering
        |
        v
Customer-level feature engineering
        |
        +-------------------------+
        |                         |
        v                         v
Retention dataset          CLV dataset
        |                         |
        v                         v
Classification models      Future spend models
        |                         |
        +-----------+-------------+
                    |
                    v
Customer segmentation
                    |
                    v
Revenue forecasting
                    |
                    v
SHAP explainability and diagnostics
                    |
                    v
Final consolidated outputs
                    |
                    v
React dashboard
```

---

## Repository Structure

```text
online_retail/
│
├── data/
│   └── online_retail_II.xlsx
│
├── assets/
│   ├── f1_rocauc_bar.png
│   └── monetaryboxplot.png
│
├── scripts/
│   └── prepare_frontend_assets.py
│
├── src/
│   ├── preprocessing.py
│   ├── classf_dataset.py
│   ├── classf_pipeline.py
│   ├── clv_dataset.py
│   ├── clv_regression.py
│   ├── tweedie_clv.py
│   ├── clustering.py
│   ├── time_series.py
│   ├── shap_analysis.py
│   ├── run_experiments.py
│   ├── app.py
│   │
│   ├── clv_diagnostic_tables/
│   ├── clv_diagnostic_plots/
│   ├── clustering_outputs/
│   ├── clustering_frontend_data/
│   ├── clustering_frontend_plots/
│   ├── time_series_outputs/
│   ├── time_series_plots/
│   ├── shap_outputs/
│   ├── shap_plots/
│   │
│   └── final_outputs/
│       ├── data/
│       ├── frontend/
│       ├── plots/
│       └── summaries/
│
└── dashboard/
    ├── public/
    │   ├── final_outputs/
    │   ├── raw_outputs/
    │   └── generated/
    │
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   ├── utils/
    │   ├── App.jsx
    │   └── main.jsx
    │
    └── package.json
```

---

## Main Modules

### 1. Preprocessing

Script:

```text
src/preprocessing.py
```

The preprocessing module standardizes and cleans the raw Excel workbook. It handles missing values, invalid prices, transaction flags, cancellation indicators, return indicators, non-product stock codes, and transaction value creation.

Important cleaning logic includes:

* Removing rows without valid customer identifiers
* Separating genuine purchases from returns and cancellations
* Filtering non-product stock codes such as postage, bank charges, manual adjustments, and platform fees
* Preserving return/cancellation behaviour as potential customer-level signals
* Creating transaction value fields for later aggregation

This step is critical because bad cleaning would make cancelled invoices, returns, and fees appear like normal customer demand.

---

### 2. Customer-Level Feature Engineering

Scripts:

```text
src/classf_dataset.py
src/clv_dataset.py
```

The project converts raw invoice lines into customer-level behavioural features.

Important features include:

* Frequency
* Monetary value
* Recency
* Average basket value
* Average quantity
* Product variety
* Purchase rate
* Average purchase gap
* Gap variability
* Purchases in the last 30 and 90 days
* Spend in the last 30 and 90 days
* Return rate
* Cancellation rate
* Spend trend ratio
* Frequency trend ratio

This transformation is important because customer-level modelling requires one row per customer, not one row per invoice item.

---

### 3. Retention Modelling

Scripts:

```text
src/classf_pipeline.py
src/run_experiments.py
```

Retention modelling predicts whether a customer will generate any future spend in the next 90 days.

The binary target is:

```text
RetentionLabel = 1 if FutureSpend90Days > 0
RetentionLabel = 0 otherwise
```

This task is useful for identifying customers likely to return, but it has an important limitation: it treats all returning customers equally, regardless of whether they spend a small or large amount.

Models tested include:

* Logistic Regression
* KNN
* Decision Tree
* SVC
* Random Forest
* XGBoost

Retention is treated as a supporting task. The main business value comes from CLV-style future spend prediction.

#### Retention Model Scores

The retention task was evaluated as a binary classification problem where the positive class represents customers who generated future spend within the 90-day prediction window.

| Model                   | Accuracy | Precision | Recall | F1 Score | ROC AUC | Best / Recorded Configuration                             |
| ----------------------- | -------: | --------: | -----: | -------: | ------: | --------------------------------------------------------- |
| Majority Class Baseline |   0.6145 |    0.6145 | 1.0000 |   0.7612 |  0.5000 | Computed from positive label share                        |
| Logistic Regression     |   0.6655 |    0.7910 | 0.6199 |   0.6951 |  0.7560 | `penalty=l2`, `C=1`                                       |
| KNN                     |   0.6655 |    0.7179 | 0.7515 |   0.7343 |  0.7443 | `n_neighbors=20`, `weights=uniform`                       |
| Decision Tree           |   0.6727 |    0.7581 | 0.6871 |   0.7209 |  0.7364 | `max_depth=3`, `min_samples_split=2`                      |
| SVC                     |   0.6475 |    0.8067 | 0.5614 |   0.6621 |  0.7582 | `kernel=linear`, `C=0.01`, `gamma=scale`                  |
| Random Forest           |   0.6871 |    0.8022 | 0.6520 |   0.7194 |  0.7649 | `n_estimators=500`, `max_depth=20`, `min_samples_leaf=18` |
| XGBoost Classifier      |   0.6960 |    0.7307 | 0.8012 |   0.7643 |  0.7734 | `n_estimators=100`, `max_depth=4`, `learning_rate=0.03`   |

The strongest standard retention model was XGBoost, with the best overall balance of F1 score and ROC AUC. The majority-class baseline is included to show that the classification models improved beyond simply predicting the dominant positive class.

#### Two-Stage Classification Submodel Scores

The two-stage CLV experiment also trained a separate purchase-probability model as Stage 1. This model was optimized more toward identifying future spenders than maximizing precision.

| Metric      |  Value |
| ----------- | -----: |
| Accuracy    | 0.6871 |
| Precision   | 0.6953 |
| Recall      | 0.8743 |
| F1 Score    | 0.7746 |
| ROC AUC     | 0.7711 |
| PR AUC      | 0.8588 |
| Brier Score | 0.1956 |

The two-stage classifier achieved high recall, meaning it captured most future spenders. However, this did not automatically translate into the best CLV model because errors in the classification stage affected the final expected value estimate.

---

### 4. CLV Prediction

Scripts:

```text
src/clv_regression.py
src/tweedie_clv.py
```

The CLV module predicts 90-day future customer spend.

The target is:

```text
FutureSpend90Days
```

This target is difficult because it is:

* Non-negative
* Zero-heavy
* Right-skewed
* Affected by a small number of very high-value customers

The final model is a **Calibrated XGBoost Tweedie Regressor**.

Tweedie regression was selected because it is better suited for targets that contain many zero or low values along with positive continuous values.

The model is evaluated not only by RMSE and R², but also by business ranking quality through revenue capture curves.

#### Original / Log-Evaluated CLV Regression Scores

These models were trained for 90-day future spend prediction and evaluated on both the original monetary scale and the log-transformed scale. The original-scale metrics show business error, while the log metrics show how well the model handled the skewed spend distribution.

| Model                   |           MSE |     RMSE |    MAE |     R² | Median AE | RMSE Log | R² Log | Best / Recorded Configuration                                |
| ----------------------- | ------------: | -------: | -----: | -----: | --------: | -------: | -----: | ------------------------------------------------------------ |
| Baseline                |             — | 4,952.48 |      — |      — |         — |        — |      — | Mean baseline from original CLV regression run               |
| Ridge Linear Regression | 11,952,042.07 | 3,457.17 | 649.64 | 0.5127 |    226.80 |   2.7018 | 0.2802 | `alpha=10`                                                   |
| KNN                     | 22,032,822.54 | 4,693.91 | 717.43 | 0.1017 |    228.25 |   2.7198 | 0.2706 | `n_neighbors=30`, `weights=uniform`, `p=1`                   |
| Decision Tree           | 20,146,146.94 | 4,488.45 | 724.13 | 0.1786 |    230.53 |   2.8238 | 0.2138 | `max_depth=5`, `min_samples_leaf=16`, `min_samples_split=50` |
| SVR                     | 18,660,774.17 | 4,319.81 | 664.76 | 0.2392 |    232.31 |   2.8590 | 0.1941 | `kernel=rbf`, `C=1`, `epsilon=0.1`, `gamma=0.01`             |
| Random Forest           | 20,327,678.67 | 4,508.62 | 691.47 | 0.1712 |    213.59 |   2.7117 | 0.2750 | `n_estimators=200`, `max_depth=20`, `min_samples_leaf=2`     |
| XGBoost                 | 19,565,310.86 | 4,423.27 | 682.60 | 0.2023 |    210.61 |   2.7170 | 0.2721 | `n_estimators=500`, `max_depth=3`, `learning_rate=0.01`      |
| Extra Trees             | 15,529,882.89 | 3,940.80 | 682.49 | 0.3668 |    224.80 |   2.7254 | 0.2676 | `n_estimators=200`, `max_depth=10`, `min_samples_leaf=8`     |
| HistGradientBoosting    | 21,143,597.70 | 4,598.22 | 688.75 | 0.1379 |    204.75 |   2.7304 | 0.2650 | `max_iter=100`, `max_depth=5`, `learning_rate=0.03`          |
| LGBM                    | 19,650,453.17 | 4,432.88 | 684.52 | 0.1988 |    224.31 |   2.7245 | 0.2681 | `n_estimators=100`, `num_leaves=15`, `max_depth=3`           |
| CatBoost                | 20,513,664.19 | 4,529.20 | 694.32 | 0.1636 |    217.09 |   2.7113 | 0.2752 | `iterations=500`, `depth=5`, `learning_rate=0.01`            |

The original/log-evaluated regression experiment showed that ordinary regression-style approaches struggled with the zero-heavy and highly skewed future spend target. Ridge regression performed best in this run by R², while Extra Trees reduced RMSE relative to most nonlinear baselines. These results motivated the later Tweedie experiments.

#### Tweedie CLV Scores

Tweedie-based modelling was tested because the CLV target was non-negative, zero-heavy, and continuous for positive spenders. This made Tweedie objectives more appropriate than ordinary regression for the final customer value task.

| Model           | Version      |           MSE |     RMSE |      MAE |      R² | Median AE |  RMSLE |   WMAPE | Revenue Error | Prediction / Actual Ratio | Spearman Rank Correlation | Calibration Factor |
| --------------- | ------------ | ------------: | -------: | -------: | ------: | --------: | -----: | ------: | ------------: | ------------------------: | ------------------------: | -----------------: |
| Baseline Mean   | Baseline     | 23,384,384.58 | 4,835.74 | 1,078.86 | -0.0000 |    821.93 | 4.3251 | 120.26% |         0.33% |                    1.0033 |                         — |             1.0000 |
| XGBoost Tweedie | Uncalibrated |  4,021,623.98 | 2,005.40 |   529.69 |  0.8280 |    253.60 | 3.4447 |  59.04% |        12.29% |                    0.8771 |                    0.6172 |             1.0000 |
| XGBoost Tweedie | Calibrated   |  3,905,660.48 | 1,976.27 |   529.88 |  0.8330 |    251.49 | 3.4513 |  59.06% |        11.27% |                    0.8873 |                    0.6172 |             1.0116 |
| LGBM Tweedie    | Uncalibrated |  7,181,825.02 | 2,679.89 |   647.89 |  0.6929 |    206.04 | 3.0997 |  72.22% |        49.47% |                    0.5053 |                    0.5234 |             1.0000 |
| LGBM Tweedie    | Calibrated   |  7,022,738.65 | 2,650.05 |   647.23 |  0.6997 |    210.89 | 3.0991 |  72.14% |        48.61% |                    0.5139 |                    0.5234 |             1.0170 |

The calibrated XGBoost Tweedie model was selected as the final CLV model because it achieved the strongest overall balance of RMSE, R², aggregate revenue alignment, and rank-order usefulness. LGBM Tweedie had a lower RMSLE, but it substantially underpredicted aggregate revenue, with a prediction-to-actual ratio close to 0.51 even after calibration.

Calibration means adjusting the scale of model predictions so that aggregate predicted revenue better aligns with aggregate actual revenue. In this project, calibration did not change the ranking logic of the model; it adjusted the predicted spend level. This mattered because the CLV model was evaluated both as an individual prediction model and as a revenue prioritization tool.

#### CLV Lift Performance

| Targeted Customer Group         | Actual Future Revenue Captured |              Lift Interpretation |
| ------------------------------- | -----------------------------: | -------------------------------: |
| Top 5% predicted CLV customers  |                         47.88% | 9.58x lift over random targeting |
| Top 10% predicted CLV customers |                         57.10% | 5.71x lift over random targeting |
| Top 20% predicted CLV customers |                         72.73% | 3.64x lift over random targeting |
| Top 30% predicted CLV customers |                         80.21% | 2.67x lift over random targeting |
| Top 50% predicted CLV customers |                         90.40% | 1.81x lift over random targeting |

The lift results are the strongest business-facing output of the CLV module. They show that the model can prioritize campaign spend toward a small group of customers that captures a disproportionately large share of future revenue.

---

### 5. Two-Stage CLV Experiment

Script:

```text
src/2stage.py
```

The project also tested a two-stage CLV approach:

```text
Predicted CLV = P(customer buys) × Expected spend if customer buys
```

This approach is conceptually reasonable, but it underperformed the direct Tweedie model.

The calibrated two-stage model achieved approximately:

```text
R² ≈ 0.585
```

The final direct calibrated XGBoost Tweedie model achieved approximately:

```text
R² ≈ 0.833
```

The two-stage model likely underperformed because classification error compounded into spend prediction error.

#### Two-Stage CLV Scores

The two-stage CLV experiment separated the problem into purchase probability and conditional spend. The final prediction was calculated as expected value:

```text
Predicted CLV = P(customer buys) × Expected spend if customer buys
```

##### Stage 2 Conditional Spend Model

| Metric                             |    Value |
| ---------------------------------- | -------: |
| Positive RMSE                      | 3,694.58 |
| Positive MAE                       |   737.25 |
| Positive R²                        |   0.6330 |
| Positive RMSLE                     |   0.8376 |
| Positive Revenue Error             |   16.08% |
| Positive Prediction / Actual Ratio |   0.8392 |

The conditional regression model was evaluated only on actual future buyers. This stage performed reasonably on positive spenders, but the final two-stage CLV prediction still depended on the purchase-probability model from Stage 1.

##### Final Two-Stage CLV Model Comparison

| Model                            |           MSE |     RMSE |      MAE |      R² | Median AE |  RMSLE | Revenue Error | Prediction / Actual Ratio | Actual Total Revenue | Predicted Total Revenue | Calibration Factor |
| -------------------------------- | ------------: | -------: | -------: | ------: | --------: | -----: | ------------: | ------------------------: | -------------------: | ----------------------: | -----------------: |
| Baseline Mean                    | 23,384,384.58 | 4,835.74 | 1,078.86 | -0.0000 |    821.93 | 4.3251 |         0.33% |                    1.0033 |           498,798.83 |              500,450.27 |             1.0000 |
| Two-Stage Tweedie Uncalibrated   | 10,739,120.00 | 3,277.06 |   617.98 |  0.5408 |    268.49 | 3.6022 |        21.57% |                    0.7843 |           498,798.83 |              391,204.53 |             1.0000 |
| Two-Stage Tweedie Calibrated     |  9,696,000.00 | 3,113.84 |   620.24 |  0.5854 |    288.73 | 3.6661 |        12.60% |                    0.8740 |           498,798.83 |              435,927.67 |             1.1143 |
| Final Calibrated XGBoost Tweedie |  3,905,660.48 | 1,976.27 |   529.88 |  0.8330 |    251.49 | 3.4513 |        11.27% |                    0.8873 |           498,798.83 |              442,570.97 |             1.0116 |

The two-stage formulation was conceptually useful, but it underperformed the direct Tweedie approach. The likely reason is error compounding: errors in the purchase-probability stage directly affected the conditional spend estimate, which weakened the final expected value prediction.

---

### 6. Customer Segmentation

Script:

```text
src/clustering.py
```

The clustering module groups customers based on behavioural features such as recency, frequency, monetary value, purchase rhythm, return behaviour, product diversity, and recent activity.

Models tested include:

* KMeans
* DBSCAN
* Gaussian Mixture Model
* Agglomerative Clustering

KMeans with 4 clusters was selected as the final segmentation model.

Although DBSCAN produced attractive metric values in some runs, it was not selected because it labelled too many customers as noise. In an earlier run, DBSCAN labelled approximately **97.52%** of customers as noise, making the high silhouette score misleading for business segmentation.

KMeans was selected because it produced assigned, interpretable, business-readable customer groups.

#### KMeans k-Search Scores

The clustering dataset contained 2,778 customers and used 23 scaled behavioural features. The first two PCA components explained 49.41% of the variance and were used for visualization.

|  K | Silhouette Score | Davies-Bouldin Index | Calinski-Harabasz Score | Inertia | Interpretation                                                                 |
| -: | ---------------: | -------------------: | ----------------------: | ------: | ------------------------------------------------------------------------------ |
|  2 |           0.3334 |               1.2456 |                  804.27 |       — | Strongest silhouette, but too coarse for business segmentation                 |
|  3 |           0.2417 |               1.5006 |                  806.34 |       — | Better separation than 4 on some metrics, but less useful business granularity |
|  4 |           0.1958 |               1.7089 |                  662.11 |       — | Final selected segmentation because it produced interpretable customer groups  |
|  5 |           0.1992 |                    — |                       — |       — | Slightly higher silhouette than k=4, but less interpretable                    |
|  6 |           0.2089 |                    — |                       — |       — | Higher complexity, weaker business clarity                                     |

Although k=2 had the best silhouette score, it was too broad to support useful customer strategy. KMeans with four clusters was selected because it separated customers into clear business groups: High-Value Loyalists, Regular Mid-Value Customers, At-Risk Inactive Customers, and New / One-Time Customers.

#### Clustering Model Comparison

| Model                    | Number of Clusters | Noise Customers | Noise Share | Silhouette Score | Davies-Bouldin Index | Calinski-Harabasz Score | Final Use                       |
| ------------------------ | -----------------: | --------------: | ----------: | ---------------: | -------------------: | ----------------------: | ------------------------------- |
| KMeans                   |                  4 |               0 |       0.00% |           0.1958 |               1.7089 |                  662.11 | Final selected model            |
| DBSCAN                   |                  4 |             623 |      22.43% |           0.3669 |               1.1807 |                  457.66 | Diagnostic only                 |
| Gaussian Mixture Model   |                  4 |               0 |       0.00% |           0.2147 |               2.0077 |                  585.39 | Alternative clustering baseline |
| Agglomerative Clustering |                  4 |               0 |       0.00% |           0.1997 |               2.0063 |                  585.15 | Hierarchical baseline           |

DBSCAN achieved a stronger silhouette score in the improved run, but it still assigned a meaningful share of customers to noise. In an earlier run, DBSCAN labelled approximately 97.52% of customers as noise, which made the high silhouette score misleading. For business segmentation, every customer should receive an actionable label, so KMeans was preferred.

#### DBSCAN Diagnostic Notes

| DBSCAN Run          | Clusters |      Noise Customers / Share | Silhouette Score | Interpretation                                                                                      |
| ------------------- | -------: | ---------------------------: | ---------------: | --------------------------------------------------------------------------------------------------- |
| Earlier DBSCAN run  |        — |                 97.52% noise |                — | Misleading result because almost all customers were treated as noise                                |
| Improved DBSCAN run |        4 | 623 customers / 22.43% noise |           0.3669 | Better than the earlier run, but still less suitable than KMeans for assigned business segmentation |

DBSCAN was useful diagnostically, but it was not selected as the final segmentation model because its best metric values came with substantial noise assignment. For campaign segmentation, every customer needs a usable business label, so complete assignment and interpretability were weighted more heavily than silhouette alone.

---

### 7. Revenue Forecasting

Script:

```text
src/time_series.py
```

The forecasting module aggregates valid purchase revenue into weekly and monthly time-series.

Models tested include:

* Naive forecast
* Moving averages
* Simple Exponential Smoothing
* Holt
* Holt-Winters
* ARIMA
* SARIMA
* Random Forest lag model
* XGBoost lag model

The best model was SARIMA, but forecasting here, is intentionally framed as mostly exploratory because the dataset contains only:

```text
106 weekly observations
25 monthly observations
```

Most models failed to beat the naive baseline, which is an important finding rather than something to hide. It indicates that the revenue series is short, noisy, and difficult to forecast reliably.

---

### 8. SHAP Explainability

Script:

```text
src/shap_analysis.py
```

SHAP outputs include:

* Feature importance tables
* Beeswarm plots
* Bar importance plots
* Dependence plots
* Waterfall plots for individual customer explanations for both retention and clv models.

SHAP is treated carefully:

> SHAP explains model attribution, not causality.

---

## Dashboard

The React dashboard is located in:

```text
dashboard/
```

It is built with:

* Vite
* React
* Tailwind CSS
* Recharts
* Plotly
* PapaParse
* Custom data loading and artifact validation utilities

The dashboard contains six main pages:

1. Overview
2. Data & Pipeline
3. Customer Value
4. Customer Segments
5. Revenue Forecast
6. Model Review & Appendix

---

## Dashboard Pages

### Overview

The overview page summarizes the strongest results of the project:

* Revenue concentration among high-value customers
* CLV model ranking performance
* Segment-level revenue concentration
* Forecasting caveats
* Evidence cards with detailed modal explanations

The main project thesis is:

> A small group of customers drives most future revenue, and CLV ranking identifies that group better than simple retention modelling.

---

### Data & Pipeline

This page explains how raw invoice rows become model-ready datasets.

It covers:

* Raw Excel workbook
* Preprocessing
* Purchase filtering
* Feature engineering
* Retention dataset construction
* CLV dataset construction
* Segmentation dataset construction
* Time-series aggregation
* Final frontend artifacts

The page also includes representative dataset previews for auditability.

---

### Customer Value

This page combines retention and CLV analysis.

It explains:

* Retention label definition
* Future spender and zero-spender counts
* Why retention is useful but incomplete
* Why CLV is more useful for prioritization
* Final CLV model performance
* CLV lift and revenue capture
* Zero-spender diagnostics
* SHAP explainability status

---

### Customer Segments

This page presents the final KMeans customer segments.

It includes:

* Segment cards
* Customer share versus revenue share
* Segment retention versus zero-spend rate
* PCA and 3D customer maps
* Segment profile heatmap
* Segment-level recommendations

The most important segment finding is:

> High-Value Loyalists are only 22.68% of customers but contribute 65.35% of future revenue.

---

### Revenue Forecast

This page reviews exploratory revenue forecasting.

It includes:

* Weekly revenue trend
* Monthly revenue trend
* Forecast model comparison
* Actual versus predicted weekly revenue
* Future 12-week forecast
* Forecast horizon controls
* Model limitations

The page clearly states that forecasting is directional and not production-grade.

---

### Model Review & Appendix

This page contains:

* Model Lab
* Model diagnostics
* Failure analysis
* SHAP explainability
* Business recommendations
* Artifact map
* Reproducibility notes
* Project health report

This section is included to make the project auditable and to show modelling judgement.

---

## How To Run The Project

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd online_retail
```

---

### 2. Create Python Environment

```bash
python -m venv .venv
```

Activate it:

```bash
# Windows
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

If a requirements file is not available, install the main libraries manually:

```bash
pip install pandas numpy scikit-learn xgboost shap matplotlib seaborn statsmodels openpyxl joblib
```

---

### 3. Place Dataset

Place the Online Retail II Excel file at:

```text
data/online_retail_II.xlsx
```

---

### 4. Run Main ML Scripts

From the project root or `src/` depending on your local setup:

```bash
cd src
python preprocessing.py
python run_experiments.py
python tweedie_clv.py
python clustering.py
python time_series.py
python shap_analysis.py
```

Some scripts may depend on previously generated intermediate files.

---

### 5. Prepare Frontend Assets

From the project root:

```bash
python scripts/prepare_frontend_assets.py
```

This copies and validates generated tables, plots, summaries, and artifacts into the dashboard’s public folder.

---

### 6. Run Dashboard

```bash
cd dashboard
npm install
npm run dev
```

Open the local URL shown by Vite, usually:

```text
http://localhost:5173
```

---

### 7. Build Dashboard

```bash
npm run build
```

The dashboard should build without runtime-breaking chart errors.

---

## Important Generated Outputs

### CLV Outputs

```text
src/clv_diagnostic_tables/
src/clv_diagnostic_plots/
```

Important files include:

* `clv_model_comparison.csv`
* `clv_lift_table.csv`
* `clv_predicted_decile_calibration.csv`
* `clv_zero_spender_diagnostics.csv`
* `clv_error_by_actual_decile.csv`

These files support CLV model comparison, lift analysis, calibration review, and error diagnostics.

---

### Clustering Outputs

```text
src/clustering_outputs/
src/clustering_frontend_data/
src/clustering_frontend_plots/
```

Important files include:

* `kmeans_cluster_profiles.csv`
* `clustered_customers.csv`
* `clustering_model_comparison.csv`
* `kmeans_k_search_results.csv`
* `dbscan_parameter_search_results.csv`
* `segment_cards.json`

These files support segmentation analysis, cluster comparison, frontend segment cards, PCA visuals, and business recommendations.

---

### Time-Series Outputs

```text
src/time_series_outputs/
src/time_series_plots/
```

Important files include:

* `weekly_revenue_series.csv`
* `monthly_revenue_series.csv`
* `forecast_model_comparison.csv`
* `weekly_forecast_results.csv`
* `future_12_week_forecast.csv`

These files support forecasting charts, model comparison, and future revenue trend review.

---

### Final Consolidated Outputs

```text
src/final_outputs/
```

This folder contains frontend-ready copies of the most important project outputs:

```text
src/final_outputs/data/
src/final_outputs/frontend/
src/final_outputs/plots/
src/final_outputs/summaries/
```

These are the artifacts used by the React dashboard.

---

## Model Selection Reasoning

### Why CLV Is More Important Than Retention

Retention answers:

```text
Will the customer return?
```

CLV answers:

```text
How much future value might the customer generate?
```

A customer who returns and spends 30 is not equivalent to a customer who returns and spends 10,000. Retention is useful for identifying likely returners, but CLV is more useful for campaign prioritization.

---

### Why XGBoost Tweedie Was Selected

Future spend is difficult to model because it is:

* Zero-heavy
* Non-negative
* Highly skewed
* Influenced by a small number of high-value customers

The Tweedie objective is better suited to this structure than ordinary regression. The final calibrated XGBoost Tweedie model produced strong RMSE, R², revenue error, and lift performance.

---

### Why KMeans Was Selected Over DBSCAN

DBSCAN produced misleadingly attractive metrics in some runs because it labelled too many customers as noise. In campaign segmentation, customers need to be assigned to interpretable groups. KMeans with 4 clusters produced stable and business-readable segments.

---

### Why Forecasting Is Treated Carefully

The weekly revenue series contains only 106 observations, and the monthly series contains only 25 observations. This is too limited for strong long-term forecasting claims. SARIMA performed best, but the module is presented as exploratory short-term planning evidence.

---

## Business Interpretation

### Protect High-Value Loyalists

High-Value Loyalists represent only 22.68% of customers but contribute 65.35% of future revenue. This group should receive the strongest retention investment.

---

### Grow Regular Mid-Value Customers

Regular Mid-Value Customers are the largest segment and contribute meaningful future revenue.

---

### Reactivate At-Risk Inactive Customers Selectively

At-Risk Inactive Customers have high recency and nearly half have zero future spend.

Recommended actions:

---

### Nurture New / One-Time Customers

New / One-Time Customers have low frequency and high zero-spend risk.

---

### Use CLV Ranking For Campaign Prioritization

The top 10% predicted CLV customers captured 57.10% of future revenue. This supports using CLV ranking for budget allocation instead of treating all retained customers equally.

---

## Limitations

This project includes limitations intentionally because they are important for honest model evaluation.

1. **Historical dataset**
   The project uses historical transaction data and does not connect to a live production system.

2. **Single main cutoff window**
   The main CLV experiment uses a fixed cutoff date. Rolling-window validation would improve robustness.

3. **Short forecasting series**
   The forecasting module uses 106 weekly observations and 25 monthly observations, limiting long-term forecast reliability.

4. **CLV outliers**
   Very high-value customers are difficult to predict exactly. The model is stronger for ranking than exact spend prediction.

5. **Zero-spender uncertainty**
   Some customers with zero future spend still receive positive predicted CLV because the model estimates expected value.

6. **SHAP is attribution, not causality**
   SHAP explains model behaviour but does not prove that changing a feature will cause a business outcome.

7. **Dataset domain limitations**
   Online Retail II is useful for modelling but does not include all real-world customer context such as marketing exposure, web behaviour, or customer acquisition source.

---

---

## Skills Demonstrated

This project demonstrates:

* Data cleaning and preprocessing
* Feature engineering
* Customer analytics
* Classification modelling
* Regression modelling
* Zero-heavy target modelling
* XGBoost and Tweedie objectives
* Model calibration
* Model comparison
* Clustering and segmentation
* Time-series forecasting
* SHAP explainability
* Business interpretation
* Dashboard development
* Artifact validation
* Reproducibility
* Error handling and model diagnostics

---

## Tech Stack

### Python / ML

* Python
* Pandas
* NumPy
* Scikit-learn
* XGBoost
* SHAP
* Statsmodels
* Matplotlib
* Seaborn
* OpenPyXL

### Frontend

* React
* Vite
* Tailwind CSS
* Recharts
* Plotly
* PapaParse
* JavaScript

---

---

## Reviewer Notes

The most important results are:

1. **CLV lift performance**
   Top 10% predicted customers captured 57.10% of future revenue.

2. **Segment revenue concentration**
   High-Value Loyalists are 22.68% of customers but generate 65.35% of future revenue.

3. **Final model choice**
   Calibrated XGBoost Tweedie achieved approximately 0.833 R².

4. **Honest forecasting treatment**
   SARIMA beat naive, but forecasting is presented as exploratory due to limited observations.

5. **Failure analysis**
   DBSCAN and two-stage CLV were tested but not selected due to weaker performance.

---

## Author

**Bhavik Malik**
B.Tech Artificial Intelligence and Machine Learning
University School of Automation and Robotics, GGSIPU

---

## License

This project is intended for academic and portfolio use. Dataset usage should follow the original Online Retail II dataset license and source terms.
