import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from utils.data_helpers import get_greeting
from config import USE_SQL, get_sql_connection, EMPLOYEE_DATA_TABLE, safe_float, safe_datetime_for_sql

def format_manual_description(log_date, admin_user, target_date, field="manual attendance"):
    return f"On {log_date.strftime('%d %B %Y')}, admin {admin_user} added data for {target_date.strftime('%d %B %Y')} regarding {field}."

def run_manual_entry(admin_name=None):
    if "login_phase" not in st.session_state or st.session_state.login_phase != "verified":
        st.stop()

    st.title("💼 Manual Entry Management")
    st.markdown("🔧 For admin use only. Adds attendance manually when biometric flow is skipped or overridden.")

    # Paths
    MASTER_PATH = "data/employee_master.csv"
    DATA_PATH = "data/employee_data.csv"

    if not os.path.exists(MASTER_PATH):
        st.error("⚠️ Employee master not found.")
        st.stop()

    employee_master = pd.read_csv(MASTER_PATH, dtype={"employee_id": str})
    employee_master.columns = employee_master.columns.str.strip().str.lower()
    employee_master["employee_name"] = employee_master["employee_name"].astype(str).str.strip()

    employee_name = st.selectbox("Select Employee", employee_master["employee_name"].unique())
    filtered = employee_master[employee_master["employee_name"] == employee_name]
    employee_id = filtered["employee_id"].values[0] if not filtered.empty else None
    salary = float(filtered["fixed_salary"].values[0]) if "fixed_salary" in filtered else 0
    hourly_rate = salary / (8 * 26)

    # Load or initialize employee data
    if os.path.exists(DATA_PATH):
        employee_data = pd.read_csv(DATA_PATH, dtype={"employee_id": str})
        if "date_only" in employee_data.columns:
            employee_data["date_only"] = pd.to_datetime(employee_data["date_only"], errors="coerce").dt.date
        else:
            employee_data["date_only"] = pd.NaT
    else:
        employee_data = pd.DataFrame(columns=[
            "employee_id", "employee_name", "start_datetime", "exit_datetime", "date_only",
            "total_hours", "extra_hours", "extra_pay", "attendance_status", "late_mark",
            "method", "confidence", "notes", "admin_user", "description",
            "reason", "timestamp", "action_type"
        ])

    with st.form("manual_attendance"):
        st.subheader("👤 Manual Attendance Form")
        selected_date = st.date_input("📅 Date", value=datetime.today().date())
        start_time = st.time_input("🕒 Start Time", step=timedelta(minutes=1))
        exit_time = st.time_input("🕓 Exit Time", step=timedelta(minutes=1))
        reason = st.text_input("✏️ Reason for Manual Entry")
        notes = st.text_input("📌 Notes (Optional)", value="Admin entry override")
        submitted = st.form_submit_button("✅ Save Manual Entry")

    if submitted:
        start_dt = datetime.combine(selected_date, start_time)
        exit_dt = datetime.combine(selected_date, exit_time)

        if exit_dt <= start_dt:
            st.error("⚠️ Exit time must be after start time.")
            st.stop()

        # Duplicate check: same employee, same date, same method
        is_duplicate = (
            (employee_data["employee_id"] == employee_id) &
            (employee_data["date_only"] == selected_date) &
            (employee_data["method"].str.lower() == "manual")
        )

        if is_duplicate.any():
            existing = employee_data[is_duplicate].iloc[0]
            st.warning(f"⚠️ Manual entry already exists for {employee_name} on {selected_date}.")
            st.markdown(f"- **Reason**: {existing['reason']}")
            st.markdown(f"- **Notes**: {existing['notes']}")
            st.markdown(f"- **Description**: {existing['description']}")
            st.stop()

        # Calculate attendance
        total_hours = (exit_dt - start_dt).total_seconds() / 3600

        # ✅ Extra hours only after 6:45 PM
        extra_start = datetime.combine(selected_date, datetime.strptime("18:45", "%H:%M").time())
        midnight = datetime.combine(selected_date + timedelta(days=1), datetime.strptime("00:00", "%H:%M").time())

        if exit_dt > extra_start:
            # Cap overtime till midnight
            overtime_end = min(exit_dt, midnight)
            extra_seconds = (overtime_end - extra_start).total_seconds()
            extra_hours = max(extra_seconds / 3600, 0)
        else:
            extra_hours = 0

        extra_pay = extra_hours * hourly_rate
        attendance_status = (
            "Absent" if total_hours < 4 else
            "Half Day" if total_hours < 6 else
            "Full Day"
        )
        is_late = start_time > datetime.strptime("09:15", "%H:%M").time()


        # Audit log
        log_date = datetime.now()
        description = format_manual_description(log_date, admin_name, selected_date)

        # Add new row
        new_row = {
            "employee_id": employee_id,
            "employee_name": employee_name,
            "start_datetime": start_dt,
            "exit_datetime": exit_dt,
            "date_only": selected_date,
            "total_hours": total_hours,
            "extra_hours": extra_hours,
            "extra_pay": extra_pay,
            "attendance_status": attendance_status,
            "late_mark": is_late,
            "method": "Manual",
            "confidence": None,
            "notes": notes,
            "admin_user": admin_name,
            "description": description,
            "reason": reason,
            "timestamp": log_date,
            "action_type": "manual_entry"
        }

        employee_data = pd.concat([employee_data, pd.DataFrame([new_row])], ignore_index=True)
        if not USE_SQL:
            employee_data.to_csv(DATA_PATH, index=False)
        if USE_SQL:
            try:
                conn = get_sql_connection()
                cursor = conn.cursor()

                insert_query = f"""
                    INSERT INTO {EMPLOYEE_DATA_TABLE} (
                        employee_id, employee_name, start_datetime, exit_datetime, date_only,
                        total_hours, extra_hours, extra_pay, attendance_status, late_mark,
                        method, confidence, notes, admin_user, description,
                        reason, timestamp, action_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

                cursor.execute(insert_query, (
                    employee_id,
                    employee_name,
                    safe_datetime_for_sql(start_dt),
                    safe_datetime_for_sql(exit_dt),
                    selected_date,
                    safe_float(total_hours),
                    safe_float(extra_hours),
                    safe_float(extra_pay),
                    attendance_status,
                    is_late,
                    "Manual",
                    None,
                    notes,
                    admin_name,
                    description,
                    reason,
                    safe_datetime_for_sql(log_date),
                    "manual_entry"
                ))

                conn.commit()
                conn.close()
                st.success("✅ Manual entry also saved to SQL Server.")
            except Exception as e:
                st.error(f"⚠️ SQL insert failed: {e}")

        greeting = get_greeting(log_date)
        st.success(f"{greeting} — Manual entry saved for {employee_name} on {selected_date} 📌")
        st.markdown(f"- **Total Hours**: {total_hours:.2f} hrs")
        st.markdown(f"- **Extra Hours**: {extra_hours:.2f} hrs")
        st.markdown(f"- **Attendance Status**: `{attendance_status}`")
        st.markdown(f"🧾 **Audit Description**: {description}")
