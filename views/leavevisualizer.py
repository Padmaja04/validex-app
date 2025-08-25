# leavevisualizer.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
from config import USE_SQL, safe_datetime_for_sql, get_sql_connection, EMPLOYEE_MASTER_TABLE, EMPLOYEE_DATA_TABLE, SALARY_LOG_TABLE

def run_leavevisualizer():
    st.set_page_config(layout="wide")
    st.title("🗖️ Leave & Attendance Visualizer")
    st.markdown("Explore attendance, Tuesday patterns, and leave concession trends.")

    # ---------------- Load Data ----------------
    if USE_SQL:
        conn = get_sql_connection()
        employee_master = pd.read_sql(f"SELECT * FROM {EMPLOYEE_MASTER_TABLE}", conn)
        employee_data = pd.read_sql(f"SELECT * FROM {EMPLOYEE_DATA_TABLE}", conn, parse_dates=["start_datetime", "exit_datetime", "date_only"])
        salary_df = pd.read_sql(f"SELECT * FROM {SALARY_LOG_TABLE}", conn, parse_dates=["data_date"])
    else:
        employee_master = pd.read_csv("data/employee_master.csv", dtype={"employee_id": str})
        employee_data = pd.read_csv("data/employee_data.csv", parse_dates=["start_datetime", "exit_datetime"])
        salary_df = pd.read_csv("data/salary_log.csv", parse_dates=["data_date"], dayfirst=False)

    # Normalize employee names
    employee_master["employee_name"] = employee_master["employee_name"].str.strip().str.lower()
    employee_data["employee_name"] = employee_data["employee_name"].str.strip().str.lower()
    employee_data["employee_id"] = employee_data["employee_id"].astype(str)

    # Prepare salary_df
    salary_df = salary_df[salary_df["data_date"].notna()]
    salary_df["data_date"] = pd.to_datetime(salary_df["data_date"], errors="coerce")
    salary_df["month_period"] = salary_df["data_date"].dt.to_period("M")

    # Clean employee_data
    employee_data["start_datetime"] = pd.to_datetime(employee_data["start_datetime"], errors="coerce")
    employee_data = employee_data[employee_data["start_datetime"].notna()]
    employee_data["date_only"] = pd.to_datetime(employee_data["date_only"], errors="coerce").dt.date

    # Load Holidays
    holidays_df = pd.read_csv("data/holidays.csv", delimiter=",", skipinitialspace=True)
    holidays_df["dates"] = pd.to_datetime(holidays_df["dates"].astype(str).str.strip().str.replace("\t", "", regex=True), errors="coerce", dayfirst=True)
    holidays_df = holidays_df[holidays_df["dates"].notna()]
    holiday_dates = holidays_df["dates"].dt.date.tolist()

    # ---------------- Employee & Month Selection ----------------
    departments = sorted(employee_master["department"].dropna().unique())
    selected_dept_matrix = st.selectbox("Department", departments, key="dept_select")
    emp_in_dept = employee_master[employee_master["department"] == selected_dept_matrix]
    emp_names = emp_in_dept["employee_name"].dropna().unique()
    selected_emp = st.selectbox("Select Employee", emp_names)

    months_available = pd.to_datetime(employee_data["date_only"]).dt.to_period("M").unique()
    selected_emp_month = st.selectbox("Select Month", sorted([str(m) for m in months_available]))
    emp_year, emp_month = map(int, selected_emp_month.split("-"))

    emp_row = emp_in_dept[emp_in_dept["employee_name"] == selected_emp]
    emp_id = str(emp_row["employee_id"].values[0]) if not pd.isna(emp_row["employee_id"].values[0]) else None

    # Filter employee attendance
    start_month = date(emp_year, emp_month, 1)
    end_month = date(emp_year, emp_month, calendar.monthrange(emp_year, emp_month)[1])

    if emp_id:
        filtered = employee_data[
            (employee_data["employee_name"] == selected_emp.lower()) &
            (employee_data["date_only"] >= start_month) &
            (employee_data["date_only"] <= end_month)
        ]
    else:
        filtered = employee_data[
            (employee_data["employee_name"].str.strip().str.lower() == selected_emp.strip().lower()) &
            (employee_data["date_only"] >= start_month) &
            (employee_data["date_only"] <= end_month)
        ]

    # ---------------- Monthly Calendar ----------------
    st.subheader(f"🗓️ Attendance for {selected_emp} — {calendar.month_name[emp_month]} {emp_year}")
    cal = calendar.monthcalendar(emp_year, emp_month)
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    header_cols = st.columns(7)
    for i in range(7):
        header_cols[i].markdown(f"**{day_names[i]}**")

    for week in cal:
        week_cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                week_cols[i].markdown(" ")
            else:
                d = date(emp_year, emp_month, day)
                mark = employee_data[
                    (employee_data["employee_name"] == selected_emp.strip().lower()) &
                    (employee_data["date_only"] == d)
                ]
                if not mark.empty:
                    status = mark["attendance_status"].values[0]
                    late = mark["late_mark"].values[0]
                    status = status.strip().lower() if isinstance(status, str) else ""
                    marker = ("H" if status == "half day" else
                              "L" if status == "full day" and late else
                              "F" if status == "full day" else
                              "L" if late else "A")
                else:
                    if d in holiday_dates:
                        holiday_name = holidays_df[holidays_df["dates"].dt.date == d]["holiday_name"].values
                        marker = f"🎉 {holiday_name[0][:8]}" if holiday_name.size > 0 else "-"
                    else:
                        marker = "A"
                week_cols[i].markdown(f"**{str(day).zfill(2)}** `{marker}`")

    st.caption("Legend: F=Full | H=Half | L=Late | A=Absent | -=Holiday/Tuesday")

    # ---------------- Monthly Summary ----------------
    filtered["attendance_status"] = filtered["attendance_status"].str.strip().str.lower()
    full_days = filtered[filtered["attendance_status"] == "full day"].shape[0]
    half_days = filtered[filtered["attendance_status"] == "half day"].shape[0]
    late_marks = filtered[filtered["late_mark"] == True].shape[0]

    # Count Tuesday absences
    tuesday_absences = 0
    all_tuesdays = [date(emp_year, emp_month, d) for d in range(1, calendar.monthrange(emp_year, emp_month)[1]+1) if date(emp_year, emp_month, d).weekday() == 1]
    present_dates = set(filtered["date_only"])
    for t in all_tuesdays:
        if t not in present_dates:
            tuesday_absences += 1

    st.subheader("📊 Monthly Summary")
    st.markdown(f"- **Full Days**: {full_days}")
    st.markdown(f"- **Half Days**: {half_days}")
    st.markdown(f"- **Late Marks**: {late_marks}")
    st.markdown(f"- **Tuesday Absences**: {tuesday_absences}")
    if tuesday_absences == 0 and full_days >= 22:
        st.success("🎖️ Eligible for Consistency + Tuesday Badge")

    # ---------------- Leave Adjustment Insights ----------------
    selected_month_period = pd.Period(selected_emp_month, freq="M")
    concession_row = salary_df[
        (salary_df["employee_id"] == emp_id) &
        (salary_df["month_period"] == selected_month_period)
    ]
    st.subheader("🛡️ Leave Adjustment Insights")
    if not concession_row.empty:
        st.markdown(f"- **Concession Granted**: {concession_row['leave_concession'].values[0]:.1f} days")
        st.markdown(f"- **Concession Amount**: ₹{concession_row['leave_concession_amount'].values[0]:,.2f}")
    else:
        st.info("No leave concession recorded for this employee in selected month.")

    # ---------------- Department Dashboard ----------------
    st.title("📆 Department Leave Dashboard")
    selected_dept = st.selectbox("Department", departments, key="dept_matrix")
    month_list = sorted(salary_df["data_date"].dropna().dt.strftime("%Y-%m").unique())
    selected_dept_month = st.selectbox("Month", month_list, key="month_matrix")
    dept_year, dept_month = map(int, selected_dept_month.split("-"))
    month_days = calendar.monthcalendar(dept_year, dept_month)

    team = employee_master[employee_master["department"] == selected_dept].dropna(subset=["employee_id", "employee_name"]).drop_duplicates(subset=["employee_id"])
    team["employee_id"] = team["employee_id"].astype(str)
    team["employee_name"] = team["employee_name"].str.strip()

    def get_marker(date_val, emp_id):
        rec = employee_data[(employee_data["employee_id"] == emp_id) & (employee_data["date_only"] == date_val)]
        if not rec.empty:
            status = rec["attendance_status"].values[0]
            late = rec.iloc[0]["late_mark"] if "late_mark" in rec.columns else False
            if late:
                return "🕑"
            elif status.lower() == "full day":
                return "✅"
            elif status.lower() == "half day":
                return "🌓"
            elif status.lower() == "absent":
                return "❌"
            else:
                return "?"
        else:
            return "💤" if date_val.weekday() == 1 else "❌"

    matrix = {}
    for _, row in team.iterrows():
        emp_id = row["employee_id"]
        emp_name = row["employee_name"]
        attendance_row = []
        for week in month_days:
            for day in week:
                if day == 0:
                    attendance_row.append("")
                else:
                    d = date(dept_year, dept_month, day)
                    attendance_row.append(get_marker(d, emp_id))
        matrix[emp_name] = attendance_row

    # Display Matrix
    day_labels = [f"{calendar.day_name[i % 7]} {day}" for week in month_days for i, day in enumerate(week) if day != 0]
    expected_length = len(day_labels)
    for key in matrix:
        values = matrix[key]
        if len(values) < expected_length:
            matrix[key] = values + [""] * (expected_length - len(values))
        elif len(values) > expected_length:
            matrix[key] = values[:expected_length]

    df_matrix = pd.DataFrame.from_dict(matrix, orient="index", columns=day_labels)
    st.dataframe(df_matrix, height=150)

    # ---------------- Performance Insights ----------------
    st.subheader("📊 Performance Insights")
    start_date = date(dept_year, dept_month, 1)
    end_date = date(dept_year, dept_month, calendar.monthrange(dept_year, dept_month)[1])
    summary_rows = []

    for _, row in team.iterrows():
        emp_id = row["employee_id"]
        emp_name = row["employee_name"]
        data = employee_data[(employee_data["employee_id"] == emp_id) & (employee_data["date_only"] >= start_date) & (employee_data["date_only"] <= end_date)]

        late = data[data["late_mark"] == True].shape[0]
        full = data[data["attendance_status"].str.strip().str.lower() == "full day"].shape[0]
        half = data[data["attendance_status"].str.strip().str.lower() == "half day"].shape[0]
        tuesday_ok = data[(data["date_only"].apply(lambda x: x.weekday()) == 1) & (data["attendance_status"].str.strip().str.lower() == "full day")].shape[0]

        lop_lookup = salary_df[(salary_df["employee_id"] == emp_id) & (salary_df["month_period"] == pd.Period(selected_dept_month, freq="M"))]
        lop = lop_lookup["lop_days"].values[0] if not lop_lookup.empty else 0
        score = full + 0.5 * half - late - lop

        if lop >= 3:
            label = "🔥 High Risk"
        elif score < 1:
            label = "⚠️ Underperforming"
        elif score >= 3 and late == 0:
            label = "🌟 Consistent Performer"
        else:
            label = "✅ Good Standing"

        badge = "🎯 Tuesday Champion" if tuesday_ok >= 4 else ""

        summary_rows.append({
            "Employee": emp_name,
            "Full Days": full,
            "Half Days": half,
            "Late": late,
            "LOP": lop,
            "Score": round(score, 1),
            "Status": label,
            "Badge": badge
        })

    df_summary = pd.DataFrame(summary_rows)
    st.dataframe(df_summary)

    # Download CSV
    csv = df_summary.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export Summary to CSV",
        data=csv,
        file_name=f"{selected_dept}_{selected_dept_month}_leave_summary.csv",
        mime="text/csv"
    )