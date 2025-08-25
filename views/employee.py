import streamlit as st
from views import attendance, mypayslip, leavevisualizer, feedbackcenter, resignation
from views import hr_assistant  # Import the existing HR assistant module
from data_utils import (
    get_employee_master, get_employee_data, get_salary_log,
    get_feedback_log, get_data_source_info, test_data_connection
)
import pandas as pd
from datetime import datetime, timedelta


def run_dashboard(view):
    """
    Main employee dashboard router that handles all employee views
    Integrates with both SQL and CSV data sources based on config
    """
    data_info = get_data_source_info()
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col2:
            if data_info.get('using_sql'):
                if data_info.get('sql_available'):
                    st.success("🗄️ SQL Connected")
                else:
                    st.error("🗄️ SQL Error")
            else:
                st.info("📁 Using CSV")

    # Route to appropriate view
    if view == "attendance":
        st.title("📝 Attendance")
        st.write("Employee attendance input panel.")
        attendance.run_attendance()

    elif view == "mypayslip":
        st.title("💰 My Payslip")
        mypayslip.run_mypayslip()

    elif view == "leavevisualizer":
        st.title("📅 Leave Visualizer")
        leavevisualizer.run_leavevisualizer()

    elif view == "feedbackcenter":
        st.title("📣 Feedback Center")
        feedbackcenter.run_feedbackcenter()

    elif view == "resignation":
        st.title("🧾 Resignation Request")
        resignation.run_resignation()

    elif view == "hr_assistant":
        st.title("💬 HR Assistant")
        hr_assistant.run_hr_assistant()

    else:
        # Default employee overview (includes the HR assistant panel at the bottom)
        show_employee_overview()


