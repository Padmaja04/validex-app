import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
from config import (
    USE_SQL, safe_get_conn, table_exists, safe_float, safe_datetime_for_sql,
    EMPLOYEE_MASTER_CSV, EMPLOYEE_DATA_CSV, SALARY_LOG_CSV, FEEDBACK_RAW_CSV ,FEEDBACK_REVIEWED_CSV,
    VERIFIED_ADMINS_CSV, RESIGNATION_LOG_CSV, BADGE_DIR,
    EMPLOYEE_MASTER_TABLE, EMPLOYEE_DATA_TABLE, SALARY_LOG_TABLE,
    FEEDBACK_RAW_TABLE,FEEDBACK_REVIEWED_TABLE, VERIFIED_ADMIN_TABLE, RESIGNATION_LOG_TABLE
)


# -------------------------------
# 📥 Enhanced Loaders with SQL/CSV Support
# -------------------------------

def get_table_columns(conn, table_name):
    """Get list of columns that actually exist in the table"""
    try:
        if "." in table_name:
            schema, tname = table_name.split(".", 1)
        else:
            schema, tname = "dbo", table_name

        cursor = conn.cursor()
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
        """, (schema.strip("[]"), tname.strip("[]")))

        columns = [row[0] for row in cursor.fetchall()]
        return columns

    except Exception as e:
        st.error(f"Error getting table columns: {str(e)}")
        return []


def build_safe_query(table_name, desired_columns, conn):
    """Build a safe SQL query using only columns that actually exist"""
    try:
        available_columns = get_table_columns(conn, table_name)

        if not available_columns:
            return None, []

        # Find which desired columns actually exist
        safe_columns = []
        for col in desired_columns:
            if col in available_columns:
                safe_columns.append(col)

        if not safe_columns:
            # If no desired columns exist, get all available columns
            safe_columns = available_columns

        query = f"SELECT {', '.join(safe_columns)} FROM {table_name}"
        return query, safe_columns

    except Exception as e:
        st.error(f"Error building safe query: {str(e)}")
        return None, []


def load_attendance_data():
    """Load attendance data from SQL or CSV based on USE_SQL setting"""
    try:
        if USE_SQL:
            conn = safe_get_conn()
            if conn is None:
                st.error("Failed to connect to SQL Server. Check your configuration.")
                return pd.DataFrame()

            # Check if tables exist
            if not table_exists(conn, EMPLOYEE_DATA_TABLE):
                st.error(f"Table {EMPLOYEE_DATA_TABLE} does not exist in database.")
                conn.close()
                return pd.DataFrame()

            if not table_exists(conn, EMPLOYEE_MASTER_TABLE):
                st.error(f"Table {EMPLOYEE_MASTER_TABLE} does not exist in database.")
                conn.close()
                return pd.DataFrame()

            # Build safe queries using available columns (updated to use extra_hours)
            punch_desired_cols = ["employee_id", "employee_name", "start_datetime", "exit_datetime",
                                  "attendance_status", "late_mark", "extra_hours"]
            master_desired_cols = ["employee_id", "employee_name", "department", "designation",
                                   "hire_date", "salary", "contact_number", "email"]

            punch_query, punch_cols = build_safe_query(EMPLOYEE_DATA_TABLE, punch_desired_cols, conn)
            master_query, master_cols = build_safe_query(EMPLOYEE_MASTER_TABLE, master_desired_cols, conn)

            if not punch_query or not master_query:
                st.error("Could not build valid queries for the tables.")
                conn.close()
                return pd.DataFrame()

            # Add WHERE clause if start_datetime column exists
            if "start_datetime" in punch_cols:
                punch_query += " WHERE start_datetime IS NOT NULL"

            st.info(f"Loading data with available columns: {', '.join(punch_cols)}")

            punch_df = pd.read_sql(punch_query, conn)
            master_df = pd.read_sql(master_query, conn)
            conn.close()

            # Convert datetime columns if they exist
            for col in ["start_datetime", "exit_datetime", "hire_date"]:
                if col in punch_df.columns:
                    punch_df[col] = pd.to_datetime(punch_df[col], errors="coerce")
                if col in master_df.columns:
                    master_df[col] = pd.to_datetime(master_df[col], errors="coerce")

        else:
            # Load from CSV files
            if not os.path.exists(EMPLOYEE_DATA_CSV):
                st.error(f"CSV file {EMPLOYEE_DATA_CSV} not found.")
                return pd.DataFrame()

            if not os.path.exists(EMPLOYEE_MASTER_CSV):
                st.error(f"CSV file {EMPLOYEE_MASTER_CSV} not found.")
                return pd.DataFrame()

            punch_df = pd.read_csv(EMPLOYEE_DATA_CSV)
            master_df = pd.read_csv(EMPLOYEE_MASTER_CSV)

            # Convert datetime columns if they exist
            datetime_cols = ["start_datetime", "exit_datetime", "hire_date"]
            for col in datetime_cols:
                if col in punch_df.columns:
                    punch_df[col] = pd.to_datetime(punch_df[col], errors="coerce")
                if col in master_df.columns:
                    master_df[col] = pd.to_datetime(master_df[col], errors="coerce")

        # Data processing (common for both SQL and CSV)
        if "employee_name" in punch_df.columns and "employee_name" in master_df.columns:
            master_df["employee_name"] = master_df["employee_name"].str.strip().str.lower()
            punch_df["employee_name"] = punch_df["employee_name"].str.strip().str.lower()

        # Merge the datasets on employee_id if both have it
        if "employee_id" in punch_df.columns and "employee_id" in master_df.columns:
            merged = punch_df.merge(master_df, on="employee_id", how="left", suffixes=('_punch', '_master'))

            # Use master employee_name if punch name is missing
            if "employee_name_master" in merged.columns and "employee_name_punch" in merged.columns:
                merged["employee_name"] = merged["employee_name_master"].fillna(merged["employee_name_punch"])

            # Clean up duplicate columns
            cols_to_drop = [col for col in merged.columns if col.endswith(('_punch', '_master'))]
            merged = merged.drop(columns=cols_to_drop, errors='ignore')
        else:
            # If no common employee_id, just use punch data
            merged = punch_df.copy()
            st.warning("Could not merge employee master data - no common employee_id column")

        # Create derived columns if possible
        if "start_datetime" in merged.columns:
            merged["date_only"] = pd.to_datetime(merged["start_datetime"], errors="coerce").dt.date
            merged["weekday"] = pd.to_datetime(merged["start_datetime"], errors="coerce").dt.day_name()
            merged["hour"] = pd.to_datetime(merged["start_datetime"], errors="coerce").dt.hour

        return merged

    except Exception as e:
        st.error(f"Error loading attendance data: {str(e)}")
        return pd.DataFrame()


def load_resignation_data():
    """Load resignation data from SQL or CSV based on USE_SQL setting"""
    try:
        if USE_SQL:
            conn = safe_get_conn()
            if conn is None:
                st.warning("Failed to connect to SQL Server for resignation data.")
                return pd.DataFrame()

            if not table_exists(conn, RESIGNATION_LOG_TABLE):
                st.warning(f"Table {RESIGNATION_LOG_TABLE} does not exist. Creating empty DataFrame.")
                conn.close()
                return pd.DataFrame()

            # Build safe query using available columns
            desired_cols = ["employee_id", "employee_name", "department", "notice_issued_date",
                            "resignation_date", "reason", "status", "admin_cleared", "clearance_notes"]

            query, available_cols = build_safe_query(RESIGNATION_LOG_TABLE, desired_cols, conn)

            if not query:
                st.warning("Could not build valid query for resignation table.")
                conn.close()
                return pd.DataFrame()

            # Add WHERE clause if notice_issued_date exists
            if "notice_issued_date" in available_cols:
                query += " WHERE notice_issued_date IS NOT NULL"

            st.info(f"Loading resignation data with columns: {', '.join(available_cols)}")

            df = pd.read_sql(query, conn)
            conn.close()

            # Convert datetime columns if they exist
            for col in ["notice_issued_date", "resignation_date"]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

        else:
            if not os.path.exists(RESIGNATION_LOG_CSV):
                st.warning(f"CSV file {RESIGNATION_LOG_CSV} not found. Creating empty DataFrame.")
                return pd.DataFrame()

            df = pd.read_csv(RESIGNATION_LOG_CSV)

            # Convert datetime columns if they exist
            datetime_cols = ["notice_issued_date", "resignation_date"]
            for col in datetime_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

        # Calculate days since notice if possible
        if "notice_issued_date" in df.columns:
            df["days_since_notice"] = (pd.Timestamp.today() - df["notice_issued_date"]).dt.days

        return df

    except Exception as e:
        st.error(f"Error loading resignation data: {str(e)}")
        return pd.DataFrame()


def load_salary_data():
    """Load salary data from SQL or CSV based on USE_SQL setting"""
    try:
        if USE_SQL:
            conn = safe_get_conn()
            if conn is None:
                return pd.DataFrame()

            if not table_exists(conn, SALARY_LOG_TABLE):
                conn.close()
                return pd.DataFrame()

            # Build safe query using available columns
            desired_cols = ["employee_id", "employee_name", "department", "salary_date",
                            "base_salary", "overtime_pay", "deductions", "net_salary"]

            query, available_cols = build_safe_query(SALARY_LOG_TABLE, desired_cols, conn)

            if not query:
                conn.close()
                return pd.DataFrame()

            # Add ORDER BY if salary_date exists
            if "salary_date" in available_cols:
                query += " ORDER BY salary_date DESC"

            df = pd.read_sql(query, conn)
            conn.close()

            # Convert datetime columns if they exist
            if "salary_date" in df.columns:
                df["salary_date"] = pd.to_datetime(df["salary_date"], errors="coerce")

        else:
            if not os.path.exists(SALARY_LOG_CSV):
                return pd.DataFrame()

            df = pd.read_csv(SALARY_LOG_CSV)

            # Convert datetime columns if they exist
            if "salary_date" in df.columns:
                df["salary_date"] = pd.to_datetime(df["salary_date"], errors="coerce")

        return df

    except Exception as e:
        st.error(f"Error loading salary data: {str(e)}")
        return pd.DataFrame()


# -------------------------------
# 📊 Enhanced Analytics Functions
# -------------------------------

def show_cxo_summary(df, resign_df):
    st.subheader("🧠 CXO Snapshot")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if "hour" in df.columns:
            avg_hour = df["hour"].dropna().mean()
            st.metric("⏰ Avg Punch-In", f"{avg_hour:.1f}:00" if pd.notnull(avg_hour) else "N/A")
        else:
            st.metric("⏰ Avg Punch-In", "N/A")

    with col2:
        if not resign_df.empty and "status" in resign_df.columns and "admin_cleared" in resign_df.columns:
            pending_clearances = resign_df[
                (resign_df["status"].str.lower() == "pending") &
                (resign_df["admin_cleared"].isnull())
                ].shape[0]
        else:
            pending_clearances = 0
        st.metric("🗂️ Pending Clearances", pending_clearances)

    with col3:
        if not df.empty and "date_only" in df.columns and "employee_id" in df.columns:
            last_punch = df.groupby("employee_id")["date_only"].max()
            cutoff = pd.Timestamp.today().date() - pd.Timedelta(days=5)
            inactive = (last_punch < cutoff).sum()
        else:
            inactive = 0
        st.metric("😴 Inactive Employees", inactive)

    with col4:
        total_employees = df["employee_id"].nunique() if not df.empty and "employee_id" in df.columns else 0
        st.metric("👥 Total Employees", total_employees)


def show_kpis(df):
    st.subheader("📌 Key Performance Indicators")

    if df.empty:
        st.info("No data available for KPIs")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_punch_hour = df["hour"].dropna().mean() if "hour" in df.columns else None
        st.metric("Avg Punch-In Hour", f"{avg_punch_hour:.2f}" if pd.notnull(avg_punch_hour) else "N/A")

    with col2:
        full_day_count = df[df["attendance_status"] == "Full Day"].shape[0] if "attendance_status" in df.columns else 0
        st.metric("Full Day Attendance", full_day_count)

    with col3:
        late_count = df[df["late_mark"] == True].shape[0] if "late_mark" in df.columns else 0
        st.metric("Late Arrivals", late_count)

    with col4:
        # Use extra_hours instead of overtime_hours
        if "extra_hours" in df.columns:
            extra_hours = df["extra_hours"].sum()
            st.metric("Total Extra Hours", f"{extra_hours:.1f}")
        else:
            st.metric("Total Extra Hours", "N/A")


def show_attendance_heatmap(df):
    """Enhanced attendance heatmap with better error handling"""
    st.subheader("📆 Attendance Heatmap")

    if df.empty or "weekday" not in df.columns or "hour" not in df.columns:
        st.info("No attendance data available for heatmap - missing weekday or hour columns")
        return

    try:
        # Create heatmap data
        heatmap_data = df.groupby(["weekday", "hour"]).size().unstack(fill_value=0)

        if heatmap_data.empty:
            st.info("No data available for heatmap visualization")
            return

        # Reorder days
        ordered_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        available_days = [day for day in ordered_days if day in heatmap_data.index]
        heatmap_data = heatmap_data.reindex(available_days)

        # Create the plot
        fig, ax = plt.subplots(figsize=(14, 8))
        sns.heatmap(heatmap_data, cmap="YlGnBu", annot=True, fmt=".0f", ax=ax, cbar_kws={'label': 'Number of Punches'})
        ax.set_title("Attendance Heatmap - Punch-ins by Day and Hour")
        ax.set_xlabel("Hour of Day")
        ax.set_ylabel("Day of Week")
        plt.tight_layout()
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Error creating heatmap: {str(e)}")


def show_late_punch_trend(df):
    st.subheader("⏰ Late Arrival Trend Analysis")

    if df.empty or "late_mark" not in df.columns:
        st.info("No late arrival data available")
        return

    late_df = df[df["late_mark"] == True]

    if late_df.empty:
        st.success("✅ No late arrivals recorded in the selected period!")
        return

    # Trend by date
    if "date_only" in late_df.columns:
        late_trend = late_df.groupby("date_only").size()
        st.bar_chart(late_trend)

    # Department-wise late arrivals
    if "department" in late_df.columns:
        dept_late = late_df.groupby("department").size().sort_values(ascending=False)
        st.subheader("Late Arrivals by Department")
        st.bar_chart(dept_late)


def show_insights_summary(df):
    st.subheader("🧾 Attendance Analytics Summary")

    if df.empty:
        st.info("📭 No attendance data available for insights.")
        return

    if "weekday" not in df.columns or "hour" not in df.columns:
        st.info("📭 No detailed punch data available for insights.")
        return

    punch_counts = df.groupby(["weekday", "hour"]).size().reset_index(name="count")

    if punch_counts.empty:
        st.info("📭 No detailed punch data available.")
        return

    # Find peak and quiet times
    busiest = punch_counts.loc[punch_counts["count"].idxmax()]
    quietest = punch_counts.loc[punch_counts["count"].idxmin()]

    # Activity analysis
    morning_shift = df[(df["hour"] >= 8) & (df["hour"] <= 10)].shape[0] if "hour" in df.columns else 0
    evening_activity = df[df["hour"] >= 18].shape[0] if "hour" in df.columns else 0

    # Display summary
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        **📊 Peak Activity:**
        - {busiest['count']} punches on {busiest['weekday']} at {busiest['hour']}:00

        **📉 Quietest Period:**
        - {quietest['count']} punches on {quietest['weekday']} at {quietest['hour']}:00
        """)

    with col2:
        st.markdown(f"""
        **🌅 Morning Activity (8-10 AM):**
        - {morning_shift} total punches

        **🌆 Evening Presence (After 6 PM):**
        - {evening_activity} total punches
        """)


