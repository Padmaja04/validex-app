import streamlit as st
import pandas as pd
import zipfile
import io
import os
from datetime import datetime, date
from utils.pdf_payslip import generate_payslip_pdf  # Updated to use same PDF generator as mypayslip
from utils.email_tools import send_email
import pyodbc
import config
import calendar
import numpy as np


def run_bulkpayslip():
    st.set_page_config(page_title="📦 Bulk Payslip", layout="wide")
    st.title("📦 Bulk Payslip Generator")
    st.markdown("Generate, download, and optionally email payslips in bulk for a selected month.")

    # 📁 Load data - Use SQL if enabled, otherwise fall back to CSV
    salary_df = None
    employee_master = None
    attendance_df = None
    is_sql = config.USE_SQL
    st.write(f"🔍 Using SQL Database: {is_sql}")

    # ------------------
    # Data Loading Logic (Same as mypayslip.py)
    # ------------------
    if is_sql:
        try:
            conn = config.safe_get_conn()
            if conn:
                st.info("Attempting to load data from SQL Server...")
                employee_master = pd.read_sql_query(f"SELECT * FROM {config.EMPLOYEE_MASTER_TABLE}", conn)
                salary_df = pd.read_sql_query(f"SELECT * FROM {config.SALARY_LOG_TABLE}", conn)
                attendance_df = pd.read_sql_query(f"SELECT * FROM {config.EMPLOYEE_DATA_TABLE}", conn)
                conn.close()
                st.success("✅ Data loaded successfully from SQL Server.")
            else:
                st.warning("SQL connection failed. Falling back to CSV files.")
                is_sql = False
        except pyodbc.Error as ex:
            st.error(f"SQL connection error: {ex}. Falling back to CSV files.")
            is_sql = False

    if not is_sql:
        st.info("Loading data from local CSV files.")
        if os.path.exists(config.SALARY_LOG_CSV):
            salary_df = pd.read_csv(config.SALARY_LOG_CSV, dtype={"employee_id": str})
        else:
            st.error(f"⚠️ File not found: {config.SALARY_LOG_CSV}")
            st.stop()

        if os.path.exists(config.EMPLOYEE_MASTER_CSV):
            employee_master = pd.read_csv(config.EMPLOYEE_MASTER_CSV, dtype={"employee_id": str})
        else:
            st.error(f"⚠️ File not found: {config.EMPLOYEE_MASTER_CSV}")
            st.stop()

        if os.path.exists(config.EMPLOYEE_DATA_CSV):
            attendance_df = pd.read_csv(config.EMPLOYEE_DATA_CSV, dtype={"employee_id": str})
        else:
            st.warning(f"⚠️ Attendance file not found: {config.EMPLOYEE_DATA_CSV}")
            attendance_df = pd.DataFrame()  # Empty dataframe as fallback

    # 🧹 Clean both datasets (Same as mypayslip.py)
    for df in [salary_df, employee_master]:
        df["employee_name"] = df["employee_name"].astype(str).str.strip().str.lower()
        df["employee_id"] = df["employee_id"].astype(str).str.strip()

    # Clean attendance data if available
    if not attendance_df.empty:
        attendance_df["employee_id"] = attendance_df["employee_id"].astype(str).str.strip()
        attendance_df["date_only"] = pd.to_datetime(attendance_df["date_only"], errors="coerce")
        attendance_df["attendance_status"] = attendance_df["attendance_status"].fillna("absent").str.lower().str.strip()

    # 📅 Format and filter salary data (Same as mypayslip.py)
    salary_df["data_date"] = pd.to_datetime(salary_df["data_date"], errors="coerce")
    salary_df = salary_df[salary_df["data_date"].notna()]
    salary_df["salary_month_str"] = salary_df["data_date"].dt.strftime("%Y-%m")
    salary_df["month_period"] = salary_df["data_date"].dt.to_period("M")

    # Get available months
    available_months = sorted(salary_df["month_period"].unique(), reverse=True)

    if not available_months:
        st.error("❌ No salary data found. Please finalize salary before generating payslips.")
        return

    selected_month = st.selectbox("📅 Select Month", available_months)
    selected_month_str = selected_month.to_timestamp().strftime("%Y-%m")
    month_str = selected_month.to_timestamp().strftime("%B %Y")

    # 🔍 Employee Filtering Options
    with st.expander("🔍 Filter Employees"):
        # Department filter
        available_departments = employee_master[
            "department"].dropna().unique() if "department" in employee_master.columns else []
        dept_filter = st.multiselect("Department", options=available_departments)

        # Date range filter
        if "join_date" in employee_master.columns:
            employee_master["join_date"] = pd.to_datetime(employee_master["join_date"], errors="coerce")
            join_start = st.date_input("Joined After", value=datetime(2020, 1, 1))
            join_end = st.date_input("Joined Before", value=datetime.today())
        else:
            join_start = None
            join_end = None

    # Apply filters
    filtered_employees = employee_master.copy()

    if join_start and join_end and "join_date" in employee_master.columns:
        filtered_employees = filtered_employees[
            (filtered_employees["join_date"] >= pd.to_datetime(join_start)) &
            (filtered_employees["join_date"] <= pd.to_datetime(join_end))
            ]

    if dept_filter:
        filtered_employees = filtered_employees[filtered_employees["department"].isin(dept_filter)]

    st.success(f"🔎 {len(filtered_employees)} employee(s) matched filter criteria.")

    # Email configuration
    send_emails = st.checkbox("✉️ Send Payslips via Email")
    smtp_config = {}
    if send_emails:
        with st.expander("📧 Email Configuration"):
            smtp_config = {
                "sender": st.text_input("Sender Email", value="your_email@gmail.com"),
                "user": st.text_input("SMTP Username", value="your_email@gmail.com"),
                "password": st.text_input("SMTP Password", type="password"),
                "host": st.text_input("SMTP Host", value="smtp.gmail.com"),
                "port": st.number_input("SMTP Port", value=587, min_value=1, max_value=65535)
            }

    # Enhanced defaults matching mypayslip.py
    enhanced_defaults = {
        # Basic salary components
        "fixed_salary": 0,
        "basic_salary": 0,
        "da": 0,
        "hra": 0,
        "cell_allowance": 0,
        "petrol_allowance": 0,
        "attendance_allowance": 0,
        "performance_allowance": 0,
        "ot_hours_amount": 0,
        "rd_allowance": 0,
        "lic_allowance": 0,
        "arrears_allowance": 0,
        "other_allowance": 0,
        "gross_earnings": 0,
        "base_salary": 0,
        "extra_pay": 0,
        "festival_bonus": 0,
        "tuesday_bonus": 0,
        "tuesday_count": 0,

        # Statutory deductions
        "employee_pf": 0,
        "employer_pf": 0,
        "pf_admin_charges": 0,
        "employee_esi": 0,
        "employer_esi": 0,
        "tax_deduction": 0,
        "mlwf_employee": 0,
        "mlwf_employer": 0,

        # Other deductions
        "advance_deduction": 0,
        "loan_deduction": 0,
        "loan_cutting": 0,
        "fine_deduction": 0,
        "extra_deduction": 0,
        "total_deductions": 0,
        "net_salary": 0,
        "ctc": 0,

        # Attendance and leave
        "extra_hours": 0,
        "late_marks": 0,
        "full_days": 0,
        "half_days": 0,
        "earned_leave_taken": 0,
        "leave_accrued": 0,
        "leave_balance": 0,
        "lop_deduction": 0,
        "leave_encashment": 0,
        "leave_concession": 0,
        "leave_concession_amount": 0,
        "lop_days": 0,
        "days_in_month": 0,
        "working_days": 0,

        # Meta fields
        "data_date": "N/A",
        "action_type": "",
        "description": ""
    }

    def build_attendance_map(employee_id, selected_month_str):
        """Build attendance map for an employee for the selected month"""
        if attendance_df.empty:
            return {}

        try:
            month_start = pd.to_datetime(selected_month_str + "-01")
            month_end = (month_start + pd.offsets.MonthEnd(1)).date()

            filtered_attendance = attendance_df[
                (attendance_df["employee_id"] == employee_id) &
                (attendance_df["date_only"].dt.date >= month_start.date()) &
                (attendance_df["date_only"].dt.date <= month_end)
                ]

            attendance_map = {}
            for _, att_row in filtered_attendance.iterrows():
                day = att_row["date_only"].day
                status = att_row["attendance_status"]
                if status == "full day":
                    attendance_map[day] = "F"
                elif status == "half day":
                    attendance_map[day] = "H"
                elif status == "late mark":
                    attendance_map[day] = "L"
                else:
                    attendance_map[day] = "A"

            # Fill missing days as 'A' (Absent) or '-' for Tuesdays
            for day in range(1, month_end.day + 1):
                dt = date(month_start.year, month_start.month, day)
                if day not in attendance_map:
                    if dt.weekday() == 1:  # Tuesday
                        attendance_map[day] = "-"
                    else:
                        attendance_map[day] = "A"

            return attendance_map
        except Exception as e:
            st.warning(f"Error building attendance map for {employee_id}: {e}")
            return {}

    def build_pdf_data(row, employee_name_clean, employee_id, month_str, attendance_map):
        """Build PDF data dictionary matching mypayslip.py format"""
        # Fill missing values with defaults
        for key, val in enhanced_defaults.items():
            if key not in row:
                row[key] = val

        pdf_data = {
            "Employee Name": employee_name_clean,
            "Employee ID": employee_id,
            "Month": month_str,
            "attendance_map": attendance_map,

            # Enhanced salary components
            "fixed_salary": row["fixed_salary"],
            "basic_salary": row["basic_salary"],
            "da": row["da"],
            "hra": row["hra"],
            "cell_allowance": row["cell_allowance"],
            "petrol_allowance": row["petrol_allowance"],
            "attendance_allowance": row["attendance_allowance"],
            "performance_allowance": row["performance_allowance"],
            "ot_hours_amount": row["ot_hours_amount"],
            "rd_allowance": row["rd_allowance"],
            "lic_allowance": row["lic_allowance"],
            "arrears_allowance": row["arrears_allowance"],
            "other_allowance": row["other_allowance"],
            "gross_earnings": row["gross_earnings"],
            "base_salary": row["base_salary"],
            "extra_pay": row["extra_pay"],
            "festival_bonus": row["festival_bonus"],
            "tuesday_bonus": row["tuesday_bonus"],
            "tuesday_count": row["tuesday_count"],

            # Enhanced deductions
            "employee_pf": row["employee_pf"],
            "employer_pf": row["employer_pf"],
            "pf_admin_charges": row["pf_admin_charges"],
            "employee_esi": row["employee_esi"],
            "employer_esi": row["employer_esi"],
            "tax_deduction": row["tax_deduction"],
            "mlwf_employee": row["mlwf_employee"],
            "mlwf_employer": row["mlwf_employer"],
            "advance_deduction": row["advance_deduction"],
            "loan_deduction": row["loan_deduction"],
            "loan_cutting": row["loan_cutting"],
            "fine_deduction": row["fine_deduction"],
            "extra_deduction": row["extra_deduction"],
            "total_deductions": row["total_deductions"],
            "net_salary": row["net_salary"],
            "ctc": row["ctc"],

            # Attendance and leave details
            "extra_hours": row["extra_hours"],
            "late_marks": row["late_marks"],
            "full_days": row["full_days"],
            "half_days": row["half_days"],
            "earned_leave_taken": row["earned_leave_taken"],
            "leave_accrued": row["leave_accrued"],
            "leave_balance": row["leave_balance"],
            "lop_deduction": row["lop_deduction"],
            "leave_encashment": row["leave_encashment"],
            "leave_concession": row["leave_concession"],
            "leave_concession_amount": row["leave_concession_amount"],
            "lop_days": row["lop_days"],
            "days_in_month": row["days_in_month"],
            "working_days": row["working_days"]
        }
        return pdf_data

    if st.button("🚀 Generate Payslips"):
        if filtered_employees.empty:
            st.error("❌ No employees match the filter criteria.")
            return

        zip_buffer = io.BytesIO()
        retry_list = []
        log = []
        successful_count = 0
        error_count = 0

        # Filter salary data for selected month
        monthly_salary = salary_df[salary_df["salary_month_str"] == selected_month_str]

        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            progress_bar = st.progress(0)
            total_employees = len(filtered_employees)

            for idx, (_, emp_row) in enumerate(filtered_employees.iterrows()):
                emp_id = str(emp_row["employee_id"]).strip()
                emp_name = str(emp_row["employee_name"]).strip().lower()
                emp_name_clean = emp_name.title()
                email_id = emp_row.get("email_id", None)

                # Update progress
                progress_bar.progress((idx + 1) / total_employees)

                # Find salary data for this employee
                employee_salary = monthly_salary[monthly_salary["employee_id"] == emp_id]

                if employee_salary.empty:
                    log.append(f"❌ No salary data for {emp_name_clean} ({emp_id}) — skipped.")
                    error_count += 1
                    continue

                # Get the latest record for this month
                row = employee_salary.sort_values("data_date", ascending=False).iloc[0].to_dict()

                # Check if salary is valid
                if row.get("net_salary", 0) <= 0 and row.get("gross_earnings", 0) <= 0:
                    log.append(f"❌ Zero salary for {emp_name_clean} ({emp_id}) — skipped.")
                    error_count += 1
                    continue

                try:
                    # Build attendance map
                    attendance_map = build_attendance_map(emp_id, selected_month_str)

                    # Build PDF data
                    pdf_data = build_pdf_data(row, emp_name_clean, emp_id, month_str, attendance_map)

                    # Generate PDF using the same function as mypayslip.py
                    pdf_bytes = generate_payslip_pdf(emp_name_clean, emp_id, pdf_data)

                    # Add to ZIP
                    filename = f"Payslip_{selected_month_str}_{emp_name_clean.replace(' ', '_')}.pdf"
                    zipf.writestr(filename, pdf_bytes)

                    # Send email if requested
                    if send_emails and email_id:
                        try:
                            send_email(pdf_bytes, filename, email_id, smtp_config)
                            log.append(f"📤 Generated and emailed to {emp_name_clean} <{email_id}>")
                        except Exception as e:
                            log.append(f"✅ Generated for {emp_name_clean} — ⚠️ Email failed: {str(e)}")
                    else:
                        log.append(f"✅ Generated payslip for {emp_name_clean}")

                    successful_count += 1

                except Exception as e:
                    retry_list.append(emp_id)
                    log.append(f"❌ Error generating payslip for {emp_name_clean}: {str(e)}")
                    error_count += 1

        # Clear progress bar
        progress_bar.empty()

        # Show results summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ Successful", successful_count)
        with col2:
            st.metric("❌ Errors", error_count)
        with col3:
            st.metric("📊 Total Processed", successful_count + error_count)

        # Download button
        if successful_count > 0:
            st.download_button(
                label=f"📦 Download ZIP for {month_str} ({successful_count} payslips)",
                data=zip_buffer.getvalue(),
                file_name=f"Payslips_{selected_month_str}.zip",
                mime="application/zip"
            )

        # Show generation log
        with st.expander(f"📋 Generation Log ({len(log)} entries)"):
            for entry in log:
                if "❌" in entry:
                    st.error(entry)
                elif "⚠️" in entry:
                    st.warning(entry)
                elif "✅" in entry:
                    st.success(entry)
                elif "📤" in entry:
                    st.info(entry)
                else:
                    st.write(entry)

        if retry_list:
            st.warning(
                f"♻️ {len(retry_list)} employee(s) had issues. Employee IDs with errors: {', '.join(retry_list)}")

        # Email summary
        if send_emails:
            email_sent = len([entry for entry in log if "📤" in entry])
            email_failed = len([entry for entry in log if "⚠️ Email failed" in entry])

            col1, col2 = st.columns(2)
            with col1:
                st.metric("📧 Emails Sent", email_sent)
            with col2:
                st.metric("📧 Email Failures", email_failed)


if __name__ == "__main__":
    run_bulkpayslip()