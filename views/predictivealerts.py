import streamlit as st
import pandas as pd
from datetime import datetime
import config


def load_data():
    """Load data from either SQL or CSV based on config settings"""
    if config.USE_SQL:
        conn = config.safe_get_conn()
        if conn is None:
            st.error("Failed to connect to SQL Server")
            return None, None, None

        try:
            # Load from SQL tables
            salary_df = pd.read_sql(f"SELECT * FROM {config.SALARY_LOG_TABLE}", conn)
            employee_master = pd.read_sql(f"SELECT * FROM {config.EMPLOYEE_MASTER_TABLE}", conn)
            employee_data = pd.read_sql(f"SELECT * FROM {config.EMPLOYEE_DATA_TABLE}", conn)

        except Exception as e:
            st.error(f"Error loading data from SQL: {str(e)}")
            return None, None, None
        finally:
            conn.close()
    else:
        try:
            # Load from CSV files
            salary_df = pd.read_csv(config.SALARY_LOG_CSV)
            employee_master = pd.read_csv(config.EMPLOYEE_MASTER_CSV)
            employee_data = pd.read_csv(config.EMPLOYEE_DATA_CSV)
        except Exception as e:
            st.error(f"Error loading CSV files: {str(e)}")
            return None, None, None

    return salary_df, employee_master, employee_data


