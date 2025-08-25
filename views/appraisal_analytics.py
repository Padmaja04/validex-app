import streamlit as st
import pandas as pd
import datetime
import os
from config import USE_SQL, get_sql_connection


def run_appraisal_analytics():
    st.title("📈 Salary Appraisal Assignment")

    # Load employee data
    master_path = "data/employee_master.csv"

    if USE_SQL:
        conn = get_sql_connection()
        master = pd.read_sql("SELECT * FROM dbo.employee_master", conn)
        conn.close()
    else:
        master = pd.read_csv(master_path)
    master["employee_id"] = master["employee_id"].astype(str)

    # Rating-to-Hike Mapping
    RATING_TO_HIKE = {
        1: 0,
        2: 1,
        3: 4,
        4: 7,
        5: 10
    }

    # Select employee
    selected_id = st.selectbox("🧾 Select Employee ID", master["employee_id"].unique())
    selected_row = master[master["employee_id"] == selected_id].iloc[0]

    st.write("👤 Employee Name:", selected_row["employee_name"].title())

    # Show both joining salary and current salary
    joining_salary = selected_row.get('fixed_salary', 0)
    current_salary = selected_row.get('new_salary', joining_salary)  # Fallback to fixed_salary if new_salary is null

    st.write("💼 Joining Salary (Fixed):", f"₹{joining_salary:,.2f}")
    st.write("💰 Current Salary:", f"₹{current_salary:,.2f}")

    # Show growth if there's a difference
    if current_salary > joining_salary:
        growth_amount = current_salary - joining_salary
        growth_percent = (growth_amount / joining_salary * 100) if joining_salary > 0 else 0
        st.success(f"📈 Salary Growth: +₹{growth_amount:,.2f} ({growth_percent:.1f}% increase)")

    # 📜 Show existing appraisal history
    if USE_SQL:
        conn = get_sql_connection()
        history_df = pd.read_sql(f"""
            SELECT * FROM dbo.appraisal_history
            WHERE employee_id = '{selected_id}'
            ORDER BY appraisal_date DESC
        """, conn)
        conn.close()
    else:
        history_path = "data/appraisal_history.csv"
        if os.path.exists(history_path):
            history_df = pd.read_csv(history_path)
            history_df = history_df[history_df["employee_id"] == selected_id]
        else:
            history_df = pd.DataFrame()

    st.subheader("📜 Appraisal History")
    if not history_df.empty:
        st.dataframe(history_df)
    else:
        st.info("No appraisal history found for this employee.")

    # Reviewer Inputs
    rating = st.slider("📊 Performance Rating (1 = Poor, 5 = Excellent)", 1, 5, 3)
    RATING_DESCRIPTIONS = {
        1: "Needs improvement → 0% hike",
        2: "Below expectations → 1% hike",
        3: "Meets expectations → 4% hike",
        4: "Exceeds expectations → 7% hike",
        5: "Outstanding → 10% hike"
    }
    st.markdown(f"**Guideline Note:** {RATING_DESCRIPTIONS[rating]}")

    reviewer = st.text_input("🧑‍💼 Reviewer ID")
    notes = st.text_area("🗒️ Reviewer Notes")

    if st.button("✅ Apply Appraisal"):
        # Use current_salary as base for calculation (not fixed_salary)
        base = current_salary if current_salary > 0 else joining_salary
        hike_percent = RATING_TO_HIKE.get(rating, 0)
        new_salary = base + base * (hike_percent / 100)
        today = datetime.datetime.now().date()

        if USE_SQL:
            conn = get_sql_connection()
            cursor = conn.cursor()
            try:
                # ✅ CORRECTED: Only update new_salary, keep fixed_salary unchanged
                cursor.execute("""
                    UPDATE dbo.employee_master
                    SET
                        performance_rating = ?,
                        appraisal_hike_percent = ?,
                        reviewer_id = ?,
                        appraisal_notes = ?,
                        appraisal_date = ?,
                        new_salary = ?
                    WHERE employee_id = ?
                """, (
                    rating, hike_percent, reviewer, notes,
                    today, round(new_salary, 2), selected_id
                ))

                # Add to appraisal history
                cursor.execute("""
                    INSERT INTO dbo.appraisal_history (
                        employee_id, reviewer_id, rating, hike_percent,
                        notes, appraisal_date, new_salary
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    selected_id, reviewer, rating, hike_percent,
                    notes, today, round(new_salary, 2)
                ))
                conn.commit()

                # Show success with growth details
                total_growth = new_salary - joining_salary
                total_growth_percent = (total_growth / joining_salary * 100) if joining_salary > 0 else 0

                st.success(f"🎉 Appraisal Applied Successfully!")
                st.info(f"💰 New Salary: ₹{round(new_salary):,}")
                st.info(f"📈 Total Growth Since Joining: +₹{total_growth:,.2f} ({total_growth_percent:.1f}%)")

            except Exception as e:
                st.error(f"❌ Failed to update SQL: {e}")
            finally:
                conn.close()

            # 🔄 Refresh and show updated history
            conn = get_sql_connection()
            history_df = pd.read_sql(f"""
                SELECT * FROM dbo.appraisal_history
                WHERE employee_id = '{selected_id}'
                ORDER BY appraisal_date DESC
            """, conn)
            conn.close()
            st.subheader("📜 Updated Appraisal History")
            st.dataframe(history_df)

        else:
            # CSV update path - ✅ CORRECTED: Only update new_salary
            master.loc[master["employee_id"] == selected_id, [
                "performance_rating", "appraisal_hike_percent", "reviewer_id",
                "appraisal_notes", "appraisal_date", "new_salary"
            ]] = [
                rating, hike_percent, reviewer, notes,
                today, round(new_salary, 2)
            ]

            new_entry = pd.DataFrame([{
                "employee_id": selected_id,
                "reviewer_id": reviewer,
                "rating": rating,
                "hike_percent": hike_percent,
                "notes": notes,
                "appraisal_date": today,
                "new_salary": round(new_salary, 2)
            }])

            history_path = "data/appraisal_history.csv"
            if os.path.exists(history_path):
                history = pd.read_csv(history_path)
                history = pd.concat([history, new_entry], ignore_index=True)
            else:
                history = new_entry

            try:
                master.to_csv(master_path, index=False)
                history.to_csv(history_path, index=False)

                # Show success with growth details
                total_growth = new_salary - joining_salary
                total_growth_percent = (total_growth / joining_salary * 100) if joining_salary > 0 else 0

                st.success(f"🎉 Appraisal Applied Successfully!")
                st.info(f"💰 New Salary: ₹{round(new_salary):,}")
                st.info(f"📈 Total Growth Since Joining: +₹{total_growth:,.2f} ({total_growth_percent:.1f}%)")

                st.dataframe(master[master["employee_id"] == selected_id])
                st.subheader("📜 Updated Appraisal History")
                st.dataframe(history[history["employee_id"] == selected_id])
            except Exception as e:
                st.error(f"❌ Failed to save updated data: {e}")


if __name__ == "__main__":
    run_appraisal_analytics()