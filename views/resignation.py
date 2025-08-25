import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, time
from data_utils import get_resignation_data, get_salary_log
from config import USE_SQL, safe_get_conn, RESIGNATION_LOG_CSV
from utils.logger import log_admin_action

def run_resignation():
    # Initialize state
    if "refresh_flag" not in st.session_state:
        st.session_state.refresh_flag = 0

    st.set_page_config(layout="wide")
    st.title("📉 Resignation Tracker")
    st.markdown("Monitor upcoming exits, trigger settlements, and analyze trends across departments.")

    # Data source info
    data_source = "SQL Server" if USE_SQL else "CSV Files"
    st.info(f"📊 Currently using: **{data_source}**")

    # Load data
    try:
        resignation_log = get_resignation_data()
        if resignation_log.empty:
            st.success("✅ No resignations recorded yet. Your team is fully staffed!")
            return
        resignation_log.columns = resignation_log.columns.str.strip().str.lower()
    except Exception as e:
        st.error(f"❌ Error loading resignation data: {e}")
        return

    today = pd.Timestamp.today()
    office_exit_time = time(17, 0)

    # Normalize columns
    resignation_log["resignation_date"] = pd.to_datetime(resignation_log.get("resignation_date"), errors="coerce")
    resignation_log["notice_issued_date"] = pd.to_datetime(resignation_log.get("notice_issued_date"), errors="coerce")
    resignation_log["notice_period_days"] = pd.to_numeric(resignation_log.get("notice_period_days", 30), errors="coerce").fillna(30)
    resignation_log["admin_cleared"] = resignation_log.get("admin_cleared", pd.Series([False] * len(resignation_log)))
    if "employee_name" not in resignation_log.columns:
        resignation_log["employee_name"] = resignation_log.get("name", "Unknown Employee")
    if "department" not in resignation_log.columns:
        resignation_log["department"] = "Unknown Department"
    if "remarks" not in resignation_log.columns:
        resignation_log["remarks"] = ""
    if "status" not in resignation_log.columns:
        resignation_log["status"] = ""

    # System status (does NOT overwrite manual)
    def smart_status(row):
        resignation_date = row.get("resignation_date")
        admin_cleared = row.get("admin_cleared", False)
        if pd.isnull(resignation_date):
            return "pending"
        resignation_day = resignation_date.date()
        now = datetime.now()
        if resignation_day == now.date():
            return "exited" if now.time() >= office_exit_time and admin_cleared else "pending"
        elif resignation_day < now.date() and admin_cleared:
            return "exited"
        else:
            return "pending"

    resignation_log["system_status"] = resignation_log.apply(smart_status, axis=1)

    # Respect manual status if present (pending/exited/cancelled). Otherwise use system_status.
    resignation_log["status"] = resignation_log["status"].astype(str).str.lower().fillna("")
    resignation_log["status"] = np.where(
        resignation_log["status"].isin(["pending", "exited", "cancelled"]),
        resignation_log["status"],
        resignation_log["system_status"]
    )

    # Notice compliance
    def check_notice_compliance(row):
        notice_issued = row.get("notice_issued_date")
        resignation_date = row.get("resignation_date")
        notice_period = row.get("notice_period_days", 30)
        if pd.notnull(notice_issued) and pd.notnull(resignation_date):
            actual_notice_days = (resignation_date - notice_issued).days
            return "✔️ Compliant" if actual_notice_days >= notice_period else "❌ Short Notice"
        return "⚠️ Unknown"

    resignation_log["complied_notice"] = resignation_log.apply(check_notice_compliance, axis=1)

    # Month selector
    valid_dates = resignation_log["resignation_date"].dropna()
    if valid_dates.empty:
        st.success("✅ No valid resignation dates found.")
        return

    month_options = valid_dates.dt.strftime("%B %Y").unique()
    selected_month = st.selectbox("Select Month", sorted(month_options, reverse=True))
    month_dt = datetime.strptime(selected_month, "%B %Y")
    year, month_num = month_dt.year, month_dt.month

    # Base monthly slice
    monthly_all = resignation_log[
        (resignation_log["resignation_date"].dt.year == year) &
        (resignation_log["resignation_date"].dt.month == month_num)
    ].copy()

    # Upcoming = exclude exited & cancelled
    monthly_resignations = monthly_all[
        ~monthly_all["status"].isin(["exited", "cancelled"])
    ].copy()

    if monthly_resignations.empty:
        st.success("✅ No upcoming resignations this month. Your team is fully staffed!")
        return

    # Days to exit
    monthly_resignations["days_to_exit"] = (
        monthly_resignations["resignation_date"] - today
    ).dt.days.fillna(9999).astype(int)

    # Status filter (use the same vocabulary you support)
    status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Cancelled", "Exited"])
    if status_filter != "All":
        # Filter on the full monthly slice so users can see cancelled/exited if chosen
        filtered = monthly_all[monthly_all["status"] == status_filter.lower()].copy()
    else:
        filtered = monthly_resignations.copy()

    # Exiting soon (15 days) – computed from the filtered set
    exiting_soon = filtered[filtered["days_to_exit"] <= 15] if "days_to_exit" in filtered.columns else pd.DataFrame()

    # Display
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📋 Upcoming Resignation Log")
        display_cols = ["employee_name", "department", "resignation_date", "status", "complied_notice", "days_to_exit", "remarks"]
        available_cols = [c for c in display_cols if c in filtered.columns]
        st.dataframe(filtered[available_cols], use_container_width=True)
    with col2:
        st.metric("📌 Total in View", len(filtered))
        st.metric("⚠️ Exiting Within 15 Days", len(exiting_soon) if not exiting_soon.empty else 0)

    if not exiting_soon.empty:
        st.warning(f"⚠️ {len(exiting_soon)} employee(s) exiting within 15 days.")
        st.dataframe(exiting_soon[available_cols], use_container_width=True)

    # Monthly trend (show active upcoming = not exited/cancelled)
    try:
        wl = resignation_log.dropna(subset=["resignation_date"]).copy()
        wl["month_year"] = wl["resignation_date"].dt.to_period("M").astype(str)
        wl_active = wl[~wl["status"].isin(["exited", "cancelled"])].copy()
        monthly_counts = wl_active.groupby("month_year").size().reset_index(name="Active Upcoming")

        st.subheader("📈 Monthly Active Resignations (excludes exited/cancelled)")
        if not monthly_counts.empty:
            st.bar_chart(monthly_counts.set_index("month_year"))
        else:
            st.info("No trend data available.")
    except Exception as e:
        st.error(f"Error creating trend chart: {e}")

    # Replacement Needed (pending only, <= 30 days)
    st.subheader("📋 Replacement Needed")
    replacement_needed = monthly_all.copy()
    replacement_needed["days_to_exit"] = (
        replacement_needed["resignation_date"] - today
    ).dt.days.fillna(9999).astype(int)
    replacement_needed = replacement_needed[
        (replacement_needed["status"] == "pending") &
        (replacement_needed["days_to_exit"] <= 30)
    ]
    if replacement_needed.empty:
        st.success("✅ No urgent replacements needed.")
    else:
        replacement_cols = ["employee_name", "department", "resignation_date", "days_to_exit", "remarks"]
        available_replacement_cols = [c for c in replacement_cols if c in replacement_needed.columns]
        st.dataframe(replacement_needed[available_replacement_cols], use_container_width=True)

    # Settlement calculation
    def calculate_settlement(emp_id):
        try:
            salary_data = get_salary_log(employee_id=emp_id)
            if not salary_data.empty:
                latest_salary = salary_data.iloc[0]
                base_settlement = latest_salary.get("net_salary", 0)
                bonus = latest_salary.get("allowances", 0) * 0.1
                return base_settlement + bonus
            return 0
        except Exception as e:
            st.error(f"Error calculating settlement for {emp_id}: {e}")
            return 0

    # Cards (show only active upcoming)
    show_cards = st.checkbox("Show Resignations as Cards")
    if show_cards:
        st.subheader("📄 Resignation Cards")
        cards_df = monthly_all[~monthly_all["status"].isin(["exited", "cancelled"])].copy()
        cards_df["days_to_exit"] = (
            cards_df["resignation_date"] - today
        ).dt.days.fillna(9999).astype(int)

        for _, row in cards_df.iterrows():
            name = row.get("employee_name", "Unknown Employee")
            dept = row.get("department", "Unknown Department")
            status = str(row.get("status", "unknown")).title()
            exit_date = row["resignation_date"].date() if pd.notnull(row.get("resignation_date")) else "Unknown"
            urgency = row.get("days_to_exit", 999)
            compliance = row.get("complied_notice", "Unknown")
            emp_id = row.get("employee_id", "")
            payout = calculate_settlement(emp_id) if emp_id else 0

            if urgency <= 7:
                urgency_badge = "<span style='color:red; font-weight:bold;'>🔥 Urgent</span>"
                card_style = "border-left: 4px solid red;"
            elif urgency <= 15:
                urgency_badge = "<span style='color:orange; font-weight:bold;'>⚠️ Soon</span>"
                card_style = "border-left: 4px solid orange;"
            else:
                urgency_badge = "<span style='color:green; font-weight:bold;'>🟢 Scheduled</span>"
                card_style = "border-left: 4px solid green;"

            st.markdown(f"""
            <div style='padding:15px; margin-bottom:15px; border-radius:10px; 
                        background-color:#f9f9f9; box-shadow:0 2px 6px rgba(0,0,0,0.1); {card_style}'>
                <h4 style='margin-top:0;'>{name.title()}</h4>
                <p><strong>🏢 Department:</strong> {dept.title()}</p>
                <p><strong>📝 Status:</strong> {status}</p>
                <p><strong>📏 Notice Compliance:</strong> {compliance}</p>
                <p><strong>📅 Exit Date:</strong> {exit_date} ({urgency} days left) {urgency_badge}</p>
                <p><strong>🧾 Estimated Settlement:</strong> ₹{payout:,.2f}</p>
                <p><strong>👤 Employee ID:</strong> {emp_id}</p>
                <p><strong>📝 Remarks:</strong> {row.get("remarks","")}</p>
            </div>
            """, unsafe_allow_html=True)

    # --- Status updater (respects manual + forces rerun) ---
    st.subheader("✏️ Update Resignation Status")
    # Work off the full monthly slice so you can also pick cancelled/exited folks to change them back if needed
    if not monthly_all.empty:
        if "employee_id" not in monthly_all.columns:
            st.error("❌ Missing 'employee_id' column in data.")
            return

        emp_id_to_update = st.selectbox(
            "Select Employee to update status",
            monthly_all['employee_id'].unique()
        )

        current_row = monthly_all.loc[monthly_all['employee_id'] == emp_id_to_update].iloc[0]
        st.write(f"**Current status:** {str(current_row.get('status','unknown')).title()}")

        new_status = st.selectbox("New Status", ["pending", "exited", "cancelled"])
        remarks = st.text_input("Remarks (optional)")

        if st.button("Update Status", key=f"update_{emp_id_to_update}"):
            try:
                if USE_SQL:
                    conn = safe_get_conn()
                    if conn:
                        with conn.cursor() as cur:
                            # Decide system_status based on the chosen status
                            if new_status.lower() == "cancelled":
                                sys_status = "Closed"
                            elif new_status.lower() == "exited":
                                sys_status = "Completed"
                            else:
                                sys_status = "Pending"

                            cur.execute("""
                                UPDATE dbo.resignation_log
                                SET status = ?, remarks = ?, system_status = ?
                                WHERE employee_id = ?
                            """, (new_status, remarks, sys_status, emp_id_to_update))
                            conn.commit()
                else:
                    # Update in-memory then persist CSV
                    resignation_log.loc[resignation_log['employee_id'] == emp_id_to_update, 'status'] = new_status
                    resignation_log.loc[resignation_log['employee_id'] == emp_id_to_update, 'remarks'] = remarks
                    resignation_log.to_csv(RESIGNATION_LOG_CSV, index=False)

                # Log action
                log_admin_action(
                    username=st.session_state.get("username", "unknown"),
                    action_type="Resignation Update",
                    emp_id=emp_id_to_update,
                    description=f"Updated status to {new_status} with remarks: {remarks}"
                )

                st.success("Resignation status updated successfully!")
                st.session_state.refresh_flag += 1
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error updating status: {e}")

    # 📊 Department-wise Analysis
    if len(monthly_resignations) > 0:
        st.subheader("📊 Department-wise Resignations")
        dept_analysis = monthly_resignations.groupby('department').agg({
            'employee_name': 'count',
            'days_to_exit': 'mean'
        }).round(2)
        dept_analysis.columns = ['Total Resignations', 'Avg Days to Exit']
        st.dataframe(dept_analysis)

    # 🚨 Critical Alerts
    critical_exits = monthly_resignations[monthly_resignations["days_to_exit"] <= 7]
    if not critical_exits.empty:
        st.error(f"🚨 CRITICAL: {len(critical_exits)} employee(s) leaving within 7 days!")
        for _, row in critical_exits.iterrows():
            st.error(
                f"• {row.get('employee_name', 'Unknown')} from {row.get('department', 'Unknown')} - {row.get('days_to_exit', 0)} days left")


if __name__ == "__main__":
    run_resignation()