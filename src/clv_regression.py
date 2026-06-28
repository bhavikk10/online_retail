import pandas as pd
import numpy as np

from sklearn.model_selection import (train_test_split, RandomizedSearchCV)

# Preprocessing utilities
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler


# Missing value handling
from sklearn.impute import SimpleImputer

# Regression models
from sklearn.linear_model import Ridge
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor

# XGBoost regressor
from xgboost import XGBRegressor

# Evaluation metrics
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    root_mean_squared_error,
    median_absolute_error
)

# Dataset creation pipeline
from classf_dataset import build_retention_dataset


# Preprocessing pipeline
from preprocessing import preprocess_online_retail


# LOADING CLEANED MASTER DATASET
   
df = preprocess_online_retail(file_path="online_retail_II.xlsx", verbose=False)

# BUILDING CUSTOMER RETENTION DATASET
   
retention_df = build_clv_dataset(
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
X = retention_df.drop(columns=['Customer_ID', 'FutureSpend90Days'])

# Target labels
y = np.log1p(retention_df['FutureSpend90Days'])

# TRAIN TEST SPLIT
# Stratify preserves class distribution balance
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


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
models = {'Ridge_linearreg': Ridge(),
          'KNN': KNeighborsRegressor(),
          'DecisionTree': DecisionTreeRegressor(random_state=42),    
          'SVR': SVR(), 
          'RandomForest': RandomForestRegressor(random_state=42),
          'XGBoost': XGBRegressor(objective='reg:squarederror', eval_metric='rmse',random_state=42),
          'ExtraTrees':ExtraTreesRegressor(random_state=42),
          'HistGBM':HistGradientBoostingRegressor(random_state=42),
          'LGBM': LGBMRegressor(objective='regression',random_state=42,verbose=-1),
          'CatBoost': CatBoostRegressor(loss_function='RMSE',random_seed=42,verbose=0)
          }
#scale_pos_weight = ((y_train == 0).sum() / (y_train == 1).sum())
   
# DEFINING RANDOM SEARCH PARAMETER GRIDS   
param_grids = {
    'Ridge_linearreg': {'model__alpha':[0.001,0.01,0.1,1,10,100]},
    'KNN': {'model__n_neighbors': [3, 5, 7, 11, 15, 20, 25, 30], 'model__weights': ['uniform', 'distance'], 'model__p': [1, 2]},
    'DecisionTree': {'model__max_depth':[3,5,10,15,20,30,None],'model__min_samples_split':[2,5,10,20,50],'model__min_samples_leaf':[1,2,4,8,16]},
    'SVR': {'model__kernel':['rbf','linear'],'model__C':[0.1,1,5,10,20,50,100],'model__gamma':['scale',0.001,0.01,0.05,0.1,0.5],'model__epsilon':[0.01,0.05,0.1,0.2]},
    'RandomForest': {'model__n_estimators':[100,200,500,1000], 'model__max_depth':[3,5,10,20,None], 'model__min_samples_split':[2,5,10,20,30,50], 'model__min_samples_leaf':[1,2,4,8,12,18], 'model__max_features':['sqrt','log2']},
    'XGBoost': {'model__n_estimators':[100,200,500,1000], 'model__max_depth':[3,4,5,6,8], 'model__learning_rate':[0.01,0.03,0.05,0.1], 'model__subsample':[0.6,0.8,1.0], 'model__colsample_bytree':[0.6,0.8,1.0], 'model__min_child_weight':[1,3,5,7], 'model__gamma':[0,0.1,0.3,0.5], 'model__reg_alpha':[0,0.01,0.1], 'model__reg_lambda':[1,2,5]},
    'ExtraTrees': {'model__n_estimators':[200,500,1000], 'model__max_depth':[5,10,20,None], 'model__min_samples_split':[2,5,10], 'model__min_samples_leaf':[1,2,4,8]},
    'HistGBM':{'model__learning_rate':[0.01,0.03,0.05,0.1], 'model__max_depth':[3,5,8,None], 'model__max_iter':[100,300,500,1000],'model__min_samples_leaf':[10,20,50],'model__l2_regularization':[0,0.01,0.1,1]},
    'LGBM': {'model__n_estimators': [100, 200, 500, 1000],'model__learning_rate': [0.01,0.03,0.05,0.1],'model__max_depth': [3,5,7,10,-1],'model__num_leaves': [15,31,63,127],'model__subsample': [0.6,0.8,1.0],'model__colsample_bytree': [0.6,0.8,1.0],'model__min_child_samples': [5,10,20,50],'model__reg_alpha': [0,0.01,0.1,1],'model__reg_lambda': [0,0.01,0.1,1,5]},
    'CatBoost': {'model__iterations':[100,200,500,1000],'model__learning_rate':[0.01,0.03,0.05,0.1],'model__depth':[3,4,5,6,8,10],'model__l2_leaf_reg':[1,3,5,7,10],'model__border_count':[32,64,128,255],'model__subsample':[0.6,0.8,1.0],'model__colsample_bylevel':[0.6,0.8,1.0],'model__random_strength':[0,0.1,0.3,0.5,1.0],'model__l2_leaf_reg':[1,3,5,7,10],'model__border_count':[32,64,128,255],'model__random_strength':[0,0.1,0.3,0.5,1.0]}}
    


baseline_pred = np.repeat(
    np.expm1(y_train).mean(),
    len(y_test)
)

baseline_rmse = root_mean_squared_error(
    np.expm1(y_test),
    baseline_pred
)

print("Baseline RMSE:",
      baseline_rmse)

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
        n_iter=120, cv=5, scoring='neg_root_mean_squared_error', random_state=42, n_jobs=-1)

    # TRAINING MODEL
    random_search.fit(X_train, y_train)

    # BEST MODEL AFTER SEARCH
    best_model = random_search.best_estimator_
    trained_models[model_name] = best_model

    # PREDICTING TEST LABELS
    y_pred = best_model.predict(X_test)

    # APPLYING EXPONENTIAL TRANSFORMATION BACK FROM LOG SCALE
    y_test_actual = np.expm1(y_test)
    y_pred_actual = np.expm1(best_model.predict(X_test))


    # CALCULATING EVALUATION METRICS
    MSE = mean_squared_error(y_test_actual, y_pred_actual)

    RMSE = root_mean_squared_error(y_test_actual, y_pred_actual)

    MAE = mean_absolute_error(y_test_actual, y_pred_actual)

    R2 = r2_score(y_test_actual, y_pred_actual)

    MEDIAN_AE = median_absolute_error(y_test_actual, y_pred_actual)

    RMSE_LOG = root_mean_squared_error(y_test, y_pred)

    R2_LOG = r2_score(y_test, y_pred)

       # PRINTING MODEL PERFORMANCE
   
    print(f"Best Params: {random_search.best_params_}")

    print(f"MSE: {MSE:.4f}")

    print(f"RMSE: {RMSE:.4f}")

    print(f"MAE: {MAE:.4f}")

    print(f"R2: {R2:.4f}")

    print(f"MEDIAN_AE: {MEDIAN_AE:.4f}")

    print(f"RMSE_LOG: {RMSE_LOG:.4f}")

    print(f"R2_LOG: {R2_LOG:.4f}")


    # STORING RESULTS
   
    results.append({'Model': model_name, 'MSE': MSE, 'RMSE': RMSE,
        'MAE': MAE, 'R2': R2, 'MEDIAN_AE': MEDIAN_AE, 'RMSE_LOG': RMSE_LOG, 'R2_LOG': R2_LOG})

   # FINAL MODEL COMPARISON TABLE
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values(by='RMSE_LOG', ascending=True)


# PRINTING FINAL RESULTS   
print("\nFinal Model Comparison:\n")
print(results_df)