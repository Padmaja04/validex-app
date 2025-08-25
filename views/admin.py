import streamlit as st
from views import manual_entry, payroll, bulkpayslip, feedbackcenter, adminaudit
from views import companyinsights, predictivealerts, resignation, leavevisualizer, analytics, appraisal_analytics, \
    appraisal_audit_log1
from data_utils import (
    get_employee_master, get_employee_data, get_feedback_log, get_data_source_info,
    test_data_connection
)
import pandas as pd
from datetime import datetime,timedelta
from data_utils import get_resignation_data
from data_utils import get_salary_log
from employee_qr_generator import display_employee_qr_interface

def run_dashboard(view, admin_name=None):
    """Main admin dashboard router that handles all admin views"""
    # Show data source status at the top
    data_info = get_data_source_info()
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col2:
            if data_info['using_sql']:
                if data_info['sql_available']:
                    st.success(f"🗄️ SQL Connected")
                else:
                    st.error(f"🗄️ SQL Error")
            else:
                st.info(f"📁 Using CSV")
    # Add to your existing sidebar
    page = st.sidebar.selectbox("Select a page:",
                                ["Dashboard", "Attendance", "Payroll", "QR Generator"])
    if page == "QR Generator":
        display_employee_qr_interface()
    # Route to appropriate view
    if view == "manual":
        st.title("📝 Manual Entry")
        st.write("Admin attendance input panel.")
        manual_entry.run_manual_entry(admin_name=admin_name)

    elif view == "payroll":
        st.title("💼 Payroll Management")
        st.write("Manage payroll records and generate salaries.")
        payroll.run_payroll()

    elif view == "appraisal_analytics":
        st.title("📈 Appraisal Trends & Insights")
        st.write("Analyze performance ratings, salary hike distributions, and reviewer patterns.")
        appraisal_analytics.run_appraisal_analytics()

    elif view == "appraisal_audit_log1":
        st.title("🧮 Appraisal Audit Alert")
        st.write("Analyze performance ratings, salary hike distributions, and reviewer patterns.")
        appraisal_audit_log1.run_appraisal_audit_log1()

    elif view == "bulkpayslip":
        st.title("📂 Bulk Payslip Generator")
        st.write("Generate payslips for all employees.")
        bulkpayslip.run_bulkpayslip()

    elif view == "feedbackcenter":
        st.title("🛎️ Feedback Center")
        st.write("Review and respond to employee feedback.")
        feedbackcenter.run_feedbackcenter()

    elif view == "adminaudit":
        st.title("🧮 Audit Alerts")
        st.write("Detect inconsistencies, duplicates, or missing entries.")
        adminaudit.run_adminaudit()

    elif view == "companyinsights":
        st.title("📊 Company Insights")
        st.write("Visualize HR metrics across headcount, trends, and attrition.")
        companyinsights.run_companyinsights()

    elif view == "predictivealerts":
        st.title("🤖 Predictive Alerts")
        st.write("View machine-driven forecasts like attrition risk.")
        predictivealerts.run_predictivealerts()

    elif view == "resignation":
        st.title("🧾 Resignation Panel")
        st.write("Approve or track employee resignations and clearance.")
        resignation.run_resignation()

    elif view == "leavevisualizer":
        st.title("📅 Leave Visualizer")
        st.write("See leave patterns across teams.")
        leavevisualizer.run_leavevisualizer()

    elif view == "analytics":
        st.title("📊 Analytics Dashboard")
        st.write("Comprehensive analytics and reporting.")
        analytics.run_analytics()

    else:
        # Default dashboard with overview
        show_admin_overview(admin_name)

