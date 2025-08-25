import streamlit as st
import pandas as pd
from datetime import datetime
import os
import pyodbc
from config import (
    USE_SQL, FEEDBACK_LOG_CSV, FEEDBACK_LOG_TABLE,
    safe_get_conn, table_exists, safe_datetime_for_sql
)


def create_feedback_table_if_not_exists(conn):
    """Create feedback_log table if it doesn't exist, or add missing columns."""
    cursor = conn.cursor()

    if not table_exists(conn, FEEDBACK_LOG_TABLE):
        # Create new table with all columns
        create_table_sql = f"""
        CREATE TABLE {FEEDBACK_LOG_TABLE} (
            id INT IDENTITY(1,1) PRIMARY KEY,
            timestamp DATETIME NOT NULL,
            employee_name NVARCHAR(100) NOT NULL,
            related_date DATE NOT NULL,
            issue_type NVARCHAR(50) NOT NULL,
            description NVARCHAR(MAX),
            status NVARCHAR(20) DEFAULT 'Pending',
            resolution NVARCHAR(MAX) DEFAULT '-',
            follow_up NVARCHAR(MAX) DEFAULT '-',
            created_at DATETIME DEFAULT GETDATE(),
            updated_at DATETIME DEFAULT GETDATE()
        )
        """
        cursor.execute(create_table_sql)
        conn.commit()
    else:
        # Table exists, check for missing columns and add them
        table_name = FEEDBACK_LOG_TABLE.split('.')[-1]  # Get table name without schema

        # Check for missing columns
        missing_columns = []
        required_columns = {
            'id': 'INT IDENTITY(1,1) PRIMARY KEY',
            'created_at': 'DATETIME DEFAULT GETDATE()',
            'updated_at': 'DATETIME DEFAULT GETDATE()'
        }

        for col_name in required_columns:
            cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = ? AND COLUMN_NAME = ?
            """, (table_name, col_name))

            if not cursor.fetchone():
                missing_columns.append((col_name, required_columns[col_name]))

        # Add missing columns (except primary key which can't be added to existing table)
        for col_name, col_definition in missing_columns:
            if col_name != 'id':  # Skip primary key for existing tables
                try:
                    alter_sql = f"ALTER TABLE {FEEDBACK_LOG_TABLE} ADD {col_name} {col_definition}"
                    cursor.execute(alter_sql)
                    conn.commit()
                except Exception as e:
                    st.warning(f"Could not add column {col_name}: {str(e)}")

    cursor.close()


def load_feedback_data():
    """Load feedback data from SQL or CSV based on USE_SQL setting."""
    required_columns = [
        "timestamp", "employee_name", "related_date", "issue_type",
        "description", "status", "resolution", "follow_up"
    ]

    if USE_SQL:
        conn = safe_get_conn()
        if conn:
            try:
                create_feedback_table_if_not_exists(conn)

                query = f"""
                SELECT timestamp, employee_name, related_date, issue_type,
                       description, status, resolution, follow_up
                FROM {FEEDBACK_LOG_TABLE}
                ORDER BY timestamp DESC
                """
                feedback_log = pd.read_sql(query, conn, parse_dates=["timestamp", "related_date"])
                conn.close()

                # Ensure all required columns exist
                for col in required_columns:
                    if col not in feedback_log.columns:
                        feedback_log[col] = "-"

                return feedback_log
            except Exception as e:
                st.error(f"Error loading from SQL: {str(e)}")
                conn.close()
                return pd.DataFrame(columns=required_columns)

    # CSV fallback or when USE_SQL is False
    if os.path.exists(FEEDBACK_LOG_CSV):
        feedback_log = pd.read_csv(FEEDBACK_LOG_CSV, parse_dates=["timestamp"])
        for col in required_columns:
            if col not in feedback_log.columns:
                feedback_log[col] = "-"
        return feedback_log
    else:
        return pd.DataFrame(columns=required_columns)


def save_feedback_data(feedback_log):
    """Save feedback data to SQL or CSV based on USE_SQL setting."""
    if USE_SQL:
        conn = safe_get_conn()
        if conn:
            try:
                create_feedback_table_if_not_exists(conn)

                # Clear existing data and insert fresh data
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM {FEEDBACK_LOG_TABLE}")

                for _, row in feedback_log.iterrows():
                    insert_sql = f"""
                    INSERT INTO {FEEDBACK_LOG_TABLE} 
                    (timestamp, employee_name, related_date, issue_type, description, status, resolution, follow_up)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(insert_sql, (
                        safe_datetime_for_sql(row['timestamp']),
                        str(row['employee_name']),
                        pd.to_datetime(row['related_date']).date() if pd.notna(row['related_date']) else None,
                        str(row['issue_type']),
                        str(row['description']),
                        str(row['status']),
                        str(row['resolution']),
                        str(row['follow_up'])
                    ))

                conn.commit()
                cursor.close()
                conn.close()
                return True
            except Exception as e:
                st.error(f"Error saving to SQL: {str(e)}")
                conn.close()
                return False

    # CSV fallback or when USE_SQL is False
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(FEEDBACK_LOG_CSV), exist_ok=True)
        feedback_log.to_csv(FEEDBACK_LOG_CSV, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving to CSV: {str(e)}")
        return False


def add_new_feedback(employee_name, related_date, issue_type, description):
    """Add new feedback entry."""
    if USE_SQL:
        conn = safe_get_conn()
        if conn:
            try:
                create_feedback_table_if_not_exists(conn)
                cursor = conn.cursor()
                insert_sql = f"""
                INSERT INTO {FEEDBACK_LOG_TABLE} 
                (timestamp, employee_name, related_date, issue_type, description, status, resolution, follow_up)
                VALUES (?, ?, ?, ?, ?, 'Pending', '-', '-')
                """
                cursor.execute(insert_sql, (
                    safe_datetime_for_sql(datetime.now()),
                    str(employee_name),
                    related_date,
                    str(issue_type),
                    str(description)
                ))
                conn.commit()
                cursor.close()
                conn.close()
                return True
            except Exception as e:
                st.error(f"Error adding feedback to SQL: {str(e)}")
                conn.close()
                return False

    # CSV fallback
    feedback_log = load_feedback_data()
    new_entry = {
        "timestamp": datetime.now(),
        "employee_name": employee_name,
        "related_date": related_date,
        "issue_type": issue_type,
        "description": description,
        "status": "Pending",
        "resolution": "-",
        "follow_up": "-"
    }
    feedback_log = pd.concat([feedback_log, pd.DataFrame([new_entry])], ignore_index=True)
    return save_feedback_data(feedback_log)


def update_feedback_entry(employee_name, timestamp, related_date, **updates):
    """Update existing feedback entry."""
    if USE_SQL:
        conn = safe_get_conn()
        if conn:
            try:
                cursor = conn.cursor()

                # Debug: Check what we're trying to update
                st.write(f"🔍 Debug - Updating: {employee_name}, {timestamp}, {related_date}")
                st.write(f"🔍 Debug - Updates: {updates}")

                # First, let's see what records exist
                debug_query = f"""
                SELECT employee_name, timestamp, related_date, status 
                FROM {FEEDBACK_LOG_TABLE} 
                WHERE employee_name = ?
                """
                cursor.execute(debug_query, (str(employee_name),))
                debug_results = cursor.fetchall()
                st.write(f"🔍 Debug - Found records for {employee_name}:")
                for row in debug_results:
                    st.write(f"   - {row}")

                # Check if updated_at column exists
                cursor.execute(f"""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{FEEDBACK_LOG_TABLE.split('.')[-1]}' 
                AND COLUMN_NAME = 'updated_at'
                """)
                has_updated_at = cursor.fetchone() is not None

                # Build dynamic update query
                set_clauses = []
                values = []
                for key, value in updates.items():
                    set_clauses.append(f"{key} = ?")
                    values.append(str(value))

                # Add updated_at only if column exists
                if has_updated_at:
                    set_clauses.append("updated_at = GETDATE()")

                # Convert timestamp to proper format for comparison
                timestamp_for_sql = safe_datetime_for_sql(pd.to_datetime(timestamp))
                values.extend([str(employee_name), timestamp_for_sql, related_date])

                update_sql = f"""
                UPDATE {FEEDBACK_LOG_TABLE} 
                SET {', '.join(set_clauses)}
                WHERE employee_name = ? AND ABS(DATEDIFF(second, timestamp, ?)) < 2 AND related_date = ?
                """

                st.write(f"🔍 Debug - SQL: {update_sql}")
                st.write(f"🔍 Debug - Values: {values}")

                rows_affected = cursor.execute(update_sql, values).rowcount
                st.write(f"🔍 Debug - Rows affected: {rows_affected}")

                conn.commit()
                cursor.close()
                conn.close()
                return rows_affected > 0
            except Exception as e:
                st.error(f"Error updating feedback in SQL: {str(e)}")
                conn.close()
                return False

    # CSV fallback
    feedback_log = load_feedback_data()
    mask = (
            (feedback_log["employee_name"] == employee_name) &
            (feedback_log["timestamp"] == timestamp) &
            (feedback_log["related_date"] == related_date)
    )

    if mask.any():
        true_index = feedback_log[mask].index[0]
        for key, value in updates.items():
            if key in feedback_log.columns:
                feedback_log.loc[true_index, key] = value
        return save_feedback_data(feedback_log)
    return False


def run_feedbackcenter():
    st.set_page_config(page_title="FeedbackCenter", layout="wide")

    st.title("💬 Feedback Center — Employee & HR View")
    st.caption(f"Submit and manage payroll-related feedback. {'Using SQL Database' if USE_SQL else 'Using CSV Files'}")

    # ---------- Session Check ----------
    if "employee_name" not in st.session_state:
        st.warning("Please log in to view or submit feedback.")
        st.stop()

    emp_name = st.session_state["employee_name"]
    user_role = st.session_state.get("user_role", "employee")

    # Load feedback data
    feedback_log = load_feedback_data()

    # ---------- Employee View ----------
    if user_role == "employee":
        st.subheader("📮 Submit New Feedback")

        today = datetime.today().date()
        selected_date = st.date_input("Related Date", max_value=today)
        issue_type = st.selectbox("Issue Type", [
            "Incorrect Late Mark", "Missing Attendance", "Wrong Deduction",
            "Biometric Failed", "Other"
        ])
        description = st.text_area("Describe your concern")

        if st.button("➕ Submit Feedback"):
            if add_new_feedback(emp_name, selected_date, issue_type, description):
                st.success("✅ Your feedback has been submitted.")
                st.rerun()
            else:
                st.error("❌ Failed to submit feedback. Please try again.")

        # Force proper datetime conversion for related_date
        feedback_log["related_date"] = pd.to_datetime(feedback_log["related_date"], errors="coerce")

        st.subheader("📋 Your Past Feedback")
        user_logs = feedback_log[feedback_log["employee_name"] == emp_name].copy()
        if not user_logs.empty:
            st.dataframe(
                user_logs[["timestamp", "issue_type", "related_date", "status", "resolution"]]
                .sort_values("timestamp", ascending=False),
                use_container_width=True
            )
        else:
            st.info("No feedback submitted yet.")

        # 🎉 Optional: Recent resolutions notification
        recently_resolved = user_logs[user_logs["status"] == "Resolved"].copy()
        if not recently_resolved.empty:
            st.info(f"🎉 {len(recently_resolved)} feedback items were recently marked as Resolved!")

        st.subheader("✏️ Follow-up on Pending Feedback")
        pending = user_logs[user_logs["status"] == "Pending"]
        if not pending.empty:
            options = pending.apply(
                lambda row: f"{row['timestamp']} — {row['issue_type']} ({row['related_date'].date()})",
                axis=1
            ).tolist()
            selected = st.selectbox("Select Feedback", options)
            selected_row = pending.iloc[options.index(selected)]

            updated_description = st.text_area("🔄 Update Description", value=selected_row["description"])
            follow_up = st.text_area("📌 Add Follow-up Note", value=selected_row["follow_up"])

            if st.button("📝 Save Follow-up"):
                if update_feedback_entry(
                        emp_name,
                        selected_row["timestamp"],
                        selected_row["related_date"],
                        description=updated_description,
                        follow_up=follow_up
                ):
                    st.success("✅ Follow-up saved.")
                    st.rerun()
                else:
                    st.error("❌ Failed to save follow-up. Please try again.")
        else:
            st.info("No pending feedback to edit.")

    # ---------- HR Admin View ----------
    elif user_role == "admin":
        st.subheader("🛡️ HR Admin Panel")

        if not feedback_log.empty:
            selected_emp = st.selectbox("Employee", ["All"] + sorted(feedback_log["employee_name"].unique()))
            selected_status = st.selectbox("Status", ["All", "Pending", "Under Review", "Resolved"])
            selected_issue = st.selectbox("Issue Type", ["All"] + sorted(feedback_log["issue_type"].unique()))

            filtered = feedback_log.copy()
            if selected_emp != "All":
                filtered = filtered[filtered["employee_name"] == selected_emp]
            if selected_status != "All":
                filtered = filtered[filtered["status"] == selected_status]
            if selected_issue != "All":
                filtered = filtered[filtered["issue_type"] == selected_issue]

            st.dataframe(filtered.sort_values("timestamp", ascending=False), use_container_width=True)

            pending_admin = filtered[filtered["status"] != "Resolved"]
            if not pending_admin.empty:
                options = pending_admin.apply(
                    lambda row: f"{row['timestamp']} — {row['employee_name']} — {row['issue_type']}",
                    axis=1
                ).tolist()
                selected = st.selectbox("Select Feedback to Resolve", options)
                selected_row = pending_admin.iloc[options.index(selected)]

                new_status = st.selectbox("New Status", ["Under Review", "Resolved"])
                resolution_note = st.text_area("Resolution Note")

                if st.button("✅ Save Resolution"):
                    st.write(f"🔍 Debug - Attempting to update:")
                    st.write(f"   - Employee: {selected_row['employee_name']}")
                    st.write(f"   - Timestamp: {selected_row['timestamp']} (type: {type(selected_row['timestamp'])})")
                    st.write(
                        f"   - Related Date: {selected_row['related_date']} (type: {type(selected_row['related_date'])})")
                    st.write(f"   - New Status: {new_status}")
                    st.write(f"   - Resolution: {resolution_note}")

                    if update_feedback_entry(
                            selected_row["employee_name"],
                            selected_row["timestamp"],
                            selected_row["related_date"],
                            status=new_status,
                            resolution=resolution_note
                    ):
                        st.success("✅ Feedback status updated.")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update feedback status. Please try again.")
            else:
                st.info("No feedback available for update.")

            # 🚨 Escalation
            escalation_days = 7
            feedback_log["timestamp"] = pd.to_datetime(feedback_log["timestamp"], errors="coerce")
            feedback_log["days_pending"] = (datetime.today() - feedback_log["timestamp"]).dt.days
            feedback_log["needs_escalation"] = (
                    (feedback_log["status"] == "Pending") &
                    (feedback_log["days_pending"] >= escalation_days)
            )
            escalated = feedback_log[feedback_log["needs_escalation"]]

            st.subheader("🚨 Escalated Feedback (Pending > 7 days)")
            if not escalated.empty:
                st.dataframe(escalated[[
                    "employee_name", "issue_type", "description", "days_pending", "timestamp"
                ]].sort_values("days_pending", ascending=False), use_container_width=True)
            else:
                st.info("No escalated feedback found.")

            # 📜 Timeline View
            timeline = feedback_log[feedback_log["employee_name"] == selected_emp].sort_values(
                "timestamp") if selected_emp != "All" else feedback_log.sort_values("timestamp")
            st.subheader("📜 Feedback History Timeline")
            for _, row in timeline.iterrows():
                st.markdown(f"🕒 {row['timestamp']} — {row['issue_type']} → **{row['status']}**")
                st.caption(f"Resolution: {row['resolution']}")
                if row['follow_up'] and row['follow_up'] != "-":
                    st.code(f"Follow-up: {row['follow_up']}")
                st.write("---")

            # 📊 Issue Insights
            st.subheader("📊 Feedback Insights")
            issue_counts = feedback_log["issue_type"].value_counts().reset_index()
            issue_counts.columns = ["Issue Type", "Count"]
            st.bar_chart(issue_counts.set_index("Issue Type"))

            # ✅ Fix date mismatch for resolution time analysis
            resolved = feedback_log[feedback_log["status"] == "Resolved"].copy()
            resolved["related_date"] = pd.to_datetime(resolved["related_date"], errors="coerce")

            invalid_dates = resolved[resolved["related_date"].isna()]
            if not invalid_dates.empty:
                st.warning(f"⚠️ Skipping {len(invalid_dates)} rows with invalid related_date format.")

            resolved["resolution_time_days"] = (resolved["timestamp"] - resolved["related_date"]).dt.days

            if not resolved.empty and "resolution_time_days" in resolved.columns:
                avg_time = resolved.groupby("issue_type")["resolution_time_days"].mean().reset_index()
                avg_time.columns = ["Issue Type", "Avg Resolution Time (Days)"]
                st.dataframe(avg_time)
            else:
                st.info("No resolved items to calculate resolution time.")
        else:
            st.info("No feedback data available.")


if __name__ == "__main__":
    run_feedbackcenter()