def run_predictivealerts():
    st.set_page_config(layout="wide")
    st.title("🔮 Predictive Alerts & HR Intelligence")

    # 📥 Load Data using config
    data_result = load_data()
    if data_result[0] is None:  # Check if data loading failed
        st.error("Unable to load data. Please check your configuration and data sources.")
        return

    salary_df, employee_master, employee_data = data_result

    # 📊 Data Processing
    # Handle datetime columns
    if 'salary_month' in salary_df.columns:
        salary_df["salary_month"] = pd.to_datetime(salary_df["salary_month"], errors="coerce")
        salary_df["month_str"] = salary_df["salary_month"].dt.strftime("%Y-%m")

    if 'start_datetime' in employee_data.columns:
        employee_data["start_datetime"] = pd.to_datetime(employee_data["start_datetime"], errors="coerce")
        employee_data = employee_data[employee_data["start_datetime"].notna()]  # filter bad rows
        employee_data["date_only"] = employee_data["start_datetime"].dt.date

    # Ensure employee_id is string for consistent joining
    salary_df["employee_id"] = salary_df["employee_id"].astype(str)
    employee_master["employee_id"] = employee_master["employee_id"].astype(str)

    # 📦 Merge department info into salary_df
    salary_df = salary_df.merge(
        employee_master[["employee_id", "department"]],
        on="employee_id",
        how="left"
    )

    # 🔍 Filters
    departments = sorted(employee_master["department"].dropna().unique())
    if not departments:
        st.error("No departments found in the data.")
        return

    selected_dept = st.selectbox("Select Department", departments)

    month_list = sorted(salary_df["month_str"].dropna().unique())
    if not month_list:
        st.error("No salary months found in the data.")
        return

    selected_month = st.selectbox("Select Month", month_list)

    # ✅ Filter by selected department - Get unique employees only
    team_df = salary_df[salary_df["department"] == selected_dept]

    # 🔍 Debug Information
    st.write("**Debug Information:**")
    st.write(f"Total records in salary_df: {len(salary_df)}")
    st.write(f"Records for {selected_dept} department: {len(team_df)}")

    if len(team_df) > 0:
        available_months = sorted(team_df["month_str"].dropna().unique())
        st.write(f"Available months for {selected_dept}: {available_months}")

        month_specific_data = team_df[team_df["month_str"] == selected_month]
        st.write(f"Records for {selected_dept} in {selected_month}: {len(month_specific_data)}")

        if len(month_specific_data) > 0:
            st.write(f"Employees in this data: {month_specific_data['employee_name'].unique().tolist()}")
    else:
        st.write(f"Available departments: {sorted(salary_df['department'].dropna().unique())}")

    # Get unique employees to avoid duplicates
    unique_employees = team_df[["employee_id", "employee_name"]].drop_duplicates()
    team_ids = unique_employees["employee_id"].tolist()
    team_names = unique_employees["employee_name"].tolist()

    # 🧠 Predictive Logic
    st.subheader(f"📈 Predictive Summary — {selected_dept} ({selected_month})")
    rows = []

    # ✅ Function to count working days in a given month excluding Tuesdays
    def count_working_days(month_date):
        if pd.isnull(month_date):
            return 0
        year = month_date.year
        month = month_date.month
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        all_days = pd.date_range(start=start, end=end - pd.Timedelta(days=1), freq="D")
        # Exclude Tuesdays (weekday=1)
        working_days = [d for d in all_days if d.weekday() != 1]
        return len(working_days)

    for emp_id, emp_name in zip(team_ids, team_names):
        # Get current month data
        current_row = salary_df[
            (salary_df["employee_id"] == emp_id) &
            (salary_df["month_str"] == selected_month)
            ]

        # Skip if no current month data
        if current_row.empty:
            continue

        # Get last 2 months of data for comparison
        last_2 = salary_df[salary_df["employee_id"] == emp_id].sort_values("salary_month", ascending=False).head(2)

        # Determine previous month data
        if len(last_2) >= 2:
            prev = last_2.iloc[1]
        elif len(last_2) == 1:
            prev = last_2.iloc[0]  # fallback to first row
        else:
            prev = None

        # Skip if prev is None
        if prev is None:
            continue

        cur = current_row.iloc[0]

        # 🧮 Calculate working days
        cur_working_days = count_working_days(cur.get("salary_month"))
        prev_working_days = count_working_days(prev.get("salary_month"))

        if cur_working_days == 0 or prev_working_days == 0:
            continue

        # 🧾 Actual LOP Days (Loss of Pay)
        actual_lop = cur_working_days - (
                cur.get("full_days", 0) +
                0.5 * cur.get("half_days", 0) +
                cur.get("leave_concession", 0)
        )

        # ✅ Calculate attendance percentage
        cur_att = (cur.get("full_days", 0) + 0.5 * cur.get("half_days", 0)) / cur_working_days
        prev_att = (prev.get("full_days", 0) + 0.5 * prev.get("half_days", 0)) / prev_working_days

        # 🚨 Risk Flags
        lop_risk = actual_lop > 2
        attendance_drop = (prev_att - cur_att) >= 0.10
        late_spike = cur.get("late_marks", 0) > prev.get("late_marks", 0)

        risk_flag = lop_risk or attendance_drop or late_spike

        # 🛑 Risk Reasons List
        risk_reason = []
        if lop_risk:
            risk_reason.append("High LOP")
        if attendance_drop:
            risk_reason.append("Attendance Drop")
        if late_spike:
            risk_reason.append("Late Spike")

        # 🌟 Bonus Eligibility
        bonus_flag = (
                cur.get("full_days", 0) >= 22 and
                cur.get("tuesday_bonus", 0) > 0 and
                cur.get("late_marks", 0) == 0 and
                cur.get("lop_days", 0) == 0
        )
        bonus_label = "🌟 Bonus Eligible" if bonus_flag else ""

        # 🧘 Burnout Signal - Convert extra_hours to numeric
        extra_hours = pd.to_numeric(cur.get("extra_hours", 0), errors='coerce')
        if pd.isna(extra_hours):
            extra_hours = 0

        no_leave = cur.get("leave_concession", 0) == 0 and prev.get("leave_concession", 0) == 0
        burnout_flag = extra_hours >= 10 and no_leave
        burnout_label = "🧘 Might Need Break" if burnout_flag else ""

        # 🌈 Final Status
        status = "🔥 Risk Alert" if risk_flag else bonus_label or burnout_label or "✅ Healthy"

        rows.append({
            "Employee": emp_name,
            "Full Days": cur.get("full_days", 0),
            "LOP": cur.get("lop_days", 0),
            "Late Marks": cur.get("late_marks", 0),
            "Tues Bonus": cur.get("tuesday_bonus", 0),
            "Extra Hours": extra_hours,
            "Risk Factors": ", ".join(risk_reason) if risk_flag else "-",
            "Status": status
        })

    # 📊 Display Table
    if rows:
        df_alerts = pd.DataFrame(rows)
        st.dataframe(df_alerts, use_container_width=True)

        # 📥 Export Button
        csv = df_alerts.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export Predictive Report",
            data=csv,
            file_name=f"{selected_dept}_{selected_month}_predictive_alerts.csv",
            mime="text/csv"
        )
    else:
        st.info("No employee data found for the selected department and month.")

    # 📊 Data Source Info
    data_source = "SQL Server" if config.USE_SQL else "CSV Files"
    st.caption(f"📊 Data loaded from: {data_source}")


if __name__ == "__main__":
    run_predictivealerts()