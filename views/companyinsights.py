import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import config  # Import your config module


def load_data_source():
    """
    Load data from either SQL or CSV based on config.USE_SQL setting
    Returns: tuple of (salary_df, employee_master)
    """
    try:
        if config.USE_SQL:
            # Load from SQL Server
            conn = config.get_sql_connection()

            # Load salary data
            salary_query = f"SELECT * FROM {config.SALARY_LOG_TABLE}"
            salary_df = pd.read_sql(salary_query, conn)

            # Load employee master data
            employee_query = f"SELECT * FROM {config.EMPLOYEE_MASTER_TABLE}"
            employee_master = pd.read_sql(employee_query, conn)

            conn.close()
            st.success("✅ Data loaded from SQL Server")

        else:
            # Load from CSV files
            salary_df = pd.read_csv(config.SALARY_LOG_CSV)
            employee_master = pd.read_csv(config.EMPLOYEE_MASTER_CSV, dtype={"employee_id": str})
            st.success("✅ Data loaded from CSV files")

        return salary_df, employee_master

    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        if config.USE_SQL:
            st.warning("Falling back to CSV files...")
            try:
                salary_df = pd.read_csv(config.SALARY_LOG_CSV)
                employee_master = pd.read_csv(config.EMPLOYEE_MASTER_CSV, dtype={"employee_id": str})
                st.success("✅ Fallback: Data loaded from CSV files")
                return salary_df, employee_master
            except Exception as csv_error:
                st.error(f"❌ CSV fallback also failed: {str(csv_error)}")
                return None, None
        return None, None


