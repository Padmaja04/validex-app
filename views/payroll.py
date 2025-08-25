import pandas as pd
import streamlit as st
import numpy as np
import os
import datetime
import calendar
from config import (
    USE_SQL,
    safe_get_conn,
    table_exists,
    SALARY_LOG_TABLE,
    SALARY_LOG_CSV,
    safe_float,
    safe_datetime_for_sql
)


# -------------------- TABLE MANAGEMENT --------------------
def create_salary_table_if_not_exists(conn):
    """Create salary_log table if it doesn't exist."""
    if not table_exists(conn, SALARY_LOG_TABLE):
        cursor = conn.cursor()
        try:
            st.info(f"🔧 Creating table {SALARY_LOG_TABLE}...")

            create_table_sql = f"""
            CREATE TABLE {SALARY_LOG_TABLE} (
                id INT IDENTITY(1,1) PRIMARY KEY,
                employee_id NVARCHAR(50) NOT NULL,
                employee_name NVARCHAR(255),
                salary_month NVARCHAR(7), -- YYYY-MM format
                data_date DATE,
                timestamp DATETIME2,
                entry_time TIME,
                fixed_salary DECIMAL(15,2) DEFAULT 0,
                basic_salary DECIMAL(15,2) DEFAULT 0,
                da DECIMAL(15,2) DEFAULT 0,
                hra DECIMAL(15,2) DEFAULT 0,
                cell_allowance DECIMAL(15,2) DEFAULT 0,
                petrol_allowance DECIMAL(15,2) DEFAULT 0,
                attendance_allowance DECIMAL(15,2) DEFAULT 0,
                performance_allowance DECIMAL(15,2) DEFAULT 0,
                ot_hours_amount DECIMAL(15,2) DEFAULT 0,
                rd_allowance DECIMAL(15,2) DEFAULT 0,
                lic_allowance DECIMAL(15,2) DEFAULT 0,
                arrears_allowance DECIMAL(15,2) DEFAULT 0,
                other_allowance DECIMAL(15,2) DEFAULT 0,
                gross_earnings DECIMAL(15,2) DEFAULT 0,
                base_salary DECIMAL(15,2) DEFAULT 0,
                extra_pay DECIMAL(15,2) DEFAULT 0,
                festival_bonus DECIMAL(15,2) DEFAULT 0,
                tuesday_bonus DECIMAL(15,2) DEFAULT 0,
                tuesday_count INT DEFAULT 0,
                employee_pf DECIMAL(15,2) DEFAULT 0,
                employer_pf DECIMAL(15,2) DEFAULT 0,
                pf_admin_charges DECIMAL(15,2) DEFAULT 0,
                employee_esi DECIMAL(15,2) DEFAULT 0,
                employer_esi DECIMAL(15,2) DEFAULT 0,
                tax_deduction DECIMAL(15,2) DEFAULT 0,
                mlwf_employee DECIMAL(15,2) DEFAULT 0,
                mlwf_employer DECIMAL(15,2) DEFAULT 0,
                advance_deduction DECIMAL(15,2) DEFAULT 0,
                loan_deduction DECIMAL(15,2) DEFAULT 0,
                loan_cutting DECIMAL(15,2) DEFAULT 0,
                fine_deduction DECIMAL(15,2) DEFAULT 0,
                extra_deduction DECIMAL(15,2) DEFAULT 0,
                total_deductions DECIMAL(15,2) DEFAULT 0,
                net_salary DECIMAL(15,2) DEFAULT 0,
                ctc DECIMAL(15,2) DEFAULT 0,
                extra_hours DECIMAL(8,2) DEFAULT 0,
                late_marks INT DEFAULT 0,
                full_days INT DEFAULT 0,
                half_days INT DEFAULT 0,
                earned_leave_taken DECIMAL(8,2) DEFAULT 0,
                leave_accrued DECIMAL(8,2) DEFAULT 0,
                leave_balance DECIMAL(8,2) DEFAULT 0,
                lop_deduction DECIMAL(15,2) DEFAULT 0,
                leave_encashment DECIMAL(15,2) DEFAULT 0,
                leave_concession DECIMAL(8,2) DEFAULT 0,
                leave_concession_amount DECIMAL(15,2) DEFAULT 0,
                action_type NVARCHAR(50),
                description NVARCHAR(500),
                lop_days DECIMAL(8,2) DEFAULT 0,
                days_in_month INT DEFAULT 0,
                working_days INT DEFAULT 0,
                total_earnings DECIMAL(15,2) DEFAULT 0
            )
            """
            cursor.execute(create_table_sql)
            conn.commit()
            st.success(f"✅ Successfully created table {SALARY_LOG_TABLE}")

        except Exception as e:
            st.error(f"❌ Error creating table: {e}")
            print(f"SQL Error: {e}")
        finally:
            cursor.close()
    else:
        st.info(f"✅ Table {SALARY_LOG_TABLE} already exists")


def check_salary_table_status():
    """Check if salary_log table exists and show its status"""
    st.write("🔍 Checking salary_log table status...")

    conn = safe_get_conn()
    if not conn:
        st.error("❌ Cannot connect to SQL Server")
        return False

    try:
        # Check if table exists
        table_exists_result = table_exists(conn, SALARY_LOG_TABLE)
        st.write(f"Table {SALARY_LOG_TABLE} exists: {table_exists_result}")

        if table_exists_result:
            # Get record count
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {SALARY_LOG_TABLE}")
            count = cursor.fetchone()[0]
            st.write(f"📊 Records in {SALARY_LOG_TABLE}: {count}")

            # Show table structure
            cursor.execute(f"""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'salary_log'
                ORDER BY ORDINAL_POSITION
            """)
            columns = cursor.fetchall()
            st.write("📋 Table structure:")
            col_data = []
            for col in columns[:15]:  # Show first 15 columns
                col_data.append([col[0], col[1], col[2]])

            if col_data:
                col_df = pd.DataFrame(col_data, columns=['Column Name', 'Data Type', 'Nullable'])
                st.dataframe(col_df)

            cursor.close()

        conn.close()
        return table_exists_result

    except Exception as e:
        st.error(f"❌ Error checking table: {e}")
        if conn:
            conn.close()
        return False