def show_admin_overview(admin_name=None):
    """Show admin overview dashboard with key metrics"""
    st.title("🛠️ Admin Dashboard")

    if admin_name:
        st.write(f"Welcome back, **{admin_name}**!")

    # Test data connection
    connection_status, connection_msg = test_data_connection()
    if connection_status:
        st.success(f"✅ {connection_msg}")
    else:
        st.error(f"❌ {connection_msg}")

    # Load data for overview
    try:
        # Employee master overview
        employee_df = get_employee_master()
        if not employee_df.empty:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                total_employees = len(employee_df)
                st.metric("👥 Total Employees", total_employees)

            with col2:
                active_employees = len(employee_df[employee_df.get('status',
                                                                   'Active') == 'Active']) if 'status' in employee_df.columns else total_employees
                st.metric("✅ Active Employees", active_employees)

            with col3:
                if 'department' in employee_df.columns:
                    departments = employee_df['department'].nunique()
                    st.metric("🏢 Departments", departments)
                else:
                    st.metric("🏢 Departments", "N/A")

            with col4:
                salary_df = get_salary_log()
                if 'base_salary' in salary_df.columns:
                    avg_salary = salary_df['base_salary'].mean()
                    if pd.notna(avg_salary):
                        st.metric("💰 Avg Base Salary", f"₹{avg_salary:,.0f}")
                    else:
                        st.metric("💰 Avg Base Salary", "N/A")
                else:
                    st.metric("💰 Avg Base Salary", "N/A")
        # 🔔 Payroll Reminder Section
        st.subheader("⏰ Payroll Reminder")
        today = datetime.today().date()
        fifteenth = today.replace(day=15)
        last_day = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

        if today == fifteenth or today == last_day:
            st.warning("⚠️ Today is a scheduled payroll update day. Please update payroll records.")
        elif today < fifteenth:
            st.info(f"Next payroll update is due on **{fifteenth.strftime('%d %b %Y')}**.")
        else:
            st.info(f"Next payroll update is due on **{last_day.strftime('%d %b %Y')}**.")

        # Recent activity
        st.subheader("📊 Quick Stats")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📈 Employee Distribution")
            if not employee_df.empty and 'department' in employee_df.columns:
                dept_counts = employee_df['department'].value_counts()
                st.bar_chart(dept_counts)
            else:
                st.info("No department data available")

        with col2:
            st.markdown("### 💬 Recent Feedback")
            try:
                feedback_df = get_feedback_log()
                feedback_df = feedback_df.sort_values(by="timestamp", ascending=False)
                if feedback_df is not None and not feedback_df.empty:
                    recent_feedback = feedback_df.head(5)
                    for _, feedback in recent_feedback.iterrows():
                        emp_name = feedback['employee_name'] if 'employee_name' in feedback else 'N/A'
                        desc = feedback['description'] if 'description' in feedback else 'No description'
                        st.write(f"**{emp_name}**: {desc[:50]}...")
                else:
                    st.info("No feedback data available")
            except Exception as e:
                st.warning(f"Could not load feedback data: {e}")

        # 🔹 Urgent Resignation Section
        st.subheader("🚨 Urgent Resignations")
        try:
            resignation_df = get_resignation_data()  # from resignation.py

            if isinstance(resignation_df, pd.DataFrame) and not resignation_df.empty:
                # Treat 'pending' status as urgent
                status_series = resignation_df.get(
                    'status',
                    pd.Series('', index=resignation_df.index, dtype='object')
                ).astype(str).str.strip().str.lower()

                urgent_df = resignation_df[status_series.eq('pending')].copy()

                if not urgent_df.empty:
                    st.warning(f"{len(urgent_df)} urgent resignation(s) require immediate action")

                    # Only show columns that exist
                    display_cols = [c for c in [
                        'employee_id', 'employee_name', 'department',
                        'notice_issued_date', 'resignation_date', 'status', 'complied_notice'
                    ] if c in urgent_df.columns]

                    st.dataframe(
                        urgent_df[display_cols] if display_cols else urgent_df,
                        use_container_width=True
                    )
                else:
                    st.success("No urgent resignations at the moment")
            else:
                st.info("No resignation data available")

        except Exception as e:
            st.error(f"Could not load resignation data: {e}")
    except Exception as e:
        st.error(f"Error loading dashboard data: {e}")
        st.info("Please check your data configuration and connection.")

    # Data source information
    st.subheader("🔧 System Information")
    data_info = get_data_source_info()

    info_col1, info_col2 = st.columns(2)

    with info_col1:
        st.write(f"**Data Source**: {data_info['data_source']}")
        st.write(f"**Using SQL**: {data_info['using_sql']}")
        if data_info['using_sql']:
            st.write(f"**SQL Available**: {data_info['sql_available']}")

    with info_col2:
        if st.button("🔄 Test Connection"):
            status, msg = test_data_connection()
            if status:
                st.success(msg)
            else:
                st.error(msg)

def get_admin_stats():
    """Get administrative statistics for dashboard"""
    stats = {}

    try:
        # Employee stats
        employee_df = get_employee_master()
        stats['total_employees'] = len(employee_df) if not employee_df.empty else 0

        if not employee_df.empty and 'status' in employee_df.columns:
            stats['active_employees'] = len(employee_df[employee_df['status'] == 'Active'])
        else:
            stats['active_employees'] = stats['total_employees']

        # Salary stats
        salary_df = get_salary_log()
        stats['total_payroll_records'] = len(salary_df) if not salary_df.empty else 0

        # Feedback stats
        feedback_df = get_feedback_log()
        stats['total_feedback'] = len(feedback_df) if not feedback_df.empty else 0

    except Exception as e:
        st.error(f"Error calculating stats: {e}")
        stats = {
            'total_employees': 0,
            'active_employees': 0,
            'total_payroll_records': 0,
            'total_feedback': 0
        }

    return stats


# Utility functions for admin operations
def search_employee(search_term):
    """Search for employees by name or ID"""
    try:
        employee_df = get_employee_master()
        if employee_df.empty:
            return pd.DataFrame()

        search_term = search_term.lower().strip()

        # Search in employee_id and employee_name columns
        mask = (
            employee_df['employee_id'].astype(str).str.lower().str.contains(search_term, na=False) |
            employee_df['employee_name'].astype(str).str.lower().str.contains(search_term, na=False)
        )

        return employee_df[mask]

    except Exception as e:
        st.error(f"Error searching employees: {e}")
        return pd.DataFrame()


def get_employee_summary(employee_id):
    """Get comprehensive summary for a specific employee"""
    try:
        # Basic info
        employee_df = get_employee_master()
        employee_info = employee_df[employee_df['employee_id'] == str(employee_id)]

        if employee_info.empty:
            return None

        # Additional data
        employee_data = get_employee_data(employee_id)
        salary_data = get_salary_log(employee_id)
        feedback_data = get_feedback_log(employee_id)

        summary = {
            'basic_info': employee_info.iloc[0].to_dict(),
            'attendance_records': len(employee_data),
            'salary_records': len(salary_data),
            'feedback_count': len(feedback_data),
            'latest_salary': salary_data.iloc[0]['net_salary'] if not salary_data.empty else None,
            'avg_performance': employee_data[
                'performance_score'].mean() if not employee_data.empty and 'performance_score' in employee_data.columns else None
        }

        return summary

    except Exception as e:
        st.error(f"Error getting employee summary: {e}")
        return None