def run_companyinsights():
    st.set_page_config(page_title="📊 Company Insights Dashboard", layout="wide")

    # Header with data source indicator
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📊 Company Insights Dashboard")
    with col2:
        data_source = "🗄️ SQL Server" if config.USE_SQL else "📁 CSV Files"
        st.markdown(f"**Data Source:** {data_source}")

    st.markdown("Explore team performance, CTC breakdowns, and employee highlights.")

    # 📥 Load Data with error handling
    with st.spinner("Loading data..."):
        salary_df, employee_master = load_data_source()

    if salary_df is None or employee_master is None:
        st.error("Failed to load data. Please check your configuration and data sources.")
        return

    # Data validation
    if salary_df.empty:
        st.warning("No salary data found.")
        return

    if employee_master.empty:
        st.warning("No employee master data found.")
        return

    # 🧹 Data Preparation
    try:
        # Clean column names
        salary_df.columns = salary_df.columns.str.strip()
        employee_master.columns = employee_master.columns.str.strip()

        # Prep date columns
        salary_df["data_date"] = pd.to_datetime(salary_df["data_date"], errors="coerce")
        salary_df = salary_df.dropna(subset=["data_date"])  # Remove rows with invalid dates

        if salary_df.empty:
            st.error("No valid date data found in salary records.")
            return

        salary_df["month_str"] = salary_df["data_date"].dt.strftime("%b %Y")

        # Ensure employee_id is string for both dataframes
        salary_df["employee_id"] = salary_df["employee_id"].astype(str)
        employee_master["employee_id"] = employee_master["employee_id"].astype(str)
        employee_master["employee_name"] = employee_master["employee_name"].astype(str)

        # 👥 Merge Salary + Employee Info
        merged_df = salary_df.merge(
            employee_master[["employee_id", "employee_name", "department", "role"]],
            on="employee_id",
            how="left"
        )

        # Handle merge column naming conflicts
        if "employee_name_y" in merged_df.columns:
            merged_df = merged_df.rename(columns={"employee_name_y": "employee_name"})
        if "employee_name_x" in merged_df.columns:
            merged_df = merged_df.drop(columns=["employee_name_x"])

        # 🔧 Fill missing values for text fields
        merged_df = merged_df.fillna({
            "department": "Unknown",
            "role": "Unknown",
            "employee_name": "Unknown Employee"
        })

        # 🔒 Ensure numeric columns exist and are numeric
        numeric_columns = [
            "full_days", "extra_hours", "late_marks", "leave_concession_amount",
            "festival_bonus", "net_salary", "leave_balance"
        ]

        for col in numeric_columns:
            if col not in merged_df.columns:
                merged_df[col] = 0
                st.warning(f"Column '{col}' not found, defaulting to 0")
            merged_df[col] = pd.to_numeric(merged_df[col], errors="coerce").fillna(0)

        # 🛡️ Dedication Index Calculation
        merged_df["score"] = (
                merged_df["full_days"] * 2
                + merged_df["extra_hours"] * 0.5
                - merged_df["late_marks"]
        )
        merged_df["dedication_index"] = merged_df["score"] + (merged_df["extra_hours"] * 5)

        # 🔥 Badge Logic
        def get_badges(row):
            badges = []
            if row.get("festival_bonus", 0) > 0:
                badges.append("🎉 Festival Bonus")
            if row.get("extra_hours", 0) >= 10:
                badges.append("⚡ Extra Hours Hero")
            if row.get("full_days", 0) >= 22:
                badges.append("🥇 Consistent Attendance")
            if row.get("leave_concession_amount", 0) > 0:
                badges.append("🛡️ Leave Concession")
            return " | ".join(badges) if badges else "—"

        merged_df["badges"] = merged_df.apply(get_badges, axis=1)

        # Data Quality Summary
        with st.expander("📋 Data Quality Summary"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Records", len(merged_df))
            with col2:
                st.metric("Unique Employees", merged_df["employee_id"].nunique())
            with col3:
                st.metric("Date Range",
                          f"{merged_df['data_date'].min().strftime('%Y-%m')} to {merged_df['data_date'].max().strftime('%Y-%m')}")
            with col4:
                st.metric("Departments", merged_df["department"].nunique())

        # 🏅 Top 3 Dedication Index
        st.subheader("🏅 Employee Highlights")
        top3 = merged_df.groupby(["employee_id", "employee_name"])["dedication_index"] \
            .sum().reset_index().sort_values("dedication_index", ascending=False).head(3)

        if top3.empty:
            st.info("No high-performers found for this period.")
        else:
            emojis = ["🥇", "🥈", "🥉"]
            for idx, row in top3.reset_index(drop=True).iterrows():
                emoji = emojis[idx] if idx < len(emojis) else "🏅"
                st.markdown(f"""
                <div style='background:#f0f8ff; padding:10px; margin-bottom:10px;
                border-left:6px solid #4682b4; border-radius:8px'>
                <h4>{emoji} {row['employee_name'].title()}</h4>
                <p>Dedication Index: {row['dedication_index']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)

        # 🎉 Badge Showcase
        st.subheader("✨ Featured Employees")
        badge_df = merged_df[merged_df["badges"] != "—"]

        if badge_df.empty:
            st.info("No employees with special badges found.")
        else:
            for _, row in badge_df.groupby("employee_name").tail(1).iterrows():
                st.markdown(f"""
                <div style='background:#fffbea; padding:10px; margin-bottom:10px;
                border-radius:8px; border-left:6px solid #f5c518'>
                <h4>{row['employee_name'].title()}</h4>
                <p>{row['badges']}</p>
                </div>
                """, unsafe_allow_html=True)

        # 📈 Monthly Salary Trend
        st.subheader("📈 Monthly Salary Trend")
        trend_df = merged_df.groupby("month_str")["net_salary"].sum().reset_index()
        trend_df = trend_df.sort_values("month_str")

        if not trend_df.empty:
            st.bar_chart(trend_df.set_index("month_str"))
        else:
            st.warning("No salary trend data available.")

        # 📊 Payroll Heatmap
        st.subheader("📊 Payroll Heatmap")
        if len(merged_df["employee_name"].unique()) > 1 and len(merged_df["month_str"].unique()) > 1:
            heatmap_df = merged_df.pivot_table(
                index="employee_name",
                columns="month_str",
                values="net_salary",
                fill_value=0
            )

            fig_heatmap = go.Figure(data=go.Heatmap(
                z=heatmap_df.values,
                x=heatmap_df.columns,
                y=heatmap_df.index,
                text=heatmap_df.round(0).astype(str).values,
                texttemplate="%{text}",
                colorscale="Bluered",
                hoverongaps=False
            ))
            fig_heatmap.update_layout(
                title="Payroll Heatmap",
                xaxis_title="Month",
                yaxis_title="Employee",
                height=max(400, len(heatmap_df.index) * 30)
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.info("Insufficient data for heatmap visualization.")

        # 💼 Department Summary
        st.subheader("💼 Department-wise Salary Stats")
        summary = merged_df.groupby("department")[
            ["net_salary", "festival_bonus", "leave_balance"]
        ].agg({
            "net_salary": ["mean", "sum", "count"],
            "festival_bonus": "mean",
            "leave_balance": "mean"
        }).round(2)

        # Flatten column names
        summary.columns = [f"{col[0]}_{col[1]}" if col[1] else col[0] for col in summary.columns]
        summary = summary.rename(columns={
            "net_salary_mean": "Avg Salary",
            "net_salary_sum": "Total Payroll",
            "net_salary_count": "Employee Count",
            "festival_bonus_mean": "Avg Festival Bonus",
            "leave_balance_mean": "Avg Leave Balance"
        })

        st.dataframe(summary, use_container_width=True)

        # Department salary distribution chart
        dept_summary = merged_df.groupby("department")["net_salary"].mean().reset_index()
        fig_bar = px.bar(
            dept_summary,
            x="net_salary",
            y="department",
            orientation="h",
            title="Average Salary by Department",
            color="net_salary",
            color_continuous_scale="Blues"
        )
        fig_bar.update_layout(height=max(300, len(dept_summary) * 50))
        st.plotly_chart(fig_bar, use_container_width=True)

        # 📊 Quick Stats
        st.subheader("📊 Quick Statistics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Payroll",
                f"₹{merged_df['net_salary'].sum():,.0f}"
            )
        with col2:
            st.metric(
                "Average Salary",
                f"₹{merged_df['net_salary'].mean():,.0f}"
            )
        with col3:
            st.metric(
                "Total Bonuses",
                f"₹{merged_df['festival_bonus'].sum():,.0f}"
            )
        with col4:
            st.metric(
                "Avg Extra Hours",
                f"{merged_df['extra_hours'].mean():.1f}"
            )

    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        st.info("Please check your data format and column names.")


if __name__ == "__main__":
    run_companyinsights()