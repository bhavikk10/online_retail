import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, FunctionTransformer
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.mixture import GaussianMixture
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score
)

from clv_dataset import build_retention_dataset
from preprocessing import preprocess_online_retail


# ============================================================
# OUTPUT FOLDERS
# ============================================================

OUTPUT_DIR = "clustering_outputs"
PLOT_DIR = "clustering_plots"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PLOT_DIR, exist_ok=True)


# ============================================================
# LOAD CLEANED MASTER DATASET
# ============================================================

df = preprocess_online_retail(
    file_path="online_retail_II.xlsx",
    verbose=False
)


# ============================================================
# BUILD CUSTOMER RETENTION / CLV DATASET
# ============================================================

clv_df = build_retention_dataset(
    df,
    cutoff_date="2011-09-09",
    prediction_days=90,
    active_days=180,
    verbose=True
)

# Ensure target exists
if "FutureSpend90Days" not in clv_df.columns:
    raise ValueError("FutureSpend90Days column is missing from clv_df.")

# Correct retention label
clv_df["RetentionLabel"] = (clv_df["FutureSpend90Days"] > 0).astype(int)


# ============================================================
# CORRECT DATASET SUMMARY
# ============================================================

total_customers = len(clv_df)
future_positive = (clv_df["FutureSpend90Days"] > 0).sum()
future_zero = (clv_df["FutureSpend90Days"] == 0).sum()
avg_future_spend = clv_df["FutureSpend90Days"].mean()

print("\nCorrect Clustering Dataset Summary:")
print(f"Total customers: {total_customers}")
print(f"Customers with future spend > 0: {future_positive}")
print(f"Customers with future spend = 0: {future_zero}")
print(f"Average future spend: {avg_future_spend:.2f}")


# ============================================================
# HANDLE AvgGapDays PROPERLY
# ============================================================

if "AvgGapDays" in clv_df.columns:
    clv_df["AvgGapDaysMissing"] = clv_df["AvgGapDays"].isna().astype(int)
else:
    raise ValueError("AvgGapDays column is missing from clv_df.")


# ============================================================
# DEFINE CLUSTERING FEATURES
# IMPORTANT:
# Do NOT include FutureSpend90Days or RetentionLabel in clustering.
# They are only used later for profiling.
# ============================================================

clustering_features = [
    "Recency",
    "Frequency",
    "Monetary",
    "AvgBasketValue",
    "AvgQuantity",
    "UniqueProducts",
    "LifetimeDays",
    "PurchaseRate",
    "AvgGapDays",
    "AvgGapDaysMissing",
    "StdGapDays",
    "PurchasesLast30Days",
    "SpendLast30Days",
    "PurchasesLast90Days",
    "SpendLast90Days",
    "ReturnRate",
    "RevenuePerDay",
    "AvgSpendPerProduct",
    "ProductDiversityRate",
    "RecencyFrequency",
    "SpendTrendRatio",
    "FrequencyLast90DaysRatio",
    "IsNewCustomer"
]

missing_features = [col for col in clustering_features if col not in clv_df.columns]

if missing_features:
    raise ValueError(f"Missing clustering features: {missing_features}")

X_cluster = clv_df[clustering_features].copy()

print("\nClustering features used:")
print(clustering_features)


# ============================================================
# FEATURE GROUPS
# ============================================================

log_features = [
    "Frequency",
    "Monetary",
    "AvgBasketValue",
    "UniqueProducts",
    "SpendLast30Days",
    "SpendLast90Days",
    "RevenuePerDay",
    "AvgSpendPerProduct",
    "ProductDiversityRate",
    "RecencyFrequency"
]

scale_features = [
    "Recency",
    "AvgQuantity",
    "LifetimeDays",
    "PurchaseRate",
    "AvgGapDays",
    "AvgGapDaysMissing",
    "StdGapDays",
    "PurchasesLast30Days",
    "PurchasesLast90Days",
    "ReturnRate",
    "SpendTrendRatio",
    "FrequencyLast90DaysRatio",
    "IsNewCustomer"
]

