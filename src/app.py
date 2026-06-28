import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import pickle
import os

# -------------------------------------------------------------
# 1. PAGE CONFIG & PREMIUM GLASSMORPHISM CSS
# -------------------------------------------------------------
st.set_page_config(
    page_title="Nexus Retail Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Midnight Glassmorphism CSS (Emojis removed)
custom_css = """
<style>
    /* Global App Background */
    .stApp {
        background-color: #0B0F19;
        color: #E2E8F0;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    
    /* Hide Streamlit elements */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Typography Overrides */
    h1, h2, h3, h4, h5 {
        color: #F8FAFC !important;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    h1 {
        background: -webkit-linear-gradient(45deg, #06B6D4, #8B5CF6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem !important;
    }
    
    /* Markdown text */
    .stMarkdown p, .stMarkdown li {
        color: #CBD5E1;
        font-size: 1.1rem;
        line-height: 1.7;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Glassmorphism Metric Containers */
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 40px rgba(6, 182, 212, 0.15);
        border-color: rgba(6, 182, 212, 0.3);
    }
    div[data-testid="metric-container"] > div {
        color: #06B6D4 !important;
        font-size: 2.2rem !important;
    }
    div[data-testid="metric-container"] label {
        color: #94A3B8 !important;
        font-size: 1rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Custom DataFrame/Table Styling */
    .dataframe th {
        background-color: #1E293B !important;
        color: #38BDF8 !important;
        border-bottom: 2px solid #06B6D4 !important;
        text-transform: uppercase;
        font-size: 0.9rem;
        letter-spacing: 0.5px;
    }
    .dataframe td {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    .dataframe tr:hover td {
        background-color: #1E293B !important;
        color: #06B6D4 !important;
    }
    
    /* Expander Glassmorphism */
    .streamlit-expanderHeader {
        background: rgba(30, 41, 59, 0.5) !important;
        border-radius: 8px !important;
        color: #38BDF8 !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# -------------------------------------------------------------
# 2. DATA LOADING & STATE
# -------------------------------------------------------------
@st.cache_data
def load_cached_results():
    clust_data, class_data, eda = None, None, None
    if os.path.exists('clustering_data.pkl'):
        with open('clustering_data.pkl', 'rb') as f:
            clust_data = pickle.load(f)
    if os.path.exists('classification_cv_results.pkl'):
        with open('classification_cv_results.pkl', 'rb') as f:
            class_data = pickle.load(f)
    if os.path.exists('eda_data.pkl'):
        with open('eda_data.pkl', 'rb') as f:
            eda = pickle.load(f)
    return clust_data, class_data, eda

clustering_data, classification_results, eda_data = load_cached_results()

# -------------------------------------------------------------
# 3. SIDEBAR NAVIGATION
# -------------------------------------------------------------
st.sidebar.markdown("# Nexus Engine")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigation Console",
    [
        "Documentation & Architecture",
        "Preprocessing & Data Funnels",
        "Customer Behavior Trends",
        "Customer Segmentation (3D)",
        "Retention Prediction (Hyperparams)"
    ]
)
st.sidebar.markdown("---")
st.sidebar.caption("System Status: ONLINE")
st.sidebar.caption("Engine: Streamlit / Plotly / Scikit-Learn")
st.sidebar.caption("Data Source: UCI Online Retail II")

# -------------------------------------------------------------
# 4. PAGES
# -------------------------------------------------------------

if page == "Documentation & Architecture":
    st.title("Codebase Architecture & Documentation")
    st.markdown("""
    This section serves as the definitive architecture guide for the Nexus Retail Analytics Engine. It details exactly what the data was at the start, how we engineered features, and what machine learning models we deployed.
    """)
    
    st.markdown("### 1. State at Start: The Raw Data")
    st.markdown("""
    The original UCI Online Retail II dataset contained **1,067,371 rows** of raw transactional logs spanning from 2009 to 2011. 
    It included 8 raw features: `Invoice` (Transaction ID), `StockCode` (Product ID), `Description` (Text name), `Quantity` (Items bought), `InvoiceDate` (Timestamp), `Price` (Unit price), `Customer_ID` (User ID), and `Country` (Origin).
    This data was extremely messy: missing user profiles, massive outlier returns, system logging errors, and test transactions.
    """)

    st.markdown("### 2. Preprocessing & Cleaning Pipeline (`preprocessing.py`)")
    with st.expander("View Preprocessing Steps", expanded=True):
        st.markdown("""
        **Data Validation:** 
        - Dropped 243,007 rows with missing `Customer_ID`.
        - Dropped 26,479 duplicate rows.
        - Dropped 70 rows with negative or zero `Price`.
        
        **Logical Flagging (Instead of Deletion):**
        - Generated `IsCancelled`: Boolean flag if `Invoice` starts with 'C'.
        - Generated `IsReturn`: Boolean flag if `Quantity` <= 0.
        - Generated `IsNonProduct`: Boolean flag if `StockCode` matches known operational codes ('POST', 'BANK CHARGES', etc.).
        
        **Formatting:**
        - Standardized string casing for `Country` and `StockCode`.
        - Casted timestamps to exact pandas `datetime64`.
        """)
        
    st.markdown("### 3. Feature Derivation & Engineering (`classf_dataset.py`)")
    with st.expander("View Derived Features", expanded=True):
        st.markdown("""
        To perform machine learning, we had to compress 800,000+ transactional logs into a structured, customer-level matrix. We derived 13 advanced mathematical features per user:
        
        **RFM Core:**
        - `Recency`: Days since the customer's last purchase.
        - `Frequency`: Total number of unique orders placed.
        - `Monetary`: Total cumulative spend.
        
        **Behavioral Velocity & Economics:**
        - `AvgBasketValue`: Average spend per order.
        - `AvgQuantity`: Average physical items purchased per order.
        - `UniqueProducts`: Total distinct items purchased.
        - `LifetimeDays`: Duration in days between a customer's first and latest purchase.
        - `PurchaseRate`: Orders placed per lifetime day (`Frequency / LifetimeDays`).
        - `AvgGapDays`: Average days elapsed between consecutive orders.
        - `PurchasesLast30Days`: Number of orders in the trailing 30 days before cutoff.
        - `SpendLast30Days`: Capital spent in the trailing 30 days.
        
        **Instability Flags:**
        - `CancellationRate`: Percentage of a user's total orders that were cancelled.
        - `ReturnRate`: Percentage of a user's total orders that were returned.
        """)
        
    st.markdown("### 4. Post-Processing & Machine Learning")
    with st.expander("View Machine Learning Pipeline"):
        st.markdown("""
        **Unsupervised Clustering (`clustering.py`):**
        - We utilized Log1P transformation to normalize skewed economic metrics, followed by a StandardScaler.
        - PCA reduced the dimensionality to 3 axes for topological analysis.
        - Models deployed: KMeans, Agglomerative Clustering, DBSCAN, Gaussian Mixture Models.
        
        **Supervised Classification (`classf_pipeline.py`):**
        - We simulated a historical cutoff at `2011-09-09`. The target label `RetentionLabel` was set to `1` if the customer made a purchase in the future 90 days, else `0`.
        - We built an advanced `sklearn` Pipeline using a `ColumnTransformer` to handle scaled and log-transformed data dynamically.
        - **Models Run:** Logistic Regression, Support Vector Machines (SVC), K-Nearest Neighbors, Decision Trees, Random Forests, and XGBoost.
        - **Tuning:** All models underwent rigorous `GridSearchCV` over predefined parameter spaces, optimizing for the `F1` score using 5-Fold Cross Validation.
        """)

elif page == "Preprocessing & Data Funnels":
    st.title("Data Preprocessing & Feature Trends")
    st.markdown("""
    Raw data is inherently noisy. Below is the visualization of our anomaly detection funnel, followed by exhaustive trend analysis of the original 8 dataset features, and finally the distribution and correlation of our custom derived ML features.
    """)
    
    # Funnel Chart
    st.markdown("### Phase 1: Data Validation Funnel")
    funnel_data = dict(
        number=[1067371, 824364, 797885, 797815],
        stage=["Raw Data", "Valid Customer IDs", "Deduplicated", "Price Validated"]
    )
    fig_funnel = go.Figure(go.Funnel(
        y = funnel_data["stage"],
        x = funnel_data["number"],
        textinfo = "value+percent initial",
        marker = {"color": ["#8B5CF6", "#6366F1", "#0EA5E9", "#10B981"]}
    ))
    fig_funnel.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#E2E8F0', size=14)
    )
    st.plotly_chart(fig_funnel, use_container_width=True)
    
    if eda_data is not None:
        st.markdown("---")
        st.markdown("### Phase 2: Original Dataset Features")
        st.markdown("Before feature engineering, we analyzed the fundamental columns of the cleaned dataset to establish base truth.")
        
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("**1. Invoice Date Trends (Revenue Over Time)**")
            if 'revenue_by_month' in eda_data:
                rev = eda_data['revenue_by_month']
                fig1 = px.line(rev, x='MonthYear', y='TransactionValue', 
                              title="Monthly Revenue Trend", color_discrete_sequence=['#06B6D4'], markers=True)
                fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#E2E8F0'), xaxis_title="Month", yaxis_title="Revenue (£)")
                st.plotly_chart(fig1, use_container_width=True)
            
            st.markdown("**3 & 4. StockCode & Description Treemap**")
            if 'treemap_products' in eda_data:
                tm = eda_data['treemap_products']
                fig3 = px.treemap(tm, path=[px.Constant("Products"), 'Product'], values='Count',
                                 color='Count', color_continuous_scale='teal', title="Top 50 Purchased Products")
                fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#E2E8F0'))
                st.plotly_chart(fig3, use_container_width=True)
            
        with c2:
            st.markdown("**2. Country of Origin**")
            top_countries = eda_data['top_countries']
            fig2 = px.bar(top_countries, x='Count', y='Country', orientation='h', 
                         title="Top 10 Source Countries", color_discrete_sequence=['#8B5CF6'])
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#E2E8F0'))
            st.plotly_chart(fig2, use_container_width=True)
            
            st.markdown("**5 & 6. Price & Quantity Distribution**")
            fig4 = go.Figure()
            fig4.add_trace(go.Box(y=eda_data['price_dist'], name="Unit Price", marker_color="#06B6D4"))
            fig4.add_trace(go.Box(y=eda_data['quantity_dist'], name="Quantity Purchased", marker_color="#F43F5E"))
            fig4.update_layout(title="Distribution of Price vs Quantity (Outliers Clipped)", 
                               paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#E2E8F0'))
            st.plotly_chart(fig4, use_container_width=True)
            
        st.markdown("**7. Customer ID**: Tracked across tracking funnels.  \n**8. Invoice ID**: Used for aggregation indexing.")
        
        st.markdown("---")
        st.markdown("### Phase 3: Derived Machine Learning Features")
        
        # Correlation Heatmap
        if 'corr_matrix' in eda_data:
            st.markdown("#### Feature Correlation Heatmap")
            st.markdown("Understanding multicollinearity between derived features.")
            corr = eda_data['corr_matrix']
            fig_corr = px.imshow(
                corr['z'], 
                x=corr['x'], y=corr['y'],
                color_continuous_scale='Viridis',
                text_auto=True,
                aspect="auto",
                title="Correlation Matrix of Derived Features"
            )
            fig_corr.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#E2E8F0'))
            st.plotly_chart(fig_corr, use_container_width=True)

        st.markdown("#### Feature Distributions")
        st.markdown("These 13 complex mathematical derivations form the core matrix used to predict churn and establish clustering topologies.")
        
        derived_dist = eda_data['derived_dist']
        features_to_plot = list(derived_dist.keys())
        
        rows = len(features_to_plot) // 3 + (1 if len(features_to_plot) % 3 != 0 else 0)
        idx = 0
        for _ in range(rows):
            cols = st.columns(3)
            for c in cols:
                if idx < len(features_to_plot):
                    feat = features_to_plot[idx]
                    fig_derived = px.histogram(derived_dist[feat], nbins=40, title=f"Distribution of {feat}", 
                                               color_discrete_sequence=['#0EA5E9'])
                    fig_derived.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                              font=dict(color='#E2E8F0'), showlegend=False, xaxis_title=feat, yaxis_title="Count")
                    c.plotly_chart(fig_derived, use_container_width=True)
                    idx += 1


elif page == "Customer Behavior Trends":
    st.title("Customer Behavior & Velocity")
    st.markdown("""
    Analyzing behavioral velocity helps pinpoint exact marketing windows. If a user is going to return naturally, they do so quickly.
    """)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Repeat Customer Rate", "72.26%")
    c2.metric("Median Purchase Gap", "24 Days")
    c3.metric("90th Percentile Gap", "135 Days")
    
    st.markdown("---")
    colA, colB = st.columns(2)
    
    with colA:
        st.markdown("### The Window of Opportunity")
        st.markdown("""
        The plot below demonstrates the cumulative probability of a returning customer making their next purchase within a specific timeframe. 
        Notice the sharp drop in velocity after 60 days. This indicates that **retention campaigns should trigger around Day 45-50 of inactivity**.
        """)
        
        x_days = ['30 Days', '60 Days', '75 Days', '90 Days']
        y_prob = [55.86, 74.70, 79.57, 83.26]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_days, y=y_prob, 
            mode='lines+markers+text',
            name='Return Probability',
            line=dict(color='#F43F5E', width=4),
            marker=dict(size=12, symbol='diamond-wide'),
            text=[f"{p}%" for p in y_prob],
            textposition="top center",
            textfont=dict(color='#F43F5E', size=14)
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#E2E8F0'),
            yaxis=dict(title='Probability (%)', range=[0, 100], gridcolor='rgba(255,255,255,0.1)'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)')
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with colB:
        if eda_data is not None and 'hourly_trend' in eda_data and 'daily_trend' in eda_data:
            st.markdown("### When do customers shop?")
            st.markdown("Time-based cadences show operational peaks, which are critical for targeted email drops and ad spend.")
            
            # Hourly trend
            hourly = eda_data['hourly_trend']
            fig_h = px.bar(hourly, x='Hour', y='Count', title="Orders by Hour of Day", color_discrete_sequence=['#10B981'])
            fig_h.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#E2E8F0'), height=250)
            st.plotly_chart(fig_h, use_container_width=True)
            
            # Daily trend
            daily = eda_data['daily_trend']
            fig_d = px.bar(daily, x='Day', y='Count', title="Orders by Day of Week", color_discrete_sequence=['#8B5CF6'])
            fig_d.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#E2E8F0'), height=250)
            st.plotly_chart(fig_d, use_container_width=True)

elif page == "Customer Segmentation (3D)":
    st.title("Topological Segmentation Maps")
    st.markdown("""
    We applied clustering algorithms to standardized, log-transformed behavioral features. 
    To visualize these hyper-dimensional groups, we applied **Principal Component Analysis (PCA)** to project them into a 3D subspace.
    """)
    
    if clustering_data is None:
        st.warning("Clustering data not found. Please run backend extraction.")
    else:
        pca_3d = clustering_data['pca_3d']
        labels_dict = clustering_data['labels']
        
        tabs = st.tabs(list(labels_dict.keys()))
        
        for idx, (model_name, labels) in enumerate(labels_dict.items()):
            with tabs[idx]:
                st.markdown(f"### {model_name} Space Topology")
                st.markdown("Rotate and zoom the 3D map to explore how the algorithm separated the customer profiles.")
                
                fig_3d = px.scatter_3d(
                    x=pca_3d[:,0], y=pca_3d[:,1], z=pca_3d[:,2],
                    color=[str(l) for l in labels],
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                    labels={'x':'PCA 1', 'y':'PCA 2', 'z':'PCA 3'},
                    title=f"3D Cluster Distribution: {model_name}"
                )
                fig_3d.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    scene=dict(
                        xaxis=dict(backgroundcolor='rgba(0,0,0,0)', gridcolor='rgba(255,255,255,0.1)', title_font=dict(color='#E2E8F0')),
                        yaxis=dict(backgroundcolor='rgba(0,0,0,0)', gridcolor='rgba(255,255,255,0.1)', title_font=dict(color='#E2E8F0')),
                        zaxis=dict(backgroundcolor='rgba(0,0,0,0)', gridcolor='rgba(255,255,255,0.1)', title_font=dict(color='#E2E8F0')),
                    ),
                    legend=dict(font=dict(color='#E2E8F0'), title=dict(text="Cluster ID"))
                )
                st.plotly_chart(fig_3d, use_container_width=True, height=700)
                
                scores = {
                    'KMeans': (0.3244, 1.1163),
                    'Agglomerative': (0.3204, 1.1298),
                    'DBSCAN': (0.4409, 0.8368),
                    'GaussianMixture': (0.2747, 1.4684)
                }
                c1, c2 = st.columns(2)
                c1.metric("Silhouette Score (Higher is Better)", scores[model_name][0])
                c2.metric("Davies Bouldin Score (Lower is Better)", scores[model_name][1])

elif page == "Retention Prediction (Hyperparams)":
    st.title("Retention Modeling & Hyperparameter Search")
    st.markdown("""
    We evaluated several models to predict 90-day churn. To prove rigor, we executed **GridSearchCV** over a hyperparameter space for each algorithm, optimizing for the `F1 Score`.
    """)
    
    if classification_results is None:
        st.warning("Classification results not found. Please run backend extraction.")
    else:
        st.markdown("### Radar Comparison of Best Models")
        st.markdown("This radar chart compares the absolute best-performing configuration of each algorithm across Accuracy, Precision, Recall, F1, and ROC AUC.")
        
        radar_df = pd.DataFrame({
            "Metric": ["Accuracy", "Precision", "Recall", "F1 Score", "ROC AUC"],
            "RandomForest": [0.6906, 0.7284, 0.7923, 0.7591, 0.7666],
            "XGBoost": [0.6906, 0.7179, 0.8187, 0.7650, 0.7608],
            "LogisticReg": [0.6744, 0.7069, 0.8040, 0.7523, 0.7578],
            "SVC": [0.6924, 0.7100, 0.8450, 0.7716, 0.7442]
        })
        
        fig_radar = go.Figure()
        
        # Fix for Plotly Scatterpolar fillcolor bug (Hex length 8 -> RGBA)
        border_colors = ['rgba(6, 182, 212, 1)', 'rgba(16, 185, 129, 1)', 'rgba(245, 158, 11, 1)', 'rgba(139, 92, 246, 1)']
        fill_colors = ['rgba(6, 182, 212, 0.2)', 'rgba(16, 185, 129, 0.2)', 'rgba(245, 158, 11, 0.2)', 'rgba(139, 92, 246, 0.2)']
        
        for idx, model in enumerate(["RandomForest", "XGBoost", "LogisticReg", "SVC"]):
            fig_radar.add_trace(go.Scatterpolar(
                r=radar_df[model],
                theta=radar_df["Metric"],
                fill='toself',
                name=model,
                line=dict(color=border_colors[idx]),
                fillcolor=fill_colors[idx]
            ))
            
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0.65, 0.85], gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#94A3B8')),
                angularaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='#E2E8F0', size=14)),
                bgcolor='rgba(0,0,0,0)'
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#E2E8F0')
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### Hyperparameter Optimization Surfaces")
        st.markdown("Select a model below to explore how tweaking specific hyperparameters drastically affected cross-validation test scores (Mean F1 Score).")
        
        model_selection = st.selectbox("Select Model for Hyperparameter Drilldown:", list(classification_results.keys()))
        
        res = classification_results[model_selection]
        params_list = res['params']
        mean_scores = res['mean_test_score']
        
        flat_params = []
        for i, p_dict in enumerate(params_list):
            row = {'Mean F1 Score': mean_scores[i]}
            for k, v in p_dict.items():
                clean_k = k.replace('model__', '')
                row[clean_k] = str(v) if isinstance(v, (bool, str)) else v
            flat_params.append(row)
            
        df_hp = pd.DataFrame(flat_params)
        
        st.markdown(f"**Top 5 Configurations for {model_selection}:**")
        st.dataframe(df_hp.sort_values(by='Mean F1 Score', ascending=False).head(5), use_container_width=True)
        
        param_cols = [c for c in df_hp.columns if c != 'Mean F1 Score']
        
        if len(param_cols) == 1:
            fig_hp = px.line(
                df_hp.sort_values(by=param_cols[0]), 
                x=param_cols[0], y="Mean F1 Score",
                markers=True, title=f"Effect of {param_cols[0]} on Performance",
                color_discrete_sequence=['#06B6D4']
            )
        elif len(param_cols) >= 2:
            x_col = param_cols[0]
            color_col = param_cols[1]
            fig_hp = px.scatter(
                df_hp, x=x_col, y="Mean F1 Score", color=color_col, size_max=15, size=[1]*len(df_hp),
                title=f"Interaction: {x_col} vs {color_col}",
                color_discrete_sequence=px.colors.qualitative.Vivid
            )
            fig_hp.update_traces(marker=dict(size=12, opacity=0.8, line=dict(width=1, color='white')))

        fig_hp.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#E2E8F0'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)', title_font=dict(color='#E2E8F0')),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title_font=dict(color='#E2E8F0'))
        )
        st.plotly_chart(fig_hp, use_container_width=True)
