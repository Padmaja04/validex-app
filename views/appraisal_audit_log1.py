import streamlit as st
import pandas as pd
import plotly.express as px
from config import USE_SQL, get_sql_connection

def run_appraisal_audit_log1():
    st.title("📊 Appraisal Intelligence Dashboard")
    st.write("An integrated view of appraisal health, reviewer behavior, and department-level fairness.")

    # Load employee master data
    if USE_SQL:
        conn = get_sql_connection()
        master_df = pd.read_sql("SELECT * FROM dbo.employee_master", conn)
        conn.close()
    else:
        master_path = "data/employee_master.csv"
        master_df = pd.read_csv(master_path)

    master_df["employee_id"] = master_df["employee_id"].astype(str)

    # 🎯 Calibration Center
    show_calibration_center(master_df)

    # 🕵️ Reviewer Audit Logs
    show_reviewer_logs(master_df)

    # 📈 Role-Based Reviewer Insights
    show_role_insights(master_df)

def show_calibration_center(master_df):
    st.markdown("### 🎯 Rating Distribution Across Organization")
    rating_distribution = master_df["performance_rating"].value_counts().sort_index()
    fig = px.bar(
        x=rating_distribution.index,
        y=rating_distribution.values,
        labels={"x": "Rating", "y": "Count"},
        title="📊 Rating Distribution"
    )
    st.plotly_chart(fig)

def show_reviewer_logs(master_df):
    st.markdown("### 🕵️ Reviewer Audit Log")
    audit_log = master_df[[
        "employee_id", "employee_name", "performance_rating",
        "appraisal_hike_percent", "reviewer_id",
        "appraisal_notes", "appraisal_date"
    ]].sort_values("appraisal_date", ascending=False)
    st.dataframe(audit_log)

def show_role_insights(master_df):
    st.markdown("### 📈 Department vs Reviewer Trends")
    insights = master_df.groupby(["department", "reviewer_id"]).agg({
        "performance_rating": "mean",
        "appraisal_hike_percent": "mean"
    }).reset_index()
    st.dataframe(insights)