# Keep only columns that actually exist
log_features = [col for col in log_features if col in X_cluster.columns]
scale_features = [col for col in scale_features if col in X_cluster.columns]


# ============================================================
# SAFE LOG TRANSFORM
# Clips negative values to zero before log1p.
# This avoids invalid values if returns create negative spend.
# ============================================================

def safe_log1p(x):
    return np.log1p(np.clip(x, a_min=0, a_max=None))


log_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("log_transform", FunctionTransformer(safe_log1p, validate=False)),
    ("scaler", StandardScaler())
])

scale_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

preprocessor = ColumnTransformer([
    ("log", log_pipeline, log_features),
    ("scale", scale_pipeline, scale_features)
], remainder="drop")


X_scaled = preprocessor.fit_transform(X_cluster)

print("\nScaled clustering matrix shape:", X_scaled.shape)


# ============================================================
# PCA FOR VISUALIZATION ONLY
# ============================================================

pca = PCA(n_components=2, random_state=42)
pca_coords = pca.fit_transform(X_scaled)

pca_df = pd.DataFrame({
    "Customer_ID": clv_df["Customer_ID"].values,
    "PCA1": pca_coords[:, 0],
    "PCA2": pca_coords[:, 1]
})

explained_variance = pca.explained_variance_ratio_.sum()

print(f"\nPCA explained variance using 2 components: {explained_variance:.4f}")


# ============================================================
# KMEANS K SEARCH
# ============================================================

print("\nRunning KMeans k-search...")

kmeans_results = []

for k in range(2, 11):
    kmeans = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=20
    )

    labels = kmeans.fit_predict(X_scaled)

    inertia = kmeans.inertia_
    silhouette = silhouette_score(X_scaled, labels)
    db_score = davies_bouldin_score(X_scaled, labels)
    ch_score = calinski_harabasz_score(X_scaled, labels)

    kmeans_results.append({
        "K": k,
        "Inertia": inertia,
        "Silhouette_Score": silhouette,
        "Davies_Bouldin_Score": db_score,
        "Calinski_Harabasz_Score": ch_score
    })

kmeans_results_df = pd.DataFrame(kmeans_results)

print("\nKMeans k-search results:")
print(kmeans_results_df)

kmeans_results_df.to_csv(
    os.path.join(OUTPUT_DIR, "kmeans_k_search_results.csv"),
    index=False
)


# ============================================================
# DBSCAN PARAMETER SEARCH
# Diagnostic only.
# DBSCAN is rejected later if noise is too high.
# ============================================================

print("\nRunning DBSCAN parameter search...")

dbscan_results = []

eps_values = [0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]
min_samples_values = [5, 10, 15, 20]

for eps in eps_values:
    for min_samples in min_samples_values:
        dbscan = DBSCAN(
            eps=eps,
            min_samples=min_samples
        )

        labels = dbscan.fit_predict(X_scaled)

        unique_labels = set(labels)
        clusters = len(unique_labels - {-1})
        noise_count = np.sum(labels == -1)
        noise_pct = noise_count / len(labels) * 100

        # Only score when at least 2 real clusters exist
        if clusters >= 2:
            valid_mask = labels != -1

            # Score only non-noise points
            if valid_mask.sum() > 1 and len(set(labels[valid_mask])) >= 2:
                silhouette = silhouette_score(X_scaled[valid_mask], labels[valid_mask])
                db_score = davies_bouldin_score(X_scaled[valid_mask], labels[valid_mask])
                ch_score = calinski_harabasz_score(X_scaled[valid_mask], labels[valid_mask])
            else:
                silhouette = np.nan
                db_score = np.nan
                ch_score = np.nan
        else:
            silhouette = np.nan
            db_score = np.nan
            ch_score = np.nan

        dbscan_results.append({
            "eps": eps,
            "min_samples": min_samples,
            "Clusters": clusters,
            "Noise_Count": noise_count,
            "Noise_%": noise_pct,
            "Silhouette_Score": silhouette,
            "Davies_Bouldin_Score": db_score,
            "Calinski_Harabasz_Score": ch_score
        })

