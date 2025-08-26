import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from datetime import date
import os
import calendar
from fpdf import FPDF
import io
from dateutil.relativedelta import relativedelta
import plotly.express as px
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import plotly.graph_objects as go
import random
import altair as alt
from deepface import DeepFace  # ✅ lowercase 'deepface'
from PIL import Image
import numpy as np
import tempfile

def login():
    st.title("🔒 Validex App Login")
    password = st.text_input("Enter password", type="password")
    if password == "validex123":  # Change this to your secret
        return True
    else:
        st.warning("Incorrect password")
        return False

if login():
    # Your actual app code starts here
    st.write("Welcome to Validex!")

st.markdown("""
    <style>
    [data-testid="stSidebarNav"] { display: none !important; }
    [data-testid="stSidebar"] { visibility: hidden !important; width: 0px !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

import sys

print(sys.executable)  # ✅ confirms which Python interpreter is being used

# 📁 Paths
badge_path = "badge/padmaja.jpg"
live_capture = "live_temp.png"  # Replace with actual webcam capture if available

# 📦 Show badge info
#st.write("Resolved badge path:", badge_path)
#st.write("Does file exist?", os.path.exists(badge_path))

# 🎫 Load badge image
badge_img = Image.open(badge_path)

# 📷 Capture live image
st.markdown("🧑‍💼 **Soft Reminder:** Please make sure your face is clearly visible and centered before capturing.")

snapshot = st.camera_input("Show your face to log attendance", key="face_attendance")
if not snapshot:
    st.warning("📷 Please capture your face to proceed.")
    st.stop()

try:
    img2 = Image.open(snapshot)
except Exception as e:
    st.error(f"❌ Live image unreadable: {e}")
    st.stop()

# 💾 Save both images to temp files (👇 place this here!)
import tempfile
with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp1:
    Image.fromarray(np.array(badge_img)).save(temp1.name)
    badge_temp_path = temp1.name

with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp2:
    Image.fromarray(np.array(img2)).save(temp2.name)
    live_temp_path = temp2.name

# 🤖 Run DeepFace verification
try:
    result = DeepFace.verify(
        img1_path=badge_temp_path,
        img2_path=live_temp_path,
        model_name="VGG-Face",
        enforce_detection=False
    )
    match = result["verified"]
    confidence = (1 - result["distance"]) * 100
    st.success(f"✅ Verification result: {match}, Confidence: {confidence:.2f}%")
    #st.write("🔍 DeepFace raw result:", result)
except Exception as e:
    st.error(f"❌ DeepFace error: {e}")
    st.stop()

# 🎯 Optional debug
st.write("🔍 DeepFace raw result:", result)


# Check the badge path itself
#st.write("Badge Path:", badge_path)
#badge_path = str(badge_path).strip()

#st.write("Badge path:", badge_path, type(badge_path))





def parse_month(selected_month):
    if selected_month == "All":
        return None, None  # or return a flag like ("All", "All")
    try:
        return datetime.strptime(selected_month, "%B %Y")
    except ValueError:
        return datetime.strptime(selected_month, "%Y-%m")


# 👇 Create the 'fonts' folder if it doesn't exist
os.makedirs("fonts", exist_ok=True)

st.title("shri swami samarth pvt.ltd")

#st.set_page_config(page_title="Payroll App", layout="wide")
#st.title("🔐 Secure Login")

# 👤 Login form
#username = st.text_input("Username")
#password = st.text_input("Password", type="password")

# 🔒 Predefined credentials
#credentials = {
    #"admin_user": {"password": "adminpass", "role": "admin"},
   # "employee_user": {"password": "employeepass", "role": "employee"}
#}

## ✅ Authentication logic
#if username and password:
    #if username in credentials and credentials[username]["password"] == password:
       # st.success(f"Welcome, {username.title()}!")
       # st.session_state["user_role"] = credentials[username]["role"]
        #st.session_state["username"] = username
    #else:
       # st.error("Invalid username or password.")


# 🚧 Prevent unauthorized access
#if "user_role" not in st.session_state:
    #st.stop()  # Stops the app from running further for unauthenticated users




st.subheader("employee entry")

if not os.path.exists("data/employee_master.csv"):
    st.error("⚠️ 'employee_master.csv' not found! Please check the file location.")
else:
    try:
        employee_master = pd.read_csv("data/employee_master.csv", dtype={"employee_id": str}, encoding="utf-8")
        if employee_master.empty:
            st.error("⚠️ 'employee_master.csv' is empty! Please add employee data.")
        #else:
           # st.write("Employee Master Data Preview:", employee_master.head())
    except Exception as e:
       st.error(f"⚠️ Error loading 'employee_master.csv': {e}")

#st.write("Employee Master Data:", employee_master)
if "employee_name" in employee_master.columns:
    employee_name = st.selectbox("Select Employee Name", employee_master["employee_name"], key="employee_select")
else:
    st.error("⚠️ 'employee_name' column is missing in 'employee_master.csv'.")

#employee_name = st.selectbox("Select Employee Name", employee_master["employee_name"])
filtered = employee_master.loc[employee_master["employee_name"] == employee_name,
                                "employee_id"].values

#st.write("Missing values:", employee_master["employee_name"].isna().sum())
employee_master = employee_master.dropna(subset=["employee_name"])
employee_master["employee_name"] = employee_master["employee_name"].astype(str)
#st.write("Columns available:", employee_master.columns.tolist())
employee_master.columns = employee_master.columns.str.strip().str.lower()
employee_master["employee_name"] = employee_master["employee_name"].str.strip()

#st.write("Employee Names Available:", employee_master["employee_name"].tolist())

if len(filtered) > 0:
    employee_id = filtered[0]
else:
    st.warning(f"Could not find ID for {employee_name}. Check your employee_master.csv.")
    employee_id = None  # or st.stop() if you'd prefer to halt the app here

if os.path.exists("data/employee_data.csv"):
 employee_data = pd.read_csv("data/employee_data.csv", dtype={"employee_id": str})
else:
 employee_data = pd.DataFrame(columns=["employee_id", "employee_name", "start_datetime", "exit_datetime", "duration_min"])

# 📁 Load Employee Master early
employee_master = pd.read_csv("data/employee_master.csv", dtype={"employee_id": str}, encoding="utf-8")
employee_master.columns = employee_master.columns.str.strip()
employee_master.columns = employee_master.columns.str.strip().str.lower()

# 🧾 Initialize employee_data before form
try:
    employee_data = pd.read_csv("data/employee_data.csv", parse_dates=["start_datetime", "exit_datetime"])
    if "date_only" in employee_data.columns:
        employee_data["date_only"] = pd.to_datetime(employee_data["date_only"]).dt.date
except FileNotFoundError:
    employee_data = pd.DataFrame()

# 📝 Attendance Entry Form
with st.form("attendance_form_entry"):
    selected_date = st.date_input("📅 Select Date")
    start_time = st.time_input("🕒 Start Time", step=timedelta(minutes=1))
    exit_time = st.time_input("🕓 Exit Time", step=timedelta(minutes=1))
    submitted = st.form_submit_button("✅ Save Entry")
if submitted:
    if exit_time <= start_time:
        st.error("⚠️ Exit time must be after start time.")
        st.stop()
        start_datetime = datetime.combine(selected_date, start_time)
        exit_datetime = datetime.combine(selected_date, exit_time)
        new_row = {
            "employee_id": employee_id,
            "employee_name": selected_employee,
            "start_datetime": start_datetime,
            "exit_datetime": exit_datetime,
            "date_only": selected_date,
            "method": "Manual",
            "notes": "Admin entry override"
            # Add the rest of your payroll fields as needed
        }
        employee_data = pd.concat([employee_data, pd.DataFrame([new_row])], ignore_index=True)
        employee_data.to_csv("employee_data.csv", index=False)
        st.success("✅ Manual entry saved.")



# 📸 Facial Recognition Attendance
st.markdown("🧑‍💼 **Soft Reminder:** Please make sure your face is clearly visible and centered before capturing.")

st.subheader("📸 Facial Recognition Attendance")
# ⏱ Get current time and date
from datetime import datetime
now = datetime.now()
today = now.date()

master_path = "data/employee_master.csv"

if not os.path.exists(master_path):
    st.error("⚠️ 'employee_master.csv' not found.")
    st.stop()

employee_master = pd.read_csv(master_path, dtype={"employee_id": str})
employee_master.columns = employee_master.columns.str.strip()
employee_master["employee_name"] = employee_master["employee_name"].astype(str).str.strip()

# 👤 Select employee
selected_employee = st.selectbox("Select Employee", employee_master["employee_name"].unique(), key="attendance_employee")
filtered = employee_master[employee_master["employee_name"] == selected_employee]
employee_id = filtered["employee_id"].values[0] if not filtered.empty else None

# 📁 Build badge path by name
badge_filename = f"{selected_employee.lower().strip()}.jpg"
badge_path = os.path.join("badge", badge_filename)
data_path = "data/employee_data.csv"

# 🧠 Show resolved path
#st.write("Resolved badge path:", badge_path)

# 🖼️ Preview badge image
if os.path.exists(badge_path):
    st.image(badge_path, caption=f"Badge for {selected_employee}")
else:
    st.warning(f"⚠️ Badge image not found: {badge_path}")
    st.stop()


# 📅 Get timestamp
now = datetime.now()
today = now.date()

# 📁 Path to attendance CSV
data_path = "data/employee_data.csv"

# 📸 Capture webcam photo
snapshot = st.camera_input("Show your face to log attendance")
if not snapshot or not employee_id:
    st.stop()

# 🔍 Compare badge with webcam snapshot
def compare_faces(img1_path, img2_file):
    img2 = Image.open(img2_file)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_img:
        Image.fromarray(np.array(img2)).save(temp_img.name)
        img2_path = temp_img.name
    result = DeepFace.verify(
        img1_path=img1_path,
        img2_path=img2_path,
        model_name="VGG-Face",
        enforce_detection=False
    )
    return result["verified"], (1 - result["distance"]) * 100

# 🧠 Run match and validate confidence
match, confidence = compare_faces(badge_path, snapshot)
confidence_threshold = 30

if not match or confidence < confidence_threshold:
    st.error(f"❌ Verification failed. Confidence: {confidence:.2f}%")
    st.stop()

# 🌞 Time-based greeting
def get_greeting(now):
    hour = now.hour
    if hour < 5:
        return "🌙 Working late? Good night!"
    elif hour < 12:
        return "🌞 Good morning! Wishing you a fresh start."
    elif hour < 17:
        return "☀️ Good afternoon! Keep up the great work."
    elif hour < 21:
        return "🌇 Good evening! Hope your day’s been productive."
    else:
        return "🌙 Wrapping up strong? Good night!"

greeting = get_greeting(now)
st.markdown(f"### {greeting} {selected_employee} 👋")

# 📁 Load attendance and normalize types
employee_data = pd.read_csv(data_path, parse_dates=["start_datetime", "exit_datetime"])
employee_data["date_only"] = pd.to_datetime(employee_data["date_only"]).dt.date
employee_data["employee_id"] = employee_data["employee_id"].astype(str)
employee_id = str(employee_id)

# 🎯 Filter today's record
mask = (employee_data["employee_id"] == employee_id) & (employee_data["date_only"] == today)
today_record = employee_data[mask]

# 🧠 Check-in if no existing record
if today_record.empty:
    new_row = {
        "employee_id": employee_id,
        "employee_name": selected_employee,
        "start_datetime": now,
        "exit_datetime": None,
        "date_only": today,
        "total_hours": None,
        "extra_hours": None,
        "extra_pay": None,
        "attendance_status": None,
        "late_mark": now.time() > datetime.strptime("09:15", "%H:%M").time(),
        "late_penalty": None,
        "method": "Face",
        "confidence": confidence,
        "notes": ""
    }
    employee_data = pd.concat([employee_data, pd.DataFrame([new_row])], ignore_index=True)
    st.success(f"✅ Checked in at {now.strftime('%H:%M')}")
    employee_data.to_csv(data_path, index=False)

# 🕓 Check-out if already checked-in and not yet out
elif pd.isnull(today_record.iloc[0]["exit_datetime"]):
    st.write("🔧 Executing checkout update...")
    check_in = today_record.iloc[0]["start_datetime"]
    elapsed_seconds = (now - check_in).total_seconds()

    if elapsed_seconds < 60:
        st.warning("⏳ Need at least 1 minute before check-out.")
        st.stop()

    total_hours = elapsed_seconds / 3600
    extra_hours = round(max(total_hours - 8, 0), 2)
    salary = filtered["fixed_salary"].values[0] if "fixed_salary" in filtered else 0
    hourly_rate = salary / (8 * 26)

    attendance_status = (
        "Absent" if total_hours < 4 else
        "Half Day" if total_hours < 6 else
        "Full Day"
    )

    late_penalty = hourly_rate * 0.5 if today_record.iloc[0]["late_mark"] else 0
    idx = today_record.index[0]

    employee_data.loc[idx, ["exit_datetime", "total_hours", "extra_hours",
                            "extra_pay", "attendance_status", "late_penalty"]] = [
        now, total_hours, extra_hours, extra_hours * hourly_rate,
        attendance_status, late_penalty
    ]

    st.balloons()
    st.success(f"🎉 Checked out at {now.strftime('%H:%M')}")
    employee_data.to_csv(data_path, index=False)

# ℹ️ Already checked out
else:
    st.info("ℹ️ Already checked out for today.")

    # Format datetime columns
    employee_data["start_datetime"] = pd.to_datetime(employee_data["start_datetime"], errors="coerce")
    employee_data["exit_datetime"] = pd.to_datetime(employee_data["exit_datetime"], errors="coerce")
    employee_data["date_only"] = employee_data["start_datetime"].dt.date

    # Define current entry
    start_datetime = datetime.combine(selected_date, start_time)
    exit_datetime = datetime.combine(selected_date, exit_time)

    if exit_datetime <= start_datetime:
        st.error("⚠️ Exit time must be after start time.")
    else:
        existing = employee_data[
            (employee_data["employee_id"] == employee_id) &
            (employee_data["date_only"] == selected_date)
            ]

        if not existing.empty:
            st.warning(f"⚠️ {employee_name} already has an attendance entry on {selected_date}. Multiple entries are not allowed.")
        else:
            total_hours = (exit_datetime - start_datetime).total_seconds() / 3600
            extra_hours = max(total_hours - 8, 0)

            # ⏱️ Determine status
            if total_hours < 4:
                attendance_status = "Absent"
            elif 4 <= total_hours < 6:
                attendance_status = "Half Day"
            else:
                attendance_status = "Full Day"

            # 🚩 Late mark logic (arrival after 9:15 AM)
            late_mark = start_time > datetime.strptime("09:15", "%H:%M").time()

            # 🚫 Late penalty — you can add more logic here later if needed
            late_penalty = 0

            # 💵 Calculate extra pay — use your hourly_rate logic if needed
            extra_pay = 0  # You can plug in: extra_pay = extra_hours * hourly_rate

            # 💰 Salary calculations
            fixed_salary_row = employee_master.loc[
                employee_master["employee_name"] == employee_name, "fixed_salary"
            ]
            fixed_salary = fixed_salary_row.values[0] if not fixed_salary_row.empty else 0
            hourly_rate = fixed_salary / (8 * 26)
            extra_pay = extra_hours * hourly_rate

            # 🚨 Late mark detection
            late_threshold = datetime.combine(selected_date, datetime.strptime("09:15", "%H:%M").time())

            is_late = start_datetime > late_threshold
            late_penalty = hourly_rate * 0.5 if is_late else 0

            new_entry = pd.DataFrame([{
                "employee_id": employee_id,
                "employee_name": employee_name,
                "start_datetime": start_datetime,
                "exit_datetime": exit_datetime,
                "date_only": selected_date,
                "total_hours": total_hours,
                "extra_hours": extra_hours,
                "extra_pay": extra_pay,
                "attendance_status": attendance_status,
                "late_mark": late_mark,
                "late_penalty": late_penalty
            }])
            required_columns = [
                "employee_id", "employee_name", "start_datetime", "exit_datetime", "date_only",
                "total_hours", "extra_hours", "extra_pay", "attendance_status",
                "late_mark", "late_penalty", "method", "confidence", "notes"
            ]

            employee_data = pd.concat([employee_data, new_entry], ignore_index=True)
            employee_data = employee_data[required_columns]  # Enforce column order
            employee_data.to_csv("employee_data.csv", index=False)
            st.write(employee_data)
            st.success(f"✅ Entry saved for {employee_name} on {selected_date}")

            st.markdown(f"- **Total Hours Worked**: {total_hours:.2f} hrs")
            st.markdown(f"- **Extra Hours**: {extra_hours:.2f} hrs")
            st.markdown(f"- **Extra Pay**: ₹{extra_pay:,.2f}")

            st.subheader("📊 Employee Data with Extra Hours Summary")
            st.dataframe(employee_data.tail(5)[[
                "employee_id", "employee_name", "date_only",
                "start_datetime", "exit_datetime", "extra_hours", "extra_pay"
            ]])
            #st.write(employee_data)
            st.dataframe(employee_data[employee_data["employee_name"] == selected_employee].tail(5))
# 🧹 Prepare employee_data fields
st.subheader("📆 Monthly Attendance Summary")

# 🧹 Prepare employee_data fields
employee_data['start_datetime'] = pd.to_datetime(employee_data['start_datetime'], errors='coerce')
employee_data['exit_datetime'] = pd.to_datetime(employee_data['exit_datetime'], errors='coerce')
employee_data['date_only'] = employee_data['start_datetime'].dt.date
employee_data['year_month'] = employee_data['start_datetime'].dt.strftime('%Y-%m')
employee_data['weekday'] = employee_data['start_datetime'].dt.strftime('%A')

# 🚫 Skip if there's no data
if employee_data.empty:
    st.info("No attendance data available yet.")
else:
    # 🧼 Drop duplicate day-attendance entries
    unique_days = employee_data.dropna(subset=["start_datetime"]).drop_duplicates(subset=["employee_id", "date_only"])

    # 📆 Add 'year_month' column to unique_days (required for groupby)
    unique_days['year_month'] = unique_days['start_datetime'].dt.strftime('%Y-%m')

    # 🔢 Group by employee and month
    attendance_summary = unique_days.groupby(["employee_id", "employee_name", "year_month", "start_datetime", "exit_datetime"]) \
        .size().reset_index(name="Total Days Present")

    st.dataframe(attendance_summary)

    # 🚧 Stop if nothing to summarize
    if attendance_summary.empty:
        st.info("No attendance summary found.")
    else:
        selected_month = st.selectbox("📅 Select Month", sorted(attendance_summary["year_month"].unique()))
        year, month = map(int, selected_month.split("-"))
        start_date = pd.Timestamp(year, month, 1)
        end_date = pd.Timestamp(year, month, calendar.monthrange(year, month)[1])

        # Load holiday calendar for attendance logic
        holiday_df = pd.read_csv("data/holidays.csv")
        holiday_df.columns = holiday_df.columns.str.strip().str.lower()

        if "dates" in holiday_df.columns:
            holiday_df["dates"] = pd.to_datetime(holiday_df["dates"], dayfirst=True).dt.date
            festival_dates = holiday_df["dates"].tolist()
        else:
            st.error("⚠️ 'dates' column not found in holidays.csv. Please check the column header.")
            festival_dates = []

        all_days = pd.date_range(start=start_date, end=end_date)
        working_days = all_days[
            (all_days.day_name() != "Tuesday") &
            (~pd.Series(all_days.date).isin(festival_dates))
        ]

        total_working_days = len(working_days)
        st.markdown(f"**📅 Total working days in {selected_month}: {total_working_days}**")

        # 📊 Add Tuesday attendance
        tuesdays = unique_days[(unique_days["weekday"] == "Tuesday") & (unique_days["year_month"] == selected_month)]
        tuesday_counts = tuesdays.groupby(["employee_id", "employee_name"]).size().reset_index(name="Tuesdays_Worked")

        # 📌 Merge into monthly summary
        summary_month = attendance_summary[attendance_summary["year_month"] == selected_month] \
            .merge(tuesday_counts, on=["employee_id", "employee_name"], how="left")
        summary_month["Tuesdays_Worked"] = summary_month["Tuesdays_Worked"].fillna(0).astype(int)

        # 📋 Show final summary
        st.subheader("🗂️ Final Monthly Attendance Summary")
        st.dataframe(summary_month.reset_index(drop=True))
        summary_month.columns = summary_month.columns.str.strip()

        #st.write("🧾 Available Columns:", summary_month.reset_index(drop=True).columns.tolist())

        summary_row = summary_month.reset_index(drop=True)

        # 🗂️ Assuming there's only one row:
       #st.session_state.total_days_present = summary_row["total_days_present"].values[0]


        def calculate_esi(gross_salary):
            if gross_salary <= 21000:
                employee_esi = round(gross_salary * 0.0075, 2)
                employer_esi = round(gross_salary * 0.0325, 2)
            else:
                employee_esi = 0
                employer_esi = 0
            return employee_esi, employer_esi


        def calculate_pf(basic_salary, override_limit=False):
            if basic_salary <= 15000 or override_limit:
                employee_pf = round(basic_salary * 0.12, 2)
                employer_pf = {
                    "pf": round(basic_salary * 0.0367, 2),
                    "eps": round(basic_salary * 0.0833, 2)
                }
            else:
                employee_pf = 0
                employer_pf = {"pf": 0, "eps": 0}
            return employee_pf, employer_pf


        def calculate_medical_insurance(opted_in, deduction_amount=500):
            return deduction_amount if opted_in else 0


        def compute_statutory_deductions(gross, basic, insurance_opt_in, override_pf=False):
            esi_emp, esi_empr = calculate_esi(gross)
            pf_emp, pf_empr = calculate_pf(basic, override_pf)
            med = calculate_medical_insurance(insurance_opt_in)

            total_employee_deduction = esi_emp + pf_emp + med
            total_employer_contrib = esi_empr + pf_empr["pf"] + pf_empr["eps"]

            return {
                "employee": {
                    "esi": esi_emp,
                    "pf": pf_emp,
                    "medical": med,
                    "total_deduction": total_employee_deduction
                },
                "employer": {
                    "esi": esi_empr,
                    "pf": pf_empr["pf"],
                    "eps": pf_empr["eps"],
                    "total_contribution": total_employer_contrib
                }
            }


        def calculate_monthly_tax(gross_annual_income, standard_deduction=50000, tax_saving_deductions=0):
            taxable_income = max(0, gross_annual_income - standard_deduction - tax_saving_deductions)
            slabs = [
                (250000, 0.00), (500000, 0.05), (750000, 0.10),
                (1000000, 0.15), (1250000, 0.20), (1500000, 0.25),
                (float("inf"), 0.30)
            ]
            tax = 0
            previous_limit = 0
            for limit, rate in slabs:
                if taxable_income > limit:
                    tax += (limit - previous_limit) * rate
                    previous_limit = limit
                else:
                    tax += (taxable_income - previous_limit) * rate
                    break
            return round(tax / 12, 2)




        # 🖋️ Signature + Footer Block
        def render_footer(pdf, employee_id, selected_month):
            pdf.ln(5)
            pdf.set_font("DejaVu", "", 8)
            pdf.cell(0, 5,
                     txt=f"Shri Swami Samarth Pvt. Ltd. • This is a system-generated payslip • Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                     ln=True, align="C")
            pdf.cell(0, 5, txt=f"Payslip Format v1.3 • Document ID: SSPL-{employee_id}-{selected_month}", ln=True,
                     align="C")
            pdf.ln(4)
            pdf.set_font("DejaVu", "", 10)
            pdf.cell(100, 10, txt="", ln=False)
            pdf.cell(80, 10, txt="__________________________", ln=True, align="R")
            pdf.cell(100, 10, txt="               ", ln=True, align="L")
            pdf.cell(100, 6, txt="", ln=False)
            pdf.cell(80, 6, txt="Authorized Signature", ln=True, align="R")
            pdf.cell(100, 6, txt="               ", ln=True, align="L")

        # 💼 PDF Payslip Generator
        def generate_payslip_pdf(employee_name, employee_id, selected_month, base_salary, extra_pay,
                                 tuesday_bonus, festival_bonus, late_deduction,
                                 employee_pf, employer_pf, tax_deduction, net_salary,
                                 late_marks, full_days, half_days, employee_data,
                                 employee_name_clean, lop_days=0,
                                 proration_note=None, leave_concession=None, leave_concession_amount=None):

            def parse_month(selected_month):
                if selected_month == "All":
                    return None
                try:
                    return datetime.strptime(selected_month, "%B %Y")
                except ValueError:
                    return datetime.strptime(selected_month, "%Y-%m")

            dt = parse_month(selected_month)
            if dt is None:
                st.info("Showing data for all months.")
            else:
                year = dt.year
                month_num = dt.month
            employer_ctc = base_salary + extra_pay + tuesday_bonus + festival_bonus + employer_pf
            HOLIDAYS = ["2025-07-17", "2025-07-29"]

            def is_weekend_or_holiday(date_obj):
                return (
                        date_obj.weekday() in [1, 6] or
                        date_obj.isoformat() in HOLIDAYS
                )

            pdf = FPDF()
            pdf.add_page()
            pdf.add_font("DejaVu", "", "fonts/DejaVuSans.ttf", uni=True)
            pdf.add_font("DejaVu", "B", "fonts/DejaVuSans-Bold.ttf", uni=True)

            # 🧾 Header
            pdf.set_font("DejaVu", "B", 12)
            pdf.cell(200, 10, txt="Shri Swami Samarth Pvt. Ltd.", ln=True, align="C")
            pdf.cell(200, 10, txt=f"Payslip for {employee_name} ({employee_id})  {selected_month}", ln=True, align="C")
            pdf.ln(5)
            # Set font smaller and start attendance calendar
            pdf.set_font("DejaVu", "", 9)
            pdf.cell(0, 6, txt=f"Attendance Calendar for {datetime(year, month, 1).strftime('%B %Y')}", ln=True)

            # Weekday headers
            weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

            for day in weekdays:
                pdf.cell(27, 6, txt=day, border=1, align="C")
            pdf.ln()

            # Start filling the grid
            first_weekday, total_days = calendar.monthrange(year, month)
            current_day = 1
            while current_day <= total_days:
                for weekday in range(7):
                    if (current_day == 1 and weekday < first_weekday) or current_day > total_days:
                        pdf.cell(27, 6, txt="", border=1)
                    else:
                        this_date = date(year, month, current_day)
                        row = employee_data[
                            (employee_data["employee_name"].str.lower().str.strip() == employee_name_clean) &
                            (employee_data["date_only"] == this_date)
                            ]

                        if not row.empty:
                            status = row["attendance_status"].values[0]
                            late = row["late_mark"].values[0] if "late_mark" in row.columns else False
                            marker = "L" if late else (
                                "F" if status == "Full Day" else "H" if status == "Half Day" else "A"
                            )
                        else:
                            marker = "-" if is_weekend_or_holiday(this_date) else "A"

                        label = f"{str(current_day).zfill(2)} {marker}"
                        pdf.cell(27, 6, txt=label, border=1, align="C")
                        current_day += 1
                pdf.ln()

            # 📘 Legend
            pdf.ln(2)
            pdf.set_font("DejaVu", "", 9)
            pdf.multi_cell(0, 5, "Legend: F = Full | H = Half | A = Absent | L = Late | - = Holiday/Tuesday")
            pdf.ln(2)
            # 💰 Salary Breakdown
            pdf.set_font("DejaVu", "", 10)
            # Row 1: Attendance
            pdf.cell(95, 10, txt=f"Full Days: {full_days}", ln=False)
            pdf.cell(95, 10, txt=f"Half Days: {half_days}", ln=True)
            # Row 2: Late & Base Salary
            pdf.cell(95, 10, txt=f"Late Marks: {late_marks}", ln=False)
            pdf.cell(95, 10, txt=f"Base Salary: ₹{base_salary:,.2f}", ln=True)
            # Row 3: Extra Pay & Tuesday Bonus
            pdf.cell(95, 10, txt=f"Extra Pay: ₹{extra_pay:,.2f}", ln=False)
            pdf.cell(95, 10, txt=f"Tuesday Bonus: ₹{tuesday_bonus:,.2f}", ln=True)
            # Row 4: Festival Bonus & Late Deduction
            pdf.cell(95, 10, txt=f"Festival Bonus: ₹{festival_bonus:,.2f}", ln=False)
            pdf.cell(95, 10, txt=f"Late Deduction: -₹{late_deduction:,.2f}", ln=True)
            # Row 5: PF Deduction & PF Contribution
            pdf.cell(95, 10, txt=f"Employee PF: -₹{employee_pf:,.2f}", ln=False)
            pdf.cell(95, 10, txt=f"Employer PF: ₹{employer_pf:,.2f}", ln=True)
            # Row 6: Tax & Gross Pay
            pdf.cell(95, 10, txt=f"Tax Deduction: -₹{tax_deduction:,.2f}", ln=False)
            gross = base_salary + extra_pay + tuesday_bonus - late_deduction
            pdf.cell(95, 10, txt=f"Gross Pay: ₹{gross:,.2f}", ln=True)
            # 📋 Leave Summary
            pdf.set_font("DejaVu", "B", 11)
            pdf.ln(1)
            pdf.cell(200, 10, txt="Leave Adjustment Summary", ln=True)
            pdf.set_font("DejaVu", "", 10)
            pdf.cell(95, 10, txt=f"Leave Concession Granted: {leave_concession:.1f} day(s)", ln=False)
            pdf.cell(95, 10, txt=f"Concession Amount: ₹{leave_concession_amount:,.2f}", ln=True)
            pdf.cell(95, 10, txt=f"Total Leave Taken: {leave_concession + lop_days:.1f} day(s)", ln=False)
            pdf.cell(95, 10, txt=f"Loss of Pay (LOP): {lop_days:.1f} day(s)", ln=True)
            # 💰 Net Pay
            pdf.ln(1)
            pdf.set_font("DejaVu", "B", 12)
            pdf.cell(200, 10, txt=f"Net Salary Payable: ₹{net_salary:,.2f}", ln=True)
            pdf.cell(200, 10, txt=f"Total Employer CTC: ₹{employer_ctc:,.2f}", ln=True)
            # 📎 Notes
            pdf.set_font("DejaVu", "", 9)
            pdf.ln(2)
            pdf.multi_cell(0, 9,
                           "Note: Provident Fund calculated at 12% of Fixed Salary, capped at ₹1,800/month as per EPF guidelines.")

            pdf.set_font("DejaVu", "", 9)
            pdf.ln(2)
            pdf.cell(0, 9, txt=f"Note: Leave concession applied for partial attendance Amount: ₹{leave_concession_amount:,.2f} for {leave_concession} day(s)", ln=True)


            if proration_note:
                pdf.set_font("DejaVu", "", 9)
                pdf.ln(2)
                pdf.multi_cell(0, 5, proration_note)

            # ✍️ Footer Block
            render_footer(pdf, employee_id, selected_month)

            return pdf.output(dest="S").encode("latin-1")



        def send_report_via_email(buffer, filename, recipients, smtp_config):
            msg = MIMEMultipart()
            msg["Subject"] = f"Monthly Payroll Report — {filename}"
            msg["From"] = smtp_config["sender"]
            msg["To"] = ", ".join(recipients)
            msg.attach(MIMEText("Please find the attached payroll summary.", "plain"))

            part = MIMEApplication(buffer.getvalue(), _subtype="pdf")
            part.add_header("Content-Disposition", "attachment", filename=filename)
            msg.attach(part)

            with smtplib.SMTP(smtp_config["host"], smtp_config["port"]) as server:
                server.starttls()
                server.login(smtp_config["user"], smtp_config["password"])
                server.send_message(msg)


        # ------------------ Streamlit UI ------------------

        st.title("🧾 Payroll Calculator")

        # 📥 Load holiday data
        holiday_bonus_df = pd.read_csv("data/festival_bonus.csv")


        # Clean and lowercase columns
        holiday_bonus_df.columns = holiday_bonus_df.columns.str.strip().str.lower()

        # Ensure correct types
        holiday_bonus_df["festival_month"] =holiday_bonus_df["festival_month"].astype(int)
        holiday_bonus_df["festival_bonus"] = holiday_bonus_df["festival_bonus"].astype(float)

        # Select employee
        available_names = employee_master["employee_name"].dropna().unique()
        employee_name = st.selectbox("Select Employee", sorted(available_names))
        employee_name_clean = employee_name.lower().strip()

        # Store in session state
        st.session_state.employee_name_clean = employee_name_clean

        # Auto-detect employee ID
        emp_id_row = employee_master[employee_master["employee_name"].str.lower().str.strip() == employee_name_clean]
        employee_id = emp_id_row["employee_id"].values[0] if not emp_id_row.empty else ""
        st.markdown(f"🆔 **Employee ID:** `{employee_id}`")

        # Select month
        #selected_month = st.text_input("Payroll Month (e.g., 2025-07 or 2025-07-08)", value="2025-07")



        # ✅ Safe unpacking logic for full date support
        parts = selected_month.split("-")
        if len(parts) == 2:
            selected_year, selected_month_num = map(int, parts)
            selected_day = 1  # Default day for monthly processing
        elif len(parts) == 3:
            selected_year, selected_month_num, selected_day = map(int, parts)
        else:
            st.error("Invalid date format. Use YYYY-MM or YYYY-MM-DD.")
            st.stop()



        # 📅 Full date object for calendar, cutoff logic, and record filtering
        selected_date_obj = datetime(selected_year, selected_month_num, selected_day)
        selected_date = datetime.now().date()  # Results in: 2025-07-08

        # 🎯 Use in bonus logic
        cutoff_date = datetime(selected_year, selected_month_num, 1) - timedelta(days=90)

        # Load holidays CSV and clean columns
        holiday_df = pd.read_csv("data/holidays.csv")
        holiday_df.columns = holiday_df.columns.str.strip().str.lower()  # standardize headers
        holiday_df["dates"] = pd.to_datetime(holiday_df["dates"], dayfirst=True)
        holiday_df["month"] = holiday_df["dates"].dt.month

        if employee_name and selected_month:
            # Fetch summary data
            summary_row = summary_month[summary_month["employee_name"].str.lower().str.strip() == employee_name_clean]
            if summary_row.empty:
                st.warning("No summary data found for the selected employee.")
            else:
                # 🎯 Attendance Summary
                total_working_days = 26  # Set a standard month baseline

                st.session_state["total_days_present"] = summary_row["Total Days Present"].values[0]
                total_days_present = st.session_state.get("total_days_present", None)

                effective_working_days = total_days_present if total_days_present else 1  # Avoid divide-by-zero

                # 💼 Fetch salary
                fixed_salary = emp_id_row["fixed_salary"].values[0] if not emp_id_row.empty else 0

                hourly_rate = fixed_salary / (8 * total_working_days) if fixed_salary else 0

                # 🎉 Festival Bonus Setup

                # Extract date parts from the selected month
                cutoff_date = datetime(selected_year, selected_month_num, 1) - timedelta(days=90)

                # Pull join date
                employee_join_date = pd.to_datetime(emp_id_row["join_date"].values[0], dayfirst=True)

                # Lookup festival row
                festival_row = holiday_bonus_df[holiday_bonus_df["festival_month"] == selected_month_num]
                festival_bonus_percent = festival_row["festival_bonus"].values[0] if not festival_row.empty else 0
                festival_name = festival_row["festival_name"].values[0] if not festival_row.empty else None

                # Compute bonus
                festival_bonus = 0

                if festival_bonus_percent > 0 and employee_join_date <= cutoff_date:
                    festival_bonus = fixed_salary * (festival_bonus_percent / 100)

                # 💾 Store final bonus value
                st.session_state["festival_bonus"] = festival_bonus

                # 🕓 Filter employee's monthly data

                monthly_data = employee_data[
                    (employee_data["employee_name"].str.lower().str.strip() == employee_name_clean) &
                    (employee_data["date_only"] >= date(selected_year, selected_month_num, 1)) &
                    (employee_data["date_only"] < date(selected_year, selected_month_num, 1) + relativedelta(months=1))
                    ].dropna(subset=["start_datetime", "exit_datetime"])

                # 🧹 Date & Time Cleaning
                monthly_data["date_only"] = pd.to_datetime(monthly_data["date_only"]).dt.date
                monthly_data["start_datetime"] = pd.to_datetime(monthly_data["start_datetime"])
                monthly_data["exit_datetime"] = pd.to_datetime(monthly_data["exit_datetime"])

                # 🗓️ Count Tuesdays worked (weekday 1 = Tuesday)
                tuesdays_worked = sum(
                    1 for _, row in monthly_data.iterrows()
                    if row["date_only"].weekday() == 1
                    and row.get("attendance_status") in ["Full Day", "Half Day"]
                )

                # 🕒 Extra Hours Calculation
                monthly_data["extra_hours"] = ((monthly_data["exit_datetime"] - monthly_data[
                    "start_datetime"]).dt.total_seconds() / 3600 - 8).clip(lower=0)
                total_extra_hours = monthly_data["extra_hours"].sum()

                # 📊 Attendance Stats
                full_day_count = (monthly_data["attendance_status"] == "Full Day").sum()
                half_day_count = (monthly_data["attendance_status"] == "Half Day").sum()
                late_mark_count = (monthly_data["late_mark"] == True).sum()
                late_day_equiv = (late_mark_count // 3) * 0.5

                st.info(
                    f"📌 Salary calculated based on {full_day_count} full days, {half_day_count} half days, and {late_mark_count} late mark(s).")

                # 👇 Leave Policy Constants
                annual_leave_limit = 14
                carry_forward_limit = 30
                leave_accrual = annual_leave_limit / 12  # ≈ 1.17/month

                # 📘 Load past balance (or 0 if no past records)
                leave_opening = 0
                try:
                    df_all = pd.read_csv("data/salary_log.csv")
                    recent = df_all[(df_all["employee_id"] == employee_id)].sort_values(by="month",
                                                                                        ascending=False).head(1)
                    if not recent.empty:
                        leave_opening = float(recent["leave_balance"].values[0])
                except:
                    pass

                # ✏️ Leave Taken — you can pull this from attendance summary or manually input it
                earned_leave_taken = st.number_input("📝 Earned Leave Taken This Month", min_value=0.0, max_value=31.0,
                                                     step=0.5, format="%.1f")

                # 🧮 Update Leave Balance
                leave_closing = min(leave_opening + leave_accrual - earned_leave_taken, carry_forward_limit)

                lop_days = max(earned_leave_taken - leave_opening - leave_accrual, 0)
                if lop_days > 0:
                    st.warning(f"📉 {lop_days:.1f} day(s) of excess leave will be deducted as LOP (Loss of Pay).")


                def remove_salary_duplicates(filepath="salary_log.csv"):
                    if not os.path.exists(filepath):
                        st.error(f"File '{filepath}' not found.")
                        return

                    df = pd.read_csv(filepath)
                    df_cleaned = df.drop_duplicates(subset=["employee_id", "month"], keep="first")

                    # ✅ Overwrite the original file
                    df_cleaned.to_csv(filepath, index=False)
                    st.success(
                        f"✅ Removed {len(df) - len(df_cleaned)} duplicate entries. Overwritten {filepath} successfully."
                    )

                    # 🔘 Trigger cleanup from Streamlit button


                if st.button("🧹 Remove Duplicate Salary Entries"):
                    remove_salary_duplicates()


                def get_leave_concession(full_days, half_days):
                        effective_days = full_days + 0.5 * half_days
                        # You can tweak this threshold (e.g. < 3 or < 5)
                        if effective_days < 3:
                            return 1.2
                        return 0


                insurance_opt = st.checkbox("Opted for Medical Insurance?")
                st.markdown(f"🔍 _Detected Extra Hours: {total_extra_hours:.2f}_")

                tab1, tab2 = st.tabs(["📋 Payroll Generator", "📊 Company Overview"])


                # 🧠 Leave Insights Module Definition
                def leave_insights_module(df, resignation_df=None, critical_threshold=3):
                    st.header("🧾 Leave Insights Dashboard")

                    if df.empty:
                        st.info("ℹ️ No leave balance data available.")
                        return

                    # 🔍 Required column check
                    required_cols = ["employee_id", "department", "total_allocated", "leaves_taken"]
                    missing = [col for col in required_cols if col not in df.columns]
                    if missing:
                        st.warning(f"⚠️ Missing columns: {', '.join(missing)}")
                        return

                    # ✅ Compute unused leave
                    df["unused"] = df["total_allocated"] - df["leaves_taken"]

                    # 📊 Department-wise unused leave chart
                    unused_by_dept = df.groupby("department")["unused"].sum().reset_index()
                    st.subheader("📊 Department-wise Unused Leave")
                    st.bar_chart(unused_by_dept.set_index("department"))

                    # 🔥 Highlight critical leave balances
                    critical_employees = df[df["unused"] <= critical_threshold]
                    if not critical_employees.empty:
                        st.subheader("🚨 Employees with Critically Low Leave Balance")
                        st.dataframe(critical_employees[["employee_id", "department", "unused"]])
                    else:
                        st.info("✅ No employees below the critical threshold.")

                    # 🧠 Predictive badge: Likely to exhaust leave
                    df["likely_exhaust"] = df["unused"] < 5  # You can tweak threshold here
                    predicted_risk = df[df["likely_exhaust"]]
                    if not predicted_risk.empty:
                        st.subheader("🧠 Employees Likely to Exhaust Leave Soon")
                        st.dataframe(predicted_risk[["employee_id", "department", "unused"]])

                    # 🌡️ Heatmap of avg leave balance by department
                    heatmap_data = df.groupby("department")["unused"].mean().reset_index()
                    heatmap = alt.Chart(heatmap_data).mark_rect().encode(
                        x="department:N",
                        y="unused:Q",
                        color=alt.Color("unused:Q", scale=alt.Scale(scheme="redyellowgreen")),
                        tooltip=["department", "unused"]
                    ).properties(title="🟨 Leave Balance Heatmap")
                    st.altair_chart(heatmap, use_container_width=True)

                    # 📈 Leave vs resignation correlation
                    if resignation_df is not None and "employee_id" in resignation_df.columns:
                        joined = pd.merge(df, resignation_df[["employee_id"]], on="employee_id", how="inner")
                        joined["resigned"] = True
                        correlation_check = joined.groupby("department").agg({
                            "unused": "mean",
                            "resigned": "sum"
                        }).reset_index()
                        st.subheader("📉 Leave vs Resignation Correlation")
                        st.dataframe(correlation_check)


                # 🧠 Utility Function: Save Salary Record
                def save_salary_record(record, filename="salary_log.csv"):
                    try:
                        if os.path.exists(filename):
                            df_existing = pd.read_csv(filename)

                            # ✅ Cleaner duplicate check using .query()
                            is_duplicate = not df_existing.query(
                                "employee_id == @record['employee_id'] and month == @record['month']"
                            ).empty

                            if is_duplicate:
                                st.warning(
                                    "⚠️ Salary record for this employee and month already exists. Skipping save.")
                                return
                        else:
                            df_existing = pd.DataFrame()

                        # 💾 Save new record
                        df_new = pd.DataFrame([record])
                        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                        df_combined.to_csv(filename, index=False)
                        st.success("✅ Salary record saved!")
                    except Exception as e:
                        st.error(f"❌ Failed to save salary record: {e}")


                def calculate_leave_concession(full_days, half_days, fixed_salary, total_working_days):
                    """
                    Returns: tuple of (leave_concession_days, leave_concession_amount)
                    """

                    def get_leave_concession(full, half):
                        effective = full + 0.5 * half
                        return 1.2 if effective < 3 else 0

                    def compute_concession_amount(fixed_salary, total_working_days, full_days, half_days):
                        leave_concession = get_leave_concession(full_days, half_days)
                        st.session_state["leave_concession"] = leave_concession
                        if total_working_days > 0:
                            amount = round((fixed_salary / total_working_days) * leave_concession, 2)
                        else:
                            amount = 0
                        return leave_concession, amount

                    return compute_concession_amount(fixed_salary, total_working_days, full_days, half_days)


                def get_payroll_badges(record):
                    badges = []

                    if record.get("festival_bonus", 0) > 0:
                        badges.append("🎉 Festival Bonus")

                    if record.get("leave_encashment", 0) > 0:
                        badges.append("💰 Leave Encashment")

                    if record.get("extra_hours", 0) >= 10:
                        badges.append("⚡ Extra Hours Hero")

                    if record.get("full_days", 0) >= 22:
                        badges.append("🥇 Consistent Attendance")

                    if record.get("leave_concession_amount", 0) > 0:
                        badges.append("🛡️ Leave Concession")

                    return " | ".join(badges) if badges else "—"


                # 💾 Load log_df globally
                if "log_df" not in st.session_state:
                    if os.path.exists("data/salary_log.csv"):
                        st.session_state.log_df = pd.read_csv("data/salary_log.csv")
                    else:
                        st.warning("🚫 salary_log.csv not found.")
                        st.stop()

                log_df = st.session_state["log_df"]

                # 🔄 Parse date fields for structured overview
                log_df["salary_month"] = pd.to_datetime(log_df["salary_month"], format="mixed", errors="coerce")
                log_df["month_num"] = log_df["salary_month"].dt.month
                log_df["year"] = log_df["salary_month"].dt.year
                log_df["month_display"] = log_df["salary_month"].dt.strftime("%B %Y")

                # if st.session_state["user_role"] == "admin":
                st.subheader("📁 Salary Log (Admin Only)")
                # --- Financial Year Settings ---
                TARGET_FY_YEAR = 2025


                def get_fy_bounds(target_year):
                    fy_start = f"{target_year}-04"
                    fy_end = f"{target_year + 1}-03"
                    return fy_start, fy_end


                fy_start, fy_end = get_fy_bounds(TARGET_FY_YEAR)

                # --- UI Validation Limits ---
                salary_limits = {
                    "net_salary": (10000, 500000),
                    "bonus": (0, 100000),
                    "pf": (0, 30000),
                    "tax": (0, 200000)
                }

                # --- Load and Clean Salary Log ---
                salary_df = pd.read_csv("data/salary_log.csv")

                # Handle full dates like '2025-07-13' and convert to 'YYYY-MM'
                salary_df['salary_month'] = salary_df['salary_month'].astype(str).str.slice(0, 7)

                # Drop duplicates
                salary_df = salary_df.drop_duplicates(subset=['employee_id', 'salary_month'], keep='last')

                # --- Archive Older Records ---
                active_salary_df = salary_df[salary_df['salary_month'] >= fy_start]
                archived_salary_df = salary_df[salary_df['salary_month'] < fy_start]

                archive_filename = f"salary_archive_before_{fy_start}.csv"

                if not archived_salary_df.empty:
                    archived_salary_df.to_csv(archive_filename, index=False)
                    st.success(f"📁 Archived older salary records to `{archive_filename}`")

                    if os.path.exists(archive_filename):
                        st.info(f"🗃️ Archive file `{archive_filename}` was created successfully.")
                    else:
                        st.error(f"❌ Archive file `{archive_filename}` was not found.")
                else:
                    st.info("✅ No records to archive this time.")

                # Work only on active FY
                salary_df = active_salary_df


                # --- Helper Functions ---
                def generate_month_list(start_year, start_month):
                    now = datetime.now()
                    start = datetime(start_year, start_month, 1)
                    months = pd.date_range(start=start, end=now, freq='MS')
                    return [dt.strftime('%Y-%m') for dt in months]


                def get_paid_months(df, emp_id):
                    emp_records = df[df['employee_id'] == emp_id]
                    return emp_records['salary_month'].dropna().unique().tolist()


                # --- App UI ---
                st.subheader("📊 Salary Log Overview")
                st.dataframe(salary_df.tail(5))
                #st.write("📋 Columns:", salary_df.columns.tolist())

                available_months = generate_month_list(start_year=TARGET_FY_YEAR, start_month=4)
                emp_id = st.selectbox("Select Employee ID", salary_df['employee_id'].unique())
                paid_months = get_paid_months(salary_df, emp_id)

                for m in available_months:
                    if m in paid_months:
                        st.button(f"🕓 {m} (Paid)", disabled=True)
                    else:
                        if st.button(f"{m} (Add Entry)", key=f"add_{emp_id}_{m}"):
                            st.success(f"✔️ Ready to add salary for {emp_id} in {m}")

                            with st.form(f"form_{emp_id}_{m}"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    net_salary = st.number_input("Net Salary",
                                                                 min_value=salary_limits["net_salary"][0],
                                                                 max_value=salary_limits["net_salary"][1])
                                    bonus = st.number_input("Festival Bonus",
                                                            min_value=salary_limits["bonus"][0],
                                                            max_value=salary_limits["bonus"][1])
                                with col2:
                                    pf = st.number_input("Employee PF",
                                                         min_value=salary_limits["pf"][0],
                                                         max_value=salary_limits["pf"][1])
                                    tax = st.number_input("Tax Deduction",
                                                          min_value=salary_limits["tax"][0],
                                                          max_value=salary_limits["tax"][1])

                                submitted = st.form_submit_button("Submit Salary Entry")

                                if submitted:
                                    if pf + tax > net_salary + bonus:
                                        st.error("❌ Deductions exceed total salary components.")
                                    else:
                                        new_entry = {
                                            "employee_id": emp_id,
                                            "month": m,
                                            "net_salary": net_salary,
                                            "bonus": bonus,
                                            "employee_pf": pf,
                                            "tax_deduction": tax
                                        }

                                        is_duplicate = ((salary_df['employee_id'] == emp_id) &
                                                        (salary_df['month'] == m)).any()
                                        if not is_duplicate:
                                            salary_df = pd.concat([salary_df, pd.DataFrame([new_entry])],
                                                                  ignore_index=True)
                                            salary_df.to_csv("salary_log.csv", index=False)
                                            st.success(f"💾 Salary entry saved for {emp_id} - {m}")
                                        else:
                                            st.warning(f"⚠️ Entry already exists for {emp_id} in {m}")

                # else:
                # st.warning("This section is restricted to administrators.")

                # ----------------------------

                with tab1:
                    st.write("📊 Salary Overview")

                    # ✅ Now this tab starts properly

                    # DECEMBER leave encashment checkbox
                    apply_encashment = False
                    if selected_month.lower() == "december":
                        apply_encashment = st.checkbox("💰 Apply Leave Encashment for December?", value=True)

                    if st.button("📥 Calculate Payroll & Generate Payslip"):
                        # 💰 Salary Calculations
                        base_salary = 0
                        effective_working_days = full_day_count + 0.5 * half_day_count

                        if "lop_days" not in st.session_state:
                            st.session_state["lop_days"] = 0

                        # 📊 Attendance Stats
                        full_day_count = (monthly_data["attendance_status"] == "Full Day").sum()
                        half_day_count = (monthly_data["attendance_status"] == "Half Day").sum()

                        # ⚠️ Attendance Check for Concession Eligibility
                        if full_day_count + half_day_count == 0:
                            st.warning(
                                "⚠️ No valid attendance recorded this month. Leave concession cannot be applied.")
                            leave_concession, leave_concession_amount = calculate_leave_concession(
                                full_day_count, half_day_count, fixed_salary, total_working_days
                            )
                            st.session_state["leave_concession"] = leave_concession
                            st.session_state["leave_concession_amount"] = leave_concession_amount

                            # ✅ NOW place this line:
                            total_paid_coverage = leave_concession + leave_opening + leave_accrual

                            lop_days = max(earned_leave_taken - total_paid_coverage, 0)
                            lop_deduction_amount = round((fixed_salary / total_working_days) * lop_days, 2)
                            st.session_state["lop_days"] = lop_days
                            st.session_state["lop_deduction_amount"] = lop_deduction_amount
                            st.session_state["lop_deduction"] = lop_deduction_amount
                        st.session_state["leave_concession"] = leave_concession
                        prorated_days = effective_working_days + leave_concession
                        base_salary = (fixed_salary / total_working_days) * prorated_days
                        st.session_state["base_salary"] = base_salary

                        # ⏬ Now safely compute salary breakdowns
                        late_deduction = (fixed_salary / total_working_days) * late_day_equiv

                        st.session_state["late_deduction"] = late_deduction

                        extra_pay = total_extra_hours * hourly_rate

                        st.session_state["extra_pay"] = extra_pay

                        tuesday_bonus = (fixed_salary / total_working_days) * tuesdays_worked

                        st.session_state["tuesday_bonus"] = tuesday_bonus

                        lop_deduction = (fixed_salary / total_working_days) * lop_days

                        st.session_state["lop_deduction"] = lop_deduction

                        prorate_pf = st.checkbox("📉 Prorate PF based on salary earned this month?",
                                                     key="prorate_pf")

                        if prorate_pf:
                                pf_base = base_salary
                                st.info("🔍 PF is being calculated on actual salary this month due to low attendance.")
                        else:
                                pf_base = fixed_salary
                                st.caption("🧾 PF is based on fixed salary as per default EPF rules.")

                        employee_pf = min(pf_base * 0.12, 1800)
                        employer_pf = min(pf_base * 0.12, 1800)

                        st.session_state["employee_pf"] = employee_pf
                        st.session_state["employer_pf"] = employer_pf

                        if employee_pf > base_salary:
                                st.warning(
                                    "⚠️ PF deduction exceeds base salary. This might look excessive to the employee.")


                        # 💰 Leave Encashment + Total Payout
                        encashment_payout = 0
                        encashable_days = max(leave_closing - carry_forward_limit, 0)
                        leave_day_rate = fixed_salary / total_working_days
                        if apply_encashment and encashable_days > 0:
                            encashment_payout = encashable_days * leave_day_rate

                            st.session_state["encashment_payout"] = encashment_payout

                            carry_forward = 0  # or load from previous record

                            leave_closing -= encashable_days

                            # 👇 Store the final leave balance
                            st.session_state["leave_closing"] = leave_closing

                        # 🗓️ Leave Summary Block (always render if variables exist)
                        if "leave_closing" in st.session_state:
                            st.subheader("🗓️ Leave Summary")
                            st.markdown(f"- **Opening Balance**: {carry_forward:.1f} days")
                            st.markdown(f"- **Accrued This Month**: {leave_concession:.1f} days")
                            st.markdown(f"- **Leave Taken**: {lop_days:.1f} days")
                            st.markdown(f"- **Closing Balance**: {st.session_state['leave_closing']:.1f} days")

                            if leave_concession > 0 and "leave_concession_amount" in st.session_state:
                                st.markdown(
                                    f"💰 _₹{st.session_state['leave_concession_amount']:,.2f} of base salary was granted for "
                                    f"{leave_concession:.1f} day leave concession._"
                                )
                        else:
                            st.info("👆 Click 'Calculate Payroll' to view updated leave summary.")

                        total_payout = (
                                base_salary + extra_pay + tuesday_bonus + festival_bonus
                                - late_deduction - lop_deduction + encashment_payout
                        )

                        # ✅ Store value in session state
                        st.session_state["total_payout"] = total_payout

                        annual_income = total_payout * 12
                        tax_deduction = calculate_monthly_tax(annual_income)

                        st.session_state["tax_deduction"] = tax_deduction

                        deductions = compute_statutory_deductions(
                            gross=total_payout,
                            basic=fixed_salary * 0.4,
                            insurance_opt_in=insurance_opt,
                            override_pf=False
                        )

                        total_emp_deduction = deductions["employee"]["total_deduction"] + tax_deduction + employee_pf
                        net_salary = total_payout - total_emp_deduction

                        st.session_state["net_salary"] = net_salary

                        if net_salary < employee_pf:
                            st.error("⚠️ Net salary is less than PF deduction! Please review this case manually.")

                        total_employer_contribution = deductions["employer"]["total_contribution"] + employer_pf
                        employer_ctc = total_payout + total_employer_contribution

                        st.session_state["employer_ctc"] = employer_ctc

                        st.success(
                            f"✅ Payroll calculated! Net Salary: ₹{net_salary:,.2f}, Employer CTC: ₹{employer_ctc:,.2f}")

                        # 💾 Save Record
                        save_salary_record({
                            "employee_id": employee_id,
                            "employee_name": employee_name,
                            "month": selected_date.strftime("%Y-%m-%d"),  # 👈 Shows full date like 2025-07-09,
                            "net_salary": net_salary,
                            "base_salary": base_salary,
                            "extra_pay": extra_pay,
                            "tuesday_bonus": tuesday_bonus,
                            "festival_bonus": festival_bonus,
                            "employee_pf": employee_pf,
                            "tax_deduction": tax_deduction,
                            "ctc": employer_ctc,
                            "timestamp": datetime.now(),
                            "extra_hours": total_extra_hours,
                            "late_marks": late_mark_count,
                            "full_days": full_day_count,
                            "half_days": half_day_count,
                            "earned_leave_taken": earned_leave_taken,
                            "leave_accrued": leave_accrual,
                            "leave_balance": leave_closing,
                            "lop_deduction": lop_deduction,
                            "leave_encashment": encashment_payout,
                            "leave_concession": leave_concession,
                            "leave_concession_amount": leave_concession_amount,

                        })

                        st.success("✅ Salary saved!")


                    # Create a list of recent months
                    def get_recent_months(n=12):
                        today = datetime.today()
                        return [
                            f"{calendar.month_name[(today.month - i - 1) % 12 + 1]} {today.year - ((today.month - i - 1) // 12)}"
                            for i in range(n)
                        ]

                    # 🗓️ Month selection dropdown
                selected_month = st.selectbox("Select a payroll month to view salary details:",
                                              get_recent_months())


                view_mode = st.radio("View Mode", ["My Salary", "Team Payroll"])

                # Common filters
                def parse_month(selected_month):
                    if selected_month == "All":
                        return None
                    try:
                        return datetime.strptime(selected_month, "%B %Y")
                    except ValueError:
                        return datetime.strptime(selected_month, "%Y-%m")


                dt = parse_month(selected_month)
                if dt is None:
                    st.info("Showing data for all months.")
                else:
                    year = dt.year
                    month_num = dt.month

                # Optional employee filter
                selected_employee = st.session_state.get("employee_name_clean", None)

                if view_mode == "My Salary":
                    emp_record = employee_master[
                        employee_master["employee_name"].str.lower().str.strip() == selected_employee
                        ]
                    selected_department = emp_record["department"].values[0]
                    selected_role = emp_record["role"].values[0]

                # Department & role selection (shown only in team view)
                # Sanitize and standardize entries
                employee_master["department"] = employee_master["department"].astype(str).str.strip().str.title()
                employee_master["role"] = employee_master["role"].astype(str).str.strip().str.title()

                # Unique dropdown lists
                departments = employee_master["department"].dropna().unique().tolist()
                roles = employee_master["role"].dropna().unique().tolist()

                # 🎛️ Dropdown UI for Team Payroll view
                if view_mode == "Team Payroll":
                    selected_department = st.selectbox("Select Department", departments)
                    selected_role = st.selectbox("Select Role", roles)

                    selected_ids = employee_master[
                        (employee_master["department"] == selected_department) &
                        (employee_master["role"] == selected_role)
                        ]["employee_id"].unique().tolist()

                else:
                    selected_ids = [employee_master[
                                        employee_master["employee_name"].str.lower().str.strip() == selected_employee
                                        ]["employee_id"].values[0]]

                # Filter log data
                filtered_payroll = log_df[
                    (log_df["employee_id"].isin(selected_ids)) &
                    (log_df["month_num"] == month_num) &
                    (log_df["year"] == int(year))
                    ]

                # Merge attendance
                filtered_payroll = filtered_payroll.merge(
                    summary_month[["employee_id", "Total Days Present"]],
                    on="employee_id",
                    how="left"
                )

                if not filtered_payroll.empty:
                    if view_mode == "Team Payroll":
                        st.subheader(f"Payroll for {selected_role} in {selected_department} ({selected_month})")
                    else:
                        st.subheader(f"Salary Details for {selected_employee.title()} ({selected_month})")

                    st.dataframe(filtered_payroll[[
                        "employee_id", "employee_name", "Total Days Present",
                        "net_salary", "base_salary", "festival_bonus", "leave_balance"
                    ]].tail(1 if view_mode == "My Salary" else len(filtered_payroll)))
                else:
                    st.warning("No records found for this selection.")
                    st.session_state["filtered_payroll"] = filtered_payroll
                    st.download_button(
                        label="Download Payroll Data",
                        data=filtered_payroll.to_csv(index=False).encode('utf-8'),
                        file_name=f"{selected_month.replace(' ', '_')}_payroll.csv",
                        mime='text/csv'
                    )


                    # 💡 Breakdown
                    st.subheader(f"💰 Salary Breakdown for {employee_name} - {selected_month}")
                    st.markdown(f"- **Fixed Salary**: ₹{fixed_salary:,.2f}")
                    if "base_salary" in st.session_state:
                        st.markdown(
                            f"- **Base Salary** (Full + Half Days + Concession): ₹{st.session_state['base_salary']:,.2f}")
                    #else:
                        #st.info("👆 Base Salary will appear after payroll is calculated.")

                    if "extra_pay" in st.session_state:
                        st.markdown(
                            f"- **Extra Pay** (from {total_extra_hours:.2f} hrs): ₹{st.session_state['extra_pay']:,.2f}")
                    #else:
                        #st.info("👆 Extra pay will appear once payroll is calculated.")

                    if "tuesday_bonus" in st.session_state:
                        st.markdown(
                            f"- **Tuesday Bonus** (for {tuesdays_worked} Tuesday{'s' if tuesdays_worked != 1 else ''}): ₹{st.session_state['tuesday_bonus']:,.2f}"
                        )
                    #else:
                        #st.info("👆 Tuesday Bonus will appear after payroll is calculated.")
                    if "lop_deduction" in st.session_state and st.session_state["lop_deduction"] > 0:
                            st.markdown(
                                f"- **LOP Deduction (Excess Leave)**: -₹{st.session_state['lop_deduction']:,.2f}")

                    if "festival_bonus" in st.session_state:
                        st.markdown(f"- **Festival Bonus**: ₹{st.session_state['festival_bonus']:,.2f}")
                        if st.session_state["festival_bonus"] > 0 and festival_name:
                            st.markdown(
                                f"- **Festival Bonus ({festival_name})**: ₹{st.session_state['festival_bonus']:,.2f}")
                    #else:
                        #st.info("👆 Festival bonus will appear once payroll is calculated.")

                    if "late_deduction" in st.session_state:
                        st.markdown(
                            f"- **Late Deduction (from {late_mark_count} late marks):** -₹{st.session_state['late_deduction']:,.2f}")
                    #else:
                        #st.info("👆 Late deduction will appear after payroll is calculated.")

                    if "employee_pf" in st.session_state:
                        st.markdown(
                            f"- **Provident Fund Deduction (Employee 12%)**: -₹{st.session_state['employee_pf']:,.2f}")
                    #else:
                        #st.info("👆 Employee PF will appear after payroll calculation.")

                    if "employer_pf" in st.session_state:
                        st.markdown(
                            f"- **Employer PF Contribution (12%)**: ₹{st.session_state['employer_pf']:,.2f}")
                    #else:
                        #st.info("👆 Employer PF will appear after payroll calculation.")

                    if "total_payout" in st.session_state:
                        st.markdown(f"- **Gross Pay Before Tax**: ₹{st.session_state['total_payout']:,.2f}")
                    #else:
                        #st.info("👆 Click 'Calculate Payroll' first to see Gross Pay.")

                    if "tax_deduction" in st.session_state:
                        st.markdown(f"- **Tax Deduction**: -₹{st.session_state['tax_deduction']:,.2f}")
                    #else:
                        #st.info("👆 Tax deduction will appear after payroll calculation.")

                    if "net_salary" in st.session_state:
                        st.markdown(f"- **Net Salary Payable**: ₹{st.session_state['net_salary']:,.2f}")
                   # else:
                        #st.info("👆 Net Salary will appear after payroll is calculated.")

                    if "employer_ctc" in st.session_state:
                        st.markdown(f"- **Employer CTC**: ₹{st.session_state['employer_ctc']:,.2f}")
                    #else:
                       #st.info("👆 Employer CTC will appear after payroll is calculated.")

                    st.subheader("🗓️ Leave Summary")
                    st.markdown(f"- **Opening Balance**: {leave_opening:.1f} days")
                    st.markdown(f"- **Accrued This Month**: {leave_accrual:.1f} days")
                    st.markdown(f"- **Leave Taken**: {earned_leave_taken:.1f} days")
                    st.markdown(f"- **Closing Balance**: {leave_closing:.1f} days")

                    if "encashment_payout" in st.session_state and st.session_state["encashment_payout"] > 0:
                            st.markdown(
                                f"- **Leave Encashment Bonus** ({encashable_days:.1f} days): ₹{st.session_state['encashment_payout']:,.2f}")

                    if "leave_concession_amount" in st.session_state and st.session_state.get("leave_concession",
                                                                                              0) > 0:
                        st.markdown(
                            f"- **Leave Concession Granted** ({st.session_state['leave_concession']:.1f} days): ₹{st.session_state['leave_concession_amount']:,.2f}"
                        )
                    if "lop_days" in st.session_state and st.session_state["lop_days"] > 0:
                        st.markdown(
                            f"- **Loss of Pay (LOP)** ({st.session_state['lop_days']:.1f} days): -₹{st.session_state['lop_deduction_amount']:,.2f}"
                        )

                    # 📄 Add Proration Note
                    if full_day_count + half_day_count == 0:
                        proration_note = "Note: You had no recorded attendance this month. Salary shown is system-generated."
                    elif full_day_count + half_day_count < total_working_days:
                        proration_note = f"Note: Salary has been prorated based on {full_day_count + 0.5 * half_day_count:.1f} working days out of {total_working_days}."
                    else:
                        proration_note = None

                    pdf_bytes = generate_payslip_pdf(
                        employee_name=employee_name,
                        employee_id=employee_id,
                        selected_month=selected_month,
                        base_salary=st.session_state.get("base_salary", 0),
                        extra_pay=st.session_state.get("extra_pay", 0),
                        tuesday_bonus=st.session_state.get("tuesday_bonus", 0),
                        festival_bonus=st.session_state.get("festival_bonus", 0),
                        late_deduction=st.session_state.get("late_deduction", 0),
                        employee_pf=st.session_state.get("employee_pf", 0),
                        employer_pf=st.session_state.get("employer_pf", 0),
                        tax_deduction=st.session_state.get("tax_deduction", 0),
                        net_salary=st.session_state.get("net_salary", 0),
                        late_marks=late_mark_count,
                        full_days=full_day_count,
                        half_days=half_day_count,
                        employee_data=employee_data,
                        employee_name_clean=employee_name_clean,
                        proration_note=proration_note,
                        leave_concession=st.session_state.get("leave_concession", 0),
                        leave_concession_amount=st.session_state.get("leave_concession_amount", 0),
                        lop_days = st.session_state.get("lop_days", 0)


                    )

                    st.download_button(
                        label="📄 Download Payslip PDF",
                        data=pdf_bytes,
                        file_name=f"Payslip_{selected_month}_{employee_name.replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )

                log_df["employee_id"] = pd.to_numeric(log_df["employee_id"], errors="coerce")
                employee_master["employee_id"] = pd.to_numeric(employee_master["employee_id"], errors="coerce")

                # 1. Merge department into log_df, if you have an employee_master DataFrame:
                if "department" not in log_df.columns:
                    # Make sure employee_master exists and has the two columns
                    if {"employee_id", "department"}.issubset(employee_master.columns):
                        log_df = (
                            log_df
                            .merge(
                                employee_master[["employee_id", "department"]],
                                on="employee_id",
                                how="left"
                            )
                            .fillna({"department": "Unknown"})
                        )
                    else:
                        st.warning("⚠️ employee_master missing 'employee_id' or 'department' columns. Skipping merge.")



                    # ------------------ Tab 2: Company Overview ------------------
                    with tab2:


                        st.subheader("📊 Company Payroll Overview")
                        #st.write("📂 Department-wise CTC", salary_df.groupby("department")["ctc"].sum())
                        tab1, tab2 = st.tabs(["Salary Insights", "Leave & Attendance"])

                        @st.cache_data
                        def generate_leave_df(employee_master):
                            import pandas as pd
                            from datetime import datetime
                            import random

                            leave_types = ["Sick", "Casual", "Earned"]
                            employee_ids = employee_master["employee_id"].dropna().unique().tolist()

                            leave_records = []
                            for eid in employee_ids[:30]:  # Use 30 employees for demo
                                for _ in range(random.randint(2, 5)):
                                    leave_date = datetime(2024, random.randint(1, 12), random.randint(1, 28))
                                    leave_records.append({
                                        "employee_id": eid,
                                        "leave_type": random.choice(leave_types),
                                        "leave_date": leave_date
                                    })

                            leave_df = pd.DataFrame(leave_records)
                            return leave_df


                        leave_df = generate_leave_df(employee_master)

                        # ⏰ Attendance status options
                        status_choices = ["Present", "Absent", "Leave", "WeekOff"]

                        attendance_records = []
                        start_date = datetime(2024, 1, 1)
                        for eid in employee_id[:30]:
                            for i in range(180):  # 6 months of data
                                current_day = start_date + timedelta(days=i)
                                status = random.choices(status_choices, weights=[0.8, 0.05, 0.1, 0.05])[0]
                                attendance_records.append({
                                    "employee_id": eid,
                                    "date": current_day,
                                    "status": status
                                })

                        # 📋 Create attendance_df
                        attendance_df = pd.DataFrame(attendance_records)

                        #st.write("🧩 Columns in salary_df:", salary_df.columns.tolist())




                        def merge_with_department(salary_df, employee_master):
                            salary_df["employee_id"] = pd.to_numeric(salary_df["employee_id"], errors="coerce")
                            employee_master["employee_id"] = pd.to_numeric(employee_master["employee_id"],
                                                                           errors="coerce")

                            salary_df = salary_df.merge(
                                employee_master[["employee_id", "department"]],
                                on="employee_id",
                                how="left"
                            ).fillna({"department": "Unknown"})

                            return salary_df  # 👈 THIS LINE is essential


                        #st.write("✅ Merged columns:", salary_df.columns.tolist())
                        # 👇 Step 1: Merge department first!
                        salary_df = merge_with_department(salary_df, employee_master)

                        # 👇 Step 2: Validate
                        if salary_df is None or salary_df.empty:
                            st.warning("⚠️ salary_df is not initialized or has no data.")
                        elif "department" not in salary_df.columns:
                            st.error("🚫 'department' column not found after merge.")
                        else:
                            #st.write("✅ Merged columns:", salary_df.columns.tolist())
                            st.write("📊 Department-wise CTC", salary_df.groupby("department")["ctc"].sum())
                        #st.write("🔍 Unique Departments:", salary_df["department"].unique())

                        leave_df = merge_with_department(leave_df, employee_master)
                        attendance_df = merge_with_department(attendance_df, employee_master)


                        #st.write("👀 Department values in master:", employee_master["department"].unique())
                        #common_ids = set(log_df["employee_id"]) & set(employee_master["employee_id"])
                        #st.write("🔗 Common employee IDs:", len(common_ids))
                        #st.write("🔍 Total rows in log_df:", log_df.shape[0])
                        # Ensure employee_id columns are numeric for reliable merging
                        log_df["employee_id"] = pd.to_numeric(log_df["employee_id"], errors="coerce")
                        employee_master["employee_id"] = pd.to_numeric(employee_master["employee_id"], errors="coerce")

                        st.write("🔍 Missing employee IDs in log_df:", log_df["employee_id"].isna().sum())

                        # STEP 1: Merge department into log_df if not already present
                        if "department" not in log_df.columns:
                            if {"employee_id", "department"}.issubset(employee_master.columns):
                                log_df = (
                                    log_df
                                    .merge(
                                        employee_master[["employee_id", "department"]],
                                        on="employee_id",
                                        how="left"
                                    )
                                    .fillna({"department": "Unknown"})
                                )
                                st.write("📊 Department distribution after merge:", log_df["department"].value_counts())
                            else:
                                st.warning(
                                    "⚠️ employee_master missing 'employee_id' or 'department' columns. Skipping merge.")
                                st.write("📊 Skipped merge — current columns in log_df:", log_df.columns.tolist())

                        # STEP 2: Apply department filtering from log_df (merged or not)
                        # Re-confirm merge pulled department info into log_df
                        #st.write("🧩 Department column sample:",
                                 #log_df[["employee_id", "department"]].drop_duplicates().head())

                        # STEP: Get all departments from log_df and build dropdown options
                        # Strip and standardize all department entries first
                        #log_df["department"] = log_df["department"].astype(str).str.strip()

                        # Preview full department variety
                        #st.write("📊 Department distribution:", log_df["department"].value_counts())

                        # Build dropdown list safely
                       # departments = sorted(set(log_df["department"].dropna()))
                        #departments = ["All"] + departments

                        # Show list for confirmation
                        #st.write("🔍 Dropdown options:", departments)

                        # Render selectbox
                        selected_dept = st.selectbox("📂 Filter by Department", departments)

                        # Generate month dropdown options from log_df
                        available_months = sorted(log_df["month"].dropna().unique())
                        available_months = ["All"] + available_months  # Optional "All" choice

                        # Render month filter
                        selected_month = st.selectbox("🗓️ Filter by Month", available_months)

                        filtered_df = log_df.copy()

                        if selected_dept != "All":
                            filtered_df = filtered_df[filtered_df["department"] == selected_dept]

                        if selected_month != "All":
                            filtered_df = filtered_df[filtered_df["month"] == selected_month]

                        st.dataframe(filtered_df)

                        # Apply filter
                        if selected_dept != "All":
                            df_dept = log_df[log_df["department"] == selected_dept].copy()
                        else:
                            df_dept = log_df.copy()

                        st.write(f"✅ Selected: `{selected_dept}` | Records: {df_dept.shape[0]}")

                        # 2. “My Salary” view
                        if view_mode == "My Salary":
                            bonus, leave = 0, 0
                            net_salary = st.session_state.get("net_salary", 0)
                            if not filtered_payroll.empty:
                                bonus = filtered_payroll["festival_bonus"].iloc[0]
                                leave = filtered_payroll["leave_balance"].iloc[0]
                                st.markdown("---")
                                st.markdown("#### 💼 Perks Overview")
                                if bonus > 0:
                                    st.success(f"🎁 Festival Bonus Received: ₹{bonus}")
                                if leave < 0:
                                    st.info(f"💸 Leave Encashed: ₹{abs(leave)}")
                                elif leave > 0:
                                    st.warning(f"🏖️ Unused Leave Balance: {leave} day(s)")
                                final_settlement = bonus + net_salary + (leave if leave < 0 else 0)
                                st.success(f"💰 Final Settlement Estimate: ₹{final_settlement:,.2f}")
                            else:
                                st.warning("⚠️ No payroll data available for this employee/month.")

                            # 3. Prepare df_dept for badges, score, dedication_index
                        for col in ["festival_bonus", "leave_encashment", "performance_bonus",
                                    "extra_hours", "late_marks", "full_days"]:
                            if col not in df_dept.columns:
                                df_dept[col] = 0

                        df_dept["badges"] = (
                            df_dept.apply(get_payroll_badges, axis=1)
                            .str.replace(">", "")
                            .str.strip()
                        )
                        df_dept["payroll_month"] = df_dept["month"].dt.strftime("%B %Y").fillna("—")
                        df_dept["score"] = df_dept["full_days"] * 2 + df_dept["extra_hours"] * 0.5 - df_dept[
                            "late_marks"]
                        df_dept["dedication_index"] = df_dept["score"] + (df_dept["extra_hours"] * 5)

                        # 4. Top 3 Dedicated Employees
                        top_three = (
                            df_dept
                            .groupby(["employee_id", "employee_name"])["dedication_index"]
                            .sum()
                            .reset_index()
                            .sort_values("dedication_index", ascending=False)
                            .head(3)
                        )

                        st.subheader("🏆 Top 3 Dedicated Employees")
                        if not top_three.empty:
                            # Employee of the Month
                            first = top_three.iloc[0]
                            st.subheader("🏅 Employee of the Month")
                            st.success(
                                f"🏆 {first['employee_name'].title()} with dedication index {first['dedication_index']:.2f}")

                            # Full Top 3
                            for rank, row in top_three.reset_index(drop=True).iterrows():
                                badge = ["🥇", "🥈", "🥉"][rank]
                                st.markdown(f"""
                                       <div style='padding:10px; margin-bottom:10px;
                                                   border-radius:8px; background:#f0f8ff;
                                                   border-left:6px solid #4682b4;'>
                                         <h4 style='margin:0'>{badge} {row['employee_name'].title()}</h4>
                                         <p style='margin:4px 0;'>📈 Dedication Index: {row['dedication_index']:.2f}</p>
                                       </div>
                                   """, unsafe_allow_html=True)
                        else:
                            st.warning("⚠️ No dedication data available to generate Top 3.")

                        # 5. Payroll Summary & Charts
                        highlights = df_dept[df_dept["badges"] != "—"]
                        summary_df = highlights.groupby("employee_name")["badges"] \
                            .apply(lambda b: " | ".join(b.unique())) \
                            .reset_index()

                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("✨ Featured Employees")
                        for _, row in summary_df.iterrows():
                            st.markdown(f"""
                                  <div style='padding:12px; margin-bottom:12px;
                                              border-radius:10px; background:#fef6e4;
                                              box-shadow:0 2px 6px rgba(0,0,0,0.1);'>
                                      <h4 style='margin:0'>{row['employee_name'].title()}</h4>
                                      <p style='margin:4px 0;'>🏅 {row['badges']}</p>
                                  </div>
                              """, unsafe_allow_html=True)

                    with col2:
                        st.subheader("📊 Payroll Summary")
                        st.metric("Total YTD Salary", f"₹{df_dept['net_salary'].sum():,.2f}")
                        st.metric("Badges Awarded", str(highlights.shape[0]))
                        st.metric("Employees Processed", str(df_dept["employee_id"].nunique()))
                        salary_chart = df_dept.groupby("payroll_month")["net_salary"].sum().reset_index()
                        st.bar_chart(salary_chart.set_index("payroll_month"))

                        with st.expander("📄 Recent Payroll Entries"):
                            st.dataframe(
                                df_dept[["employee_id", "employee_name", "payroll_month", "net_salary", "badges"]].tail(
                                    5))

                            # 6. Dedication Index Trend
                            st.markdown("---")
                            st.subheader("📈 Dedication Index Trend")
                            trend_df = (
                                df_dept
                                .groupby(df_dept["month"].dt.to_period("M"))["dedication_index"]
                                .sum()
                                .reset_index()
                            )
                            trend_df["month_str"] = trend_df["month"].dt.strftime("%b %Y")
                            st.line_chart(trend_df.set_index("month_str")["dedication_index"], height=250)

                        # 7. Leave Balance Overview
                        st.markdown("---")
                        st.subheader("🗓️ Leave Balance Overview")
                        if "leave_balance" in df_dept.columns:
                            leave_summary = (
                                df_dept.groupby(["employee_id", "employee_name"])["leave_balance"]
                                .last()
                                .reset_index()
                                .sort_values(by="leave_balance", ascending=False)
                            )
                            with st.expander("📁 Leave Balances"):
                                st.dataframe(leave_summary)
                            st.metric("📌 Average Leave Balance", f"{leave_summary['leave_balance'].mean():.1f} days")
                        else:
                            leave_summary = pd.DataFrame()
                            st.info("ℹ️ No leave data found yet. Run payroll with leave tracking first.")

                            # 📄 Generate PDF Summary & store in session_state


                        if st.button("📤 Email Monthly Report"):
                            if "pdf_buffer" in st.session_state and "file_name" in st.session_state:
                                smtp_config = {
                                    "host": st.secrets["SMTP_HOST"],
                                    "port": st.secrets["SMTP_PORT"],
                                    "user": st.secrets["SMTP_USER"],
                                    "password": st.secrets["SMTP_PASSWORD"],
                                    "sender": st.secrets["SMTP_SENDER"]
                                }
                                recipients = ["hr@company.com", "finance@company.com"]
                                send_report_via_email(
                                    st.session_state["pdf_buffer"],
                                    st.session_state["file_name"],
                                    recipients,
                                    smtp_config
                                )
                                st.success("✅ Monthly report emailed successfully!")
                            else:
                                st.error("⚠️ Please generate the PDF summary before emailing it.")


                       #def generate_payroll_heatmap(df, employee_col="Employee", month_col="Month",
                                                        # salary_col="Salary"):
                           #pivot = df.pivot_table(index=employee_col, columns=month_col, values=salary_col,
                                                  # fill_value=0)
                            #fig = px.imshow(pivot, color_continuous_scale="Bluered", text_auto=True)
                           # fig = px.imshow(pivot, color_continuous_scale="Bluered", zmin=25000, zmax=30000)

                            #fig.update_layout(title="Payroll Heatmap", xaxis_title=month_col, yaxis_title=employee_col)
                           # return fig


                        # 👉 Clean and format the month column before visualization
                       # df_dept["month"] = pd.to_datetime(df_dept["month"], errors="coerce").dt.strftime("%b")

                        # Now generate the heatmap
                        #fig = generate_payroll_heatmap(
                           # df_dept,
                            #employee_col="employee_name",
                            #month_col="month",
                            #salary_col="net_salary"
                        #)
                        #st.subheader("📊 Monthly Payroll Heatmap")
                        #st.plotly_chart(fig, use_container_width=True)

                    # 📊 Heatmap function with emoji overlay
                    def generate_payroll_heatmap(df, employee_col="employee_name", month_col="month",
                                                 salary_col="net_salary"):
                        # Format month column
                        df[month_col] = pd.to_datetime(df[month_col], errors="coerce").dt.strftime("%b %Y")

                        # Create pivot table
                        pivot = df.pivot_table(index=employee_col, columns=month_col, values=salary_col, fill_value=0)

                        # Sort employees by dedication score
                        if "dedication_index" in df.columns:
                            sorted_employees = df.sort_values("dedication_index", ascending=False)[
                                employee_col].unique()
                            pivot = pivot.loc[sorted_employees]

                        # Emoji label for top performers
                        top_threshold = pivot.max().max() * 0.98
                        label_matrix = pivot.applymap(
                            lambda val: f"🥇 {val:.0f}" if val >= top_threshold else f"{val:.0f}")

                        # Build heatmap
                        fig = go.Figure(data=go.Heatmap(
                            z=pivot.values,
                            x=pivot.columns,
                            y=pivot.index,
                            text=label_matrix.values,
                            texttemplate="%{text}",
                            colorscale="Bluered",
                            zmin=25000,
                            zmax=30000
                        ))
                        fig.update_layout(
                            title="Payroll Heatmap with Highlights",
                            xaxis_title="Month",
                            yaxis_title="Employee"
                        )
                        return fig


                    # 🧭 Sidebar filters
                    #selected_dept = st.selectbox("📂 Select Department", df_dept["department"].unique())
                    #selected_month = st.selectbox("🗓️ Select Month", df_dept["month"].unique())

                    # 🔍 Apply filters
                    filtered_df = df_dept[
                        (df_dept["department"] == selected_dept) &
                        (df_dept["month"] == selected_month)
                        ]

                    # 📊 Display Payroll Heatmap
                    st.subheader("📊 Monthly Payroll Heatmap")
                    fig = generate_payroll_heatmap(filtered_df)
                    st.plotly_chart(fig, use_container_width=True)

                    # ✅ Convert key columns to numeric
                    for col in ["net_salary", "festival_bonus", "leave_balance"]:
                        if col in df_dept.columns:
                            df_dept[col] = pd.to_numeric(df_dept[col], errors="coerce")

                    # 💼 Department-Wise Summary
                    dept_summary = df_dept.groupby("department")[
                        ["net_salary", "festival_bonus", "leave_balance"]].mean().round(0)

                    st.subheader("💼 Department-Wise Salary Overview")
                    st.dataframe(dept_summary)

                    # 📈 Net Salary Bar Chart
                    fig = px.bar(
                        dept_summary.reset_index(),
                        x="net_salary",
                        y="department",
                        orientation="h",
                        color="net_salary",
                        color_continuous_scale="Viridis",
                        title="Department Salary Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)


                    def merge_with_department(df, employee_master):
                        df["employee_id"] = pd.to_numeric(df["employee_id"], errors="coerce")
                        employee_master["employee_id"] = pd.to_numeric(employee_master["employee_id"], errors="coerce")

                        # Normalize columns
                        df.columns = df.columns.str.strip().str.lower()
                        employee_master.columns = employee_master.columns.str.strip().str.lower()

                        # Remove pre-existing 'department' and 'role' to prevent suffixing
                        df = df.drop(columns=[col for col in ["department", "role"] if col in df.columns])

                        # Merge cleanly
                        merged = df.merge(
                            employee_master[["employee_id", "department", "role"]],
                            on="employee_id",
                            how="left"
                        ).fillna({"department": "Unknown", "role": "Unknown"})

                        return merged


                    # 👥 Extract dropdown options
                    departments = sorted(employee_master["department"].dropna().unique().tolist())
                    designations = sorted(employee_master["role"].dropna().unique().tolist())
                    leave_types = sorted(leave_df["leave_type"].dropna().unique().tolist())

                    # 🎛️ Sidebar filters
                    selected_dept = st.selectbox("📁 Select Department", ["All"] + departments)
                    selected_role = st.multiselect("🧑‍💼 Filter by Role", designations)
                    selected_leave_type = st.multiselect("🌴 Leave Types", leave_types)


                    def apply_filters(df):
                        if selected_dept != "All":
                            df = df[df["department"] == selected_dept]
                        if selected_role:
                            df = df[df["role"].isin(selected_role)]
                        return df


                    # 📄 Salary Data Handling
                    salary_df = merge_with_department(salary_df, employee_master)
                    salary_df.columns = salary_df.columns.str.strip().str.lower()
                    salary_df = apply_filters(salary_df)

                    # 🔧 Add missing columns for aggregation
                    for col in ["basic", "hra", "deductions"]:
                        if col not in salary_df.columns:
                            salary_df[col] = 0  # or np.nan based on preference

                    # 💡 Derive deductions from existing components
                    salary_df["deductions"] = (
                            salary_df.get("tax_deduction", 0) +
                            salary_df.get("employee_pf", 0) +
                            salary_df.get("lop_deduction", 0)
                    )

                    # 📊 Salary Summary by Department
                    salary_summary = salary_df.groupby("department").agg({
                        "basic": "sum",
                        "hra": "sum",
                        "deductions": "sum",
                        "ctc": "sum"
                    }).reset_index()
                    st.bar_chart(salary_summary.set_index("department")["ctc"])

                    # 📅 Leave Summary
                    leave_df = merge_with_department(leave_df, employee_master)
                    leave_df = apply_filters(leave_df)
                    leave_df["leave_date"] = pd.to_datetime(leave_df["leave_date"], errors="coerce")

                    # Optional: strip time, if needed
                    leave_df["leave_date"] = leave_df["leave_date"].dt.date

                    # Filter for current year only
                    leave_df = leave_df[pd.to_datetime(leave_df["leave_date"]).dt.year == 2025]

                    # Add month column after filtering
                    leave_df["month"] = pd.to_datetime(leave_df["leave_date"]).dt.to_period("M")

                    monthly_leave = leave_df.groupby(["department", "leave_date", "leave_type"]).size().reset_index(
                        name="count")
                    st.write("📊 Monthly Leave Summary", monthly_leave)

                    # 📋 Attendance Summary
                    attendance_df = merge_with_department(attendance_df, employee_master)
                    attendance_df = apply_filters(attendance_df)

                    # 🧾 Leave Balance Overview
                    try:
                        leave_balance_df = pd.read_csv("leave_balance_df.csv")  # ✅ Load CSV before proceeding
                    except FileNotFoundError:
                        st.warning("🚫 leave_balance_df.csv not found. Please check the file name or path.")
                    else:
                        if isinstance(leave_balance_df, pd.DataFrame):
                            st.markdown("### 🧾 Leave Balance Overview")

                            # 📌 Diagnostics Before Merge
                            st.write("📏 Shape before merge:", leave_balance_df.shape)
                            st.write("💡 Columns before merge:", leave_balance_df.columns.tolist())
                            st.write("🧪 Preview before merge:", leave_balance_df.head())

                            # 🔄 Merge department and role info safely
                            leave_balance_df = merge_with_department(leave_balance_df, employee_master)

                            # 🧼 Apply sidebar filters (if any)
                            leave_balance_df = apply_filters(leave_balance_df)

                            # 📊 Post-filter diagnostics
                            st.write("📏 Shape after filter:", leave_balance_df.shape)
                            st.write("🧾 Columns after merge and filter:", leave_balance_df.columns.tolist())

                            # 🔍 Required column check
                            required_cols = ["employee_id", "department", "total_allocated", "leaves_taken"]
                            missing = [col for col in required_cols if col not in leave_balance_df.columns]

                            if missing:
                                st.warning(f"⚠️ Missing columns: {', '.join(missing)}")
                            elif leave_balance_df.empty:
                                st.info("ℹ️ No data available for leave balance after filtering.")
                            else:
                                # ✅ Perform calculation
                                leave_balance_df["unused"] = leave_balance_df["total_allocated"] - leave_balance_df[
                                    "leaves_taken"]

                                # 📊 Display summary
                                st.subheader("📋 Leave Balance Summary")
                                st.dataframe(leave_balance_df[["employee_id", "department", "unused"]])
                        else:
                            st.warning("🚫 leave_balance_df is not a valid DataFrame.")




                    def apply_leave_carry_forward(df_leaves, leave_balance_df, eligible_types=["Earned"], max_days=15):
                        df_leaves["leave_date"] = pd.to_datetime(df_leaves["leave_date"], errors="coerce")
                        df_leaves["year"] = df_leaves["leave_date"].dt.year
                        previous_year = df_leaves["year"].max()

                        # Filter only eligible leave types from last year
                        carry_forward = df_leaves[
                            (df_leaves["year"] == previous_year) &
                            (df_leaves["leave_type"].isin(eligible_types))
                            ]

                        # 🟩 Calculate carry forward summary per employee
                        carry_summary = carry_forward.groupby("employee_id").size().clip(upper=max_days).reset_index(name="carried_forward")

                        carry_summary.rename(columns={"count": "carried_forward"}, inplace=True)

                        # 🔄 Merge with existing leave_balance_df
                        updated_df = leave_balance_df.copy()
                        updated_df = pd.merge(updated_df, carry_summary, on="employee_id", how="left")
                        updated_df["carried_forward"].fillna(0, inplace=True)
                        updated_df["total_allocated"] += updated_df["carried_forward"]

                        # 📊 Display insights
                        st.subheader("🔄 Leave Carry Forward Summary")

                        total_rolled = updated_df["carried_forward"].sum()
                        st.metric("🟩 Total Rolled Over", f"{total_rolled} days")

                        max_hit = (updated_df["carried_forward"] >= max_days).sum()
                        st.metric("🎯 Employees Reaching Max", f"{max_hit}")

                        zero_carry = (updated_df["carried_forward"] == 0).sum()
                        st.metric("🔄 Zero Carry Forward", f"{zero_carry}")

                        # ✏️ Optional manual override panel
                        st.markdown("#### ✏️ Manual Override for HR")
                        if updated_df["employee_id"].nunique() == 0:
                            st.info("ℹ️ No employees eligible for override at this time.")
                        else:


                          selected_emp = st.selectbox("Select Employee to Override", updated_df["employee_id"].unique())
                          new_value = st.number_input("Override Carry Forward Value", min_value=0, max_value=max_days)
                        if st.button("Apply Override"):
                            updated_df.loc[updated_df["employee_id"] == selected_emp, "carried_forward"] = new_value
                            st.success(f"✅ Carry forward manually set to {new_value} for {selected_emp}")

                        return updated_df


                    leave_balance_df = apply_leave_carry_forward(leave_df, leave_balance_df)

                    # 📅 Leave Calendar Per Employee
                    st.subheader("📅 Leave Calendar Viewer")

                    # 🧹 Clean up and prepare leave_df
                    if "leave_date" in leave_df.columns:
                        leave_df["leave_date"] = pd.to_datetime(leave_df["leave_date"], errors="coerce").dt.date
                    else:
                        st.warning("⚠️ 'leave_date' column missing in leave_df.")

                    # 🔍 Employee selector
                    if "employee_id" in leave_df.columns:
                        emp_ids = leave_df["employee_id"].dropna().unique()
                        if len(emp_ids) == 0:
                            st.info("ℹ️ No employees available for calendar view.")
                        else:
                            selected_emp = st.selectbox("Choose Employee", emp_ids)

                            # 🧮 Filter data for selected employee
                            emp_leave_calendar = leave_df[leave_df["employee_id"] == selected_emp]


                            # 🛠️ Reliability Diagnostics
                            def diagnose_leave_calendar(df):
                                issues = {}
                                issues["missing_dates"] = df["leave_date"].isna().sum()
                                issues["duplicates"] = df.duplicated(subset=["employee_id", "leave_date"]).sum()
                                issues["conflicts"] = df.duplicated(subset=["employee_id", "leave_date", "leave_type"],
                                                                    keep=False).sum()
                                return issues


                            st.write("🧪 Reliability Checks", diagnose_leave_calendar(emp_leave_calendar))

                            # 📊 Display leave data
                            if emp_leave_calendar.empty:
                                st.info(f"ℹ️ No leave records found for {selected_emp}.")
                            else:
                                st.markdown(f"### 🗓️ Leave Calendar for {selected_emp}")
                                st.dataframe(emp_leave_calendar[["leave_date", "leave_type", "department"]])
                    else:
                        st.warning("⚠️ 'employee_id' column missing in leave_df.")

                    # 📥 Load resignation data
                    resignation_log = pd.read_csv("data/resignation_log.csv")
                    resignation_log["resignation_date"] = pd.to_datetime(resignation_log["resignation_date"])


                    # 🗓️ Parse selected month
                    def parse_month(selected_month):
                        # Example format: "July 2025" or "2025-07"
                        if selected_month == "All":
                            return None, None
                        try:
                            dt = datetime.strptime(selected_month, "%B %Y")  # e.g. "July 2025"
                        except ValueError:
                            dt = datetime.strptime(selected_month, "%Y-%m")  # fallback: "2025-07"
                        return dt.year, dt.month


                    # 🔍 Use the parsed values
                    year, month_num = parse_month(selected_month)

                    # 📉 Filter resignations
                    if year is None and month_num is None:
                        st.info("Showing data for all months.")
                        monthly_resignations = resignation_log  # show full data
                    else:
                        monthly_resignations = resignation_log[
                            (resignation_log["resignation_date"].dt.month == month_num) &
                            (resignation_log["resignation_date"].dt.year == year)
                            ]

                    # ⏳ Filter exits within next X days
                    days_range = st.slider("⏳ Filter exits within next X days", 0, 90, 30)
                    cutoff_date = pd.Timestamp.today() + pd.Timedelta(days=days_range)
                    monthly_resignations = monthly_resignations[
                        monthly_resignations["resignation_date"] <= cutoff_date
                        ]

                    # 📅 Optional: highlight exits before a specific date
                    selected_date = st.date_input(
                        f"📅 Show resignations effective before {pd.Timestamp.today() + pd.Timedelta(days=30):%d %b %Y}",
                        pd.Timestamp.today() + pd.Timedelta(days=30)
                    )

                    monthly_resignations = monthly_resignations[
                        monthly_resignations["resignation_date"] <= pd.to_datetime(selected_date)
                        ]

                    st.subheader("📉 Resignation Tracker")
                    if not monthly_resignations.empty:
                        st.dataframe(monthly_resignations)
                        st.metric("Total Resignations", len(monthly_resignations))
                    else:
                        st.info("✅ No resignations recorded for this month.")

                    status_filter = st.selectbox("📝 Filter by Resignation Status", ["All", "Pending", "Settled"])

                    if status_filter != "All":
                        monthly_resignations = monthly_resignations[
                            monthly_resignations["status"].str.lower() == status_filter.lower()
                            ]

                    today = pd.Timestamp.today()
                    monthly_resignations["days_to_exit"] = (monthly_resignations["resignation_date"] - today).dt.days

                    exiting_soon = monthly_resignations[monthly_resignations["days_to_exit"] <= 15]

                    if not exiting_soon.empty:
                        st.warning(
                            f"⚠️ {len(exiting_soon)} employee(s) have resignations effective in the next 15 days.")
                        st.dataframe(exiting_soon)


                    def tag_status(status):
                        status = status.lower()
                        if status == "pending":
                            return "🕒 Pending"
                        elif status == "settled":
                            return "✅ Settled"
                        return "—"


                    monthly_resignations["status_tag"] = monthly_resignations["status"].apply(tag_status)

                    dept_options = resignation_log["department"].dropna().unique().tolist()
                    selected_dept = st.selectbox("🏢 View Resignations by Department", ["All"] + dept_options)

                    if selected_dept != "All":
                        monthly_resignations = monthly_resignations[
                            monthly_resignations["department"].str.strip().str.title() == selected_dept.title()
                            ]

                    resignation_log["month_year"] = resignation_log["resignation_date"].dt.to_period("M").astype(str)
                    monthly_counts = resignation_log.groupby("month_year").size().reset_index(name="Resignations")

                    st.subheader("📈 Resignation Trends")
                    st.bar_chart(monthly_counts.set_index("month_year"))

                    settled_cases = monthly_resignations[monthly_resignations["status"].str.lower() == "settled"]

                    if not settled_cases.empty:
                        st.markdown("#### ✅ Final Settlements Triggered")
                        for _, row in settled_cases.iterrows():
                            emp_id = row["employee_id"]
                            emp_name = row["employee_name"]

                            # Grab payroll logic for that employee
                            filtered_payroll = st.session_state.get("filtered_payroll", 0)
                            emp_row = filtered_payroll[filtered_payroll["employee_id"] == emp_id]

                            if not emp_row.empty:
                                bonus = emp_row["festival_bonus"].iloc[0]
                                leave = emp_row["leave_balance"].iloc[0]
                                net_salary = st.session_state.get("net_salary", 0)
                                final_settlement = bonus + net_salary + (leave if leave < 0 else 0)

                                st.markdown(f"""
                                    <div style='background:#e0f7fa; padding:12px; margin:8px 0; border-radius:8px;'>
                                    <strong>{emp_name.title()}</strong><br>
                                    🎁 Bonus: ₹{bonus} | 💸 Leave Adj: ₹{leave if leave < 0 else 0} | 💼 Net: ₹{net_salary}<br>
                                    🧾 <strong>Final Settlement: ₹{final_settlement:,.2f}</strong>
                                    </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.info(f"📄 No payroll record found for {emp_name.title()} this month.")

                    def calculate_settlement(emp_id):
                        emp_row = filtered_payroll[filtered_payroll["employee_id"] == emp_id]
                        if not emp_row.empty:
                            bonus = emp_row["festival_bonus"].iloc[0]
                            leave = emp_row["leave_balance"].iloc[0]
                            net_salary = st.session_state.get("net_salary", 0)
                            return bonus + net_salary + (leave if leave < 0 else 0)
                        return None


                    st.markdown("## 📉 Resignation Analytics & Final Settlement Dashboard")

                    # Load resignation log
                    resignation_log = pd.read_csv("data/resignation_log.csv")
                    resignation_log["resignation_date"] = pd.to_datetime(resignation_log["resignation_date"])
                    resignation_log["month_year"] = resignation_log["resignation_date"].dt.to_period("M").astype(str)

                    # Date filter for urgency
                    days_range = st.slider("⏳ Show resignations within next X days", 0, 90, 30)
                    cutoff_date = pd.Timestamp.today() + pd.Timedelta(days=days_range)
                    filtered_resignations = resignation_log[resignation_log["resignation_date"] <= cutoff_date]

                    # 📊 Monthly exit volume
                    monthly_exit = resignation_log.groupby("month_year").size().reset_index(name="Resignations")
                    st.subheader("📊 Monthly Exit Volume")
                    st.bar_chart(monthly_exit.set_index("month_year"))

                    # 🏢 Department-wise turnover
                    dept_turnover = resignation_log["department"].value_counts().reset_index()
                    dept_turnover.columns = ["Department", "Resignations"]
                    st.subheader("🏢 Department-wise Turnover")
                    st.dataframe(dept_turnover)

                    # 📉 Exit rate vs employee base
                    employee_count = log_df["employee_id"].nunique() if "log_df" in locals() else 1
                    exit_rate = len(resignation_log) / employee_count * 100
                    st.metric("📉 Exit Rate", f"{exit_rate:.2f}% of employee base")

                    # 🔁 Status-based filters
                    status_choice = st.selectbox("🔁 Filter by Resignation Status", ["All", "Pending", "Settled"])
                    if status_choice != "All":
                        filtered_resignations = filtered_resignations[
                            filtered_resignations["status"].str.lower() == status_choice.lower()
                            ]


                    # 💰 Final Settlement Summary
                    def calculate_settlement(emp_id):
                        row = filtered_payroll[filtered_payroll["employee_id"] == emp_id]
                        if not row.empty:
                            bonus = row["festival_bonus"].iloc[0]
                            leave = row["leave_balance"].iloc[0]
                            net_salary = st.session_state.get("net_salary", 0)
                            return bonus + net_salary + (leave if leave < 0 else 0)
                        return 0


                    filtered_resignations["final_settlement"] = filtered_resignations["employee_id"].apply(
                        calculate_settlement)
                    st.subheader("💰 Final Settlement Overview")
                    st.dataframe(filtered_resignations[
                                     ["employee_name", "department", "status", "resignation_date", "final_settlement"]])

                    # 📄 Aggregate payout
                    total_settlement = filtered_resignations["final_settlement"].sum()
                    st.metric("📄 Aggregate Final Settlement", f"₹{total_settlement:,.2f}")

                    # 📈 Stacked exits by department
                    stacked_data = resignation_log.groupby(["month_year", "department"]).size().reset_index(
                        name="Count")
                    fig_stack = px.bar(
                        stacked_data, x="month_year", y="Count", color="department",
                        title="📈 Monthly Resignations by Department"
                    )
                    st.plotly_chart(fig_stack, use_container_width=True)

                    if "notice_issued_date" in resignation_log.columns:
                        resignation_log["notice_issued_date"] = pd.to_datetime(resignation_log["notice_issued_date"],
                                                                               errors='coerce')
                        resignation_log["resignation_date"] = pd.to_datetime(resignation_log["resignation_date"],
                                                                             errors='coerce')

                        # Now it's safe to calculate
                        resignation_log["notice_period_days"] = (
                                resignation_log["resignation_date"] - resignation_log["notice_issued_date"]
                        ).dt.days
                    else:
                        st.info("ℹ️ 'notice_issued_date' column not found in resignation_log.")

                    # ⏳ Sparkline: Notice period vs resignation date
                    resignation_log["notice_period_days"] = (
                                resignation_log["resignation_date"] - resignation_log["notice_issued_date"]).dt.days
                    spark_data = resignation_log[["resignation_date", "notice_period_days"]].dropna()
                    fig_spark = px.line(spark_data, x="resignation_date", y="notice_period_days",
                                        title="⏳ Notice Period Trend")
                    st.plotly_chart(fig_spark, use_container_width=True)

                    # 📍 Timeline: Next 30-day exits
                    timeline_resignations = resignation_log[
                        (resignation_log["resignation_date"] >= pd.Timestamp.today()) &
                        (resignation_log["resignation_date"] <= cutoff_date)
                        ]

                    st.subheader(f"📍 Timeline Feed — Resignations before {cutoff_date.date()}")
                    for _, row in timeline_resignations.iterrows():
                        urgency = (row["resignation_date"] - pd.Timestamp.today()).days
                        st.markdown(f"""
                            <div style='background:#f9f9f9; padding:8px; margin:8px 0; border-left:5px solid #FFA726;'>
                                <strong>{row['employee_name'].title()}</strong> — {row['department']}<br>
                                🗓️ Exit Date: {row['resignation_date'].date()} ({urgency} days left)<br>
                                📝 Status: {row['status'].title()} | 🧾 Estimated Settlement: ₹{calculate_settlement(row['employee_id']):,.2f}
                            </div>
                        """, unsafe_allow_html=True)


                    def render_resignation_card(row):
                        department_emojis = {
                            "Electrical": "🔌",
                            "Electronic": "📡",
                            "Design": "🎨"
                        }
                        dept_name = row.get("department", "—").title()
                        dept_badge = department_emojis.get(dept_name, "🏢")  # fallback for undefined departments

                        status = row["status"].strip().lower()
                        days_left = (row["resignation_date"] - pd.Timestamp.today()).days

                        # 🎨 Style settings based on resignation status
                        if status == "pending":
                            bg_color = "#fff3e0"  # soft orange
                            tag = "💼 Settlement Pending"
                        elif status == "settled":
                            bg_color = "#e0f7e9"  # pastel green
                            tag = "✅ Settled"
                        else:
                            bg_color = "#f0f0f0"
                            tag = "—"

                        exit_note = f"⏳ {days_left} day(s) to exit" if days_left > 0 else "📤 Exit date passed"
                        settlement_value = calculate_settlement(row["employee_id"])
                        settlement_block = (
                            f"<p style='margin:4px 0;'>🧾 Final Settlement: ₹{settlement_value:,.2f}</p>"
                            if settlement_value else ""
                        )

                        return f"""
                            <div style='padding:12px; margin-bottom:12px;
                                        border-radius:10px; background-color:{bg_color};
                                        box-shadow:0 2px 6px rgba(0,0,0,0.1);'>
                                <h4 style='margin:0'>{row['employee_name'].title()} ({row['employee_id']})</h4>
                                <p style='margin:4px 0;'>🗓️ Resignation Date: {row['resignation_date'].date()}</p>
                                <p style='margin:4px 0;'>🏢 Department: {row.get('department', '—').title()}</p>
                                <p style='margin:4px 0;'>📝 Status: <strong>{tag}</strong></p>
                                <p style='margin:4px 0;'>{exit_note}</p>
                                {settlement_block}
                                <p style='margin:4px 0;'>🏢 Department: {dept_badge} {dept_name}</p>

                            </div>
                        """


                    card_mode = st.toggle("🃏 Show Resignations as Cards")

                    if not monthly_resignations.empty:
                        st.subheader(f"📉 Resignations in {selected_month}")

                        if card_mode:
                            for _, row in monthly_resignations.iterrows():
                                st.markdown(render_resignation_card(row), unsafe_allow_html=True)
                        else:
                            st.dataframe(monthly_resignations)
                    else:
                        st.info("✅ No resignations found this month.")

                    filter_soon = st.toggle("⏰ Show only resignations within next 30 days")

                    if filter_soon:
                        monthly_resignations = monthly_resignations[
                            (monthly_resignations["resignation_date"] - pd.Timestamp.today()).dt.days <= 30
                            ]


                    def calculate_leave_encashment(leave_balance_df, resignation_log, salary_df,
                                                   daily_rate_col="basic"):
                        # 🛡️ Ensure 'unused' is calculated before merging
                        if "unused" not in leave_balance_df.columns:
                            st.warning("⚠️ 'unused' leave column missing. Calculating it now.")
                            leave_balance_df["unused"] = leave_balance_df["total_allocated"] - leave_balance_df[
                                "leaves_taken"]

                        # 🔗 Merge resignation data with leave balance
                        resigned_emps = pd.merge(resignation_log, leave_balance_df, on="employee_id", how="inner")

                        # 💰 Merge salary info
                        resigned_emps = pd.merge(resigned_emps, salary_df[["employee_id", daily_rate_col]],
                                                 on="employee_id", how="left")

                        # 🧼 Resolve department naming conflict
                        if "department_x" in resigned_emps.columns:
                            resigned_emps["department"] = resigned_emps["department_x"]
                        elif "department" in resigned_emps.columns:
                            resigned_emps["department"] = resigned_emps["department"]
                        else:
                            resigned_emps["department"] = "Unknown"

                        # 💸 Calculate daily encashment rate and value
                        resigned_emps["daily_encash_rate"] = resigned_emps[daily_rate_col] / 30
                        resigned_emps["encash_value"] = resigned_emps["unused"] * resigned_emps["daily_encash_rate"]

                        # 🧾 Display Summary Table
                        st.subheader("💰 Leave Encashment at Resignation")

                        required_cols = ["employee_id", "department", "unused", "daily_encash_rate", "encash_value"]
                        missing = [col for col in required_cols if col not in resigned_emps.columns]
                        if missing:
                            st.warning(f"⚠️ Missing columns: {', '.join(missing)}")
                        else:
                            st.dataframe(resigned_emps[required_cols])

                            total_payout = resigned_emps["encash_value"].sum()
                            st.metric("🧾 Total Encashment Liability", f"₹{total_payout:,.2f}")

                        return resigned_emps


                    encashment_df = calculate_leave_encashment(leave_balance_df, resignation_log, salary_df)

                    leave_insights_module(leave_balance_df, resignation_log)

                    # 🖨️ PDF Summary Generator
                    def generate_pdf_summary(company_name, top_employee_name, top_score, summary_df, log_df,
                                             leave_summary):
                        month_obj = parse_month(selected_month)
                        year = month_obj.year
                        month = month_obj.month
                        calendar_matrix = calendar.monthcalendar(year, month)

                        pdf = FPDF()
                        pdf.add_page()
                        pdf.add_font("DejaVu", "", "fonts/DejaVuSans.ttf", uni=True)
                        pdf.add_font("DejaVu", "B", "fonts/DejaVuSans-Bold.ttf", uni=True)
                        pdf.set_font("DejaVu", "B", 16)
                        pdf.cell(0, 10, f"{company_name}", ln=True, align="C")
                        pdf.cell(0, 10, f"– Payroll Highlights – {selected_month}", ln=True, align="C")

                        pdf.set_font("DejaVu", "", 12)
                        pdf.cell(0, 8, f"🏆 Employee of the Month: {top_employee_name.title()} – Score: {top_score:.2f}",
                                 ln=True)
                        pdf.cell(0, 8, "———", ln=True)
                        pdf.cell(0, 8, "✨ Featured Employees:", ln=True)

                        for _, row in summary_df.iterrows():
                            badge_clean = "🏅 " + row["badges"].replace(">", "").strip()
                            pdf.cell(0, 8, f"• {row['employee_name'].title()} – {badge_clean}", ln=True)

                        pdf.cell(0, 8, "———", ln=True)
                        pdf.cell(0, 8, "📊 Payroll Summary:", ln=True)
                        pdf.cell(0, 8, f"• Total YTD Salary: ₹{log_df['net_salary'].sum():,.2f}", ln=True)
                        pdf.cell(0, 8, f"• Badges Awarded: {summary_df.shape[0]}", ln=True)
                        pdf.cell(0, 8, f"• Employees Processed: {log_df['employee_id'].nunique()}", ln=True)
                        pdf.cell(0, 8, "———", ln=True)
                        pdf.cell(0, 8, "📄 Recent Payroll Entries:", ln=True)

                        recent = log_df[["employee_name", "payroll_month", "net_salary", "badges"]].tail(5)
                        for _, row in recent.iterrows():
                            badge = "🏅 " + str(row["badges"]).replace(">", "").strip()
                            pdf.cell(0, 8,
                                     f"- {row['employee_name'].title()} | {row['payroll_month']} | ₹{row['net_salary']:,.2f} | {badge}",
                                     ln=True)

                        if not leave_summary.empty:
                            pdf.cell(0, 8, "———", ln=True)
                            pdf.cell(0, 8, "🗓️ Leave Balance Overview:", ln=True)
                            for _, row in leave_summary.iterrows():
                                pdf.cell(0, 8, f"- {row['employee_name'].title()}: {row['leave_balance']:.2f} days",
                                         ln=True)
                            avg_leave = leave_summary["leave_balance"].mean()
                            pdf.cell(0, 8, f"• Average Leave Balance: {avg_leave:.1f} days", ln=True)

                        buffer = io.BytesIO()
                        pdf.output(buffer)
                        buffer.seek(0)

                        file_name = f"payroll_summary_{selected_month}_v2.pdf"
                        return buffer, file_name


                    if st.button("📄 Generate PDF Summary"):
                        pdf_buffer, file_name = generate_pdf_summary(
                            company_name="Shri Swami Samarth Pvt. Ltd.",
                            top_employee_name=first["employee_name"],
                            top_score=first["dedication_index"],
                            summary_df=summary_df,
                            log_df=df_dept,
                            leave_summary=leave_summary
                        )
                        st.session_state["pdf_buffer"] = pdf_buffer
                        st.session_state["file_name"] = file_name
                        st.success(f"✅ PDF generated: {file_name}")

                        if "pdf_buffer" in st.session_state and "file_name" in st.session_state:
                            st.download_button(
                                label="📥 Download Payroll Summary (PDF)",
                                data=st.session_state["pdf_buffer"],
                                file_name=st.session_state["file_name"],
                                mime="application/pdf"
                            )


            def generate_payslip_pdf(employee_name, employee_id, selected_month, base_salary, extra_pay,

                                     tuesday_bonus, late_deduction, tax_deduction, net_salary,

                                     late_marks, full_days, half_days,

                                     employee_data, employee_name_clean):

                from fpdf import FPDF

                from datetime import datetime

                year, month = map(int, selected_month.split("-"))

                calendar_matrix = calendar.monthcalendar(year, month)

                # 🗓️ Holiday markers

                HOLIDAYS = ["2025-07-17", "2025-07-29"]

                holiday_dates = [datetime.strptime(d, "%Y-%m-%d").date() for d in HOLIDAYS]

                pdf = FPDF()

                pdf.add_page()

                # 🎨 Font setup

                pdf.add_font("DejaVu", "", "fonts/DejaVuSans.ttf", uni=True)

                pdf.add_font("DejaVu", "B", "fonts/DejaVuSans-Bold.ttf", uni=True)

                pdf.set_font("DejaVu", "B", 12)

                # 🧾 Header

                pdf.cell(200, 10, txt="Shri Swami Samarth Pvt. Ltd.", ln=True, align="C")

                pdf.cell(200, 10, txt=f"Payslip for {employee_name} ({employee_id})", ln=True, align="C")

                pdf.cell(200, 10, txt=f"Month: {selected_month}", ln=True, align="C")

                pdf.ln(5)

                # 🗓️ Attendance Grid

                pdf.set_font("DejaVu", "", 10)

                pdf.cell(200, 8, txt=f"Attendance Calendar for {datetime(year, month, 1).strftime('%B %Y')}", ln=True)

                for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
                    pdf.cell(22, 8, txt=day, border=1, align="C")

                pdf.ln()

                for week in calendar_matrix:

                    for day in week:

                        if day == 0:

                            pdf.cell(22, 8, txt="", border=1)

                        else:

                            this_date = datetime(year, month, day).date()

                            row = employee_data[

                                (employee_data["employee_name"].str.lower().str.strip() == employee_name_clean) &

                                (employee_data["date_only"] == this_date)

                                ]

                            if not row.empty:

                                status = row["attendance_status"].values[0]

                                late = row["late_mark"].values[0] if "late_mark" in row.columns else False

                                marker = "L" if late else (

                                    "F" if status == "Full Day" else "H" if status == "Half Day" else "A"

                                )

                            else:

                                marker = "-" if this_date.weekday() == 1 or this_date in holiday_dates else "A"

                            label = f"{str(day).zfill(2)} {marker}"

                            pdf.cell(22, 8, txt=label, border=1, align="C")

                    pdf.ln()

                pdf.ln(2)

                pdf.set_font("DejaVu", "", 9)

                pdf.multi_cell(0, 5, "Legend: F = Full | H = Half | A = Absent | L = Late | - = Holiday/Tuesday")

                pdf.ln(4)

                # 💰 Salary Details

                pdf.set_font("DejaVu", "", 11)

                pdf.cell(200, 10, txt=f"Full Days Worked: {full_days}", ln=True)

                pdf.cell(200, 10, txt=f"Half Days Worked: {half_days}", ln=True)

                pdf.cell(200, 10, txt=f"Late Marks: {late_marks}", ln=True)

                pdf.cell(200, 10, txt=f"Base Salary: ₹{base_salary:,.2f}", ln=True)

                pdf.cell(200, 10, txt=f"Extra Pay: ₹{extra_pay:,.2f}", ln=True)

                pdf.cell(200, 10, txt=f"Tuesday Bonus: ₹{tuesday_bonus:,.2f}", ln=True)

                pdf.cell(200, 10, txt=f"Late Deduction: -₹{late_deduction:,.2f}", ln=True)

                pdf.cell(200, 10, txt=f"Tax Deduction: -₹{tax_deduction:,.2f}", ln=True)

                gross = base_salary + extra_pay + tuesday_bonus - late_deduction

                pdf.cell(200, 10, txt=f"Gross Pay (Before Tax): ₹{gross:,.2f}", ln=True)

                pdf.ln(5)

                # ✅ Net Pay

                pdf.set_font("DejaVu", "B", 12)

                pdf.cell(200, 10, txt=f"Net Salary Payable: ₹{net_salary:,.2f}", ln=True)

                return bytes(pdf.output(dest="S"))

