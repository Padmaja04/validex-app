# views/hr_assistant.py
import streamlit as st
import pandas as pd

# Local CSVs only (offline)
EMPLOYEE_MASTER = "data/employee_master.csv"
SALARY_LOG = "data/salary_log.csv"
EMPLOYEE_DATA = "data/employee_data.csv"

@st.cache_data
def load_data():
    def load_csv(path, dtypes=None):
        try:
            return pd.read_csv(path, dtype=dtypes or {})
        except Exception:
            return pd.DataFrame()
    em = load_csv(EMPLOYEE_MASTER, {"employee_id": str})
    sl = load_csv(SALARY_LOG, {"employee_id": str})
    ed = load_csv(EMPLOYEE_DATA, {"employee_id": str})
    return em, sl, ed


def _reply(q, em, sl, ed, employee_id=None, employee_name=None):
    ql = (q or "").lower().strip()

    # Salary / Payslip
    if any(k in ql for k in ["salary", "payslip", "net pay", "ctc"]):
        if employee_id and not sl.empty and "net_salary" in sl.columns:
            s = sl[sl["employee_id"] == str(employee_id)]
            if not s.empty:
                # Just take the last row (instead of sorting by date)
                latest = s.iloc[-1].get("net_salary")
                if pd.notna(latest):
                    return f"💰 Your latest recorded net salary is ₹{latest:,.0f}. You can also check it in **My Payslip**."
        return "💰 You can view or download your payslip in **My Payslip**."

    # Attendance
    if "attendance" in ql or "present" in ql or "hours" in ql:
        if employee_id and not ed.empty:
            a = ed[ed["employee_id"] == str(employee_id)]
            if not a.empty:
                days = len(a)
                return f"📅 You have **{days}** attendance records. Open **Attendance** for details."
        return "📅 Open the **Attendance** module to see your records."

    # Leave
    if "leave" in ql:
        return "🏖️ Use the **Leave Visualizer** to review leave patterns. (Per-employee leave balance coming soon.)"

    # Help
    if "help" in ql or "what can you do" in ql:
        return "ℹ️ I can answer quick questions about **payslips/salary**, **attendance**, and **leave**."

    return "❓ Sorry, I didn’t get that. Ask about **salary/payslip**, **attendance**, or **leave**."

def run_hr_assistant():
    st.markdown("### 💬 HR Assistant (offline)")

    em, sl, ed = load_data()

    if "hr_chat" not in st.session_state:
        st.session_state.hr_chat = []

    col_in, col_btn = st.columns([4, 1])
    with col_in:
        user_input = st.text_input("Ask me something...", key="hr_input")
    with col_btn:
        send = st.button("Send", key="hr_send")

    if (send or st.session_state.get("hr_submit_enter")) and (user_input or "").strip():
        reply_text = _reply(
            user_input,
            em, sl, ed,
            employee_id=st.session_state.get("employee_id"),
            employee_name=st.session_state.get("employee_name"),
        )
        st.session_state.hr_chat.append(("You", user_input))
        st.session_state.hr_chat.append(("Assistant", reply_text))
        st.session_state.hr_submit_enter = False  # reset

    # Show chat history
    for who, msg in st.session_state.hr_chat[-10:]:
        if who == "You":
            st.markdown(f"**🧑 {who}:** {msg}")
        else:
            st.markdown(f"**🤖 {who}:** {msg}")