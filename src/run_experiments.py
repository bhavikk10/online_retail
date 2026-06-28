import pandas as pd
import numpy as np
import pickle
import os

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA

from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.mixture import GaussianMixture

# Datasets
from preprocessing import preprocess_online_retail
from classf_dataset import build_retention_dataset

print("Loading and preprocessing data...")
df = preprocess_online_retail(file_path="online_retail_II.xlsx", verbose=False)

print("Building retention dataset...")
retention_df = build_retention_dataset(
    df, cutoff_date='2011-09-09', prediction_days=90, active_days=180, verbose=False
)

# ---------------------------------------------------------
# CLUSTERING EXPERIMENTS (PCA 3D EXTRACT)
# ---------------------------------------------------------
print("Running clustering and PCA...")
retention_df['AvgGapDays'] = retention_df['AvgGapDays'].fillna(999)
cluster_features = ['Recency','Frequency','Monetary','AvgBasketValue','PurchaseRate','AvgGapDays','SpendLast30Days']
X_cluster = retention_df[cluster_features].copy()

log_features = ['Frequency','Monetary','AvgBasketValue','SpendLast30Days']
scale_features = ['Recency','PurchaseRate','AvgGapDays']

log_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('log_transform', FunctionTransformer(np.log1p)),
    ('scaler', StandardScaler())])

scale_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())])

preprocessor_cluster = ColumnTransformer([
    ('log', log_pipeline, log_features),
    ('scale', scale_pipeline, scale_features)])

X_processed = preprocessor_cluster.fit_transform(X_cluster)

# 3D PCA for visualization
pca = PCA(n_components=3)
X_pca_3d = pca.fit_transform(X_processed)

clustering_models = {
    'KMeans': KMeans(n_clusters=4, random_state=42),
    'Agglomerative': AgglomerativeClustering(n_clusters=4),
    'DBSCAN': DBSCAN(eps=1.2, min_samples=10),
    'GaussianMixture': GaussianMixture(n_components=4, random_state=42)
}

cluster_labels_dict = {}
for name, model in clustering_models.items():
    if name == 'GaussianMixture':
        labels = model.fit_predict(X_processed)
    else:
        labels = model.fit_predict(X_processed)
    cluster_labels_dict[name] = labels

clustering_data = {
    'pca_3d': X_pca_3d,
    'labels': cluster_labels_dict,
    'customer_ids': retention_df['Customer_ID'].values
}

with open('clustering_data.pkl', 'wb') as f:
    pickle.dump(clustering_data, f)


# ---------------------------------------------------------
# CLASSIFICATION EXPERIMENTS (GridSearchCV)
# ---------------------------------------------------------
print("Running classification GridSearch...")
X = retention_df.drop(columns=['Customer_ID', 'RetentionLabel'])
y = retention_df['RetentionLabel']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

log_features_cls = ['Frequency','Monetary','AvgBasketValue','SpendLast30Days','UniqueProducts']
scale_features_cls = ['AvgQuantity','Recency','LifetimeDays','PurchaseRate','AvgGapDays','PurchasesLast30Days','CancellationRate','ReturnRate']

preprocessor_cls = ColumnTransformer([
    ('log', log_pipeline, log_features_cls),
    ('scale', scale_pipeline, scale_features_cls)])

models = {
    'LogisticRegression': LogisticRegression(max_iter=1000),
    'KNN': KNeighborsClassifier(),
    'DecisionTree': DecisionTreeClassifier(random_state=42),
    'SVC': SVC(probability=True, random_state=42),
    'RandomForest': RandomForestClassifier(random_state=42),
    'XGBoost': XGBClassifier(eval_metric='logloss', random_state=42)
}

# Smaller grid for speed but exhaustive enough to show trends
param_grids = {
    'LogisticRegression': {'model__C': [0.001, 0.01, 0.1, 1, 10, 100]},
    'KNN': {'model__n_neighbors': [3, 5, 7, 9, 11, 15, 21]},
    'DecisionTree': {'model__max_depth': [3, 5, 10, 15, 20]},
    'SVC': {'model__C': [0.1, 1, 10], 'model__kernel': ['rbf', 'linear']},
    'RandomForest': {'model__n_estimators': [50, 100, 200, 300], 'model__max_depth': [3, 5, 10]},
    'XGBoost': {'model__learning_rate': [0.01, 0.05, 0.1, 0.2], 'model__max_depth': [3, 5, 7]}
}

cv_results_dict = {}

for model_name, model in models.items():
    print(f"GridSearching {model_name}...")
    pipeline = Pipeline([('preprocessing', preprocessor_cls), ('model', model)])
    
    grid_search = GridSearchCV(
        estimator=pipeline, 
        param_grid=param_grids[model_name],
        cv=5, 
        scoring='f1', 
        n_jobs=-1
    )
    
    grid_search.fit(X_train, y_train)
    
    # Store cv_results_
    cv_results_dict[model_name] = {
        'params': grid_search.cv_results_['params'],
        'mean_test_score': grid_search.cv_results_['mean_test_score'],
        'std_test_score': grid_search.cv_results_['std_test_score']
    }

with open('classification_cv_results.pkl', 'wb') as f:
    pickle.dump(cv_results_dict, f)

print("All experiments completed and saved!")
