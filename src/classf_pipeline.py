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
log_features = ['Frequency', 'Monetary', 'AvgBasketValue', 'UniqueProducts', 'SpendLast30Days', 'SpendLast90Days', 'SpendPrior90Days', 'RevenuePerDay', 'AvgSpendPerProduct', 'ProductDiversityRate']

# FEATURES NEEDING NORMAL SCALING ONLY   
scale_features = ['AvgQuantity','Recency', 'LifetimeDays', 'PurchaseRate','AvgGapDays','StdGapDays','PurchasesLast30Days','PurchasesLast90Days','ReturnRate', 'IsNewCustomer','RecencyFrequency','SpendTrendRatio','FrequencyLast90DaysRatio']

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
    ('scale', scale_pipeline, scale_features)],
    remainder='drop')


# DEFINING MODELS   
scale_pos_weight = ( (y_train == 0).sum() / (y_train == 1).sum() )
models = {'LogisticRegression': LogisticRegression(class_weight='balanced', max_iter=5000),
          'KNN': KNeighborsClassifier(),
          'DecisionTree': DecisionTreeClassifier(class_weight='balanced'),    
          'SVC': SVC(probability=True,class_weight='balanced'), 
          'RandomForest': RandomForestClassifier(class_weight='balanced'),
          'XGBoost': XGBClassifier(eval_metric='logloss', scale_pos_weight=1, random_state=42)}
#scale_pos_weight = ((y_train == 0).sum() / (y_train == 1).sum())
   
# DEFINING RANDOM SEARCH PARAMETER GRIDS   
param_grids = {
    'LogisticRegression': {'model__C': [0.01, 0.1, 1, 10], 'model__penalty': ['l2']},
    'KNN': {'model__n_neighbors': [3, 5, 7, 11, 15, 20], 'model__weights': ['uniform', 'distance']},
    'DecisionTree': {'model__max_depth': [3, 5, 10, 20, 50], 'model__min_samples_split': [2, 5, 10]},
    'SVC': {'model__C': [0.01,0.1,1,5,10,50], 'model__kernel': ['rbf','linear'], 'model__gamma': ['scale',0.01,0.05,0.1,0.5,0.75,1,1.5]},
    'RandomForest': {'model__n_estimators':[100,200,500,1000], 'model__max_depth':[3,5,10,20,None], 'model__min_samples_split':[2,5,10,20,30], 'model__min_samples_leaf':[1,2,4,8,12,18], 'model__max_features':['sqrt','log2']},
    'XGBoost': {'model__n_estimators':[100,200,500,1000], 'model__max_depth':[3,4,5,6,8], 'model__learning_rate':[0.01,0.03,0.05,0.1], 'model__subsample':[0.6,0.8,1.0], 'model__colsample_bytree':[0.6,0.8,1.0], 'model__min_child_weight':[1,3,5]}
    }

   
# STORING MODEL RESULTS   
results = []
trained_models = {}

# TRAINING AND EVALUATING MODELS   
for model_name, model in models.items():
    print(f"\nTraining {model_name}...")
    
    # CREATING COMPLETE MODEL PIPELINE
    pipeline = Pipeline([('preprocessing', preprocessor), ('model', model)])
    
    # RANDOMIZED HYPERPARAMETER SEARCH
    random_search = RandomizedSearchCV(estimator=pipeline, param_distributions=param_grids[model_name],
        n_iter=120, cv=5, scoring='roc_auc', random_state=42, n_jobs=-1)

    # TRAINING MODEL
    random_search.fit(X_train, y_train)

    # BEST MODEL AFTER SEARCH
    best_model = random_search.best_estimator_
    trained_models[model_name] = best_model

    # PREDICTING TEST LABELS
    y_pred = best_model.predict(X_test)

    # PREDICTING CLASS PROBABILITIES
    y_prob = best_model.predict_proba(X_test)[:, 1]

    #Exp
    # thresholds = np.arange(0.1,0.9,0.01)

    # best_thr = 0.5
    # best_f1 = 0

    # for thr in thresholds:
    #     pred = (y_prob >= thr).astype(int)

    #     score = f1_score(y_test,pred)

    #     if score > best_f1:
    #         best_f1 = score
    #         best_thr = thr

    # print(best_thr,best_f1)

    # y_pred = (y_prob >= best_thr).astype(int)

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