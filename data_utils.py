# data_utils.py
"""
Utility functions for data operations that work with both SQL and CSV
based on config.py settings
"""
import pandas as pd
import os
from datetime import datetime
from config import (
    USE_SQL, safe_get_conn,
    EMPLOYEE_MASTER_CSV, EMPLOYEE_DATA_CSV, SALARY_LOG_CSV,
    FEEDBACK_LOG_CSV, VERIFIED_ADMINS_CSV, RESIGNATION_LOG_CSV,
    EMPLOYEE_MASTER_TABLE, EMPLOYEE_DATA_TABLE, SALARY_LOG_TABLE,
    FEEDBACK_LOG_TABLE, VERIFIED_ADMIN_TABLE, RESIGNATION_LOG_TABLE,
    safe_float, safe_datetime_for_sql
)

# Global variable to store debug messages for Streamlit
DEBUG_MESSAGES = []


def add_debug_message(message):
    """Add debug message that can be displayed in Streamlit"""
    global DEBUG_MESSAGES
    DEBUG_MESSAGES.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    print(message)  # Also print to console


def get_debug_messages():
    """Get all debug messages"""
    global DEBUG_MESSAGES
    return DEBUG_MESSAGES.copy()


def clear_debug_messages():
    """Clear debug messages"""
    global DEBUG_MESSAGES
    DEBUG_MESSAGES = []


# ==================== EMPLOYEE MASTER ====================

def get_employee_master():
    """Get employee master data from SQL or CSV based on config"""
    if USE_SQL:
        try:
            conn = safe_get_conn()
            if conn:
                query = f"SELECT * FROM {EMPLOYEE_MASTER_TABLE}"
                df = pd.read_sql(query, conn)
                conn.close()
                return df
        except Exception as e:
            add_debug_message(f"SQL Error in get_employee_master: {e}")

    # CSV fallback
    if os.path.exists(EMPLOYEE_MASTER_CSV):
        return pd.read_csv(EMPLOYEE_MASTER_CSV, dtype={"employee_id": str})
    else:
        return pd.DataFrame(columns=[
            'employee_id', 'employee_name', 'department', 'position',
            'hire_date', 'salary', 'status'
        ])