def export_attendance_summary(df, dept):
    st.subheader("📤 Export Attendance Data")

    if df.empty:
        st.info("No data available for export")
        return

    # Prepare export data
    export_df = df.copy()

    # Add summary statistics - only use columns that exist
    summary_stats = {
        'Total Records': len(export_df),
        'Date Range': f"{export_df['date_only'].min()} to {export_df['date_only'].max()}" if 'date_only' in export_df.columns else "N/A",
        'Department': dept
    }

    if 'employee_id' in export_df.columns:
        summary_stats['Unique Employees'] = export_df['employee_id'].nunique()

    col1, col2 = st.columns(2)

    with col1:
        filename = f"{dept.lower().replace(' ', '_')}_attendance_summary_{datetime.now().strftime('%Y%m%d')}.csv"
        st.download_button(
            label="📥 Download Detailed CSV",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name=filename,
            mime="text/csv",
            key="attendance_download"
        )

    with col2:
        # Export summary only
        summary_filename = f"{dept.lower().replace(' ', '_')}_summary_{datetime.now().strftime('%Y%m%d')}.txt"
        summary_text = "\n".join([f"{k}: {v}" for k, v in summary_stats.items()])
        st.download_button(
            label="📊 Download Summary",
            data=summary_text,
            file_name=summary_filename,
            mime="text/plain",
            key="summary_download"
        )