dbscan_results_df = pd.DataFrame(dbscan_results)

dbscan_results_df = dbscan_results_df.sort_values(
    by=["Noise_%", "Silhouette_Score"],
    ascending=[True, False]
)

print("\nDBSCAN search results:")
print(dbscan_results_df.head(15))

dbscan_results_df.to_csv(
    os.path.join(OUTPUT_DIR, "dbscan_parameter_search_results.csv"),
    index=False
)


# ============================================================
# FINAL MODEL CHOICE
# K=4 is chosen for business interpretability.
# K=2 may have better pure clustering metrics, but K=4 gives
# more useful customer segments.
# ============================================================

FINAL_K = 4


# ============================================================
# TRAIN FINAL CLUSTERING MODELS
# ============================================================

models = {
    "KMeans": KMeans(
        n_clusters=FINAL_K,
        random_state=42,
        n_init=20
    ),
    "Agglomerative": AgglomerativeClustering(
        n_clusters=FINAL_K
    ),
    "GaussianMixture": GaussianMixture(
        n_components=FINAL_K,
        random_state=42
    )
}

model_results = {}

for model_name, model in models.items():
    print(f"\nRunning {model_name}...")

    if model_name == "GaussianMixture":
        labels = model.fit_predict(X_scaled)
    else:
        labels = model.fit_predict(X_scaled)

    clusters = len(set(labels))
    noise_count = np.sum(labels == -1)
    noise_pct = noise_count / len(labels) * 100

    silhouette = silhouette_score(X_scaled, labels)
    db_score = davies_bouldin_score(X_scaled, labels)
    ch_score = calinski_harabasz_score(X_scaled, labels)

    model_results[model_name] = {
        "labels": labels,
        "Clusters": clusters,
        "Noise_Count": noise_count,
        "Noise_%": noise_pct,
        "Silhouette_Score": silhouette,
        "Davies_Bouldin_Score": db_score,
        "Calinski_Harabasz_Score": ch_score
    }

    print(f"Clusters found: {clusters}")
    print(f"Noise count: {noise_count}")
    print(f"Noise %: {noise_pct:.2f}")
    print(f"Silhouette Score: {silhouette:.4f}")
    print(f"Davies Bouldin Score: {db_score:.4f}")
    print(f"Calinski Harabasz Score: {ch_score:.4f}")


# ============================================================
# OPTIONAL DBSCAN FINAL DIAGNOSTIC
# Pick best DBSCAN with acceptable noise if possible.
# Reject if noise is too high.
# ============================================================

acceptable_dbscan = dbscan_results_df[
    (dbscan_results_df["Clusters"] >= 2) &
    (dbscan_results_df["Noise_%"] <= 40)
].copy()

if len(acceptable_dbscan) > 0:
    best_dbscan_row = acceptable_dbscan.sort_values(
        by="Silhouette_Score",
        ascending=False
    ).iloc[0]
else:
    best_dbscan_row = dbscan_results_df.iloc[0]

best_eps = best_dbscan_row["eps"]
best_min_samples = int(best_dbscan_row["min_samples"])

print("\nRunning DBSCAN diagnostic...")
print(f"Best DBSCAN eps: {best_eps}")
print(f"Best DBSCAN min_samples: {best_min_samples}")

dbscan_final = DBSCAN(
    eps=best_eps,
    min_samples=best_min_samples
)

dbscan_labels = dbscan_final.fit_predict(X_scaled)

dbscan_clusters = len(set(dbscan_labels) - {-1})
dbscan_noise_count = np.sum(dbscan_labels == -1)
dbscan_noise_pct = dbscan_noise_count / len(dbscan_labels) * 100

if dbscan_clusters >= 2:
    valid_mask = dbscan_labels != -1

    if valid_mask.sum() > 1 and len(set(dbscan_labels[valid_mask])) >= 2:
        dbscan_silhouette = silhouette_score(X_scaled[valid_mask], dbscan_labels[valid_mask])
        dbscan_db_score = davies_bouldin_score(X_scaled[valid_mask], dbscan_labels[valid_mask])
        dbscan_ch_score = calinski_harabasz_score(X_scaled[valid_mask], dbscan_labels[valid_mask])
    else:
        dbscan_silhouette = np.nan
        dbscan_db_score = np.nan
        dbscan_ch_score = np.nan