def test_salary_log_query():
    """Test querying the salary_log table"""
    st.subheader("🧪 Test Salary Log Query")

    conn = safe_get_conn()
    if not conn:
        st.error("❌ Cannot connect to SQL Server")
        return

    try:
        # First, ensure table exists
        create_salary_table_if_not_exists(conn)

        # Test basic query
        st.write("Testing basic query...")
        cursor = conn.cursor()

        # Get record count
        cursor.execute(f"SELECT COUNT(*) FROM {SALARY_LOG_TABLE}")
        count = cursor.fetchone()[0]
        st.write(f"📊 Total records: {count}")

        # If records exist, show some data
        if count > 0:
            cursor.execute(f"""
                SELECT TOP 5 employee_id, employee_name, salary_month, net_salary, timestamp 
                FROM {SALARY_LOG_TABLE} 
                ORDER BY timestamp DESC
            """)
            data = cursor.fetchall()

            if data:
                df = pd.DataFrame(data, columns=['Employee ID', 'Name', 'Month', 'Net Salary', 'Timestamp'])
                st.dataframe(df)
        else:
            st.info("⚠️ No records found in salary_log table")

        # Test the exact query used in load_data
        st.write("---")
        st.write("Testing load_data query...")
        try:
            salary_log = pd.read_sql(f"SELECT * FROM {SALARY_LOG_TABLE}", conn)
            st.success(f"✅ Successfully loaded {len(salary_log)} records using pandas.read_sql")

            if not salary_log.empty:
                st.write("Sample columns:")
                st.write(list(salary_log.columns)[:10])
        except Exception as e:
            st.error(f"❌ Error with pandas.read_sql: {e}")

        cursor.close()
        conn.close()

    except Exception as e:
        st.error(f"❌ Query test error: {e}")
        if conn:
            conn.close()


