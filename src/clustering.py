# clustering_pipeline.py
import pandas as pd
import numpy as np

from sklearn.preprocessing import (
    StandardScaler,
    FunctionTransformer
)

from sklearn.impute import SimpleImputer

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

# Clustering algorithms
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
# Gaussian Mixture clustering
from sklearn.mixture import GaussianMixture

# Dimensionality reduction
from sklearn.decomposition import PCA

# Clustering evaluation metrics
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score
)

# Dataset generation pipeline
from classf_dataset import (
    build_retention_dataset
)

# Master preprocessing pipeline
from preprocessing import (
    preprocess_online_retail
)


# HANDLING MISSING GAP VALUES
# Customers with single purchases have no gap history
retention_df['AvgGapDays'] = (
    retention_df['AvgGapDays']
    .fillna(999)
)

  
# SELECTING FEATURES FOR CLUSTERING
# Keeping only behavioral segmentation features
cluster_features = ['Recency','Frequency','Monetary','AvgBasketValue','PurchaseRate','AvgGapDays','SpendLast30Days']
  
# CREATING CLUSTERING FEATURE MATRIX
X = retention_df[cluster_features].copy()

# FEATURES NEEDING LOG TRANSFORMATION: Highly skewed behavioral features
log_features = ['Frequency','Monetary','AvgBasketValue','SpendLast30Days']

# FEATURES NEEDING STANDARD SCALING
scale_features = ['Recency','PurchaseRate','AvgGapDays']

  
# PIPELINE FOR LOG-TRANSFORMED FEATURES
log_pipeline = Pipeline([
    # Filling missing values
    ('imputer', SimpleImputer(strategy='median')),
    # Applying log(1+x) transformation
    ('log_transform', FunctionTransformer(np.log1p)),
    # Standardizing transformed values
    ('scaler', StandardScaler())])
  
# PIPELINE FOR NORMAL FEATURES
scale_pipeline = Pipeline([
    # Filling missing values
    ('imputer', SimpleImputer(strategy='median')),
    # Standard scaling
    ('scaler', StandardScaler())])

  
# COMBINING PREPROCESSING PIPELINES
preprocessor = ColumnTransformer([
    ('log', log_pipeline, log_features),
    ('scale', scale_pipeline, scale_features)
])

# PREPROCESSING CLUSTERING FEATURES
X_processed = preprocessor.fit_transform(X)

# PCA DIMENSIONALITY REDUCTION
# Reducing dimensions for visualization and noise reduction
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_processed)

  
# DEFINING CLUSTERING MODELS
clustering_models = {'KMeans': KMeans(n_clusters=4, random_state=42),
                     'Agglomerative': AgglomerativeClustering(n_clusters=4),
                     'DBSCAN': DBSCAN(eps=1.2,min_samples=10),
                     'GaussianMixture': GaussianMixture(n_components=4,random_state=42)}


# STORING CLUSTERING RESULTS
results = []

# TRAINING AND EVALUATING CLUSTERING MODELS
for model_name, model in clustering_models.items():
    print(f"\nRunning {model_name}...")

    # FITTING CLUSTERING MODEL
    if model_name == 'GaussianMixture':
        # Gaussian mixture uses fit_predict separately
        cluster_labels = model.fit_predict(X_processed)

    else:
        # Standard clustering prediction
        cluster_labels = model.fit_predict(X_processed)

    # COUNTING UNIQUE CLUSTERS
    n_clusters = len(set(cluster_labels))

    # HANDLING DBSCAN NOISE LABELS
    # DBSCAN may create noise points labeled -1
    if -1 in cluster_labels:
        valid_mask = cluster_labels != -1
        X_eval = X_processed[valid_mask]
        labels_eval = cluster_labels[valid_mask]
    else:
        X_eval = X_processed
        labels_eval = cluster_labels

    # COMPUTING CLUSTERING METRICS
    silhouette = silhouette_score(
        X_eval,
        labels_eval
    )
    davies = davies_bouldin_score(
        X_eval,
        labels_eval
    )
    calinski = calinski_harabasz_score(
        X_eval,
        labels_eval
    )

    # PRINTING CLUSTERING PERFORMANCE
    print(f"Clusters found: {n_clusters}")
    print(f"Silhouette Score: {silhouette:.4f}")
    print(f"Davies Bouldin Score: {davies:.4f}")
    print(f"Calinski Harabasz Score: {calinski:.4f}")

    # STORING RESULTS
    results.append({
        'Model': model_name,
        'Clusters': n_clusters,
        'Silhouette Score': silhouette,
        'Davies Bouldin Score': davies,
        'Calinski Harabasz Score': calinski})

    # SAVING CLUSTER LABELS
    retention_df[f'{model_name}_Cluster'] = (cluster_labels)
 
# FINAL CLUSTERING RESULTS TABLE
results_df = pd.DataFrame(results)

# PRINTING FINAL MODEL COMPARISON
print("\nFinal Clustering Comparison:\n")
print(results_df)

  
# DISPLAYING CLUSTER DISTRIBUTIONS
for model_name in clustering_models.keys():
    print(f"\n{model_name} Cluster Counts:\n")
    print(
        retention_df[
            f'{model_name}_Cluster'
        ].value_counts()
    )

# DISPLAYING SAMPLE CLUSTERED DATA
print("\nClustered Dataset Sample:\n")
print(
    retention_df[
        [
            'Customer_ID',
            'KMeans_Cluster',
            'Agglomerative_Cluster',
            'DBSCAN_Cluster',
            'GaussianMixture_Cluster'
        ]
    ].head()
)