else:
    dbscan_silhouette = np.nan
    dbscan_db_score = np.nan
    dbscan_ch_score = np.nan

model_results["DBSCAN"] = {
    "labels": dbscan_labels,
    "Clusters": dbscan_clusters,
    "Noise_Count": dbscan_noise_count,
    "Noise_%": dbscan_noise_pct,
    "Silhouette_Score": dbscan_silhouette,
    "Davies_Bouldin_Score": dbscan_db_score,
    "Calinski_Harabasz_Score": dbscan_ch_score
}

print(f"DBSCAN clusters found: {dbscan_clusters}")
print(f"DBSCAN noise count: {dbscan_noise_count}")
print(f"DBSCAN noise %: {dbscan_noise_pct:.2f}")


# ============================================================
# MODEL COMPARISON
# ============================================================

comparison_rows = []

for model_name, result in model_results.items():
    comparison_rows.append({
        "Model": model_name,
        "Clusters": result["Clusters"],
        "Noise_Count": result["Noise_Count"],
        "Noise_%": result["Noise_%"],
        "Silhouette_Score": result["Silhouette_Score"],
        "Davies_Bouldin_Score": result["Davies_Bouldin_Score"],
        "Calinski_Harabasz_Score": result["Calinski_Harabasz_Score"]
    })

comparison_df = pd.DataFrame(comparison_rows)

comparison_df = comparison_df.sort_values(
    by="Silhouette_Score",
    ascending=False
)

print("\nFinal Clustering Comparison:")
print(comparison_df)

comparison_df.to_csv(
    os.path.join(OUTPUT_DIR, "clustering_model_comparison.csv"),
    index=False
)


# ============================================================
# ADD CLUSTERS TO DATASET
# ============================================================

clustered_customers = clv_df.copy()

clustered_customers["KMeans_Cluster"] = model_results["KMeans"]["labels"]
clustered_customers["Agglomerative_Cluster"] = model_results["Agglomerative"]["labels"]
clustered_customers["GaussianMixture_Cluster"] = model_results["GaussianMixture"]["labels"]
clustered_customers["DBSCAN_Cluster"] = model_results["DBSCAN"]["labels"]

pca_df["KMeans_Cluster"] = clustered_customers["KMeans_Cluster"].values
pca_df["Agglomerative_Cluster"] = clustered_customers["Agglomerative_Cluster"].values
pca_df["GaussianMixture_Cluster"] = clustered_customers["GaussianMixture_Cluster"].values
pca_df["DBSCAN_Cluster"] = clustered_customers["DBSCAN_Cluster"].values


# ============================================================
# CLUSTER COUNTS
# ============================================================

print("\nKMeans Cluster Counts:")
print(clustered_customers["KMeans_Cluster"].value_counts().sort_index())

print("\nAgglomerative Cluster Counts:")
print(clustered_customers["Agglomerative_Cluster"].value_counts().sort_index())

print("\nGaussianMixture Cluster Counts:")
print(clustered_customers["GaussianMixture_Cluster"].value_counts().sort_index())

print("\nDBSCAN Cluster Counts:")
print(clustered_customers["DBSCAN_Cluster"].value_counts().sort_index())


# ============================================================
# KMEANS CLUSTER PROFILE
# ============================================================

profile_rows = []

