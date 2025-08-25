import streamlit as st
import time
from datetime import datetime, timedelta
import sys
import os
import pandas as pd

# ---------- Add project root to sys.path ----------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from views import admin, employee

# Import config settings
from config import (
    USE_SQL, safe_get_conn,
    EMPLOYEE_MASTER_CSV, VERIFIED_ADMINS_CSV,
    EMPLOYEE_MASTER_TABLE, VERIFIED_ADMIN_TABLE
)
# Inject manifest.json
st.markdown(
    """
    <link rel="manifest" href="/static/manifest.json">
    <script>
      if ("serviceWorker" in navigator) {
        window.addEventListener("load", function() {
          navigator.serviceWorker.register("/static/sw.js").then(function(registration) {
            console.log("ServiceWorker registered with scope:", registration.scope);
          }, function(err) {
            console.log("ServiceWorker registration failed:", err);
          });
        });
      }
    </script>
    """,
    unsafe_allow_html=True
)
# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Secure Login | Shri Swami Samarth Pvt. Ltd", layout="wide")


# ---------- SECURITY HELPER FUNCTIONS (MOVED TO TOP) ----------
def generate_session_token():
    """Generate a simple session token for additional security"""
    import hashlib
    import random
    import string

    timestamp = str(datetime.now().timestamp())
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    token_string = f"{timestamp}_{random_str}"
    return hashlib.md5(token_string.encode()).hexdigest()


