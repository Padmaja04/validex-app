import streamlit as st
import pandas as pd
from utils.pdf_payslip import generate_payslip_pdf
import os
import numpy as np
from datetime import date
import pyodbc  # Import the ODBC library
import config  # Import your config file
import calendar
import datetime


def run_mypayslip():
    st.set_page_config(page_title="📟 My Payslip", layout="centered")
    st.title("📟 My Payslip")
    st.markdown("View and download your monthly salary details as a PDF.")

    # 🔐 Get session details
    employee_name = str(st.session_state.get("employee_name", "")).strip().lower()
    employee_id = str(st.session_state.get("employee_id", "")).strip()

    # 📁 Load data - Use SQL if enabled, otherwise fall back to CSV
    salary_df = None
    employee_master = None
    attendance_df = None
    is_sql = config.USE_SQL
    st.write(f"🔍 Using SQL Database: {is_sql}")

    # ------------------
    # Data Loading Logic
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

    # 🧹 Clean both datasets
    for df in [salary_df, employee_master]:
        df["employee_name"] = df["employee_name"].astype(str).str.strip().str.lower()
        df["employee_id"] = df["employee_id"].astype(str).str.strip()

    # 🔍 Match employee
    emp_row = employee_master[
        (employee_master["employee_name"] == employee_name) &
        (employee_master["employee_id"] == employee_id)
        ]

    if emp_row.empty:
        st.error(f"⚠️ No matching employee found for ID: `{employee_id}`, Name: `{employee_name}`.")
        st.stop()

    employee_name_clean = emp_row.iloc[0]["employee_name"].title()

    # 📅 Format and filter salary data
    salary_df["data_date"] = pd.to_datetime(salary_df["data_date"], errors="coerce")
    salary_df = salary_df[salary_df["data_date"].notna()]
    salary_df["salary_month_str"] = salary_df["data_date"].dt.strftime("%Y-%m")
    salary_df["month_period"] = salary_df["data_date"].dt.to_period("M")

    # 📌 Filter this employee only
    employee_salary = salary_df[salary_df["employee_id"] == employee_id]

    if employee_salary.empty:
        st.warning("⚠️ No salary records found for you.")
        return

    available_months = sorted(employee_salary["month_period"].unique(), reverse=True)
    selected_month = st.selectbox("📅 Select Month", available_months)
    selected_month_str = selected_month.to_timestamp().strftime("%Y-%m")
    month_str = selected_month.to_timestamp().strftime("%B %Y")

    # 🎯 Filter selected month for this employee
    monthly_salary_rows = employee_salary[
        employee_salary["salary_month_str"] == selected_month_str
        ]

    if monthly_salary_rows.empty:
        st.info("ℹ️ No finalized salary data for this month.")
        return

    # Get the latest record for this month (should be only one per month now)
    row = monthly_salary_rows.sort_values("data_date", ascending=False).iloc[0].to_dict()

    # Enhanced defaults to match payroll.py structure
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
        "ctc": 0,  # Using single ctc field as per updated payroll.py

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

    # Fill missing values
    for key, val in enhanced_defaults.items():
        row[key] = row.get(key, val)

    if row["net_salary"] <= 0 and row["gross_earnings"] <= 0:
        st.info("ℹ️ No finalized salary data or zero salary computed for this month.")
        return

    # 📊 Enhanced Display Summary - Payslip Style Layout
    st.subheader(f"💼 Payslip for {month_str}")

    # Employee Information Header
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Employee Name:** {employee_name_clean}")
        st.markdown(f"**Employee ID:** {employee_id}")
    with col2:
        st.markdown(f"**Month:** {month_str}")
        finalized_date = pd.to_datetime(row["data_date"], errors="coerce")
        finalized_str = finalized_date.strftime("%Y-%m-%d") if pd.notnull(finalized_date) else "N/A"
        st.markdown(f"**Generated On:** {finalized_str}")

    st.markdown("---")

    # Salary Components in Two Columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💰 **EARNINGS**")
        earnings_data = [
            ("Basic Salary", row["basic_salary"]),
            ("DA (Dearness Allowance)", row["da"]),
            ("HRA (House Rent Allow)", row["hra"]),
            ("Cell Allowance", row["cell_allowance"]),
            ("Petrol Allowance", row["petrol_allowance"]),
            ("Attendance Allowance", row["attendance_allowance"]),
            ("Performance Allowance", row["performance_allowance"]),
            ("OT Hours Amount", row["ot_hours_amount"]),
            ("RD Allowance", row["rd_allowance"]),
            ("LIC Allowance", row["lic_allowance"]),
            ("Arrears Allowance", row["arrears_allowance"]),
            ("Other Allowance", row["other_allowance"]),
            ("Festival Bonus", row["festival_bonus"]),
            ("Tuesday Bonus", row["tuesday_bonus"]),
            ("Leave Concession Amount", row["leave_concession_amount"]),
        ]

        for label, value in earnings_data:
            if value > 0:
                st.markdown(f"- **{label}**: ₹{float(value):,.2f}")

        st.markdown("---")
        st.markdown(f"### **GROSS EARNINGS: ₹{float(row['gross_earnings']):,.2f}**")

    with col2:
        st.markdown("### 💸 **DEDUCTIONS**")
        deductions_data = [
            ("Employee PF", row["employee_pf"]),
            ("Employee ESI", row["employee_esi"]),
            ("Tax Deduction", row["tax_deduction"]),
            ("MLWF Employee", row["mlwf_employee"]),
            ("Advance Deduction", row["advance_deduction"]),
            ("Loan Deduction", row["loan_deduction"]),
            ("Loan Cutting", row["loan_cutting"]),
            ("Fine Deduction", row["fine_deduction"]),
            ("Extra Deduction", row["extra_deduction"]),
            ("LOP Deduction", row["lop_deduction"]),
        ]

        for label, value in deductions_data:
            if value > 0:
                st.markdown(f"- **{label}**: ₹{float(value):,.2f}")

        st.markdown("---")
        st.markdown(f"### **TOTAL DEDUCTIONS: ₹{float(row['total_deductions']):,.2f}**")

    st.markdown("---")

    # Net Salary and CTC
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("**NET SALARY**", f"₹{float(row['net_salary']):,.2f}")
    with col2:
        st.metric("**CTC**", f"₹{float(row['ctc']):,.2f}")
    with col3:
        st.metric("**Fixed Salary**", f"₹{float(row['fixed_salary']):,.2f}")

    # Attendance Summary
    st.markdown("---")
    st.markdown("### 📅 **ATTENDANCE SUMMARY**")

    att_col1, att_col2, att_col3, att_col4 = st.columns(4)
    with att_col1:
        st.metric("Full Days", int(row["full_days"]))
    with att_col2:
        st.metric("Half Days", int(row["half_days"]))
    with att_col3:
        st.metric("Late Marks", int(row["late_marks"]))
    with att_col4:
        st.metric("LOP Days", int(row["lop_days"]))

    # Calendar details
    cal_col1, cal_col2, cal_col3 = st.columns(3)
    with cal_col1:
        st.metric("Days in Month", int(row["days_in_month"]))
    with cal_col2:
        st.metric("Working Days", int(row["working_days"]))
    with cal_col3:
        st.metric("Leave Concession", float(row["leave_concession"]))

    # 📅 Load attendance and build attendance_map
    try:
        if not is_sql:
            # Fallback to CSV for attendance if SQL failed earlier
            if os.path.exists(config.EMPLOYEE_DATA_CSV):
                attendance_df = pd.read_csv(config.EMPLOYEE_DATA_CSV, dtype={"employee_id": str})
            else:
                st.warning(f"⚠️ Attendance file not found: {config.EMPLOYEE_DATA_CSV}")
                attendance_map = {}
                return

        attendance_df["date_only"] = pd.to_datetime(attendance_df["date_only"], errors="coerce")
        attendance_df["employee_id"] = attendance_df["employee_id"].astype(str)
        attendance_df["attendance_status"] = attendance_df["attendance_status"].fillna("absent").str.lower().str.strip()

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

    except Exception as e:
        st.warning(f"📛 Error generating attendance calendar: {e}")
        attendance_map = {}

    # 📄 Enhanced PDF data dictionary aligned with payroll.py
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
        "ctc": row["ctc"],  # Using single ctc field

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

    # 🖨️ PDF Generation & Download
    pdf_bytes = generate_payslip_pdf(employee_name_clean, employee_id, pdf_data)
    st.download_button(
        label="📄 Download Enhanced Payslip PDF",
        data=pdf_bytes,
        file_name=f"Payslip_{selected_month_str}_{employee_name_clean.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )

    # Additional debugging information (expandable)
    with st.expander("🔍 Debug Information", expanded=False):
        st.write("**Raw Salary Data:**")
        debug_data = {k: v for k, v in row.items() if k in enhanced_defaults.keys()}
        st.json(debug_data)

        if attendance_map:
            st.write("**Attendance Map:**")
            st.write(attendance_map)


if __name__ == "__main__":
    run_mypayslip()