# -------------------------------
# 🚦 Enhanced Exit Management
# -------------------------------

def show_clearance_bottlenecks(resign_df, key_suffix=""):
    st.subheader("🚦 Clearance Bottleneck Analysis")

    if resign_df.empty:
        st.info("No resignation data available")
        return

    # Find stuck clearances
    stuck_df = resign_df[
        (resign_df["status"].str.lower() == "pending") &
        (resign_df["admin_cleared"].isnull())
        ] if "status" in resign_df.columns and "admin_cleared" in resign_df.columns else pd.DataFrame()

    if stuck_df.empty:
        st.success("✅ No clearance delays detected!")
        return

    # Calculate metrics
    stuck_df = stuck_df.copy()
    if "notice_issued_date" in stuck_df.columns:
        stuck_df["days_since_notice"] = (pd.Timestamp.today() - stuck_df["notice_issued_date"]).dt.days

    # Display metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🔴 Pending Clearances", len(stuck_df))

    with col2:
        if "days_since_notice" in stuck_df.columns:
            avg_delay = stuck_df["days_since_notice"].mean()
            st.metric("⏳ Avg Days Pending", f"{avg_delay:.1f}")
        else:
            st.metric("⏳ Avg Days Pending", "N/A")

    with col3:
        if "days_since_notice" in stuck_df.columns:
            max_delay = stuck_df["days_since_notice"].max()
            st.metric("🚨 Longest Delay", f"{max_delay} days")
        else:
            st.metric("🚨 Longest Delay", "N/A")

    # Show detailed table
    st.subheader("Detailed Bottleneck Report")
    display_columns = ["employee_name", "department", "notice_issued_date", "days_since_notice", "reason"]
    available_columns = [col for col in display_columns if col in stuck_df.columns]

    if available_columns:
        st.dataframe(stuck_df[available_columns].sort_values("days_since_notice", ascending=False)
                     if "days_since_notice" in available_columns else stuck_df[available_columns])
    else:
        st.dataframe(stuck_df)