def show_employee_overview():
    """
    Show employee overview dashboard with personal metrics
    Works with both SQL and CSV data sources
    """
    st.title("👤 Employee Dashboard")

    employee_name = st.session_state.get("employee_name", "Employee")
    employee_id = st.session_state.get("employee_id", None)

    st.write(f"Welcome back, **{employee_name}**!")

    # Show data source and connection status
    data_info = get_data_source_info()
    connection_status, connection_msg = test_data_connection()

    col1, col2 = st.columns([2, 1])
    with col1:
        if connection_status:
            st.success(f"✅ {connection_msg}")
        else:
            st.error(f"❌ {connection_msg}")
    with col2:
        st.info(f"📊 Data Source: {data_info.get('data_source', 'Unknown')}")

    if not employee_id:
        st.warning("⚠️ Employee ID not found in session. Please login again.")
        return

    try:
        # Personal info
        employee_df = get_employee_master()
        if not employee_df.empty:
            # Normalize employee_id for comparison
            employee_df['employee_id'] = employee_df['employee_id'].astype(str)
            employee_info = employee_df[employee_df['employee_id'] == str(employee_id)]

            if not employee_info.empty:
                emp_data = employee_info.iloc[0]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("👤 Employee ID", emp_data.get('employee_id', 'N/A'))
                with col2:
                    st.metric("🏢 Department", emp_data.get('department', 'N/A'))
                with col3:
                    st.metric("💼 Position", emp_data.get('role', emp_data.get('position', 'N/A')))

        # Quick stats
        st.subheader("📊 Your Quick Stats")
        col1, col2, col3, col4 = st.columns(4)

        # Attendance count
        with col1:
            try:
                attendance_df = get_employee_data(employee_id)
                attendance_count = len(attendance_df) if not attendance_df.empty else 0
                st.metric("📅 Attendance Records", attendance_count)
            except Exception as e:
                st.metric("📅 Attendance Records", "N/A")
                st.caption(f"Error: {str(e)[:30]}...")

        # Payslip count
        with col2:
            try:
                salary_df = get_salary_log(employee_id)
                salary_count = len(salary_df) if not salary_df.empty else 0
                st.metric("💰 Payslip Records", salary_count)
            except Exception as e:
                st.metric("💰 Payslip Records", "N/A")
                st.caption(f"Error: {str(e)[:30]}...")

        # Feedback count
        with col3:
            try:
                all_feedback = get_feedback_log()
                feedback_count = 0

                if not all_feedback.empty:
                    if 'employee_name' in all_feedback.columns:
                        # Filter by employee name
                        current_employee_name = st.session_state.get("employee_name", "").lower().strip()
                        if current_employee_name:
                            all_feedback['employee_name_lower'] = all_feedback['employee_name'].astype(
                                str).str.lower().str.strip()
                            employee_feedback = all_feedback[
                                all_feedback['employee_name_lower'] == current_employee_name]
                            feedback_count = len(employee_feedback)
                    elif 'employee_id' in all_feedback.columns:
                        # Filter by employee ID
                        all_feedback['employee_id'] = all_feedback['employee_id'].astype(str)
                        employee_feedback = all_feedback[all_feedback['employee_id'] == str(employee_id)]
                        feedback_count = len(employee_feedback)

                st.metric("💬 Feedback Count", feedback_count)
            except Exception as e:
                st.metric("💬 Feedback Count", "N/A")
                st.caption(f"Error: {str(e)[:30]}...")

        # Latest salary - FIXED VERSION
        with col4:
            try:
                # Get salary data using the data_utils function
                salary_df = get_salary_log(employee_id)

                if salary_df is None or salary_df.empty:
                    st.metric("💵 Latest Salary", "No Records")
                    st.caption("No salary data found")
                else:
                    # Debug info for troubleshooting
                    if st.session_state.get('debug_mode', False):
                        st.caption(f"Found {len(salary_df)} salary records")
                        st.caption(f"Data source: {data_info.get('data_source')}")

                    # Ensure proper column formatting
                    salary_df.columns = salary_df.columns.str.strip().str.lower()

                    # Sort by date if available
                    date_columns = ['salary_month', 'pay_date', 'date']
                    date_col = None
                    for col in date_columns:
                        if col in salary_df.columns:
                            date_col = col
                            break

                    if date_col:
                        try:
                            salary_df[date_col] = pd.to_datetime(salary_df[date_col], errors="coerce")
                            salary_df = salary_df.sort_values(by=date_col, ascending=False)
                        except:
                            pass  # If date sorting fails, use original order

                    # Get the latest salary
                    latest_record = salary_df.iloc[0]

                    # Try different possible column names for net salary
                    salary_columns = ['net_salary', 'total_salary', 'salary', 'net_pay', 'final_amount']
                    net_salary = None

                    for col in salary_columns:
                        if col in latest_record.index:
                            try:
                                net_salary = pd.to_numeric(latest_record[col], errors="coerce")
                                if pd.notna(net_salary):
                                    break
                            except:
                                continue

                    if net_salary is not None and pd.notna(net_salary):
                        st.metric("💵 Latest Salary", f"₹{net_salary:,.0f}")
                        if date_col and pd.notna(latest_record[date_col]):
                            st.caption(
                                f"For {latest_record[date_col].strftime('%b %Y') if hasattr(latest_record[date_col], 'strftime') else latest_record[date_col]}")
                    else:
                        st.metric("💵 Latest Salary", "N/A")
                        st.caption("Salary data incomplete")

            except Exception as e:
                st.metric("💵 Latest Salary", "Error")
                st.caption(f"Error: {str(e)[:30]}...")

        # Recent activity
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 Recent Attendance")
            try:
                attendance_df = get_employee_data(employee_id)
                if not attendance_df.empty:
                    # Sort by date if available
                    date_columns = ['date', 'date_only', 'attendance_date']
                    for date_col in date_columns:
                        if date_col in attendance_df.columns:
                            try:
                                attendance_df[date_col] = pd.to_datetime(attendance_df[date_col], errors='coerce')
                                attendance_df = attendance_df.sort_values(date_col, ascending=False)
                                break
                            except:
                                continue

                    recent_attendance = attendance_df.head(5).copy()

                    for _, record in recent_attendance.iterrows():
                        # Get date
                        date_str = "N/A"
                        for date_col in date_columns:
                            if date_col in record.index and pd.notna(record[date_col]):
                                if hasattr(record[date_col], 'strftime'):
                                    date_str = record[date_col].strftime('%Y-%m-%d')
                                else:
                                    date_str = str(record[date_col])[:10]
                                break

                        status = record.get('attendance_status', record.get('status', 'N/A'))
                        hours = record.get('total_hours', record.get('hours_worked', 0))

                        st.write(f"**{date_str}**: {status} ({hours}h)")
                else:
                    st.info("No attendance records found")
            except Exception as e:
                st.warning(f"Could not load attendance data: {e}")

        with col2:
            st.subheader("💬 Recent Feedback")
            try:
                all_feedback = get_feedback_log()
                if not all_feedback.empty:
                    # Try to filter feedback for current employee
                    employee_feedback = pd.DataFrame()

                    if 'employee_name' in all_feedback.columns:
                        current_employee_name = st.session_state.get("employee_name", "").lower().strip()
                        if current_employee_name:
                            all_feedback['employee_name_lower'] = all_feedback['employee_name'].astype(
                                str).str.lower().str.strip()
                            employee_feedback = all_feedback[
                                all_feedback['employee_name_lower'] == current_employee_name]
                    elif 'employee_id' in all_feedback.columns:
                        all_feedback['employee_id'] = all_feedback['employee_id'].astype(str)
                        employee_feedback = all_feedback[all_feedback['employee_id'] == str(employee_id)]

                    if not employee_feedback.empty:
                        recent_feedback = employee_feedback.head(5)
                        for _, fb in recent_feedback.iterrows():
                            issue_type = fb.get('issue_type', fb.get('feedback_type', 'General'))
                            status = fb.get('status', 'N/A')
                            description = str(fb.get('description', fb.get('feedback_text', 'No description')))[:50]
                            date = fb.get('related_date', fb.get('feedback_date', 'N/A'))

                            st.write(f"**{issue_type}** ({status}) - {date}")
                            st.write(f"📝 {description}...")
                            st.write("---")
                    else:
                        st.info("No feedback records found for your account")
                else:
                    st.info("No feedback records found")
            except Exception as e:
                st.warning(f"Could not load feedback data: {e}")

        # Performance summary
        st.subheader("📊 Performance Summary")
        try:
            attendance_df = get_employee_data(employee_id)
            if not attendance_df.empty and 'performance_score' in attendance_df.columns:
                performance_scores = pd.to_numeric(attendance_df['performance_score'], errors='coerce')
                performance_scores = performance_scores.dropna()

                if len(performance_scores) > 0:
                    avg_performance = performance_scores.mean()
                    st.progress(min(max(avg_performance / 10.0, 0), 1))
                    st.write(f"Average Performance Score: **{avg_performance:.2f}/10**")
                else:
                    st.info("No performance data available")
            else:
                st.info("No performance data available")
        except Exception as e:
            st.warning(f"Could not load performance data: {e}")

    except Exception as e:
        st.error(f"Error loading dashboard data: {e}")
        st.info("Please check your data configuration and connection.")

    # System information
    st.subheader("🔧 System Information")
    data_info = get_data_source_info()
    info_col1, info_col2 = st.columns(2)

    with info_col1:
        st.write(f"**Data Source**: {data_info.get('data_source')}")
        st.write(f"**Employee ID**: {employee_id}")
        st.write(f"**SQL Status**: {'Connected' if data_info.get('sql_available') else 'Disconnected'}")

    with info_col2:
        if st.button("🔄 Refresh Data"):
            st.rerun()
        if st.button("🐛 Toggle Debug Mode"):
            st.session_state['debug_mode'] = not st.session_state.get('debug_mode', False)
            st.rerun()

    # HR Assistant panel (always available on the overview)
    st.markdown("---")
    with st.expander("💬 HR Assistant", expanded=False):
        hr_assistant.run_hr_assistant()