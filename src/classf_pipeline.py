import pandas as pd
import numpy as np

from sklearn.model_selection import (train_test_split, RandomizedSearchCV)

# Preprocessing utilities
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler


# Missing value handling
from sklearn.impute import SimpleImputer

# Classification models
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier

# XGBoost classifier
from xgboost import XGBClassifier

# Evaluation metrics
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report
)

# Dataset creation pipeline
from classf_dataset import build_retention_dataset


# Preprocessing pipeline
from preprocessing import preprocess_online_retail


# LOADING CLEANED MASTER DATASET
   
df = preprocess_online_retail(file_path="online_retail_II.xlsx", verbose=False)

# BUILDING CUSTOMER RETENTION DATASET
   
retention_df = build_retention_dataset(
    df,
    cutoff_date='2011-09-09',
    prediction_days=90,
    active_days=180,
    verbose=True
)


# HANDLING AvgGapDays MISSING VALUES
# Customers with one purchase have no gap history
retention_df['AvgGapDays'] = (retention_df['AvgGapDays'].fillna(999))

# SPLITTING FEATURES AND TARGET
# Input features
X = retention_df.drop(columns=['Customer_ID', 'RetentionLabel'])

# Target labels
y = retention_df['RetentionLabel']


# TRAIN TEST SPLIT
# Stratify preserves class distribution balance
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)


# FEATURES NEEDING LOG TRANSFORMATION  
# Highly right-skewed behavioral features
log_features = ['Frequency','Monetary','AvgBasketValue','SpendLast30Days','UniqueProducts']

# FEATURES NEEDING NORMAL SCALING ONLY   
scale_features = ['AvgQuantity','Recency','LifetimeDays','PurchaseRate','AvgGapDays','PurchasesLast30Days','CancellationRate','ReturnRate']


# PIPELINE FOR LOG-TRANSFORMED FEATURES   
log_pipeline = Pipeline([
    # Filling missing values
    ('imputer', SimpleImputer(strategy='median')),
    # Applying log(1+x)
    ('log_transform', FunctionTransformer(np.log1p)),
    # Standardizing transformed values
    ('scaler', StandardScaler())])

# PIPELINE FOR STANDARD-SCALED FEATURES   
scale_pipeline = Pipeline([
    # Filling missing values
    ('imputer', SimpleImputer(strategy='median')),
    # Standard scaling
    ('scaler', StandardScaler())])


# COMBINING PREPROCESSING PIPELINES   
preprocessor = ColumnTransformer([
    ('log', log_pipeline, log_features),
    ('scale', scale_pipeline, scale_features)])


# DEFINING MODELS   
models = {'LogisticRegression': LogisticRegression(),'KNN': KNeighborsClassifier(),'DecisionTree': DecisionTreeClassifier(),    
    'SVC': SVC(probability=True), 'RandomForest': RandomForestClassifier(),'XGBoost': XGBClassifier(eval_metric='logloss')}

   
# DEFINING RANDOM SEARCH PARAMETER GRIDS   
param_grids = {
    'LogisticRegression': {'model__C': [0.01, 0.1, 1, 10], 'model__penalty': ['l2']},
    'KNN': {'model__n_neighbors': [3, 5, 7, 11], 'model__weights': ['uniform', 'distance']},
    'DecisionTree': {'model__max_depth': [3, 5, 10, 20], 'model__min_samples_split': [2, 5, 10]},
    'SVC': {'model__C': [0.1, 1, 10], 'model__kernel': ['rbf', 'linear']},
    'RandomForest': {'model__n_estimators': [100, 200, 500], 'model__max_depth': [5, 10, 20], 'model__min_samples_split': [2, 5]},
    'XGBoost': {'model__n_estimators': [100, 200, 500], 'model__max_depth': [3, 5, 7], 'model__learning_rate': [0.01, 0.05, 0.1], 'model__subsample': [0.8, 1.0]}
}

   
# STORING MODEL RESULTS   
results = []

# TRAINING AND EVALUATING MODELS   
for model_name, model in models.items():
    print(f"\nTraining {model_name}...")
    
    # CREATING COMPLETE MODEL PIPELINE
    pipeline = Pipeline([('preprocessing', preprocessor), ('model', model)])
    
    # RANDOMIZED HYPERPARAMETER SEARCH
    random_search = RandomizedSearchCV(estimator=pipeline, param_distributions=param_grids[model_name],
        n_iter=10, cv=5, scoring='f1', random_state=42, n_jobs=-1)

    # TRAINING MODEL
    random_search.fit(X_train, y_train)

    # BEST MODEL AFTER SEARCH
    best_model = random_search.best_estimator_

    # PREDICTING TEST LABELS
    y_pred = best_model.predict(X_test)

    # PREDICTING CLASS PROBABILITIES
    y_prob = best_model.predict_proba(X_test)[:, 1]

    # CALCULATING EVALUATION METRICS
    accuracy = accuracy_score(y_test, y_pred)

    precision = precision_score(y_test, y_pred)

    recall = recall_score(y_test, y_pred)

    f1 = f1_score(y_test, y_pred)

    roc_auc = roc_auc_score(y_test, y_prob)

       # PRINTING MODEL PERFORMANCE
   
    print(f"Best Params: {random_search.best_params_}")

    print(f"Accuracy: {accuracy:.4f}")

    print(f"Precision: {precision:.4f}")

    print(f"Recall: {recall:.4f}")

    print(f"F1 Score: {f1:.4f}")

    print(f"ROC AUC: {roc_auc:.4f}")

    # STORING RESULTS
   
    results.append({'Model': model_name, 'Accuracy': accuracy, 'Precision': precision,
        'Recall': recall, 'F1 Score': f1, 'ROC AUC': roc_auc})

   # FINAL MODEL COMPARISON TABLE
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values(by='ROC AUC', ascending=False)


# PRINTING FINAL RESULTS   
print("\nFinal Model Comparison:\n")
print(results_df)