def add_employee(employee_data):
    """Add new employee to SQL or CSV based on config"""
    if USE_SQL:
        try:
            conn = safe_get_conn()
            if conn:
                cursor = conn.cursor()
                insert_query = f"""
                INSERT INTO {EMPLOYEE_MASTER_TABLE} 
                (employee_id, employee_name, department, position, hire_date, salary, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(insert_query, [
                    str(employee_data['employee_id']),
                    str(employee_data['employee_name']),
                    str(employee_data.get('department', '')),
                    str(employee_data.get('position', '')),
                    safe_datetime_for_sql(employee_data.get('hire_date')),
                    safe_float(employee_data.get('salary', 0)),
                    str(employee_data.get('status', 'Active'))
                ])
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            add_debug_message(f"SQL Error in add_employee: {e}")

    # CSV fallback
    try:
        df = get_employee_master()
        new_row = pd.DataFrame([employee_data])
        df = pd.concat([df, new_row], ignore_index=True)
        os.makedirs(os.path.dirname(EMPLOYEE_MASTER_CSV), exist_ok=True)
        df.to_csv(EMPLOYEE_MASTER_CSV, index=False)
        return True
    except Exception as e:
        add_debug_message(f"CSV Error in add_employee: {e}")
        return False


# ==================== EMPLOYEE DATA ====================

def get_employee_data(employee_id=None):
    """Get employee data from SQL or CSV based on config"""
    if USE_SQL:
        try:
            conn = safe_get_conn()
            if conn:
                if employee_id:
                    query = f"SELECT * FROM {EMPLOYEE_DATA_TABLE} WHERE employee_id = ?"
                    df = pd.read_sql(query, conn, params=[str(employee_id)])
                else:
                    query = f"SELECT * FROM {EMPLOYEE_DATA_TABLE}"
                    df = pd.read_sql(query, conn)
                conn.close()
                return df
        except Exception as e:
            add_debug_message(f"SQL Error in get_employee_data: {e}")

    # CSV fallback
    if os.path.exists(EMPLOYEE_DATA_CSV):
        df = pd.read_csv(EMPLOYEE_DATA_CSV, dtype={"employee_id": str})
        if employee_id:
            return df[df['employee_id'] == str(employee_id)]
        return df
    else:
        return pd.DataFrame(columns=[
            'employee_id', 'date', 'attendance_status', 'hours_worked',
            'performance_score', 'notes'
        ])


def add_employee_data(data):
    """Add employee data record to SQL or CSV based on config"""
    if USE_SQL:
        try:
            conn = safe_get_conn()
            if conn:
                cursor = conn.cursor()
                insert_query = f"""
                INSERT INTO {EMPLOYEE_DATA_TABLE}
                (employee_id, date, attendance_status, hours_worked, performance_score, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """
                cursor.execute(insert_query, [
                    str(data['employee_id']),
                    safe_datetime_for_sql(data.get('date')),
                    str(data.get('attendance_status', '')),
                    safe_float(data.get('hours_worked', 0)),
                    safe_float(data.get('performance_score', 0)),
                    str(data.get('notes', ''))
                ])
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            add_debug_message(f"SQL Error in add_employee_data: {e}")

    # CSV fallback
    try:
        df = get_employee_data()
        new_row = pd.DataFrame([data])
        df = pd.concat([df, new_row], ignore_index=True)
        os.makedirs(os.path.dirname(EMPLOYEE_DATA_CSV), exist_ok=True)
        df.to_csv(EMPLOYEE_DATA_CSV, index=False)
        return True
    except Exception as e:
        add_debug_message(f"CSV Error in add_employee_data: {e}")
        return False


# ==================== SALARY LOG ====================

def get_salary_log(employee_id=None, start_date=None, end_date=None, debug_mode=False):
    """Get salary log data from SQL or CSV based on config"""
    if debug_mode:
        clear_debug_messages()  # Clear previous messages for this call

    add_debug_message(f"get_salary_log called with employee_id={employee_id}")
    add_debug_message(f"USE_SQL={USE_SQL}")

    if USE_SQL:
        try:
            add_debug_message("Attempting SQL connection...")
            conn = safe_get_conn()
            if conn:
                add_debug_message("SQL connection successful")
                query = f"SELECT * FROM {SALARY_LOG_TABLE} WHERE 1=1"
                params = []

                if employee_id:
                    # Normalize ID to string without decimals
                    normalized_id = str(int(float(employee_id)))
                    query += " AND employee_id = ?"
                    params.append(normalized_id)
                    add_debug_message(f"Added employee_id filter: {normalized_id}")

                if start_date:
                    query += " AND pay_date >= ?"
                    params.append(start_date)
                    add_debug_message(f"Added start_date filter: {start_date}")

                if end_date:
                    query += " AND pay_date <= ?"
                    params.append(end_date)
                    add_debug_message(f"Added end_date filter: {end_date}")

                query += " ORDER BY pay_date DESC"
                add_debug_message(f"Final SQL query: {query}")
                add_debug_message(f"Query parameters: {params}")

                df = pd.read_sql(query, conn, params=params)
                conn.close()

                add_debug_message(f"SQL returned {len(df)} records")
                if not df.empty:
                    add_debug_message(f"SQL columns: {list(df.columns)}")
                    if debug_mode:
                        add_debug_message(f"First record: {dict(df.iloc[0])}")

                # Ensure employee_id column is normalized
                if 'employee_id' in df.columns:
                    df['employee_id'] = df['employee_id'].astype(str).str.replace(".0", "", regex=False)

                add_debug_message(f"Returning SQL data with {len(df)} records")
                return df

            else:
                add_debug_message("SQL connection failed (safe_get_conn returned None), falling back to CSV")

        except Exception as e:
            add_debug_message(f"SQL Error in get_salary_log: {e}")
            add_debug_message(f"Exception type: {type(e).__name__}")
            import traceback
            add_debug_message(f"Full traceback: {traceback.format_exc()}")

    # CSV fallback
    add_debug_message("Using CSV fallback")
    if os.path.exists(SALARY_LOG_CSV):
        add_debug_message(f"CSV file exists: {SALARY_LOG_CSV}")
        df = pd.read_csv(SALARY_LOG_CSV, dtype={"employee_id": str})
        add_debug_message(f"CSV loaded with {len(df)} records")

        # Normalize IDs in the DataFrame
        if 'employee_id' in df.columns:
            df['employee_id'] = df['employee_id'].astype(str).str.replace(".0", "", regex=False)

        if employee_id:
            normalized_id = str(int(float(employee_id)))
            df = df[df['employee_id'] == normalized_id]
            add_debug_message(f"After employee_id filter: {len(df)} records")

        if start_date or end_date:
            if 'pay_date' in df.columns:
                df['pay_date'] = pd.to_datetime(df['pay_date'], errors='coerce')
                if start_date:
                    df = df[df['pay_date'] >= pd.to_datetime(start_date)]
                if end_date:
                    df = df[df['pay_date'] <= pd.to_datetime(end_date)]
                add_debug_message(f"After date filter: {len(df)} records")

        result = df.sort_values('pay_date', ascending=False) if 'pay_date' in df.columns else df
        add_debug_message(f"Returning CSV data with {len(result)} records")
        return result
    else:
        add_debug_message(f"CSV file does not exist: {SALARY_LOG_CSV}")
        return pd.DataFrame(columns=[
            'employee_id', 'pay_date', 'basic_salary', 'allowances',
            'deductions', 'net_salary', 'pay_period'
        ])


def debug_salary_in_streamlit(employee_id):
    """Debug function specifically for Streamlit that shows what's happening"""
    try:
        import streamlit as st
    except ImportError:
        return "Streamlit not available for debugging"

    st.write("### 🐛 Detailed Salary Debug Information")

    if not employee_id:
        st.error("No employee_id provided")
        return

    st.write(f"**Employee ID:** {employee_id}")
    st.write(f"**USE_SQL setting:** {USE_SQL}")

    # Test SQL connection first
    if USE_SQL:
        try:
            conn = safe_get_conn()
            if conn:
                st.success("✅ SQL connection test successful")

                cursor = conn.cursor()

                # Check if table exists
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = '{SALARY_LOG_TABLE}'
                """)
                table_exists = cursor.fetchone()[0] > 0
                st.write(f"**Table '{SALARY_LOG_TABLE}' exists:** {'✅ Yes' if table_exists else '❌ No'}")

                if table_exists:
                    # Get total count
                    cursor.execute(f"SELECT COUNT(*) FROM {SALARY_LOG_TABLE}")
                    total_count = cursor.fetchone()[0]
                    st.write(f"**Total records in table:** {total_count}")

                    # Get count for this employee
                    cursor.execute(f"SELECT COUNT(*) FROM {SALARY_LOG_TABLE} WHERE employee_id = ?", [str(employee_id)])
                    emp_count = cursor.fetchone()[0]
                    st.write(f"**Records for employee {employee_id}:** {emp_count}")

                    # Show sample data structure
                    cursor.execute(f"SELECT TOP 1 * FROM {SALARY_LOG_TABLE}")
                    sample_row = cursor.fetchone()
                    if sample_row:
                        columns = [desc[0] for desc in cursor.description]
                        st.write("**Table structure:**")
                        for i, col in enumerate(columns):
                            st.write(f"  - {col}: {type(sample_row[i]).__name__}")

                    # Test the actual query that would be used
                    test_query = f"SELECT * FROM {SALARY_LOG_TABLE} WHERE employee_id = ? ORDER BY pay_date DESC"
                    cursor.execute(test_query, [str(employee_id)])
                    test_results = cursor.fetchall()
                    st.write(f"**Direct query result:** {len(test_results)} records")

                    if test_results:
                        st.write("**Sample direct query result:**")
                        sample_df = pd.DataFrame([test_results[0]], columns=columns)
                        st.dataframe(sample_df)

                conn.close()
            else:
                st.error("❌ SQL connection failed (safe_get_conn returned None)")
        except Exception as e:
            st.error(f"❌ SQL connection test failed: {e}")
            st.code(str(e))

    # Now test the actual function with debug mode
    st.write("### Testing get_salary_log function:")

    try:
        result_df = get_salary_log(employee_id, debug_mode=True)

        # Show debug messages
        debug_msgs = get_debug_messages()
        if debug_msgs:
            st.write("**Debug Messages:**")
            for msg in debug_msgs[-20:]:  # Show last 20 messages
                st.code(msg)

        # Show results
        st.write(f"**Function returned:** {len(result_df)} records")
        if not result_df.empty:
            st.write("**Returned columns:**", list(result_df.columns))
            st.write("**Sample returned data:**")
            st.dataframe(result_df.head(3))

            # Check if this looks like SQL or CSV data
            if len(debug_msgs) > 0:
                if any("SQL data" in msg for msg in debug_msgs):
                    st.success("✅ Data came from SQL")
                elif any("CSV data" in msg for msg in debug_msgs):
                    st.warning("⚠️ Data came from CSV (fallback)")
        else:
            st.warning("Function returned empty DataFrame")

    except Exception as e:
        st.error(f"Function test failed: {e}")
        import traceback
        st.code(traceback.format_exc())


def add_salary_record(salary_data):
    """Add salary record to SQL or CSV based on config"""
    if USE_SQL:
        try:
            conn = safe_get_conn()
            if conn:
                cursor = conn.cursor()
                insert_query = f"""
                INSERT INTO {SALARY_LOG_TABLE}
                (employee_id, pay_date, basic_salary, allowances, deductions, net_salary, pay_period)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(insert_query, [
                    str(salary_data['employee_id']),
                    safe_datetime_for_sql(salary_data.get('pay_date')),
                    safe_float(salary_data.get('basic_salary', 0)),
                    safe_float(salary_data.get('allowances', 0)),
                    safe_float(salary_data.get('deductions', 0)),
                    safe_float(salary_data.get('net_salary', 0)),
                    str(salary_data.get('pay_period', ''))
                ])
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            add_debug_message(f"SQL Error in add_salary_record: {e}")

    # CSV fallback
    try:
        df = get_salary_log()
        new_row = pd.DataFrame([salary_data])
        df = pd.concat([df, new_row], ignore_index=True)
        os.makedirs(os.path.dirname(SALARY_LOG_CSV), exist_ok=True)
        df.to_csv(SALARY_LOG_CSV, index=False)
        return True
    except Exception as e:
        add_debug_message(f"CSV Error in add_salary_record: {e}")
        return False


# ==================== FEEDBACK LOG ====================

def get_feedback_log(employee_id=None):
    """Get feedback log from SQL or CSV based on config"""
    if USE_SQL:
        try:
            conn = safe_get_conn()
            if conn:
                if employee_id:
                    query = f"SELECT * FROM {FEEDBACK_LOG_TABLE} WHERE employee_id = ? ORDER BY feedback_date DESC"
                    df = pd.read_sql(query, conn, params=[str(employee_id)])
                else:
                    query = f"SELECT * FROM {FEEDBACK_LOG_TABLE} ORDER BY feedback_date DESC"
                    df = pd.read_sql(query, conn)
                conn.close()
                return df
        except Exception as e:
            add_debug_message(f"SQL Error in get_feedback_log: {e}")

    # CSV fallback
    if os.path.exists(FEEDBACK_LOG_CSV):
        df = pd.read_csv(FEEDBACK_LOG_CSV, dtype={"employee_id": str})
        if employee_id:
            df = df[df['employee_id'] == str(employee_id)]
        return df.sort_values('feedback_date', ascending=False) if 'feedback_date' in df.columns else df
    else:
        return pd.DataFrame(columns=[
            'employee_id', 'feedback_date', 'feedback_type',
            'feedback_text', 'rating', 'reviewer'
        ])


def add_feedback(feedback_data):
    """Add feedback record to SQL or CSV based on config"""
    if USE_SQL:
        try:
            conn = safe_get_conn()
            if conn:
                cursor = conn.cursor()
                insert_query = f"""
                INSERT INTO {FEEDBACK_LOG_TABLE}
                (employee_id, feedback_date, feedback_type, feedback_text, rating, reviewer)
                VALUES (?, ?, ?, ?, ?, ?)
                """
                cursor.execute(insert_query, [
                    str(feedback_data['employee_id']),
                    safe_datetime_for_sql(feedback_data.get('feedback_date', datetime.now())),
                    str(feedback_data.get('feedback_type', '')),
                    str(feedback_data.get('feedback_text', '')),
                    safe_float(feedback_data.get('rating', 0)),
                    str(feedback_data.get('reviewer', ''))
                ])
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            add_debug_message(f"SQL Error in add_feedback: {e}")

    # CSV fallback
    try:
        df = get_feedback_log()
        new_row = pd.DataFrame([feedback_data])
        df = pd.concat([df, new_row], ignore_index=True)
        os.makedirs(os.path.dirname(FEEDBACK_LOG_CSV), exist_ok=True)
        df.to_csv(FEEDBACK_LOG_CSV, index=False)
        return True
    except Exception as e:
        add_debug_message(f"CSV Error in add_feedback: {e}")
        return False


# ==================== RESIGNATION LOG ====================

def get_resignation_data():
    """Load resignation records from SQL or CSV"""
    try:
        if USE_SQL:
            try:
                conn = safe_get_conn()
                if conn:
                    query = f"SELECT * FROM {RESIGNATION_LOG_TABLE} ORDER BY resignation_date DESC"
                    df = pd.read_sql(query, conn)
                    conn.close()

                    # Ensure correct dtypes based on your SQL table
                    for col in ["employee_id", "employee_name", "department", "status", "complied_notice"]:
                        if col in df.columns:
                            df[col] = df[col].astype(str)

                    for date_col in ["resignation_date", "notice_issued_date"]:
                        if date_col in df.columns:
                            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

                    if "notice_period_days" in df.columns:
                        df["notice_period_days"] = pd.to_numeric(df["notice_period_days"], errors="coerce").fillna(
                            30).astype(int)

                    if "admin_cleared" in df.columns:
                        df["admin_cleared"] = df["admin_cleared"].astype(bool)

                    return df
            except Exception as e:
                add_debug_message(f"SQL Error in get_resignation_data: {e}")

        # CSV fallback
        if os.path.exists(RESIGNATION_LOG_CSV):
            df = pd.read_csv(RESIGNATION_LOG_CSV, dtype={"employee_id": str})

            # Ensure correct dtypes
            for col in ["employee_id", "employee_name", "department", "status", "complied_notice"]:
                if col in df.columns:
                    df[col] = df[col].astype(str)

            for date_col in ["resignation_date", "notice_issued_date"]:
                if date_col in df.columns:
                    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

            if "notice_period_days" in df.columns:
                df["notice_period_days"] = pd.to_numeric(df["notice_period_days"], errors="coerce").fillna(30).astype(
                    int)

            if "admin_cleared" in df.columns:
                df["admin_cleared"] = df["admin_cleared"].astype(bool)

            return df.sort_values('resignation_date', ascending=False) if 'resignation_date' in df.columns else df

        # Return empty DataFrame with columns matching your SQL table
        return pd.DataFrame(columns=[
            "employee_id", "employee_name", "department", "notice_issued_date",
            "notice_period_days", "resignation_date", "status", "complied_notice", "admin_cleared"
        ])

    except Exception as e:
        add_debug_message(f"Error loading resignation data: {e}")
        return pd.DataFrame(columns=[
            "employee_id", "employee_name", "department", "notice_issued_date",
            "notice_period_days", "resignation_date", "status", "complied_notice", "admin_cleared"
        ])


def add_resignation_record(resignation_data):
    """Add resignation record to SQL or CSV based on config"""
    if USE_SQL:
        try:
            conn = safe_get_conn()
            if conn:
                cursor = conn.cursor()
                insert_query = f"""
                INSERT INTO {RESIGNATION_LOG_TABLE}
                (employee_id, employee_name, department, notice_issued_date, notice_period_days,
                 resignation_date, status, complied_notice, admin_cleared)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(insert_query, [
                    str(resignation_data['employee_id']),
                    str(resignation_data.get('employee_name', '')),
                    str(resignation_data.get('department', '')),
                    safe_datetime_for_sql(resignation_data.get('notice_issued_date')),
                    int(resignation_data.get('notice_period_days', 30)),
                    safe_datetime_for_sql(resignation_data.get('resignation_date')),
                    str(resignation_data.get('status', 'pending')),
                    str(resignation_data.get('complied_notice', '')),
                    bool(resignation_data.get('admin_cleared', False))
                ])
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            print(f"SQL Error in add_resignation_record: {e}")

    # CSV fallback
    try:
        df = get_resignation_data()
        new_row = pd.DataFrame([resignation_data])
        df = pd.concat([df, new_row], ignore_index=True)
        os.makedirs(os.path.dirname(RESIGNATION_LOG_CSV), exist_ok=True)
        df.to_csv(RESIGNATION_LOG_CSV, index=False)
        return True
    except Exception as e:
        print(f"CSV Error in add_resignation_record: {e}")
        return False


def update_resignation_status(employee_id, new_status, admin_cleared=None):
    """Update resignation status for an employee"""
    if USE_SQL:
        try:
            conn = safe_get_conn()
            if conn:
                cursor = conn.cursor()
                if admin_cleared is not None:
                    update_query = f"""
                    UPDATE {RESIGNATION_LOG_TABLE} 
                    SET status = ?, admin_cleared = ? 
                    WHERE employee_id = ?
                    """
                    cursor.execute(update_query, [new_status, bool(admin_cleared), str(employee_id)])
                else:
                    update_query = f"""
                    UPDATE {RESIGNATION_LOG_TABLE} 
                    SET status = ? 
                    WHERE employee_id = ?
                    """
                    cursor.execute(update_query, [new_status, str(employee_id)])
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            print(f"SQL Error in update_resignation_status: {e}")

    # CSV fallback
    try:
        df = get_resignation_data()
        mask = df['employee_id'] == str(employee_id)
        if mask.any():
            df.loc[mask, 'status'] = new_status
            if admin_cleared is not None:
                df.loc[mask, 'admin_cleared'] = bool(admin_cleared)
            df.to_csv(RESIGNATION_LOG_CSV, index=False)
            return True
        return False
    except Exception as e:
        print(f"CSV Error in update_resignation_status: {e}")
        return False


def update_resignation_compliance(employee_id, complied_notice):
    """Update resignation notice compliance for an employee"""
    if USE_SQL:
        try:
            conn = safe_get_conn()
            if conn:
                cursor = conn.cursor()
                update_query = f"""
                UPDATE {RESIGNATION_LOG_TABLE} 
                SET complied_notice = ? 
                WHERE employee_id = ?
                """
                cursor.execute(update_query, [str(complied_notice), str(employee_id)])
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            print(f"SQL Error in update_resignation_compliance: {e}")

    # CSV fallback
    try:
        df = get_resignation_data()
        mask = df['employee_id'] == str(employee_id)
        if mask.any():
            df.loc[mask, 'complied_notice'] = str(complied_notice)
            df.to_csv(RESIGNATION_LOG_CSV, index=False)
            return True
        return False
    except Exception as e:
        print(f"CSV Error in update_resignation_compliance: {e}")
        return False


def get_resignation_by_employee(employee_id):
    """Get resignation record for a specific employee"""
    try:
        df = get_resignation_data()
        return df[df['employee_id'] == str(employee_id)]
    except Exception as e:
        print(f"Error getting resignation for employee {employee_id}: {e}")
        return pd.DataFrame()


def get_resignations_by_date_range(start_date, end_date):
    """Get resignations within a specific date range"""
    try:
        df = get_resignation_data()
        if 'resignation_date' in df.columns:
            df['resignation_date'] = pd.to_datetime(df['resignation_date'])
            mask = (df['resignation_date'] >= pd.to_datetime(start_date)) & \
                   (df['resignation_date'] <= pd.to_datetime(end_date))
            return df[mask]
        return pd.DataFrame()
    except Exception as e:
        print(f"Error getting resignations by date range: {e}")
        return pd.DataFrame()


def get_urgent_resignations(days=7):
    """Get resignations happening within specified days"""
    try:
        df = get_resignation_data()
        if 'resignation_date' in df.columns and not df.empty:
            df['resignation_date'] = pd.to_datetime(df['resignation_date'])
            today = pd.Timestamp.today()
            future_date = today + pd.Timedelta(days=days)

            mask = (df['resignation_date'] >= today) & \
                   (df['resignation_date'] <= future_date) & \
                   (df['status'] != 'exited')
            return df[mask]
        return pd.DataFrame()
    except Exception as e:
        print(f"Error getting urgent resignations: {e}")
        return pd.DataFrame()


def get_department_resignation_stats():
    """Get resignation statistics by department"""
    try:
        df = get_resignation_data()
        if df.empty:
            return pd.DataFrame()

        stats = df.groupby('department').agg({
            'employee_id': 'count',
            'resignation_date': ['min', 'max'],
            'notice_period_days': 'mean'
        }).round(2)

        stats.columns = ['Total_Resignations', 'First_Resignation', 'Last_Resignation', 'Avg_Notice_Days']
        return stats.reset_index()
    except Exception as e:
        print(f"Error getting department resignation stats: {e}")
        return pd.DataFrame()


# ==================== VERIFIED ADMINS ====================

def get_verified_admins():
    """Get verified admins from SQL or CSV based on config"""
    if USE_SQL:
        try:
            conn = safe_get_conn()
            if conn:
                query = f"SELECT * FROM {VERIFIED_ADMIN_TABLE}"
                df = pd.read_sql(query, conn)
                conn.close()
                return df
        except Exception as e:
            print(f"SQL Error in get_verified_admins: {e}")

    # CSV fallback
    if os.path.exists(VERIFIED_ADMINS_CSV):
        return pd.read_csv(VERIFIED_ADMINS_CSV)
    else:
        return pd.DataFrame(columns=['admin_user', 'admin_role', 'permissions'])


# ==================== UTILITY FUNCTIONS ====================

def get_data_source_info():
    """Get information about current data source"""
    return {
        'using_sql': USE_SQL,
        'data_source': 'SQL Server' if USE_SQL else 'CSV Files',
        'sql_available': bool(safe_get_conn()) if USE_SQL else False
    }


def test_data_connection():
    """Test the current data connection"""
    if USE_SQL:
        try:
            conn = safe_get_conn()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                conn.close()
                return True, "SQL connection successful"
        except Exception as e:
            return False, f"SQL connection failed: {e}"
    else:
        # Test CSV directory access
        try:
            csv_dir = os.path.dirname(EMPLOYEE_MASTER_CSV)
            if os.path.exists(csv_dir) or os.access(os.path.dirname(csv_dir), os.W_OK):
                return True, "CSV directory accessible"
            else:
                return False, "CSV directory not accessible"
        except Exception as e:
            return False, f"CSV access error: {e}"


def backup_data_to_csv():
    """Backup all SQL data to CSV files (useful for migrations or backups)"""
    if not USE_SQL:
        return False, "Not using SQL - no backup needed"

    try:
        # Backup employee master
        emp_master = get_employee_master()
        if not emp_master.empty:
            os.makedirs(os.path.dirname(EMPLOYEE_MASTER_CSV), exist_ok=True)
            emp_master.to_csv(EMPLOYEE_MASTER_CSV, index=False)

        # Backup employee data
        emp_data = get_employee_data()
        if not emp_data.empty:
            os.makedirs(os.path.dirname(EMPLOYEE_DATA_CSV), exist_ok=True)
            emp_data.to_csv(EMPLOYEE_DATA_CSV, index=False)

        # Backup salary log
        salary_log = get_salary_log()
        if not salary_log.empty:
            os.makedirs(os.path.dirname(SALARY_LOG_CSV), exist_ok=True)
            salary_log.to_csv(SALARY_LOG_CSV, index=False)

        # Backup feedback log
        feedback_log = get_feedback_log()
        if not feedback_log.empty:
            os.makedirs(os.path.dirname(FEEDBACK_LOG_CSV), exist_ok=True)
            feedback_log.to_csv(FEEDBACK_LOG_CSV, index=False)

        # Backup resignation log
        resignation_log = get_resignation_data()
        if not resignation_log.empty:
            os.makedirs(os.path.dirname(RESIGNATION_LOG_CSV), exist_ok=True)
            resignation_log.to_csv(RESIGNATION_LOG_CSV, index=False)

        # Backup verified admins
        verified_admins = get_verified_admins()
        if not verified_admins.empty:
            os.makedirs(os.path.dirname(VERIFIED_ADMINS_CSV), exist_ok=True)
            verified_admins.to_csv(VERIFIED_ADMINS_CSV, index=False)

        return True, "All data backed up to CSV successfully"
    except Exception as e:
        return False, f"Backup failed: {e}"


def get_system_stats():
    """Get overall system statistics"""
    try:
        stats = {
            'data_source': 'SQL Server' if USE_SQL else 'CSV Files',
            'total_employees': len(get_employee_master()),
            'total_resignations': len(get_resignation_data()),
            'urgent_resignations': len(get_urgent_resignations()),
            'total_feedback_records': len(get_feedback_log()),
            'total_salary_records': len(get_salary_log()),
            'connection_status': test_data_connection()[0]
        }
        return stats
    except Exception as e:
        print(f"Error getting system stats: {e}")
        return {}