def export_clearance_report(df, key):
    st.subheader("📤 Export Clearance Report")

    if df.empty:
        st.info("No resignation data available for export")
        return

    # Prepare bottlenecks data
    stuck = df[
        (df["status"].str.lower() == "pending") &
        (df["admin_cleared"].isnull())
        ] if "status" in df.columns and "admin_cleared" in df.columns else pd.DataFrame()

    if stuck.empty:
        st.success("✅ No bottlenecks to export - all clearances are on track!")
        return

    filename = f"clearance_bottlenecks_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

    st.download_button(
        label="📥 Download Bottlenecks Report",
        data=stuck.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        key=key
    )

    st.info(f"Report includes {len(stuck)} pending clearances")


# -------------------------------
# 🧠 Enhanced Behavioral Analytics
# -------------------------------

def show_punch_consistency(df):
    st.subheader("📏 Employee Attendance Consistency")

    if df.empty or "employee_id" not in df.columns or "date_only" not in df.columns:
        st.info("No data available for consistency analysis - missing employee_id or date_only columns")
        return

    # Calculate consistency scores
    employee_punch_days = df.groupby("employee_id")["date_only"].nunique()
    total_days = df["date_only"].nunique()

    if total_days == 0:
        st.info("No valid dates found for consistency calculation")
        return

    consistency_df = pd.DataFrame({
        'employee_id': employee_punch_days.index,
        'days_present': employee_punch_days.values,
        'total_days': total_days,
        'consistency_score': (employee_punch_days.values / total_days * 100).round(1)
    })

    # Merge with employee names if available
    if "employee_name" in df.columns:
        name_mapping = df.groupby("employee_id")["employee_name"].first()
        consistency_df["employee_name"] = consistency_df["employee_id"].map(name_mapping)

    # Show top and bottom performers
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏆 Most Consistent")
        top_5 = consistency_df.nlargest(5, 'consistency_score')
        display_cols = ['employee_id', 'consistency_score']
        if 'employee_name' in consistency_df.columns:
            display_cols = ['employee_id', 'employee_name', 'consistency_score']
        st.dataframe(top_5[display_cols].fillna('N/A'))

    with col2:
        st.subheader("⚠️ Needs Attention")
        bottom_5 = consistency_df.nsmallest(5, 'consistency_score')
        display_cols = ['employee_id', 'consistency_score']
        if 'employee_name' in consistency_df.columns:
            display_cols = ['employee_id', 'employee_name', 'consistency_score']
        st.dataframe(bottom_5[display_cols].fillna('N/A'))


def show_weekend_activity(df):
    st.subheader("🌤️ Weekend Work Pattern Analysis")

    if df.empty or "weekday" not in df.columns:
        st.info("No weekday data available for weekend analysis")
        return

    weekends = df[df["weekday"].isin(["Saturday", "Sunday"])]

    if weekends.empty:
        st.info("📅 No weekend activity recorded")
        return

    col1, col2 = st.columns(2)

    with col1:
        weekend_summary = weekends["weekday"].value_counts()
        st.bar_chart(weekend_summary)
        st.metric("Total Weekend Punches", len(weekends))

    with col2:
        # Department-wise weekend activity - only if department column exists
        if "department" in weekends.columns:
            dept_weekend = weekends.groupby("department").size().sort_values(ascending=False)
            st.subheader("Weekend Activity by Department")
            st.bar_chart(dept_weekend)
        else:
            st.info("Department data not available for weekend analysis")


def show_department_summary(df):
    st.subheader("🏢 Department-wise Activity Overview")

    if df.empty or "department" not in df.columns:
        st.info("No department data available - department column not found in the dataset")
        return

    # Basic department stats - only use columns that exist
    agg_dict = {
        "employee_id": "nunique",
        "date_only": "nunique" if "date_only" in df.columns else lambda x: 0
    }

    # Add late_mark aggregation only if column exists
    if "late_mark" in df.columns:
        agg_dict["late_mark"] = lambda x: x.sum() if x.dtype == bool else 0

    # Add extra_hours aggregation only if column exists (changed from overtime_hours)
    if "extra_hours" in df.columns:
        agg_dict["extra_hours"] = lambda x: x.sum() if pd.api.types.is_numeric_dtype(x) else 0

    dept_summary = df.groupby("department").agg(agg_dict)

    # Rename columns
    column_names = {
        "employee_id": "unique_employees",
        "date_only": "active_days"
    }

    if "late_mark" in agg_dict:
        column_names["late_mark"] = "late_arrivals"

    if "extra_hours" in agg_dict:
        column_names["extra_hours"] = "total_extra_hours"

    dept_summary = dept_summary.rename(columns=column_names)

    st.dataframe(dept_summary)

    # Visual representation
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Employee Count by Department")
        st.bar_chart(dept_summary["unique_employees"])

    with col2:
        st.subheader("Late Arrivals by Department")
        if "late_arrivals" in dept_summary.columns and dept_summary["late_arrivals"].sum() > 0:
            st.bar_chart(dept_summary["late_arrivals"])
        else:
            st.info("No late arrivals recorded or late arrival data not available")


def show_hr_alerts(df):
    st.subheader("⚠️ HR Alert System")

    if df.empty:
        st.info("No data available for HR alerts")
        return

    alerts = []

    # Check for departments with no recent activity - only if department column exists
    if "department" in df.columns and "date_only" in df.columns:
        yesterday = pd.Timestamp.today().date() - timedelta(days=1)
        recent_activity = df[df["date_only"] >= yesterday - timedelta(days=2)]

        if not recent_activity.empty:
            active_depts = recent_activity["department"].dropna().unique()
            all_depts = df["department"].dropna().unique()
            missing_depts = [d for d in all_depts if d not in active_depts]

            if missing_depts:
                alerts.append(f"🛑 No recent activity from: {', '.join(missing_depts)}")

    # Check for inactive employees
    if "employee_id" in df.columns and "date_only" in df.columns:
        last_punch = df.groupby("employee_id")["date_only"].max()
        cutoff = pd.Timestamp.today().date() - timedelta(days=7)
        inactive_employees = last_punch[last_punch < cutoff]

        if not inactive_employees.empty:
            alerts.append(f"⏳ {len(inactive_employees)} employees inactive for 7+ days")

    # Check for excessive late arrivals - only if late_mark column exists
    if "late_mark" in df.columns and "date_only" in df.columns:
        recent_week = df[df["date_only"] >= pd.Timestamp.today().date() - timedelta(days=7)]
        if not recent_week.empty:
            late_count = recent_week[recent_week["late_mark"] == True].shape[0]
            total_punches = len(recent_week)

            if total_punches > 0 and (late_count / total_punches) > 0.2:
                alerts.append(
                    f"🚨 High late arrival rate: {late_count}/{total_punches} ({late_count / total_punches * 100:.1f}%)")

    # Display alerts
    if alerts:
        for alert in alerts:
            st.error(alert)
    else:
        st.success("✅ All HR metrics are within normal parameters")