# -------------------- LOAD DATA --------------------
def load_data():
    if USE_SQL:
        conn = safe_get_conn()
        if conn:
            try:
                st.write("🔍 Loading data from SQL Server...")

                # Load master data
                master = pd.read_sql("SELECT * FROM dbo.employee_master", conn)
                st.write(f"✅ Loaded {len(master)} employee master records")

                # Load attendance data
                attendance = pd.read_sql("SELECT * FROM dbo.employee_data", conn)
                st.write(f"✅ Loaded {len(attendance)} attendance records")

                # Load salary log with detailed checking
                if table_exists(conn, SALARY_LOG_TABLE):
                    st.write(f"✅ Table {SALARY_LOG_TABLE} exists, loading data...")

                    # Check record count first
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT COUNT(*) FROM {SALARY_LOG_TABLE}")
                    record_count = cursor.fetchone()[0]
                    cursor.close()

                    st.write(f"📊 Found {record_count} salary log records")

                    if record_count > 0:
                        salary_log = pd.read_sql(f"SELECT * FROM {SALARY_LOG_TABLE}", conn)
                        st.write(f"✅ Successfully loaded {len(salary_log)} salary log records")
                    else:
                        salary_log = pd.DataFrame()
                        st.info("⚠️ No salary records found in table")
                else:
                    salary_log = pd.DataFrame()
                    st.warning(f"⚠️ Table {SALARY_LOG_TABLE} does not exist")

                conn.close()

            except Exception as e:
                st.error(f"Error loading from SQL: {str(e)}")
                st.write(f"Error details: {type(e).__name__}: {str(e)}")
                if conn:
                    conn.close()
                return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        else:
            st.error("❌ Could not establish SQL connection")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    else:
        # CSV fallback
        try:
            master = pd.read_csv("data/employee_master.csv")
            attendance = pd.read_csv("data/employee_data.csv")
            if os.path.exists(SALARY_LOG_CSV):
                salary_log = pd.read_csv(SALARY_LOG_CSV)
            else:
                salary_log = pd.DataFrame()
        except Exception as e:
            st.error(f"Error loading CSV files: {str(e)}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Clean & format data
    if not master.empty:
        master["employee_id"] = master["employee_id"].astype(str)
        master["employee_name"] = master["employee_name"].str.strip().str.lower()

    if not attendance.empty:
        attendance["employee_id"] = attendance["employee_id"].astype(str)
        attendance["employee_name"] = attendance["employee_name"].str.strip().str.lower()
        attendance["date_only"] = pd.to_datetime(attendance["date_only"], errors="coerce")

        if "late_mark" not in attendance.columns:
            attendance["late_mark"] = False

    if not salary_log.empty:
        if "data_date" in salary_log.columns:
            salary_log["data_date"] = pd.to_datetime(
                salary_log["data_date"], errors="coerce"
            ).dt.date
        salary_log["employee_id"] = salary_log["employee_id"].astype(str)

    return master, attendance, salary_log


# -------------------- SAVE SALARY LOG --------------------
def safe_number(val):
    """Convert values to float safely for SQL DECIMAL fields"""
    try:
        if val is None:
            return 0.0
        if isinstance(val, str):
            val = val.strip()
            if val == "" or val.lower() == "nan":
                return 0.0
        return float(val)
    except Exception:
        return 0.0


def save_salary_log(salary_log):
    st.write(f"💾 Storage Mode: {'SQL Database' if USE_SQL else 'CSV Files'}")

    if USE_SQL:
        conn = safe_get_conn()
        if conn:
            try:
                create_salary_table_if_not_exists(conn)
                cursor = conn.cursor()

                success_count, error_count = 0, 0
                for idx, row in salary_log.iterrows():
                    try:
                        # Clean row values
                        row = row.fillna(0)

                        # Ensure data_date is not empty
                        if not row.get("data_date") or str(row["data_date"]) in ["", "NaT", "NaN"]:
                            try:
                                # default: first day of salary_month
                                row["data_date"] = pd.to_datetime(str(row["salary_month"]) + "-01").date()
                            except Exception:
                                row["data_date"] = datetime.date.today()

                        # Handle entry_time safely
                        entry_time = row.get("entry_time")
                        if pd.isna(entry_time) or entry_time in ["", "NaT", "NaN"]:
                            entry_time = None

                        # Remove existing record for same employee & month
                        delete_sql = f"DELETE FROM {SALARY_LOG_TABLE} WHERE employee_id = ? AND salary_month = ?"
                        cursor.execute(delete_sql, (str(row['employee_id']), row['salary_month']))

                        # Insert new record
                        insert_sql = f"""
                        INSERT INTO {SALARY_LOG_TABLE} (
                            employee_id, employee_name, salary_month, data_date, timestamp,
                            entry_time, fixed_salary, basic_salary, da, hra,
                            cell_allowance, petrol_allowance, attendance_allowance, performance_allowance,
                            ot_hours_amount, rd_allowance, lic_allowance, arrears_allowance, other_allowance,
                            gross_earnings, base_salary, extra_pay, festival_bonus, tuesday_bonus,
                            tuesday_count, employee_pf, employer_pf, pf_admin_charges, employee_esi,
                            employer_esi, tax_deduction, mlwf_employee, mlwf_employer, advance_deduction,
                            loan_deduction, loan_cutting, fine_deduction, extra_deduction, total_deductions,
                            net_salary, ctc, extra_hours, late_marks, full_days, half_days,
                            earned_leave_taken, leave_accrued, leave_balance, lop_deduction,
                            leave_encashment, leave_concession, leave_concession_amount, action_type,
                            description, lop_days, days_in_month, working_days, total_earnings
                        ) VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                        """

                        values = (
                            str(row['employee_id']),
                            row['employee_name'],
                            row['salary_month'],
                            row['data_date'],
                            safe_datetime_for_sql(row['timestamp']),
                            entry_time,

                            safe_number(row['fixed_salary']),
                            safe_number(row['basic_salary']),
                            safe_number(row['da']),
                            safe_number(row['hra']),
                            safe_number(row['cell_allowance']),
                            safe_number(row['petrol_allowance']),
                            safe_number(row['attendance_allowance']),
                            safe_number(row['performance_allowance']),
                            safe_number(row['ot_hours_amount']),
                            safe_number(row['rd_allowance']),
                            safe_number(row['lic_allowance']),
                            safe_number(row['arrears_allowance']),
                            safe_number(row['other_allowance']),
                            safe_number(row['gross_earnings']),
                            safe_number(row['base_salary']),
                            safe_number(row['extra_pay']),
                            safe_number(row['festival_bonus']),
                            safe_number(row['tuesday_bonus']),
                            int(row['tuesday_count']),
                            safe_number(row['employee_pf']),
                            safe_number(row['employer_pf']),
                            safe_number(row['pf_admin_charges']),
                            safe_number(row['employee_esi']),
                            safe_number(row['employer_esi']),
                            safe_number(row['tax_deduction']),
                            safe_number(row['mlwf_employee']),
                            safe_number(row['mlwf_employer']),
                            safe_number(row['advance_deduction']),
                            safe_number(row['loan_deduction']),
                            safe_number(row['loan_cutting']),
                            safe_number(row['fine_deduction']),
                            safe_number(row['extra_deduction']),
                            safe_number(row['total_deductions']),
                            safe_number(row['net_salary']),
                            safe_number(row['ctc']),
                            safe_number(row['extra_hours']),
                            int(row['late_marks']),
                            int(row['full_days']),
                            int(row['half_days']),
                            safe_number(row['earned_leave_taken']),
                            safe_number(row['leave_accrued']),
                            safe_number(row['leave_balance']),
                            safe_number(row['lop_deduction']),
                            safe_number(row['leave_encashment']),
                            safe_number(row['leave_concession']),
                            safe_number(row['leave_concession_amount']),
                            row['action_type'],
                            row['description'],
                            safe_number(row['lop_days']),
                            int(row['days_in_month']),
                            int(row['working_days']),
                            safe_number(row.get('total_earnings', 0))
                        )

                        cursor.execute(insert_sql, values)
                        success_count += 1

                    except Exception as e:
                        st.error(f"❌ Error inserting row {idx}: {e}")
                        error_count += 1

                conn.commit()
                cursor.close()
                conn.close()

                if success_count > 0:
                    st.success(f"✅ SQL: Inserted {success_count} rows")
                if error_count > 0:
                    st.warning(f"⚠️ SQL: {error_count} errors occurred")

            except Exception as e:
                st.error(f"Error saving to SQL: {str(e)}")
                if conn:
                    conn.close()
    else:
        # CSV fallback
        try:
            os.makedirs(os.path.dirname(SALARY_LOG_CSV), exist_ok=True)
            salary_log.to_csv(SALARY_LOG_CSV, index=False)
            st.success("✅ CSV: Saved to file")
        except Exception as e:
            st.error(f"Error saving to CSV: {str(e)}")
# -------------------- CALENDAR UTILITY FUNCTIONS --------------------
def get_month_info(year, month):
    """Get comprehensive month information including working days."""
    # Get total days in month
    days_in_month = calendar.monthrange(year, month)[1]

    # Create date range for the month
    month_start = datetime.date(year, month, 1)
    month_end = datetime.date(year, month, days_in_month)

    # Count working days (excluding Tuesdays as per your business logic)
    working_days = 0
    current_date = month_start
    while current_date <= month_end:
        if current_date.weekday() != 1:  # Skip Tuesdays (1 = Tuesday)
            working_days += 1
        current_date += datetime.timedelta(days=1)

    return {
        'days_in_month': days_in_month,
        'working_days': working_days,
        'month_start': month_start,
        'month_end': month_end
    }


def get_month_display_info(year, month):
    """Get display-friendly month information."""
    month_info = get_month_info(year, month)
    is_leap_year = calendar.isleap(year)

    month_name = calendar.month_name[month]

    special_notes = []
    if month == 2:  # February
        if is_leap_year:
            special_notes.append("🗓️ Leap Year February (29 days)")
        else:
            special_notes.append("🗓️ Regular February (28 days)")
    elif month_info['days_in_month'] == 31:
        special_notes.append("🗓️ Long Month (31 days)")
    elif month_info['days_in_month'] == 30:
        special_notes.append("🗓️ Standard Month (30 days)")

    return {
        'month_name': month_name,
        'year': year,
        'special_notes': special_notes,
        **month_info
    }


# -------------------- SALARY CALCULATION FUNCTIONS --------------------
def calculate_salary_components(monthly_salary):
    """Calculate detailed salary components based on gross salary."""
    # Standard breakdown percentages (can be customized)
    basic_percentage = 0.60              #0.60  # 60% of gross
    da_percentage = 0.21              #0.21  # 21% of gross
    hra_percentage = 0.10             #0.10  # 10% of gross
    performance_percentage = 0.09     #0.09  # 9% of gross

    basic_salary = monthly_salary * basic_percentage
    da = monthly_salary * da_percentage
    hra = monthly_salary * hra_percentage
    performance_allowance = monthly_salary * performance_percentage

    # Fixed allowances (can be made configurable)
    cell_allowance = 0
    petrol_allowance = 0
    attendance_allowance = 0
    ot_hours_amount = 0
    rd_allowance = 0
    lic_allowance = 0
    arrears_allowance = 0
    other_allowance = 0

    gross_earnings = (basic_salary + da + hra + cell_allowance + petrol_allowance +
                      attendance_allowance + performance_allowance + ot_hours_amount +
                      rd_allowance + lic_allowance + arrears_allowance + other_allowance)

    return {
        'basic_salary': basic_salary,
        'da': da,
        'hra': hra,
        'cell_allowance': cell_allowance,
        'petrol_allowance': petrol_allowance,
        'attendance_allowance': attendance_allowance,
        'performance_allowance': performance_allowance,
        'ot_hours_amount': ot_hours_amount,
        'rd_allowance': rd_allowance,
        'lic_allowance': lic_allowance,
        'arrears_allowance': arrears_allowance,
        'other_allowance': other_allowance,
        'gross_earnings': gross_earnings
    }


def calculate_statutory_deductions(gross_earnings, basic_salary, da):
    """Calculate PF, ESI, MLWF and other statutory deductions."""

    # PF Calculation (12% on basic + da, max limit 15000)
    pf_eligible_amount = min(basic_salary + da, 15000)  # PF ceiling on Basic + DA
    employee_pf = pf_eligible_amount * 0.12
    employer_pf = pf_eligible_amount * 0.12

    # PF Admin charges (typically 0.65% of PF eligible amount)
    pf_admin_charges = pf_eligible_amount * 0.0065

    # ESI Calculation (0.75% employee, 3.25% employer on amounts <= 21000)
    esi_ceiling = 21000
    employee_esi = 0
    employer_esi = 0

    if gross_earnings <= esi_ceiling:
        employee_esi = gross_earnings * 0.0075  # 0.75%
        employer_esi = gross_earnings * 0.0325  # 3.25%

    # MLWF (Maharashtra Labour Welfare Fund)
    # Employee: Re 1 if salary > 3000, Employer: Re 1 if salary > 3000
    mlwf_employee = 1 if gross_earnings > 3000 else 0
    mlwf_employer = 1 if gross_earnings > 3000 else 0

    return {
        'employee_pf': employee_pf,
        'employer_pf': employer_pf,
        'pf_admin_charges': pf_admin_charges,
        'employee_esi': employee_esi,
        'employer_esi': employer_esi,
        'mlwf_employee': mlwf_employee,
        'mlwf_employer': mlwf_employer,
        'total_employee_deductions': employee_pf + employee_esi + mlwf_employee
    }


def calculate_lop_days_corrected_v2(emp_id, attendance, month_start, month_end):
    """
    CORRECTED LOP calculation with proper logic.

    Key Points:
    1. LOP should be based on ACTUAL working days in month (excluding Tuesdays)
    2. Count days employee was actually absent from required working days
    3. Consider partial attendance (half days) appropriately
    """

    # Get all working days (excluding Tuesdays as per business logic)
    all_working_days = []
    current_date = month_start

    while current_date <= month_end:
        if current_date.weekday() != 1:  # Skip Tuesdays (1 = Tuesday)
            all_working_days.append(current_date)
        current_date += datetime.timedelta(days=1)

    total_working_days = len(all_working_days)

    # Get attendance for this employee in this month
    attn_emp = attendance[attendance["employee_id"] == emp_id].copy()
    attn_emp["date_only"] = pd.to_datetime(attn_emp["date_only"], errors="coerce")
    attn_emp = attn_emp[attn_emp["date_only"].notna()]
    attn_emp["date_only"] = attn_emp["date_only"].dt.date

    # Create attendance dictionary
    attn_dict = attn_emp.set_index("date_only")["attendance_status"].str.lower().str.strip().to_dict()

    # Count different types of attendance
    full_days_attended = 0
    half_days_attended = 0
    late_marks = 0
    absent_days = 0

    st.write(f"🔍 **LOP Analysis for Employee {emp_id}:**")
    st.write(f"   - Total working days in month: {total_working_days}")

    for work_day in all_working_days:
        status = str(attn_dict.get(work_day, "absent") or "absent").lower().strip()

        if status == "full day":
            full_days_attended += 1
        elif status == "half day":
            half_days_attended += 1
        elif status == "late mark":
            late_marks += 1
            full_days_attended += 1  # Late mark = present but late
        else:
            absent_days += 1

    # Calculate effective days worked
    # Half day = 0.5, Full day/Late mark = 1.0
    effective_days_worked = full_days_attended + (half_days_attended * 0.5)

    # LOP Days = Total Working Days - Effective Days Worked
    lop_days = total_working_days - effective_days_worked

    st.write(f"   - Full days attended: {full_days_attended}")
    st.write(f"   - Half days attended: {half_days_attended}")
    st.write(f"   - Late marks: {late_marks}")
    st.write(f"   - Absent days: {absent_days}")
    st.write(f"   - Effective days worked: {effective_days_worked}")
    st.write(f"   - **Raw LOP days: {lop_days}**")

    return max(0, lop_days)  # LOP cannot be negative


def calculate_lop_deduction_corrected(monthly_salary, days_in_month, lop_days_final):
    """
    CORRECTED LOP deduction calculation.

    Current logic uses: daily_base_salary = monthly_salary / days_in_month

    Issues to consider:
    1. Should LOP be based on calendar days or working days?
    2. Should it be based on gross salary or basic salary only?

    Standard Practice:
    - LOP = (Monthly Gross Salary / Calendar Days) * LOP Days
    - Some companies use: (Monthly Basic Salary / Calendar Days) * LOP Days
    """

    st.write(f"💰 **LOP Deduction Calculation:**")

    # Method 1: Based on Gross Salary and Calendar Days (Current approach)
    daily_rate_gross = monthly_salary / days_in_month
    lop_deduction_gross = lop_days_final * daily_rate_gross

    st.write(f"   📊 **Method 1: Gross Salary Base**")
    st.write(f"   - Monthly Salary: ₹{monthly_salary:,.2f}")
    st.write(f"   - Calendar Days: {days_in_month}")
    st.write(f"   - Daily Rate: ₹{daily_rate_gross:,.2f}")
    st.write(f"   - LOP Days: {lop_days_final}")
    st.write(f"   - **LOP Deduction: ₹{lop_deduction_gross:,.2f}**")

    return lop_deduction_gross


def build_salary_row_monthly_corrected_lop(emp_row, attendance, selected_date):
    """Build salary row with CORRECTED LOP calculation."""
    emp_id = emp_row["employee_id"]
    emp_name = emp_row["employee_name"]

    try:
        new_salary = emp_row.get("new_salary")
        fixed_salary = emp_row.get("fixed_salary", 0)

        # Priority logic: new_salary > fixed_salary > 0
        if pd.notnull(new_salary) and float(new_salary) > 0:
            monthly_salary = float(new_salary)
            salary_source = "new_salary"
        elif pd.notnull(fixed_salary) and float(fixed_salary) > 0:
            monthly_salary = float(fixed_salary)
            salary_source = "fixed_salary"
        else:
            monthly_salary = 0.0
            salary_source = "none"

        st.write(f"🔍 Debug for {emp_name}: Using {monthly_salary} from {salary_source}")

    except (TypeError, ValueError) as e:
        st.write(f"   - Error: {e}")
        monthly_salary = 0.0

    # Get month information
    year = selected_date.year
    month = selected_date.month
    month_info = get_month_info(year, month)

    days_in_month = month_info['days_in_month']
    working_days = month_info['working_days']
    month_start = pd.to_datetime(month_info['month_start'])
    month_end = pd.to_datetime(month_info['month_end'])

    st.write(f"📅 Calendar: {days_in_month} days, {working_days} working days")

    # Calculate detailed salary components
    salary_components = calculate_salary_components(monthly_salary)

    # Filter attendance for the month
    attn = attendance[
        (attendance["employee_id"] == emp_id) &
        (attendance["date_only"] >= month_start) &
        (attendance["date_only"] <= month_end)
        ]

    # Count attendance types
    full_days = attn[attn["attendance_status"].str.lower().str.strip() == "full day"].shape[0]
    half_days = attn[attn["attendance_status"].str.lower().str.strip() == "half day"].shape[0]
    late_marks = attn[attn["attendance_status"].str.lower().str.strip() == "late mark"].shape[0]

    # Extra pay handling
    extra_pay_from_attendance = attn["extra_pay"].sum() if "extra_pay" in attn.columns else 0
    extra_hours = attn["extra_hours"].sum() if "extra_hours" in attn.columns else 0

    ot_allowance = extra_pay_from_attendance
    salary_components['ot_hours_amount'] = ot_allowance

    # Recalculate gross earnings including OT allowance
    gross_earnings = (salary_components['basic_salary'] + salary_components['da'] +
                      salary_components['hra'] + salary_components['cell_allowance'] +
                      salary_components['petrol_allowance'] + salary_components['attendance_allowance'] +
                      salary_components['performance_allowance'] + salary_components['ot_hours_amount'] +
                      salary_components['rd_allowance'] + salary_components['lic_allowance'] +
                      salary_components['arrears_allowance'] + salary_components['other_allowance'])

    salary_components['gross_earnings'] = gross_earnings

    # CORRECTED LOP calculation
    lop_days = calculate_lop_days_corrected_v2(emp_id, attendance, month_info['month_start'], month_info['month_end'])

    # Leave concession (monthly accrual)
    monthly_accrual = 1.2
    leave_concession = min(lop_days, monthly_accrual)

    # LOP days after concession
    lop_days_final = max(0, lop_days - leave_concession)

    # CORRECTED LOP deduction calculation
    lop_deduction = calculate_lop_deduction_corrected(monthly_salary, days_in_month, lop_days_final)
    leave_concession_amount = leave_concession * (monthly_salary / days_in_month)

    st.write(f"📊 **Final LOP Analysis:**")
    st.write(f"   - Raw LOP days: {lop_days}")
    st.write(f"   - Leave concession: {leave_concession}")
    st.write(f"   - Final LOP days: {lop_days_final}")
    st.write(f"   - LOP deduction: ₹{lop_deduction:,.2f}")
    st.write(f"   - Leave concession amount: ₹{leave_concession_amount:,.2f}")

    # Calculate earnings after LOP
    base_earnings_after_lop = gross_earnings - lop_deduction
    total_earnings = base_earnings_after_lop + leave_concession_amount

    st.write(f"💰 **Earnings breakdown:**")
    st.write(f"   - Gross earnings: ₹{gross_earnings:,.2f}")
    st.write(f"   - Less LOP deduction: ₹{lop_deduction:,.2f}")
    st.write(f"   - Plus leave concession: ₹{leave_concession_amount:,.2f}")
    st.write(f"   - **Total earnings: ₹{total_earnings:,.2f}**")

    # Calculate statutory deductions on gross earnings
    statutory_deductions = calculate_statutory_deductions(
        gross_earnings,
        salary_components['basic_salary'],
        salary_components['da']
    )

    # Tax calculation (5% of total earnings)
    tax_deduction = total_earnings * 0.05

    # Additional deductions
    advance_deduction = 0
    loan_deduction = 0
    loan_cutting = 0
    fine_deduction = 0
    extra_deduction = 0

    # Total deductions including ESI
    total_deductions = (
            statutory_deductions['employee_pf'] +
            statutory_deductions['employee_esi'] +
            statutory_deductions['mlwf_employee'] +
            tax_deduction +
            advance_deduction +
            loan_deduction +
            loan_cutting +
            fine_deduction +
            extra_deduction
    )

    # Net salary
    net_salary = total_earnings - total_deductions

    # CTC calculation
    ctc = (total_earnings +
           statutory_deductions['employer_pf'] +
           statutory_deductions['employer_esi'] +
           statutory_deductions['mlwf_employer'] +
           statutory_deductions['pf_admin_charges'])

    st.write(f"✅ **Final calculation:**")
    st.write(f"   - Total earnings: ₹{total_earnings:,.2f}")
    st.write(f"   - Total deductions: ₹{total_deductions:,.2f}")
    st.write(f"   - **Net salary: ₹{net_salary:,.2f}**")

    return {
        "employee_id": emp_id,
        "employee_name": emp_name,
        "salary_month": f"{year}-{month:02d}",
        "data_date": month_end.date(),
        "timestamp": datetime.datetime.now(),
        "entry_time": datetime.datetime.now().time(),
        "fixed_salary": monthly_salary,
        "basic_salary": salary_components['basic_salary'],
        "da": salary_components['da'],
        "hra": salary_components['hra'],
        "cell_allowance": salary_components['cell_allowance'],
        "petrol_allowance": salary_components['petrol_allowance'],
        "attendance_allowance": salary_components['attendance_allowance'],
        "performance_allowance": salary_components['performance_allowance'],
        "ot_hours_amount": salary_components['ot_hours_amount'],
        "rd_allowance": salary_components['rd_allowance'],
        "lic_allowance": salary_components['lic_allowance'],
        "arrears_allowance": salary_components['arrears_allowance'],
        "other_allowance": salary_components['other_allowance'],
        "gross_earnings": gross_earnings,
        "base_salary": monthly_salary / days_in_month,
        "extra_pay": extra_pay_from_attendance,
        "festival_bonus": 0,
        "tuesday_bonus": 0,
        "tuesday_count": 0,  # Calculate separately if needed
        "employee_pf": statutory_deductions['employee_pf'],
        "employer_pf": statutory_deductions['employer_pf'],
        "pf_admin_charges": statutory_deductions['pf_admin_charges'],
        "employee_esi": statutory_deductions['employee_esi'],
        "employer_esi": statutory_deductions['employer_esi'],
        "tax_deduction": tax_deduction,
        "mlwf_employee": statutory_deductions['mlwf_employee'],
        "mlwf_employer": statutory_deductions['mlwf_employer'],
        "advance_deduction": advance_deduction,
        "loan_deduction": loan_deduction,
        "loan_cutting": loan_cutting,
        "fine_deduction": fine_deduction,
        "extra_deduction": extra_deduction,
        "total_deductions": total_deductions,
        "net_salary": net_salary,
        "ctc": ctc,
        "extra_hours": extra_hours,
        "late_marks": late_marks,
        "full_days": full_days,
        "half_days": half_days,
        "earned_leave_taken": 0,
        "leave_accrued": monthly_accrual,
        "leave_balance": 0,
        "lop_deduction": lop_deduction,
        "leave_encashment": 0,
        "leave_concession": leave_concession,
        "leave_concession_amount": leave_concession_amount,
        "action_type": "finalized",
        "description": f"Auto-generated payroll for {calendar.month_name[month]} {year}",
        "lop_days": lop_days_final,
        "days_in_month": days_in_month,
        "working_days": working_days,
        "total_earnings": total_earnings,
    }


# Additional validation functions
def validate_lop_logic():
    """Explain and validate LOP calculation logic."""
    st.info("""
    📋 **LOP CALCULATION LOGIC VALIDATION:**

    **Current Logic Issues:**
    1. ❌ Uses `daily_base_salary = monthly_salary / days_in_month`
    2. ❌ But LOP should be based on actual attendance vs required working days
    3. ❌ Half days are not properly weighted in absence calculation

    **Corrected Logic:**
    1. ✅ Count total working days (exclude Tuesdays)
    2. ✅ Count effective days worked: Full days + (Half days × 0.5)
    3. ✅ LOP Days = Working Days - Effective Days Worked
    4. ✅ LOP Deduction = (Monthly Salary ÷ Calendar Days) × LOP Days

    **Example:**
    - Month has 30 calendar days, 25 working days
    - Employee worked: 20 full days + 2 half days = 21 effective days
    - LOP Days = 25 - 21 = 4 days
    - LOP Deduction = (₹30,000 ÷ 30) × 4 = ₹4,000
    """)


def debug_lop_calculation(emp_id, attendance, month_start, month_end, monthly_salary, days_in_month):
    """Debug LOP calculation step by step."""
    st.write("🔍 **STEP-BY-STEP LOP DEBUG:**")

    # Step 1: Working days
    working_days = []
    current_date = month_start
    while current_date <= month_end:
        if current_date.weekday() != 1:  # Not Tuesday
            working_days.append(current_date)
        current_date += datetime.timedelta(days=1)

    st.write(f"**Step 1:** Total working days = {len(working_days)}")

    # Step 2: Employee attendance
    emp_attn = attendance[attendance["employee_id"] == emp_id].copy()
    emp_attn["date_only"] = pd.to_datetime(emp_attn["date_only"]).dt.date
    attn_dict = emp_attn.set_index("date_only")["attendance_status"].str.lower().to_dict()

    # Step 3: Count attendance
    present_days = {"full": 0, "half": 0, "late": 0, "absent": 0}

    for day in working_days:
        status = attn_dict.get(day, "absent")
        if "full" in status:
            present_days["full"] += 1
        elif "half" in status:
            present_days["half"] += 1
        elif "late" in status:
            present_days["late"] += 1
        else:
            present_days["absent"] += 1

    st.write(f"**Step 2:** Attendance breakdown: {present_days}")

    # Step 4: Calculate effective days
    effective_days = present_days["full"] + present_days["late"] + (present_days["half"] * 0.5)
    lop_days = len(working_days) - effective_days

    st.write(f"**Step 3:** Effective days worked = {effective_days}")
    st.write(f"**Step 4:** LOP days = {len(working_days)} - {effective_days} = {lop_days}")

    # Step 5: LOP amount
    daily_rate = monthly_salary / days_in_month
    lop_amount = lop_days * daily_rate

    st.write(f"**Step 5:** Daily rate = ₹{monthly_salary:,.0f} ÷ {days_in_month} = ₹{daily_rate:,.2f}")
    st.write(f"**Step 6:** LOP deduction = {lop_days} × ₹{daily_rate:,.2f} = ₹{lop_amount:,.2f}")

    return lop_days, lop_amount


# -------------------- CORRECTED PAYROLL SUMMARY DISPLAY --------------------
def display_payroll_summary(salary_data):
    """Display detailed payroll summary with corrected earnings flow including ESI and OT."""
    st.subheader("📄 Corrected Payroll Summary")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**💰 EARNINGS CALCULATION**")
        st.write("---")

        # Show the correct earnings flow
        gross_earnings = salary_data.get('gross_earnings', 0)
        lop_deduction = salary_data.get('lop_deduction', 0)
        ot_allowance = salary_data.get('extra_pay', 0)  # OT allowance
        leave_concession_amount = salary_data.get('leave_concession_amount', 0)
        total_earnings = salary_data.get('total_earnings', 0)

        earnings_flow = [
            ["Gross Salary Components:", ""],
            ["  - Basic Salary", f"₹{salary_data.get('basic_salary', 0):,.0f}"],
            ["  - DA (Dearness Allow)", f"₹{salary_data.get('da', 0):,.0f}"],
            ["  - HRA (House Rent Allow)", f"₹{salary_data.get('hra', 0):,.0f}"],
            ["  - Performance Allowance", f"₹{salary_data.get('performance_allowance', 0):,.0f}"],
            ["  - OT Allowance", f"₹{salary_data.get('ot_hours_amount', 0):,.0f}"],
            ["", ""],
            ["**GROSS EARNINGS**", f"**₹{gross_earnings:,.0f}**"],
            ["", ""],
            ["Attendance Adjustments:", ""],
            [f"  - Less: LOP Deduction ({salary_data.get('lop_days', 0)} days)", f"-₹{lop_deduction:,.0f}"],
            ["  - Plus: Leave Concession", f"+₹{leave_concession_amount:,.0f}"],
            ["", ""],
            ["**TOTAL EARNINGS**", f"**₹{total_earnings:,.0f}**"]
        ]

        earnings_df = pd.DataFrame(earnings_flow, columns=["Component", "Amount"])
        st.dataframe(earnings_df, hide_index=True, use_container_width=True)

    with col2:
        st.write("**💸 DEDUCTIONS**")
        st.write("---")
        deductions_data = {
            "Component": ["Employee PF", "Employee ESI", "Tax (5%)", "MLWF",
                          "Advance", "Loan", "Fine", "Other"],
            "Amount": [
                salary_data.get('employee_pf', 0),
                salary_data.get('employee_esi', 0),  # ESI now included
                salary_data.get('tax_deduction', 0),
                salary_data.get('mlwf_employee', 0),
                salary_data.get('advance_deduction', 0),
                salary_data.get('loan_deduction', 0),
                salary_data.get('fine_deduction', 0),
                salary_data.get('extra_deduction', 0)
            ]
        }

        deductions_df = pd.DataFrame(deductions_data)
        deductions_df['Amount'] = deductions_df['Amount'].apply(lambda x: f"₹{x:,.0f}")
        st.dataframe(deductions_df, hide_index=True)

        st.write(f"**TOTAL DEDUCTIONS: ₹{salary_data.get('total_deductions', 0):,.0f}**")

    # Final Summary
    st.write("---")
    st.subheader("🏆 FINAL CALCULATION")

    summary_col1, summary_col2, summary_col3 = st.columns(3)

    with summary_col1:
        st.metric("**Total Earnings**", f"₹{total_earnings:,.0f}")

    with summary_col2:
        st.metric("**Total Deductions**", f"₹{salary_data.get('total_deductions', 0):,.0f}")

    with summary_col3:
        st.metric("**NET SALARY**", f"₹{salary_data.get('net_salary', 0):,.0f}")

    # Attendance and CTC info
    st.write("---")
    att_col1, att_col2 = st.columns(2)

    with att_col1:
        st.write("**📅 ATTENDANCE SUMMARY**")
        st.write(f"- Days in Month: {salary_data.get('days_in_month', 0)}")
        st.write(f"- Working Days: {salary_data.get('working_days', 0)}")
        st.write(f"- Full Days: {salary_data.get('full_days', 0)}")
        st.write(f"- Half Days: {salary_data.get('half_days', 0)}")
        st.write(f"- Late Marks: {salary_data.get('late_marks', 0)}")
        st.write(f"- Extra Hours: {salary_data.get('extra_hours', 0)}")
        st.write(f"- LOP Days (Final): {salary_data.get('lop_days', 0)}")
        st.write(f"- Leave Concession: {salary_data.get('leave_concession', 0)}")

    with att_col2:
        st.write("**💼 CTC BREAKDOWN**")
        st.write(f"- Total Earnings: ₹{total_earnings:,.0f}")
        st.write(f"- Employer PF: ₹{salary_data.get('employer_pf', 0):,.0f}")
        st.write(f"- Employer ESI: ₹{salary_data.get('employer_esi', 0):,.0f}")
        st.write(f"- PF Admin Charges: ₹{salary_data.get('pf_admin_charges', 0):,.0f}")
        st.write(f"- MLWF Employer: ₹{salary_data.get('mlwf_employer', 0):,.0f}")
        st.write(f"**Total CTC: ₹{salary_data.get('ctc', 0):,.0f}**")

    # ESI Eligibility Information
    st.write("---")
    st.write("**📋 STATUTORY COMPLIANCE**")

    esi_col1, esi_col2 = st.columns(2)

    with esi_col1:
        st.write("**ESI Details:**")
        if salary_data.get('employee_esi', 0) > 0:
            st.write(f"- ESI Eligible: ✅ Yes")
            st.write(f"- Employee ESI (0.75%): ₹{salary_data.get('employee_esi', 0):,.2f}")
            st.write(f"- Employer ESI (3.25%): ₹{salary_data.get('employer_esi', 0):,.2f}")
        else:
            st.write(f"- ESI Eligible: ❌ No (Gross > ₹21,000)")

    with esi_col2:
        st.write("**PF Details:**")
        st.write(f"- Employee PF (12%): ₹{salary_data.get('employee_pf', 0):,.2f}")
        st.write(f"- Employer PF (12%): ₹{salary_data.get('employer_pf', 0):,.2f}")
        st.write(f"- PF Admin Charges: ₹{salary_data.get('pf_admin_charges', 0):,.2f}")


# Additional function to explain extra pay flow
def explain_extra_pay_flow():
    """Explain how extra pay flows through the payroll system."""
    st.info("""
    📋 **EXTRA PAY FLOW EXPLANATION:**

    **Step 1: Data Collection**
    - Extra pay is calculated in `attendance.py` based on overtime hours
    - Extra pay can also be manually entered in `manual_entry.py`
    - Both are stored in the attendance table as `extra_pay` field

    **Step 2: Transfer to Payroll**
    - During payroll calculation, all `extra_pay` amounts for the month are summed
    - This total becomes the **OT Allowance** (`ot_hours_amount`) in salary components

    **Step 3: Inclusion in Gross Earnings**
    - OT Allowance is added to the gross earnings calculation:
    - Gross = Basic + DA + HRA + Performance + **OT Allowance** + Other Allowances

    **Step 4: Statutory Impact**
    - OT Allowance affects **ESI calculation** (if total gross ≤ ₹21,000)
    - OT Allowance affects **PF calculation** (if Basic+DA+OT ≤ ₹15,000)
    - OT Allowance affects **Tax calculation** (5% of total earnings)

    **Step 5: Final Calculation**
    - Total Earnings = Gross Earnings - LOP + Leave Concession
    - Net Salary = Total Earnings - All Deductions (including ESI/PF on OT)
    """)


def validate_extra_pay_calculation(attendance_data, employee_id, month_start, month_end):
    """Validate extra pay calculation for debugging."""
    st.write("🔍 **EXTRA PAY VALIDATION:**")

    # Filter attendance for the employee and month
    emp_attendance = attendance_data[
        (attendance_data["employee_id"] == employee_id) &
        (attendance_data["date_only"] >= month_start) &
        (attendance_data["date_only"] <= month_end)
        ]

    if emp_attendance.empty:
        st.write("❌ No attendance data found for validation")
        return 0

    # Check for extra_pay column
    if "extra_pay" not in emp_attendance.columns:
        st.write("⚠️ No extra_pay column in attendance data")
        return 0

    # Calculate totals
    total_extra_pay = emp_attendance["extra_pay"].sum()
    total_extra_hours = emp_attendance["extra_hours"].sum() if "extra_hours" in emp_attendance.columns else 0

    # Show breakdown
    st.write(f"- Total extra hours: {total_extra_hours}")
    st.write(f"- Total extra pay: ₹{total_extra_pay:,.2f}")

    # Show daily breakdown if requested
    if st.checkbox("Show daily extra pay breakdown", key=f"breakdown_{employee_id}"):
        daily_data = emp_attendance[["date_only", "extra_hours", "extra_pay"]].copy()
        daily_data = daily_data[daily_data["extra_pay"] > 0]  # Only show days with extra pay

        if not daily_data.empty:
            st.dataframe(daily_data)
        else:
            st.write("No days with extra pay found")

    return total_extra_pay


# Additional function to validate ESI calculation
def validate_esi_calculation(gross_earnings, employee_esi, employer_esi):
    """Validate ESI calculation and show debug info."""
    esi_ceiling = 21000

    st.write("🔍 **ESI CALCULATION VALIDATION:**")
    st.write(f"- Gross Earnings: ₹{gross_earnings:,.2f}")
    st.write(f"- ESI Ceiling: ₹{esi_ceiling:,.2f}")

    if gross_earnings <= esi_ceiling:
        expected_employee_esi = gross_earnings * 0.0075
        expected_employer_esi = gross_earnings * 0.0325

        st.write(f"- Expected Employee ESI (0.75%): ₹{expected_employee_esi:,.2f}")
        st.write(f"- Expected Employer ESI (3.25%): ₹{expected_employer_esi:,.2f}")
        st.write(f"- Calculated Employee ESI: ₹{employee_esi:,.2f}")
        st.write(f"- Calculated Employer ESI: ₹{employer_esi:,.2f}")

        if abs(expected_employee_esi - employee_esi) < 0.01:
            st.write("✅ Employee ESI calculation is correct")
        else:
            st.write("❌ Employee ESI calculation error")

        if abs(expected_employer_esi - employer_esi) < 0.01:
            st.write("✅ Employer ESI calculation is correct")
        else:
            st.write("❌ Employer ESI calculation error")
    else:
        st.write("- ESI not applicable (gross earnings > ceiling)")
        if employee_esi == 0 and employer_esi == 0:
            st.write("✅ ESI correctly set to 0")
        else:
            st.write("❌ ESI should be 0 for high earners")


# -------------------- MAIN PAYROLL FUNCTION --------------------
def run_payroll():
    st.title("💼 Enhanced Payroll Management")
    st.caption(f"{'Using SQL Database' if USE_SQL else 'Using CSV Files'}")

    master, attendance, salary_log = load_data()

    if master.empty or attendance.empty:
        st.error("❌ Could not load employee master or attendance data.")
        return

    with st.expander("📊 Attendance Status Overview", expanded=False):
        if not attendance.empty:
            status_counts = attendance["attendance_status"].str.strip().str.lower().value_counts()
            st.dataframe(status_counts.rename("Count").reset_index().rename(columns={"index": "Status"}))
        else:
            st.info("No attendance data available")

    st.subheader("⚙️ Options")
    override = st.checkbox("♻️ Override existing salary entries")
    run_all = st.checkbox("👥 Finalize for all employees", value=True)

    if not run_all:
        name_options = master["employee_name"].str.title().unique()
        emp_name_title = st.selectbox("👤 Employee", name_options)
        emp_name = emp_name_title.lower()
        emp_rows = master[master["employee_name"] == emp_name].to_dict("records")
    else:
        emp_rows = master.to_dict("records")

    selected_month = st.date_input("📆 Choose month", datetime.date.today().replace(day=1))

    # Show calendar information for selected month
    display_info = get_month_display_info(selected_month.year, selected_month.month)
    st.info(
        f"📅 Selected: **{display_info['month_name']} {display_info['year']}** - {display_info['days_in_month']} days, {display_info['working_days']} working days")
    for note in display_info['special_notes']:
        st.write(f"   {note}")

    if st.button("📤 Finalize Monthly Salary"):
        if not emp_rows:
            st.warning("⚠️ No employees matched the selection.")
            return

        count = 0
        new_rows = []
        debug_data = []

        for emp_row in emp_rows:
            emp_id = emp_row["employee_id"]

            # Check if entry already exists
            already_exists = False
            if not salary_log.empty:
                already_exists = (
                        (salary_log["employee_id"].astype(str) == str(emp_id)) &
                        (salary_log["salary_month"] == selected_month.strftime("%Y-%m"))
                ).any()

            if override and already_exists:
                # Remove existing entry
                salary_log = salary_log[~(
                        (salary_log["employee_id"].astype(str) == str(emp_id)) &
                        (salary_log["salary_month"] == selected_month.strftime("%Y-%m"))
                )]
            elif not override and already_exists:
                st.info(f"⏭️ Skipping {emp_row['employee_name']} - entry already exists")
                continue

            # CORRECTED: Use the correct function name
            new_row = build_salary_row_monthly_corrected_lop(emp_row, attendance, selected_month)
            if new_row:
                new_rows.append(new_row)
                count += 1
                debug_data.append({
                    "Employee": emp_row["employee_name"],
                    "Fixed Salary": new_row["fixed_salary"],
                    "Gross Earnings": new_row["gross_earnings"],
                    "LOP Deduction": new_row["lop_deduction"],
                    "Total Earnings": new_row.get("total_earnings", 0),
                    "Total Deductions": new_row["total_deductions"],
                    "Net Salary": new_row["net_salary"],
                    "CTC": new_row["ctc"],
                    "LOP Days": new_row["lop_days"],
                    "Leave Concession": new_row["leave_concession"],
                })

        if count > 0:
            # Add new rows to salary_log
            if new_rows:
                new_df = pd.DataFrame(new_rows)
                salary_log = pd.concat([salary_log, new_df], ignore_index=True)

            # Show enhanced preview
            st.write("📋 Corrected Salary Log Preview:")
            preview_cols = ["employee_id", "employee_name", "salary_month", "fixed_salary",
                            "gross_earnings", "lop_deduction", "total_deductions", "net_salary", "ctc"]
            available_cols = [col for col in preview_cols if col in salary_log.columns]
            st.dataframe(salary_log[available_cols].tail(count))

            # Save the data
            save_salary_log(salary_log)
            st.success(
                f"✅ Finalized corrected salary for {count} employee(s) for {display_info['month_name']} {display_info['year']}.")

            # Show detailed payroll summary for last processed employee
            if new_rows:
                st.write("---")
                display_payroll_summary(new_rows[-1])

            if st.checkbox("🔍 Show detailed calculation breakdown"):
                st.write("📊 Corrected Calculation Details:")
                debug_df = pd.DataFrame(debug_data)
                st.dataframe(debug_df)

                # Show calculation verification
                if new_rows:
                    st.write("---")
                    st.write("🧮 **Calculation Verification:**")
                    for row in new_rows[-min(count, 3):]:  # Show last 3 entries max
                        st.write(f"**{row['employee_name'].title()}:**")

                        # Verify the earnings flow
                        gross = row['gross_earnings']
                        lop_ded = row['lop_deduction']
                        extra_pay = row['extra_pay']
                        leave_conc = row['leave_concession_amount']
                        total_earn = row.get('total_earnings', 0)
                        deductions = row['total_deductions']
                        net = row['net_salary']

                        st.write(f"   📊 **Earnings Flow:**")
                        st.write(f"      - Gross Earnings: ₹{gross:,.2f}")
                        st.write(f"      - Less LOP Deduction: -₹{lop_ded:,.2f}")
                        st.write(f"      - Plus Extra Pay: +₹{extra_pay:,.2f}")
                        st.write(f"      - Plus Leave Concession: +₹{leave_conc:,.2f}")
                        st.write(f"      - **Total Earnings: ₹{total_earn:,.2f}**")
                        st.write(f"   💸 **Deductions:**")
                        st.write(f"      - Employee PF: ₹{row['employee_pf']:,.2f}")
                        st.write(f"      - Tax (5%): ₹{row['tax_deduction']:,.2f}")
                        st.write(f"      - MLWF: ₹{row['mlwf_employee']:,.2f}")
                        st.write(f"      - **Total Deductions: ₹{deductions:,.2f}**")
                        st.write(f"   🏆 **Net Salary: ₹{net:,.2f}**")

                        # Verify calculation
                        calculated_net = total_earn - deductions
                        if abs(calculated_net - net) < 0.01:
                            st.write(
                                f"   ✅ **Calculation Verified!** ({total_earn:,.2f} - {deductions:,.2f} = {calculated_net:,.2f})")
                        else:
                            st.write(f"   ❌ **Calculation Error!** Expected: {calculated_net:,.2f}, Got: {net:,.2f}")

                        st.write("---")
        else:
            st.warning("⚠️ No new entries were finalized.")

    # Add salary log viewer
    if not salary_log.empty:
        with st.expander("📊 View Existing Salary Log", expanded=False):
            # Show summary statistics
            st.write("**📈 Summary Statistics:**")
            total_employees = salary_log['employee_id'].nunique()
            total_records = len(salary_log)
            avg_net_salary = salary_log['net_salary'].mean()
            total_ctc = salary_log['ctc'].sum()

            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
            with stat_col1:
                st.metric("Total Employees", total_employees)
            with stat_col2:
                st.metric("Total Records", total_records)
            with stat_col3:
                st.metric("Avg Net Salary", f"₹{avg_net_salary:,.0f}")
            with stat_col4:
                st.metric("Total CTC", f"₹{total_ctc:,.0f}")

            # Show full dataframe
            st.dataframe(salary_log)

            # Download options
            csv_data = salary_log.to_csv(index=False)
            st.download_button(
                label="📥 Download Salary Log as CSV",
                data=csv_data,
                file_name=f"corrected_salary_log_{datetime.date.today().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    # Add debugging section
    with st.expander("🔧 Debug Information", expanded=False):
        st.write("**System Information:**")
        st.write(f"- Storage Mode: {'SQL Database' if USE_SQL else 'CSV Files'}")
        st.write(f"- Master Records: {len(master) if not master.empty else 0}")
        st.write(f"- Attendance Records: {len(attendance) if not attendance.empty else 0}")
        st.write(f"- Salary Log Records: {len(salary_log) if not salary_log.empty else 0}")

        if not attendance.empty:
            st.write("**Attendance Status Distribution:**")
            status_dist = attendance["attendance_status"].value_counts()
            st.dataframe(status_dist)


if __name__ == "__main__":
    run_payroll()