for cluster_id in sorted(clustered_customers["KMeans_Cluster"].unique()):
    temp = clustered_customers[clustered_customers["KMeans_Cluster"] == cluster_id]

    cluster_size = len(temp)
    total_future_revenue = temp["FutureSpend90Days"].sum()
    total_historical_revenue = temp["Monetary"].sum()
    retained_customers = (temp["FutureSpend90Days"] > 0).sum()

    profile_rows.append({
        "KMeans_Cluster": cluster_id,
        "ClusterSize": cluster_size,
        "CustomerShare_%": cluster_size / len(clustered_customers) * 100,

        "AvgRecency": temp["Recency"].mean(),
        "AvgFrequency": temp["Frequency"].mean(),
        "AvgMonetary": temp["Monetary"].mean(),
        "TotalHistoricalRevenue": total_historical_revenue,

        "AvgBasketValue": temp["AvgBasketValue"].mean(),
        "AvgQuantity": temp["AvgQuantity"].mean(),
        "UniqueProducts_mean": temp["UniqueProducts"].mean(),
        "LifetimeDays_mean": temp["LifetimeDays"].mean(),
        "PurchaseRate_mean": temp["PurchaseRate"].mean(),
        "AvgGapDays": temp["AvgGapDays"].mean(),
        "AvgGapDaysMissingRate_%": temp["AvgGapDaysMissing"].mean() * 100,
        "StdGapDays_mean": temp["StdGapDays"].mean(),

        "PurchasesLast30Days_mean": temp["PurchasesLast30Days"].mean(),
        "SpendLast30Days_mean": temp["SpendLast30Days"].mean(),
        "PurchasesLast90Days_mean": temp["PurchasesLast90Days"].mean(),
        "SpendLast90Days_mean": temp["SpendLast90Days"].mean(),

        "ReturnRate_mean": temp["ReturnRate"].mean(),
        "RevenuePerDay_mean": temp["RevenuePerDay"].mean(),
        "AvgSpendPerProduct_mean": temp["AvgSpendPerProduct"].mean(),
        "ProductDiversityRate_mean": temp["ProductDiversityRate"].mean(),
        "RecencyFrequency_mean": temp["RecencyFrequency"].mean(),
        "SpendTrendRatio_mean": temp["SpendTrendRatio"].mean(),
        "FrequencyLast90DaysRatio_mean": temp["FrequencyLast90DaysRatio"].mean(),
        "IsNewCustomer_mean": temp["IsNewCustomer"].mean(),

        "AvgFutureSpend90Days": temp["FutureSpend90Days"].mean(),
        "TotalFutureRevenue": total_future_revenue,
        "FutureRevenueShare_%": total_future_revenue / clustered_customers["FutureSpend90Days"].sum() * 100,
        "RetentionRate_%": retained_customers / cluster_size * 100,
        "ZeroFutureSpendRate_%": (temp["FutureSpend90Days"] == 0).mean() * 100
    })

profile_df = pd.DataFrame(profile_rows)


# ============================================================
# AUTOMATIC SEGMENT NAMING BASED ON PROFILE
# ============================================================

# Rank clusters by future revenue, retention, recency, and frequency
profile_df["RevenueRank"] = profile_df["AvgFutureSpend90Days"].rank(ascending=False)
profile_df["RetentionRank"] = profile_df["RetentionRate_%"].rank(ascending=False)
profile_df["RecencyRank"] = profile_df["AvgRecency"].rank(ascending=True)
profile_df["FrequencyRank"] = profile_df["AvgFrequency"].rank(ascending=False)

segment_names = {}

best_cluster = profile_df.sort_values(
    by=["AvgFutureSpend90Days", "RetentionRate_%", "AvgFrequency"],
    ascending=[False, False, False]
).iloc[0]["KMeans_Cluster"]

new_cluster = profile_df.sort_values(
    by=["IsNewCustomer_mean", "AvgFrequency"],
    ascending=[False, True]
).iloc[0]["KMeans_Cluster"]

inactive_cluster = profile_df.sort_values(
    by=["AvgRecency", "ZeroFutureSpendRate_%"],
    ascending=[False, False]
).iloc[0]["KMeans_Cluster"]

for _, row in profile_df.iterrows():
    cluster_id = row["KMeans_Cluster"]

    if cluster_id == best_cluster:
        segment_names[cluster_id] = "High-Value Loyalists"
    elif cluster_id == new_cluster:
        segment_names[cluster_id] = "New / One-Time Customers"
    elif cluster_id == inactive_cluster:
        segment_names[cluster_id] = "At-Risk Inactive Customers"
    else:
        segment_names[cluster_id] = "Regular Mid-Value Customers"

