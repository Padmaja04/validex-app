# adminaudit.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
from config import (
    USE_SQL, get_sql_connection,
    EMPLOYEE_DATA_CSV, EMPLOYEE_MASTER_CSV, VERIFIED_ADMINS_CSV,
    EMPLOYEE_DATA_TABLE, EMPLOYEE_MASTER_TABLE, VERIFIED_ADMIN_TABLE
)

def run_adminaudit():
    st.set_page_config(page_title="Admin Audit Logs", layout="wide")
    st.title("🔍 Admin Audit Logs")

    # Show data source info
    st.info(f"📦 Data Source: {'SQL Database' if USE_SQL else 'CSV Files'}")

    # -------------------- LOADERS --------------------
    def load_employee_data():
        if USE_SQL:
            with get_sql_connection() as conn:
                return pd.read_sql(f"SELECT * FROM {EMPLOYEE_DATA_TABLE}", conn)
        else:
            return pd.read_csv(EMPLOYEE_DATA_CSV)

    def load_employee_master():
        if USE_SQL:
            with get_sql_connection() as conn:
                return pd.read_sql(f"SELECT * FROM {EMPLOYEE_MASTER_TABLE}", conn)
        else:
            return pd.read_csv(EMPLOYEE_MASTER_CSV)

    def load_verified_admins():
        if USE_SQL:
            with get_sql_connection() as conn:
                df = pd.read_sql(f"SELECT admin_user FROM {VERIFIED_ADMIN_TABLE}", conn)
        else:
            if not os.path.exists(VERIFIED_ADMINS_CSV):
                st.warning("⚠️ Verified admins file not found.")
                return []
            df = pd.read_csv(VERIFIED_ADMINS_CSV)

        if "admin_user" not in df.columns:
            st.error("❌ 'admin_user' column missing in verified admins data.")
            return []
        return df["admin_user"].astype(str).str.strip().str.lower().dropna().unique().tolist()

    # -------------------- LOAD DATA --------------------
    log_df = load_employee_data()
    employee_master = load_employee_master()
    verified_list = load_verified_admins()

    if log_df.empty or employee_master.empty:
        st.warning("🔁 Waiting for data...")
        return

    # Normalize fields
    log_df["admin_user"] = log_df["admin_user"].astype(str).str.strip().str.lower()
    log_df["employee_id"] = log_df["employee_id"].astype(str).str.strip().str.upper()
    employee_master["employee_id"] = employee_master["employee_id"].astype(str).str.strip().str.upper()

    # Ensure audit columns
    audit_cols = ["timestamp", "admin_user", "action_type", "description", "reason", "date_only"]
    for col in audit_cols:
        if col not in log_df.columns:
            log_df[col] = pd.NA

    # Risky action detection
    def is_risky(row):
        keywords = ["override", "manual", "clearance bypass", "status change"]
        combined = f"{str(row['action_type'])} {str(row['description'])}".lower()
        return any(k in combined for k in keywords)

    log_df["is_risky"] = log_df.apply(is_risky, axis=1)

    # Merge employee names
    if "employee_name" not in employee_master.columns:
        employee_master["employee_name"] = "Unknown"
    log_df = pd.merge(
        log_df,
        employee_master[["employee_id", "employee_name"]],
        on="employee_id",
        how="left",
        suffixes=('', '_master')
    )
    log_df["employee_name"] = log_df["employee_name"].fillna("Unknown")

    # Verified badge
    log_df["admin_user_display"] = log_df["admin_user"].apply(
        lambda x: f"{x} ✅" if x in verified_list else x
    )

    # Date range
    log_df["timestamp"] = pd.to_datetime(log_df["timestamp"], errors="coerce")
    valid_timestamps = log_df["timestamp"].dropna()
    date_min = valid_timestamps.min().date() if not valid_timestamps.empty else datetime(2023, 1, 1).date()
    date_max = valid_timestamps.max().date() if not valid_timestamps.empty else datetime.today().date()

    # -------------------- FILTERS --------------------
    st.subheader("🔎 Filter Controls")
    with st.expander("Adjust filters", expanded=True):
        admins = sorted(log_df["admin_user"].dropna().unique())
        employees = sorted(log_df["employee_name"].dropna().unique())
        actions = sorted(log_df["action_type"].dropna().unique())

        selected_admin = st.selectbox("Admin", ["All"] + admins)
        selected_emp = st.selectbox("Employee", ["All"] + employees)
        selected_action = st.selectbox("Action Type", ["All"] + actions)
        filter_verified = st.checkbox("✅ Show only verified")
        date_range = st.date_input("Date Range", value=[date_min, date_max])

    # Apply filters
    filtered = log_df.copy()
    if selected_admin != "All":
        filtered = filtered[filtered["admin_user"] == selected_admin]
    if selected_emp != "All":
        filtered = filtered[filtered["employee_name"] == selected_emp]
    if selected_action != "All":
        filtered = filtered[filtered["action_type"] == selected_action]
    if filter_verified:
        verified_normalized = [v.strip().lower() for v in verified_list]
        filtered = filtered[filtered["admin_user"].isin(verified_normalized)]

    # Date filter
    start_date = datetime.combine(date_range[0], datetime.min.time())
    end_date = datetime.combine(date_range[1], datetime.max.time())
    filtered = filtered.dropna(subset=["timestamp"])
    filtered = filtered[(filtered["timestamp"] >= start_date) & (filtered["timestamp"] <= end_date)]

    # -------------------- DISPLAY --------------------
    st.subheader("📋 Filtered Logs")
    st.caption(f"🔍 Showing {len(filtered)} entries")
    st.dataframe(filtered.sort_values("timestamp", ascending=False)[[
        "timestamp", "date_only", "admin_user_display", "employee_name",
        "action_type", "description", "reason", "is_risky"
    ]], use_container_width=True)

    # Action Trends
    st.subheader("📈 Action Trends")
    if not filtered.empty:
        chart_data = filtered.copy()
        chart_data["date_only"] = chart_data["timestamp"].dt.date
        count_data = chart_data.groupby(["date_only", "action_type"]).size().reset_index(name="count")
        fig = px.bar(count_data, x="date_only", y="count", color="action_type",
                     title="Actions Over Time", labels={"date_only": "Date", "count": "Count"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📭 No actions to plot.")

    # Risky actions
    st.subheader("🚨 Risky Actions")
    risky = filtered[filtered["is_risky"]]
    if not risky.empty:
        st.dataframe(risky.sort_values("timestamp", ascending=False)[[
            "timestamp", "date_only", "admin_user_display", "employee_name",
            "action_type", "description", "reason"
        ]], use_container_width=True)
    else:
        st.info("✅ No risky edits detected.")

    # Download option
    if not filtered.empty:
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Filtered Logs",
            csv,
            file_name="filtered_admin_logs.csv",
            mime="text/csv"
        )