# -------------------------------
# 📝 Enhanced Feedback System
# -------------------------------

def log_feedback(category, department, message, sender="Anonymous", path="data/feedback_raw.csv"):
    """Enhanced feedback logging with SQL/CSV support - maintains your original two-file system"""
    if len(message.strip()) < 5:
        st.warning("⚠️ Feedback message is too short. Please provide more details.")
        return False

    try:
        new_entry = {
            "timestamp": datetime.now(),
            "category": category,
            "department": department,
            "sender": sender,
            "message": message.strip(),
            "status": "Pending"
        }

        if USE_SQL:
            conn = safe_get_conn()
            if conn is None:
                st.error("Failed to connect to database for feedback logging")
                return False

            # Check what columns actually exist in the table
            existing_columns = get_table_columns(conn, FEEDBACK_RAW_TABLE)

            if not existing_columns:
                # Table doesn't exist, create it with all columns
                create_query = f"""
                CREATE TABLE {FEEDBACK_RAW_TABLE} (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    timestamp DATETIME NOT NULL,
                    category NVARCHAR(100),
                    department NVARCHAR(100),
                    sender NVARCHAR(100),
                    message NVARCHAR(MAX),
                    status NVARCHAR(50) DEFAULT 'Pending',
                    created_date DATETIME DEFAULT GETDATE()
                )
                """
                conn.execute(create_query)
                conn.commit()
                existing_columns = ["timestamp", "category", "department", "sender", "message", "status"]

            # Build insert query with only existing columns
            insert_columns = []
            insert_values = []
            insert_placeholders = []

            column_mapping = {
                "timestamp": safe_datetime_for_sql(new_entry["timestamp"]),
                "category": new_entry["category"],
                "department": new_entry["department"],
                "sender": new_entry["sender"],
                "message": new_entry["message"],
                "status": new_entry["status"]
            }

            for col, value in column_mapping.items():
                if col in existing_columns:
                    insert_columns.append(col)
                    insert_values.append(value)
                    insert_placeholders.append("?")

            if insert_columns:
                insert_query = f"""
                    INSERT INTO {FEEDBACK_RAW_TABLE} 
                    ({', '.join(insert_columns)})
                    VALUES ({', '.join(insert_placeholders)})
                """

                conn.execute(insert_query, insert_values)
                conn.commit()
                st.success(f"Feedback logged with available columns: {', '.join(insert_columns)}")
            else:
                st.error("No compatible columns found in feedback table")
                conn.close()
                return False

            conn.close()

        else:
            # CSV fallback - Using your original two-file approach
            df_entry = pd.DataFrame([{
                **new_entry,
                "timestamp": new_entry["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            }])

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)

            if os.path.exists(path):
                try:
                    df_existing = pd.read_csv(path)
                    df_updated = pd.concat([df_existing, df_entry], ignore_index=True)
                except pd.errors.ParserError:
                    df_updated = df_entry
            else:
                df_updated = df_entry

            df_updated.to_csv(path, index=False)

        return True

    except Exception as e:
        st.error(f"Failed to log feedback: {str(e)}")
        return False


def sync_feedback_entries(raw_path="data/feedback_raw.csv", reviewed_path="data/feedback_reviewed.csv"):
    """Enhanced version of your original sync function with SQL support"""
    try:
        if USE_SQL:
            # For SQL, we don't need separate files - status field handles this
            return

        # CSV mode - preserve your original two-file sync logic
        if not os.path.exists(raw_path):
            return  # Nothing to sync

        try:
            raw_df = pd.read_csv(raw_path)
        except pd.errors.ParserError:
            return  # Invalid raw file format

        # Load reviewed feedback or create a new one
        if os.path.exists(reviewed_path):
            try:
                reviewed_df = pd.read_csv(reviewed_path)
            except pd.errors.ParserError:
                reviewed_df = pd.DataFrame(columns=raw_df.columns)
        else:
            reviewed_df = pd.DataFrame(columns=raw_df.columns)

        # Find new entries that aren't yet reviewed
        if not reviewed_df.empty and "timestamp" in reviewed_df.columns:
            new_entries = raw_df[~raw_df["timestamp"].isin(reviewed_df["timestamp"])]
        else:
            new_entries = raw_df

        if not new_entries.empty:
            merged_df = pd.concat([reviewed_df, new_entries], ignore_index=True)
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(reviewed_path), exist_ok=True)
            merged_df.to_csv(reviewed_path, index=False)

    except Exception as e:
        st.error(f"Error syncing feedback: {str(e)}")


def load_feedback_data():
    """Load feedback data from SQL or CSV - maintains your original two-file logic"""
    try:
        if USE_SQL:
            conn = safe_get_conn()
            if conn is None:
                return pd.DataFrame()

            if not table_exists(conn, FEEDBACK_REVIEWED_TABLE):
                conn.close()
                return pd.DataFrame()

            # Use the safe query approach like other functions
            desired_cols = ["timestamp", "category", "department", "sender", "message", "status"]
            query, available_cols = build_safe_query(FEEDBACK_REVIEWED_TABLE, desired_cols, conn)

            if not query:
                st.warning("Could not build valid query for feedback table.")
                conn.close()
                return pd.DataFrame()

            # Add ORDER BY if timestamp exists
            if "timestamp" in available_cols:
                query += " ORDER BY timestamp DESC"

            st.info(f"Loading feedback data with columns: {', '.join(available_cols)}")

            df = pd.read_sql(query, conn)
            conn.close()

            # Convert timestamp column if it exists
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

            return df

        else:
            # CSV mode - use your original reviewed file approach
            reviewed_path = "data/feedback_reviewed.csv"

            if not os.path.exists(reviewed_path):
                # Try to sync first
                sync_feedback_entries()

            if os.path.exists(reviewed_path):
                try:
                    df = pd.read_csv(reviewed_path)
                    return df
                except pd.errors.ParserError:
                    return pd.DataFrame()

            return pd.DataFrame()

    except Exception as e:
        st.error(f"Error loading feedback data: {str(e)}")
        return pd.DataFrame()


def update_feedback_status(feedback_df, row_index, new_status, reviewed_path="data/feedback_reviewed.csv"):
    """Update feedback status - handles both SQL and CSV"""
    try:
        if USE_SQL:
            conn = safe_get_conn()
            if conn is None:
                return False

            # Get the timestamp to identify the record
            timestamp = feedback_df.iloc[row_index]["timestamp"]

            # Check if status column exists
            existing_columns = get_table_columns(conn, FEEDBACK_REVIEWED_TABLE)

            if "status" in existing_columns:
                update_query = f"""
                    UPDATE {FEEDBACK_REVIEWED_TABLE} 
                    SET status = ?
                    WHERE timestamp = ?
                """
                conn.execute(update_query, (new_status, timestamp))
            else:
                st.warning("Status column not found in feedback table - update skipped")
                conn.close()
                return False

            conn.commit()
            conn.close()
            return True

        else:
            # CSV mode - update the reviewed file
            if "status" in feedback_df.columns:
                feedback_df.iloc[row_index, feedback_df.columns.get_loc("status")] = new_status

                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(reviewed_path), exist_ok=True)
                feedback_df.to_csv(reviewed_path, index=False)
                return True
            else:
                st.warning("Status column not found in feedback data")
                return False

    except Exception as e:
        st.error(f"Error updating feedback status: {str(e)}")
        return False

# -------------------------------
# 🏠 Main Application
# -------------------------------

def run_analytics():
    # Set page configuration
    st.set_page_config(
        page_title="Validex HR Analytics",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Check authentication
    if "login_phase" not in st.session_state or st.session_state.login_phase != "verified":
        st.warning("⚠️ Please log in to access the analytics dashboard.")
        st.stop()

    # Sidebar configuration
    st.sidebar.markdown("## 🔍 **Validex HR Dashboard**")
    st.sidebar.caption("Advanced HR Analytics Platform")
    st.sidebar.markdown("---")

    # Display current data source
    data_source = "🗄️ SQL Server" if USE_SQL else "📁 CSV Files"
    st.sidebar.info(f"**Data Source:** {data_source}")

    # About section
    with st.sidebar.expander("ℹ️ About Validex"):
        st.markdown("""
        **Validex HR Analytics Platform**

        🎯 **Features:**
        - Real-time attendance monitoring
        - Behavioral pattern analysis  
        - Exit process management
        - Predictive HR insights
        - Multi-format data export

        🏢 **Built by:** Shri Swami Samarth Pvt Ltd  
        👨‍💻 **Developer:** Padmaja
        """)

    # Load data with error handling
    with st.spinner("Loading data..."):
        df = load_attendance_data()
        resign_df = load_resignation_data()
        salary_df = load_salary_data()

    # Debug mode toggle
    if st.sidebar.checkbox("🛠️ Debug Mode"):
        st.sidebar.subheader("Data Status")
        st.sidebar.write(f"Attendance records: {len(df)}")
        st.sidebar.write(f"Resignation records: {len(resign_df)}")
        st.sidebar.write(f"Salary records: {len(salary_df)}")

        if not df.empty:
            st.sidebar.write("Attendance columns:", df.columns.tolist())

        if st.sidebar.button("Show Sample Data"):
            st.subheader("🔍 Sample Data Preview")

            col1, col2 = st.columns(2)
            with col1:
                st.write("**Attendance Data Sample:**")
                st.dataframe(df.head(3) if not df.empty else pd.DataFrame({"Status": ["No data"]}))

            with col2:
                st.write("**Resignation Data Sample:**")
                st.dataframe(resign_df.head(3) if not resign_df.empty else pd.DataFrame({"Status": ["No data"]}))

    # Main content area
    st.title("📊 Validex HR Analytics Dashboard")
    st.markdown("### Comprehensive workforce insights and analytics")

    if df.empty:
        st.error("❌ No attendance data available. Please check your data source configuration.")
        st.stop()

    # Date range filter
    st.markdown("---")
    st.subheader("📅 Data Filters")

    col1, col2 = st.columns(2)

    with col1:
        # Date range selection
        df_dates = df.dropna(subset=["date_only"]) if "date_only" in df.columns else pd.DataFrame()
        if not df_dates.empty:
            min_date = df_dates["date_only"].min()
            max_date = df_dates["date_only"].max()

            date_range = st.date_input(
                "Select Date Range:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="date_filter"
            )

            if len(date_range) == 2:
                start_date, end_date = date_range
                if start_date <= end_date:
                    df = df[(df["date_only"] >= start_date) & (df["date_only"] <= end_date)]
                else:
                    st.warning("⚠️ Start date must be before or equal to end date")
        else:
            st.warning("⚠️ No valid dates found in attendance data")

    with col2:
        # Department filter
        if "department" in df.columns:
            departments = ["All Departments"] + sorted(df["department"].dropna().unique().tolist())
        else:
            departments = ["All Departments"]

        selected_dept = st.selectbox(
            "📁 Filter by Department:",
            options=departments,
            key="dept_filter"
        )

        if selected_dept != "All Departments" and "department" in df.columns:
            filtered_df = df[df["department"] == selected_dept].copy()
            filtered_resign_df = resign_df[resign_df[
                                               "department"] == selected_dept].copy() if not resign_df.empty and "department" in resign_df.columns else pd.DataFrame()
        else:
            filtered_df = df.copy()
            filtered_resign_df = resign_df.copy()

    # Display current filter status
    date_range_info = len(filtered_df['date_only'].dropna().unique()) if 'date_only' in filtered_df.columns else 0
    st.info(
        f"📊 Showing data for **{selected_dept}** | Records: {len(filtered_df)} | Date range: {date_range_info} days")

    # Main dashboard tabs
    st.markdown("---")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Attendance Analytics",
        "🚦 Exit Management",
        "🧠 Behavioral Insights",
        "💰 Compensation Analysis",
        "📝 Feedback Center"
    ])

    # Tab 1: Attendance Analytics
    with tab1:
        st.header("📊 Attendance Analytics Dashboard")

        # Executive summary
        show_cxo_summary(filtered_df, filtered_resign_df)

        st.markdown("---")

        # KPIs section
        show_kpis(filtered_df)

        st.markdown("---")

        # Visual analytics
        col1, col2 = st.columns([2, 1])

        with col1:
            show_attendance_heatmap(filtered_df)

        with col2:
            show_late_punch_trend(filtered_df)

        st.markdown("---")

        # Detailed insights
        show_insights_summary(filtered_df)

        st.markdown("---")

        # Export functionality
        export_attendance_summary(filtered_df, selected_dept)

        # Feedback section
        st.markdown("---")
        st.subheader("💬 Feedback on Attendance Analytics")
        feedback_attendance = st.text_area(
            "Share your thoughts on attendance analytics:",
            placeholder="Enter your feedback, suggestions, or questions about the attendance data...",
            key="feedback_attendance"
        )

        if st.button("Submit Attendance Feedback", key="submit_attendance"):
            if feedback_attendance.strip():
                if log_feedback("Attendance", selected_dept, feedback_attendance):
                    st.success("✅ Thank you! Your feedback has been recorded.")
                    st.rerun()
            else:
                st.warning("Please enter some feedback before submitting.")

    # Tab 2: Exit Management
    with tab2:
        st.header("🚦 Employee Exit Management")

        if filtered_resign_df.empty:
            st.info("📭 No resignation data available for the selected filters.")
        else:
            # Clearance bottlenecks
            show_clearance_bottlenecks(filtered_resign_df, key_suffix=f"dept_{selected_dept.lower().replace(' ', '_')}")

            st.markdown("---")

            # Additional exit analytics
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📈 Resignation Trends")
                if "notice_issued_date" in filtered_resign_df.columns:
                    monthly_resignations = filtered_resign_df.groupby(
                        filtered_resign_df["notice_issued_date"].dt.to_period("M")
                    ).size()

                    if not monthly_resignations.empty:
                        st.bar_chart(monthly_resignations)
                    else:
                        st.info("No trend data available")
                else:
                    st.info("Date information not available")

            with col2:
                st.subheader("📋 Resignation Reasons")
                if "reason" in filtered_resign_df.columns:
                    reason_counts = filtered_resign_df["reason"].value_counts()
                    if not reason_counts.empty:
                        st.bar_chart(reason_counts)
                    else:
                        st.info("No reason data available")
                else:
                    st.info("Reason information not available")

            st.markdown("---")

            # Export functionality
            export_clearance_report(filtered_resign_df,
                                    key=f"clearance_export_{selected_dept.lower().replace(' ', '_')}")

        # Feedback section
        st.markdown("---")
        st.subheader("💬 Feedback on Exit Management")
        feedback_exit = st.text_area(
            "Share your thoughts on exit management processes:",
            placeholder="Enter feedback about resignation processes, clearance bottlenecks, or suggestions for improvement...",
            key="feedback_exit"
        )

        if st.button("Submit Exit Management Feedback", key="submit_exit"):
            if feedback_exit.strip():
                if log_feedback("Exit Management", selected_dept, feedback_exit):
                    st.success("✅ Thank you! Your feedback has been recorded.")
                    st.rerun()
            else:
                st.warning("Please enter some feedback before submitting.")

    # Tab 3: Behavioral Insights
    with tab3:
        st.header("🧠 Employee Behavioral Analytics")

        # Consistency analysis
        show_punch_consistency(filtered_df)

        st.markdown("---")

        # Weekend activity
        show_weekend_activity(filtered_df)

        st.markdown("---")

        # Department overview
        show_department_summary(filtered_df)

        st.markdown("---")

        # Advanced behavioral analytics
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🔮 Late Arrival Predictions")
            if not filtered_df.empty and "late_mark" in filtered_df.columns and "weekday" in filtered_df.columns:
                late_by_day = filtered_df[filtered_df["late_mark"] == True].groupby("weekday").size()
                if not late_by_day.empty:
                    st.bar_chart(late_by_day)
                    most_likely_day = late_by_day.idxmax()
                    st.metric("Highest Risk Day", most_likely_day)
                else:
                    st.success("✅ No late arrival patterns detected")
            else:
                st.info("Late arrival data not available")

        with col2:
            st.subheader("👤 Attendance Personalities")
            if not filtered_df.empty and "hour" in filtered_df.columns and "employee_id" in filtered_df.columns:
                profile_df = filtered_df.dropna(subset=["hour"]).groupby("employee_id")["hour"].agg(
                    ['mean', 'std']).reset_index()
                profile_df.columns = ["employee_id", "avg_hour", "consistency"]
                profile_df = profile_df.head(10)  # Top 10

                if not profile_df.empty:
                    st.dataframe(profile_df.round(2))
                else:
                    st.info("Not enough data for personality analysis")
            else:
                st.info("Time data not available for personality analysis")

        st.markdown("---")

        # HR alerts
        show_hr_alerts(filtered_df)

        # Feedback section
        st.markdown("---")
        st.subheader("💬 Feedback on Behavioral Analytics")
        feedback_behavior = st.text_area(
            "Share insights about behavioral patterns:",
            placeholder="Comments on employee behavior patterns, suggestions for improvement, or questions about the analysis...",
            key="feedback_behavior"
        )

        if st.button("Submit Behavioral Feedback", key="submit_behavior"):
            if feedback_behavior.strip():
                if log_feedback("Behavioral Analytics", selected_dept, feedback_behavior):
                    st.success("✅ Thank you! Your feedback has been recorded.")
                    st.rerun()
            else:
                st.warning("Please enter some feedback before submitting.")

    # Tab 4: Compensation Analysis
    with tab4:
        st.header("💰 Compensation Analysis")

        if salary_df.empty:
            st.info("📭 No salary data available. Enable salary tracking to view compensation analytics.")
        else:
            # Filter salary data by department if needed
            if selected_dept != "All Departments" and "department" in salary_df.columns:
                dept_salary_df = salary_df[salary_df["department"] == selected_dept]
            else:
                dept_salary_df = salary_df

            if not dept_salary_df.empty:
                col1, col2, col3 = st.columns(3)

                with col1:
                    avg_salary = dept_salary_df["base_salary"].mean() if "base_salary" in dept_salary_df.columns else 0
                    st.metric("💵 Average Base Salary", f"₹{avg_salary:,.0f}")

                with col2:
                    total_overtime = dept_salary_df[
                        "overtime_pay"].sum() if "overtime_pay" in dept_salary_df.columns else 0
                    st.metric("⏰ Total Overtime Pay", f"₹{total_overtime:,.0f}")

                with col3:
                    total_deductions = dept_salary_df[
                        "deductions"].sum() if "deductions" in dept_salary_df.columns else 0
                    st.metric("📉 Total Deductions", f"₹{total_deductions:,.0f}")

                st.markdown("---")

                # Salary distribution
                if "base_salary" in dept_salary_df.columns:
                    st.subheader("📊 Salary Distribution")
                    fig, ax = plt.subplots(figsize=(10, 6))
                    dept_salary_df["base_salary"].hist(bins=20, ax=ax, color='skyblue', alpha=0.7)
                    ax.set_xlabel("Base Salary (₹)")
                    ax.set_ylabel("Number of Employees")
                    ax.set_title("Salary Distribution")
                    st.pyplot(fig)
            else:
                st.info(f"No salary data available for {selected_dept}")

        # Feedback section
        st.markdown("---")
        st.subheader("💬 Feedback on Compensation Analysis")
        feedback_compensation = st.text_area(
            "Share thoughts on compensation analysis:",
            placeholder="Comments about salary trends, overtime patterns, or compensation-related insights...",
            key="feedback_compensation"
        )

        if st.button("Submit Compensation Feedback", key="submit_compensation"):
            if feedback_compensation.strip():
                if log_feedback("Compensation", selected_dept, feedback_compensation):
                    st.success("✅ Thank you! Your feedback has been recorded.")
                    st.rerun()
            else:
                st.warning("Please enter some feedback before submitting.")

    # Tab 5: Feedback Center
    with tab5:
        st.header("📝 Feedback Management Center")

        # Sync feedback entries (preserves your original logic for CSV mode)
        sync_feedback_entries("data/feedback_raw.csv", "data/feedback_reviewed.csv")

        # Load existing feedback
        feedback_df = load_feedback_data()

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("📋 Review Dashboard Feedback")

            if feedback_df.empty:
                st.info("No feedback entries found. Submit feedback from other tabs to see them here.")
            else:
                # Filter options - preserving your original filtering logic
                expected_cols = ["timestamp", "category", "department", "sender", "message", "status"]

                # Ensure all expected columns exist
                for col in expected_cols:
                    if col not in feedback_df.columns:
                        feedback_df[col] = ""

                # Category and status filters
                filter_col1, filter_col2 = st.columns(2)

                with filter_col1:
                    categories = feedback_df['category'].dropna().unique().tolist()
                    if categories:
                        selected_category = st.selectbox("Filter by Tab", options=categories, key="feedback_tab_filter")
                    else:
                        selected_category = None
                        st.info("No categories available for filtering")

                with filter_col2:
                    departments = feedback_df['department'].dropna().unique().tolist()
                    if departments:
                        selected_dept_feedback = st.selectbox("Filter by Department", options=departments,
                                                              key="feedback_dept_filter")
                    else:
                        selected_dept_feedback = None
                        st.info("No departments available for filtering")

                # Apply filters - preserving your original logic
                if selected_category and selected_dept_feedback:
                    filtered_feedback = feedback_df[
                        (feedback_df['category'] == selected_category) &
                        (feedback_df['department'] == selected_dept_feedback) &
                        (feedback_df['status'].str.lower() == "pending")
                        ]
                else:
                    filtered_feedback = feedback_df[feedback_df['status'].str.lower() == "pending"]

                st.subheader("📄 Filtered Feedback")

                if not filtered_feedback.empty:
                    # Display recent feedback
                    st.dataframe(filtered_feedback.tail(10))

                    # Update status functionality - preserving your original approach
                    st.markdown("---")
                    st.subheader("✏️ Update Feedback Status")

                    option_labels = [
                        f"{row['timestamp']} | {row['message'][:30]}..."
                        for _, row in filtered_feedback.iterrows()
                    ]

                    if option_labels:
                        selected_idx = st.selectbox(
                            "Select entry to update:",
                            options=range(len(option_labels)),
                            format_func=lambda i: option_labels[i],
                            key="feedback_update_selector"
                        )

                        # Get the actual index from the original DataFrame
                        row_idx = filtered_feedback.index[selected_idx]
                        row_data = filtered_feedback.loc[row_idx]

                        st.write("🔎 Current Feedback Entry:")
                        st.write(row_data[['category', 'department', 'message', 'status']])

                        new_action = st.text_input("🛠️ Update Status:", value=row_data['status'],
                                                   key="status_update_input")

                        if st.button("✅ Save Update", key="save_feedback_update"):
                            # Find the position in the original dataframe
                            original_row_idx = feedback_df.index[feedback_df['timestamp'] == row_data['timestamp']][0]

                            if update_feedback_status(feedback_df, original_row_idx, new_action):
                                st.success("✅ Feedback status updated successfully!")
                                st.toast("✅ Feedback marked as resolved and saved.")
                                # Force refresh of the page
                                st.rerun()
                            else:
                                st.error("❌ Failed to update feedback status.")
                    else:
                        st.info("No pending feedback entries found for update.")
                else:
                    st.info("No matching feedback entries found for the selected filters.")

        with col2:
            st.subheader("📊 Feedback Statistics")

            if not feedback_df.empty:
                # Category distribution
                st.subheader("By Category")
                category_counts = feedback_df["category"].value_counts()
                st.bar_chart(category_counts)

                # Status distribution
                st.subheader("Status Overview")
                status_counts = feedback_df["status"].value_counts()
                for status, count in status_counts.items():
                    st.metric(status, count)

                # Department distribution
                st.subheader("By Department")
                dept_counts = feedback_df["department"].value_counts()
                st.bar_chart(dept_counts)
            else:
                st.info("No statistics available yet.")

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 20px;'>
            <p><strong>Validex HR Analytics Platform</strong></p>
            <p>🏢 Shri Swami Samarth Pvt Ltd | 👨‍💻 Built by Padmaja</p>
            <p>Data Source: {} | Last Updated: {}</p>
        </div>
        """.format(
            "SQL Server Database" if USE_SQL else "CSV Files",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ),
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    run_analytics()