profile_df["SegmentName"] = profile_df["KMeans_Cluster"].map(segment_names)

clustered_customers["KMeans_SegmentName"] = clustered_customers["KMeans_Cluster"].map(segment_names)


# Put useful columns first
front_cols = [
    "Customer_ID",
    "KMeans_Cluster",
    "KMeans_SegmentName",
    "Agglomerative_Cluster",
    "GaussianMixture_Cluster",
    "DBSCAN_Cluster",
    "FutureSpend90Days",
    "RetentionLabel"
]

other_cols = [col for col in clustered_customers.columns if col not in front_cols]
clustered_customers = clustered_customers[front_cols + other_cols]


print("\nFinal KMeans Cluster Profile:")
print(profile_df.sort_values(by="AvgFutureSpend90Days", ascending=False))


# ============================================================
# SAVE OUTPUT FILES
# ============================================================

profile_df.to_csv(
    os.path.join(OUTPUT_DIR, "kmeans_cluster_profiles.csv"),
    index=False
)

clustered_customers.to_csv(
    os.path.join(OUTPUT_DIR, "clustered_customers.csv"),
    index=False
)

pca_df.to_csv(
    os.path.join(OUTPUT_DIR, "pca_cluster_coordinates.csv"),
    index=False
)

feature_means = clustered_customers.groupby("KMeans_Cluster")[clustering_features].mean()

feature_means.to_csv(
    os.path.join(OUTPUT_DIR, "kmeans_cluster_feature_means.csv")
)


# ============================================================
# PLOTS
# ============================================================

plt.figure(figsize=(8, 6))
plt.scatter(
    pca_df["PCA1"],
    pca_df["PCA2"],
    c=pca_df["KMeans_Cluster"],
    alpha=0.7
)
plt.title("KMeans Customer Segments - PCA View")
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")
plt.colorbar(label="KMeans Cluster")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "kmeans_pca_clusters.png"), dpi=300)
plt.close()


plt.figure(figsize=(8, 5))
plt.plot(
    kmeans_results_df["K"],
    kmeans_results_df["Inertia"],
    marker="o"
)
plt.title("KMeans Elbow Curve")
plt.xlabel("Number of Clusters")
plt.ylabel("Inertia")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "kmeans_elbow_curve.png"), dpi=300)
plt.close()


plt.figure(figsize=(8, 5))
plt.plot(
    kmeans_results_df["K"],
    kmeans_results_df["Silhouette_Score"],
    marker="o"
)
plt.title("KMeans Silhouette Scores")
plt.xlabel("Number of Clusters")
plt.ylabel("Silhouette Score")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "kmeans_silhouette_scores.png"), dpi=300)
plt.close()


# ============================================================
# FINAL MESSAGE
# ============================================================

print("\nSaved clustering output files in:")
print(OUTPUT_DIR)

print("\nSaved clustering plot files in:")
print(PLOT_DIR)

print("\nImportant files created:")
print(os.path.join(OUTPUT_DIR, "clustering_model_comparison.csv"))
print(os.path.join(OUTPUT_DIR, "kmeans_k_search_results.csv"))
print(os.path.join(OUTPUT_DIR, "dbscan_parameter_search_results.csv"))
print(os.path.join(OUTPUT_DIR, "kmeans_cluster_profiles.csv"))
print(os.path.join(OUTPUT_DIR, "clustered_customers.csv"))
print(os.path.join(OUTPUT_DIR, "pca_cluster_coordinates.csv"))
print(os.path.join(OUTPUT_DIR, "kmeans_cluster_feature_means.csv"))

print("\nRecommended final segmentation model for frontend:")
print("KMeans with 4 clusters")

print("\nReason:")
print("KMeans is selected because it gives balanced, interpretable customer groups.")
print("DBSCAN is not selected because it marks too many customers as noise.")
print("GaussianMixture may score slightly better, but its clusters are usually less frontend-friendly.")

print("\nClustered Dataset Sample:")
print(clustered_customers.head())