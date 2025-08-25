import streamlit as st
import time
from datetime import datetime, timedelta
import os

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="shri swami samarth pvt.ltd | Secure Login", layout="wide")

# ---------- SESSION INIT ----------
for key, val in {
    "login_phase": "initial",
    "session_expiry": None,
    "active_view": None
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ---------- SESSION EXPIRY CHECK ----------
if st.session_state.session_expiry and datetime.now() > st.session_state.session_expiry:
    for k in ["login_phase", "user_role", "employee_name", "username", "session_expiry", "active_view"]:
        st.session_state.pop(k, None)
    st.warning("⏳ Session expired. Please log in again.")
    st.rerun()

# ---------- CREDENTIALS ----------
credentials = {
    "admin_user": {"password": "adminuser", "role": "admin", "name": "Admin Padmaja"},
    "employee_user": {"password": "employeepass", "role": "employee", "name": "Padmaja"},
    "rahul_user": {"password": "rahul123", "role": "employee", "name": "Rahul"}
}

# ---------- PAGE FUNCTIONS ----------
def show_manual_entry():
    st.title("📝 Manual Entry")
    st.write("Admin attendance input panel.")

def show_feedbackcenter():
    st.title("🛎️ Admin Feedback")
    st.write("Review feedback submitted by employees.")

def show_payroll():
    st.title("💼 Payroll Management")
    st.write("Manage payroll records here.")

def show_attendance():
    st.title("📊 Attendance")
    st.write("Your attendance summary.")

def show_payslip():
    st.title("💰 Payslip")
    st.write("View your salary breakdown.")

def show_feedback_employee():
    st.title("📣 Feedback Center")
    st.write("Submit feedback to HR.")

# ---------- LOGIN UI ----------
if st.session_state.login_phase == "initial":
    st.markdown("""
        <style>
        [data-testid="stSidebarNav"], [data-testid="stSidebar"], [data-testid="collapsedControl"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 3], gap="large")

    with col1:
        if os.path.exists("assets/shri swami samarth pvt.ltd.png"):
            st.image("assets/shri swami samarth pvt.ltd.png", width=500)
        else:
            st.markdown("### 🖼️ PulseHR")

    with col2:
        st.markdown("<h2 style='color:#4285F4;'>Welcome to shri swami samarth pvt.ltd</h2>", unsafe_allow_html=True)
        greeting = "🌅 Good Morning" if datetime.now().hour < 12 else \
                   "🌞 Good Afternoon" if datetime.now().hour < 18 else "🌙 Good Evening"
        st.caption(greeting)

        with st.form("login_form"):
            username = st.text_input("👤 Username")
            password = st.text_input("🔒 Password", type="password")
            login_btn = st.form_submit_button("🔑 Login")

        if login_btn and username and password:
            user = credentials.get(username)
            if user and password == user["password"]:
                st.session_state.update({
                    "user_role": user["role"],
                    "employee_name": user["name"],
                    "username": username,
                    "login_phase": "verified",
                    "session_expiry": datetime.now() + timedelta(minutes=15)
                })
                st.success("✅ Login successful.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")

# ---------- DASHBOARD ----------
elif st.session_state.login_phase == "verified":
    role = st.session_state.get("user_role")
    name = st.session_state.get("employee_name")

    with st.sidebar:
        st.markdown(f"### 👤 Welcome, {name}")
        if role == "admin":
            st.title("🛠️ Admin Navigation")
            if st.button("💼 Payroll"): st.session_state.active_view = "payroll"
            if st.button("📝 Manual Entry"): st.session_state.active_view = "manual"
            if st.button("🛎️ Feedback Center"): st.session_state.active_view = "admin_feedback"
        else:
            st.title("📋 Employee Navigation")
            if st.button("📊 Attendance"): st.session_state.active_view = "attendance"
            if st.button("💰 My Payslip"): st.session_state.active_view = "payslip"
            if st.button("📣 Feedback Center"): st.session_state.active_view = "employee_feedback"

        if st.button("🔓 Logout"):
            for key in ["login_phase", "user_role", "employee_name", "username", "session_expiry", "active_view"]:
                st.session_state.pop(key, None)
            st.rerun()

    # ---------- VIEW ROUTING ----------
    view = st.session_state.get("active_view")
    if view == "manual": show_manual_entry()
    elif view == "payroll": show_payroll()
    elif view == "admin_feedback": show_feedbackcenter()
    elif view == "attendance": show_attendance()
    elif view == "payslip": show_payslip()
    elif view == "employee_feedback": show_feedback_employee()
    else:
        st.markdown(f"### 👋 Hello {name}")
        st.info("Please select an option from the sidebar.")