def log_security_event(event_type, username, details=""):
    """Log security events"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {event_type} - User: {username} - {details}\n"

    try:
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        with open("logs/security_audit.log", "a") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Failed to write security log: {e}")


# ---------- INIT SESSION STATE ----------
for key, value in {
    "login_phase": "initial",
    "session_expiry": None,
    "active_view": None,
    "user_role": None,
    "employee_name": None,
    "admin_name": None,
    "username": None,
    "employee_id": None,  # Added employee_id to session state
    "login_timestamp": None,  # Added login timestamp
    "session_token": None  # Added session token for security
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------- SESSION EXPIRY CHECK ----------
if st.session_state.session_expiry and datetime.now() > st.session_state.session_expiry:
    # Log session expiry
    if st.session_state.get("username"):
        log_security_event("SESSION_EXPIRED", st.session_state.get("username"))

    for k in ["login_phase", "user_role", "employee_name", "admin_name", "username",
              "session_expiry", "active_view", "employee_id", "login_timestamp", "session_token"]:
        st.session_state.pop(k, None)
    st.warning("⏳ Session expired. Please login again.")
    st.rerun()


# ---------- DATA ACCESS FUNCTIONS ----------
def get_employee_master():
    """Get employee master data from SQL or CSV based on config"""
    if USE_SQL:
        try:
            conn = safe_get_conn()
            if conn:
                query = f"SELECT * FROM {EMPLOYEE_MASTER_TABLE}"
                df = pd.read_sql(query, conn)
                conn.close()
                # Ensure proper column names
                df.columns = df.columns.str.strip().str.lower()
                return df
        except Exception as e:
            st.error(f"SQL Error: {e}. Falling back to CSV.")

    # CSV fallback or when USE_SQL is False
    if os.path.exists(EMPLOYEE_MASTER_CSV):
        df = pd.read_csv(EMPLOYEE_MASTER_CSV, dtype={"employee_id": str})
        df.columns = df.columns.str.strip().str.lower()
        return df
    else:
        return pd.DataFrame(columns=['employee_id', 'employee_name', 'department', 'position'])


def get_verified_admins():
    """Get verified admins data from SQL or CSV based on config"""
    if USE_SQL:
        try:
            conn = safe_get_conn()
            if conn:
                query = f"SELECT * FROM {VERIFIED_ADMIN_TABLE}"
                df = pd.read_sql(query, conn)
                conn.close()
                # Ensure proper column names
                df.columns = df.columns.str.strip().str.lower()
                return df
        except Exception as e:
            st.error(f"SQL Error: {e}. Falling back to CSV.")

    # CSV fallback or when USE_SQL is False
    if os.path.exists(VERIFIED_ADMINS_CSV):
        df = pd.read_csv(VERIFIED_ADMINS_CSV)
        df.columns = df.columns.str.strip().str.lower()
        return df
    else:
        return pd.DataFrame(columns=['admin_user', 'admin_role'])


def find_employee_id(employee_name, employee_master):
    """Find employee ID from master data"""
    if employee_master.empty:
        return None

    # Clean and normalize names for comparison
    employee_master_clean = employee_master.copy()
    employee_master_clean["employee_name"] = employee_master_clean["employee_name"].str.strip().str.lower()
    employee_name_clean = employee_name.strip().lower()

    # Find matching employee
    match = employee_master_clean[employee_master_clean["employee_name"] == employee_name_clean]

    if not match.empty:
        return str(match.iloc[0]["employee_id"])

    return None


# ---------- ENHANCED CREDENTIALS WITH EMPLOYEE IDS ----------
credentials = {
    "admin_user": {"password": "adminuser", "role": "admin", "name": "Admin Padmaja"},
    "padmaja_user": {"password": "padmaja123", "role": "employee", "name": "Padmaja"},
    "rahul_user": {"password": "rahul123", "role": "employee", "name": "Rahul"},
    "prashant_user": {"password": "prashant123", "role": "admin", "name": "Admin Prashant"},
    "sunil_user": {"password": "sunil123", "role": "employee", "name": "Sunil"},
    "shivaji_user": {"password": "shivaji123", "role": "employee", "name": "Shivaji"}
}

# ---------- LOGIN SCREEN ----------
if st.session_state.login_phase == "initial":
    st.markdown("""
        <style>
        [data-testid="stSidebarNav"], [data-testid="stSidebar"], [data-testid="collapsedControl"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
        }
        .login-card {
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.1);
            margin-top: 2rem;
        }
        .security-info {
            background-color: #e3f2fd;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #2196f3;
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # Show data source status
    data_source = "SQL Server" if USE_SQL else "CSV Files"
    st.info(f"🔌 Data Source: {data_source}")

    # Security notice
    st.markdown("""
    <div class="security-info">
        <h4>🛡️ Enhanced Security Notice</h4>
        <p>This system now uses secure session management:</p>
        <ul>
            <li>✅ No employee selection dropdown in attendance</li>
            <li>✅ Attendance tied to your login credentials</li>
            <li>✅ Session tokens for additional security</li>
            <li>✅ Full audit logging</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([0.5, 0.5], gap="large")

    with col1:
        if os.path.exists("assets/shri swami samarth pvt.ltd.png"):
            st.image("assets/shri swami samarth pvt.ltd.png", width=300)
        else:
            st.markdown("### 🗾️ Shri Swami Samarth Pvt. Ltd")

    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("<h2 style='color:#4285F4;'>Welcome to Shri Swami Samarth Pvt. Ltd</h2>", unsafe_allow_html=True)

        greeting = "🌅 Good Morning" if datetime.now().hour < 12 else \
            "🌞 Good Afternoon" if datetime.now().hour < 18 else "🌙 Good Evening"
        st.caption(greeting)

        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")

        if st.button("🔓 Login", type="primary"):
            user = credentials.get(username)
            if user and password == user["password"]:
                username_clean = user["name"].strip().lower()

                # Load employee master using configured data source
                try:
                    employee_master = get_employee_master()
                    if not employee_master.empty:
                        employee_master["employee_name"] = employee_master["employee_name"].str.strip().str.lower()
                except Exception as e:
                    st.error(f"Error loading employee data: {e}")
                    employee_master = pd.DataFrame()

                # Load admin master using configured data source
                try:
                    admin_master = get_verified_admins()
                    if not admin_master.empty:
                        admin_master["admin_user"] = admin_master["admin_user"].str.strip().str.lower()
                except Exception as e:
                    st.error(f"Error loading admin data: {e}")
                    admin_master = pd.DataFrame()

                # Generate session token
                session_token = generate_session_token()
                login_timestamp = datetime.now()

                # --- EMPLOYEE LOGIN ---
                if not employee_master.empty and username_clean in employee_master["employee_name"].values:
                    matched_emp = employee_master[employee_master["employee_name"] == username_clean]
                    emp_id = str(matched_emp.iloc[0]["employee_id"])

                    st.session_state.update({
                        "login_phase": "verified",
                        "user_role": "employee",
                        "employee_name": user["name"],
                        "employee_id": emp_id,
                        "username": username,
                        "session_expiry": datetime.now() + timedelta(hours=8),  # Extended for full work day
                        "session_token": session_token,
                        "login_timestamp": login_timestamp
                    })

                    # Log successful employee login
                    log_security_event("EMPLOYEE_LOGIN_SUCCESS", username, f"Employee ID: {emp_id}")

                # --- ADMIN LOGIN ---
                elif not admin_master.empty and username_clean in admin_master["admin_user"].values:
                    st.session_state.update({
                        "login_phase": "verified",
                        "user_role": "admin",
                        "admin_name": user["name"],
                        "username": username,
                        "session_expiry": datetime.now() + timedelta(hours=8),
                        "session_token": session_token,
                        "login_timestamp": login_timestamp
                    })

                    # Log successful admin login
                    log_security_event("ADMIN_LOGIN_SUCCESS", username)

                else:
                    # Check if data is available
                    if employee_master.empty and admin_master.empty:
                        st.error("❌ No employee or admin data found. Please check your data configuration.")
                        log_security_event("LOGIN_FAILED_NO_DATA", username)
                    else:
                        st.error("❌ User authenticated but not found in employee or admin master.")
                        log_security_event("LOGIN_FAILED_NOT_IN_MASTER", username)
                    st.stop()

                st.success(f"✅ Login successful using {data_source}")
                st.success(f"🔐 Session token generated: {session_token[:8]}...")
                time.sleep(2)
                st.rerun()
            else:
                st.error("❌ Invalid credentials.")
                log_security_event("LOGIN_FAILED_INVALID_CREDENTIALS", username or "unknown")

        # Show connection test for debugging
        if st.checkbox("🔧 Show Connection Details"):
            st.write(f"**USE_SQL Setting:** {USE_SQL}")
            if USE_SQL:
                try:
                    conn = safe_get_conn()
                    if conn:
                        st.success("✅ SQL connection successful")
                        conn.close()
                    else:
                        st.error("❌ SQL connection failed")
                except Exception as e:
                    st.error(f"❌ SQL connection error: {e}")
            else:
                csv_exists = os.path.exists(EMPLOYEE_MASTER_CSV) and os.path.exists(VERIFIED_ADMINS_CSV)
                if csv_exists:
                    st.success("✅ CSV files found")
                else:
                    st.error("❌ CSV files not found")

        st.markdown('</div>', unsafe_allow_html=True)

# ---------- DASHBOARD VIEW ----------
elif st.session_state.login_phase == "verified":
    role = st.session_state["user_role"]

    # Get the appropriate name based on role
    if role == "admin":
        name = st.session_state.get("admin_name", "Admin")
    else:
        name = st.session_state.get("employee_name", "Employee")

    # Session info display
    session_info = {
        "login_time": st.session_state.get("login_timestamp", datetime.now()).strftime("%H:%M:%S"),
        "expires": st.session_state.get("session_expiry", datetime.now()).strftime("%H:%M:%S"),
        "token": st.session_state.get("session_token", "unknown")[:8] + "...",
    }

    with st.sidebar:
        st.markdown(f"### 👤 Welcome, {name}")

        # Show enhanced session info
        data_source = "SQL" if USE_SQL else "CSV"
        st.caption(f"📊 Data Source: {data_source}")

        # Session security info
        with st.expander("🔐 Session Info"):
            st.text(f"Login: {session_info['login_time']}")
            st.text(f"Expires: {session_info['expires']}")
            st.text(f"Token: {session_info['token']}")

            if role == "employee":
                emp_id = st.session_state.get("employee_id", "unknown")
                st.text(f"Employee ID: {emp_id}")

        if role == "admin":
            st.markdown("### 🛠️ Admin Navigation")
            if st.button("📝 Manual Entry"):
                st.session_state.active_view = "manual"
            if st.button("💼 Payroll"):
                st.session_state.active_view = "payroll"
            if st.button("📈 Appraisal Trends & Insights"):
                st.session_state.active_view = "appraisal_analytics"
            if st.button("📋 Appraisal Audit"):
                st.session_state.active_view = "appraisal_audit_log1"
            if st.button("📂 Bulk Payslip"):
                st.session_state.active_view = "bulkpayslip"
            if st.button("📮 Feedback Center"):
                st.session_state.active_view = "feedbackcenter"
            if st.button("📊 Company Insights"):
                st.session_state.active_view = "companyinsights"
            if st.button("🔮 Predictive Alerts"):
                st.session_state.active_view = "predictivealerts"
            if st.button("📉 Resignation"):
                st.session_state.active_view = "resignation"
            if st.button("📋 Audit Alerts"):
                st.session_state.active_view = "adminaudit"
            if st.button("📅 Leave Visualizer"):
                st.session_state.active_view = "leavevisualizer"
            if st.button("📈 Trends & Insights"):
                st.session_state.active_view = "analytics"

        else:
            st.markdown("### 📋 Employee Navigation")
            if st.button("📊 Attendance", type="primary"):
                st.session_state.active_view = "attendance"
                # Log attendance access
                log_security_event("ATTENDANCE_ACCESS_REQUEST",
                                   st.session_state.get("username", "unknown"),
                                   f"Employee ID: {st.session_state.get('employee_id', 'unknown')}")
            if st.button("💰 My Payslip"):
                st.session_state.active_view = "mypayslip"
            if st.button("📣 Feedback Center"):
                st.session_state.active_view = "feedbackcenter"
            if st.button("🧾 Resignation"):
                st.session_state.active_view = "resignation"
            if st.button("📅 Leave Visualizer"):
                st.session_state.active_view = "leavevisualizer"

        # Enhanced logout with security logging
        if st.button("🔓 Logout"):
            # Log logout event
            log_security_event("LOGOUT",
                               st.session_state.get("username", "unknown"),
                               f"Session duration: {datetime.now() - st.session_state.get('login_timestamp', datetime.now())}")

            # Clear all session data
            for k in ["login_phase", "user_role", "employee_name", "admin_name", "username",
                      "session_expiry", "active_view", "employee_id", "login_timestamp", "session_token"]:
                st.session_state.pop(k, None)
            st.rerun()

    # ✅ Route to View
    view = st.session_state.get("active_view")

    if role == "admin":
        # Pass the correct admin_name from session state
        admin.run_dashboard(view, admin_name=st.session_state.get("admin_name"))
    else:
        # Employee context is already available in st.session_state
        # The attendance system will read directly from session state
        employee.run_dashboard(view)

    # Session timeout warning
    if st.session_state.get("session_expiry"):
        time_remaining = st.session_state["session_expiry"] - datetime.now()
        if time_remaining.total_seconds() < 1800:  # 30 minutes warning
            minutes_left = int(time_remaining.total_seconds() / 60)
            st.warning(f"⏰ Session expires in {minutes_left} minutes")


# ---------- SESSION VALIDATION FUNCTIONS ----------
def validate_session():
    """Validate current session integrity"""
    required_keys = ["login_phase", "user_role", "session_token", "login_timestamp"]

    for key in required_keys:
        if key not in st.session_state:
            return False

    if st.session_state["login_phase"] != "verified":
        return False

    # Additional session validation can be added here
    return True


# ---------- MAIN EXECUTION ----------
if __name__ == "__main__":
    # Validate session integrity
    if st.session_state.get("login_phase") == "verified" and not validate_session():
        st.error("🔒 Session integrity check failed. Please login again.")
        # Clear potentially corrupted session
        for k in list(st.session_state.keys()):
            if k.startswith(('login_', 'user_', 'employee_', 'admin_', 'session_')):
                st.session_state.pop(k, None)
        st.rerun()