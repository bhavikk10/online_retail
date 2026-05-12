import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Configuration
st.set_page_config(
    page_title="Online Retail Analytics",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for specific colors and fixing table text visibility
custom_css = """
<style>
    /* Primary Headings */
    h1, h2, h3, h4, h5 {
        color: #2D3748 !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Secondary Colors (Deep Amber) */
    .st-emotion-cache-16idsys p {
        color: #744210 !important;
        font-weight: 600;
    }
    
    hr {
        border-color: #744210 !important;
    }

    /* Table Styling */
    th {
        background-color: #744210 !important;
        color: white !important;
        font-weight: bold !important;
    }
    
    /* Fix text visibility in table rows */
    td {
        color: #2D3748 !important;
        font-weight: 500 !important;
    }
    
    tr:nth-child(even) {
        background-color: #FFFBEB !important;
    }
    
    tr:nth-child(odd) {
        background-color: #FFFFFF !important;
    }
    
    /* Metric Card Styling */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    }
    
    div[data-testid="metric-container"] > div {
        color: #744210;
    }
    
    /* Text readability inside dark mode */
    .stMarkdown p, .stMarkdown li {
        font-size: 1.05rem;
        line-height: 1.6;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Overview & Preprocessing", "Customer Behavior", "Customer Segmentation", "Retention Prediction"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Insights Source:** Pre-computed metrics from `preprocessingtest.ipynb`")
st.sidebar.markdown("**Data Source:** UCI Online Retail II Dataset")

if page == "Overview & Preprocessing":
    st.title("Data Overview & Preprocessing")
    st.markdown("### Cleaning & Formatting the Dataset (`preprocessing.py`)")
    
    st.markdown("""
    The foundation of our entire data science pipeline relies on an extremely rigorous data cleaning process. The original UCI Online Retail II dataset contained raw, unformatted transactional logs spanning from 2009 to 2011. Without proper processing, analytical models would train on noise, resulting in poor predictive performance.
    
    **To prepare this data for machine learning, our `preprocessing.py` script performed the following extensive steps:**
    
    1. **Handling Missing Values:** We identified and removed **243,007 rows** that completely lacked a `Customer_ID`. Transactions without a known customer ID cannot be attributed to a user profile, making them useless for behavioral modeling or cohort analysis.
    2. **Deduplication:** We removed **26,479 exactly duplicated rows**. These duplicates were likely artifacts of system logging errors or multiple submissions at checkout.
    3. **Price Correction:** We filtered out **70 transactions** where the unit price was listed as zero or negative, which were likely system tests or corrupted data points.
    4. **Feature Engineering (Flags):** Instead of deleting anomalies outright, we created specific boolean flags to isolate them. We flagged invoices starting with 'C' as cancellations (`IsCancelled = True`), and negative quantities as returns (`IsReturn = True`). Furthermore, non-product operational codes like 'POSTAGE', 'BANK CHARGES', and 'AMAZONFEE' were separated so our models focus solely on product interactions.
    5. **Standardization & Typing:** Dates were properly cast to pandas datetime objects to enable time-series calculations. String attributes like `StockCode` and `Country` were stripped of trailing whitespaces and standardized to ensure consistency across the dataset.
    """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Initial Records", "1,067,371")
        st.metric("Missing Customer IDs", "243,007")
    with col2:
        st.metric("Final Cleaned Records", "797,815")
        st.metric("Duplicate Rows Removed", "26,479")
    with col3:
        st.metric("Unique Customers", "5,939")
        st.metric("Unique Invoices", "44,870")

    st.markdown("### Transaction Adjustments")
    st.markdown("By parsing invoice prefixes and negative quantities, we accurately identified cancelled and returned orders. These are flagged in our dataset to ensure they don't artificially inflate revenue calculations, customer lifetime value, or engagement metrics downstream.")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Cancelled Transactions", "18,390")
    with c2:
        st.metric("Return Transactions", "18,390")
        
    st.info("Date Range of Cleaned Dataset: **2009-12-01 07:45:00** to **2011-12-09 12:50:00**")


elif page == "Customer Behavior":
    st.title("Customer Behavior Analysis")
    st.markdown("### Purchase Patterns and Retention Rates (`behavior.py`)")
    
    st.markdown("""
    To understand how our customers shop, the `behavior.py` module aggregates the cleaned transaction logs into a condensed, highly informative **invoice-level dataset**. 
    
    **How we derived these insights:**
    - We exclude cancelled, returned, and non-product transactions. We only want to analyze successful, revenue-generating behavior.
    - We calculate **Inter-purchase Gaps** by sorting each customer's invoices chronologically and calculating the exact timedelta (in days) between consecutive orders using the pandas `shift()` operation.
    - The **Repeat Customer Rate** is calculated by aggregating the number of unique invoices per customer, and identifying the percentage of total unique customers who have an invoice count strictly greater than 1.
    """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Repeat Customer Rate", "72.26%")
    with col2:
        st.metric("Median Inter-purchase Gap", "24.0 Days")
    with col3:
        st.metric("Mean Inter-purchase Gap", "51.4 Days")
        
    st.markdown("---")
    st.markdown("### Return Windows")
    st.markdown("""
    The data reveals that **if a customer is going to return, they are highly likely to do so quickly.** We measured the percentage of returning customers who make their next purchase within specific timeframes. 
    A median gap of 24 days suggests a natural monthly purchasing cycle for active buyers, and a significant drop-off in likelihood of return after 90 days. This clearly indicates that any targeted marketing campaigns should be triggered *before* a user reaches the 60 to 90 day inactivity threshold.
    """)
    
    # Simple Bar Chart for Return Windows
    return_data = pd.DataFrame({
        "Timeframe": ["Within 30 Days", "Within 60 Days", "Within 75 Days", "Within 90 Days"],
        "Return Rate (%)": [55.86, 74.70, 79.57, 83.26]
    })
    
    fig = px.bar(
        return_data, 
        x="Timeframe", 
        y="Return Rate (%)", 
        text="Return Rate (%)",
        color_discrete_sequence=["#744210"],
        title="Probability of Return Purchase Over Time"
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', yaxis_range=[0,100])
    st.plotly_chart(fig, use_container_width=True)


elif page == "Customer Segmentation":
    st.title("Customer Segmentation (Clustering)")
    st.markdown("### Unsupervised Learning on Customer Behavior (`clustering.py`)")
    
    st.markdown("""
    Instead of treating all customers identically, we employ advanced unsupervised machine learning to discover natural, mathematically distinct groupings within our user base. This is the exact purpose of the `clustering.py` script.
    
    **Detailed Pipeline Methodology:**
    1. **Feature Extraction:** First, we aggregate the raw data to the customer level. We extract standard RFM features (Recency, Frequency, Monetary value) alongside advanced behavioral metrics like `AvgGapDays` (how often they shop) and `SpendLast30Days` (recent momentum).
    2. **Scaling & Transformation:**
       - **Log Transformation:** Financial metrics (Monetary, AvgBasketValue, SpendLast30Days) are highly right-skewed (a few whales spend vastly more than average users). We apply `np.log1p` to these features to compress the long tail, ensuring the clustering algorithm isn't overwhelmed by extreme outliers.
       - **Standard Scaling:** After log transformation, all features (including linear features like Recency) are normalized using Scikit-Learn's `StandardScaler` so that every variable has a mean of 0 and a standard deviation of 1. This prevents variables with larger magnitudes from dominating distance calculations.
    3. **Dimensionality Reduction:** We pass the scaled data through PCA (Principal Component Analysis) to reduce noise and multicollinearity before feeding it into the clustering models.
    4. **Clustering Models:** We evaluate 4 different algorithms to group customers into 4 distinct segments (KMeans, Agglomerative, DBSCAN, and Gaussian Mixture Models).
    
    **Evaluating the Clusters:**
    - **Silhouette Score:** Measures how similar an object is to its own cluster compared to other clusters (values range from -1 to 1). A higher score indicates dense, well-separated clusters.
    - **Davies-Bouldin Score:** Evaluates the average 'similarity' ratio of each cluster with its most similar cluster. Lower values indicate better separation.
    """)
    
    # Hardcoded Clustering Data
    cluster_results = pd.DataFrame({
        "Model": ["KMeans", "Agglomerative", "DBSCAN", "GaussianMixture"],
        "Clusters": [4, 4, 4, 4],
        "Silhouette Score": [0.3244, 0.3204, 0.4409, 0.2747],
        "Davies Bouldin Score": [1.1163, 1.1298, 0.8368, 1.4684],
        "Calinski Harabasz Score": [1597.69, 1523.85, 885.65, 1289.03]
    })
    
    st.table(cluster_results)
    
    st.markdown("### Cluster Distribution Summary")
    st.markdown("""
    Below we visualize how the algorithms distribute our 5,900+ customers into the 4 learned segments. 
    - **KMeans** provides a relatively balanced and intuitive segmentation, naturally grouping users into tiers (e.g., VIPs, Occasional Shoppers, New Users, Churn Risks). This makes it highly actionable for marketing.
    - **DBSCAN**, however, groups the vast majority of users into a single giant core cluster, while isolating the rest as outliers. While mathematically valid for finding anomalies, it is less useful for standard tiered marketing campaigns.
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**KMeans Clusters**")
        km_dist = pd.DataFrame({"Cluster": ["Segment 0", "Segment 1", "Segment 2", "Segment 3"], "Count": [709, 413, 859, 797]})
        fig_km = px.pie(km_dist, values='Count', names='Cluster', hole=0.4, color_discrete_sequence=px.colors.sequential.YlOrBr)
        st.plotly_chart(fig_km, use_container_width=True)
        
    with col2:
        st.markdown("**Agglomerative Clusters**")
        agg_dist = pd.DataFrame({"Cluster": ["Segment 0", "Segment 1", "Segment 2", "Segment 3"], "Count": [836, 413, 1031, 498]})
        fig_agg = px.pie(agg_dist, values='Count', names='Cluster', hole=0.4, color_discrete_sequence=px.colors.sequential.YlOrBr)
        st.plotly_chart(fig_agg, use_container_width=True)


elif page == "Retention Prediction":
    st.title("Retention Prediction Models")
    st.markdown("### Predicting 90-Day Churn (`classf_dataset.py` & `classf_pipeline.py`)")
    
    st.markdown("""
    Predicting whether a customer will return allows the business to proactively target at-risk users with retention campaigns.
    
    **Building the Feature Set (`classf_dataset.py`):**
    - **Cutoff Simulation:** We artificially cut off our historical data on `2011-09-09`. Any transaction data before this date is aggregated to create historical features (e.g., total spend, average gap days, cancellation rate).
    - **Target Labeling:** We look at the "future" 90-day window (`2011-09-09` to `2011-12-08`). If a customer makes at least one purchase in this window, their label is set to `1` (Retained). If they do not, their label is `0` (Churned).
    - **Active Window Filter:** We only generate predictions for customers who were active in the 180 days leading up to the cutoff. Filtering out heavily dormant users ensures the model learns the nuances of recent customer churn, rather than trivially predicting that someone who hasn't shopped in 2 years won't shop tomorrow.
    """)
    
    st.markdown("**Dataset Split Configuration:**")
    st.code("Cutoff Date: 2011-09-09\nPrediction End: 2011-12-08\nActive Customer Window: 180 Days")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Active Customers", "2,778")
    with col2:
        st.metric("Overall Retention Rate", "61.45%")
    with col3:
        st.metric("Retained vs Lost", "1707 / 1071")
        
    st.markdown("---")
    st.markdown("### Model Pipeline & Hyperparameter Tuning (`classf_pipeline.py`)")
    st.markdown("""
    Using the engineered dataset, we trained a battery of machine learning classification models.
    
    **The Pipeline Architecture:**
    1. **Preprocessing Transformer:** We utilize a Scikit-Learn `ColumnTransformer`. The dataset is split into two tracks: skewed features (like Frequency and Monetary) undergo `SimpleImputer(median) -> Log1p Transformation -> StandardScaler`, while normally distributed features undergo `SimpleImputer(median) -> StandardScaler`.
    2. **Model Training:** This perfectly scaled data is passed directly into a classifier. We train multiple algorithms including Logistic Regression, Support Vector Machines (SVC), Decision Trees, Random Forests, and XGBoost.
    3. **RandomizedSearchCV:** For every model, we perform an exhaustive 5-fold cross-validation search over a predefined hyperparameter grid, maximizing the F1 score to find the optimal configuration.
    
    *As shown below, tree-based ensemble methods (Random Forest and XGBoost) achieved the best trade-off between Recall (successfully identifying returning users) and overall ROC AUC (the model's overall capability to distinguish between churners and retainees).*
    """)
    
    # Hardcoded Classification Data
    classf_results = pd.DataFrame({
        "Model": ["RandomForest", "XGBoost", "LogisticRegression", "SVC", "KNN", "DecisionTree"],
        "Accuracy": [0.6924, 0.6906, 0.6745, 0.6924, 0.6871, 0.6871],
        "Precision": [0.7317, 0.7179, 0.7069, 0.7101, 0.7211, 0.7346],
        "Recall": [0.7895, 0.8187, 0.8041, 0.8450, 0.8012, 0.7690],
        "F1 Score": [0.7595, 0.7650, 0.7524, 0.7717, 0.7590, 0.7514],
        "ROC AUC": [0.7640, 0.7609, 0.7579, 0.7442, 0.7395, 0.7391]
    })
    
    # Format to percentage for better readability
    format_cols = ["Accuracy", "Precision", "Recall", "F1 Score", "ROC AUC"]
    for c in format_cols:
        classf_results[c] = (classf_results[c] * 100).map('{:.2f}%'.format)
        
    st.table(classf_results)
    
    # Optional bar chart for ROC AUC
    chart_data = pd.DataFrame({
        "Model": ["RandomForest", "XGBoost", "LogisticRegression", "SVC", "KNN", "DecisionTree"],
        "ROC AUC": [0.7640, 0.7609, 0.7579, 0.7442, 0.7395, 0.7391]
    })
    
    chart_data = chart_data.sort_values(by="ROC AUC", ascending=True)
    fig = px.bar(chart_data, x="ROC AUC", y="Model", orientation='h', 
                 title="ROC AUC Score by Model", color_discrete_sequence=["#744210"])
    fig.update_layout(xaxis_range=[0.7, 0.8], plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)
