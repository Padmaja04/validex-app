import pandas as pd

# 🔧 Corrected and extended employee master with join_date
employee_master = {
    "employee_id": [],
    "employee_name": [],
    "department": [],
    "role":[],
    "fixed_salary": [],
    "join_date": []  # ✅ Added for festival bonus eligibility
}
holidays = {
    "dates": [],
    "holiday_name": []
}
# 🔧 Corrected key name from 'haliday_name' to 'holiday_name'
festival_bonus = {
   "festival_name": [],
   "festival_month": [],
   "festival_bonus": []
}



# Create DataFrames
data = pd.DataFrame(employee_master)
data1 = pd.DataFrame(holidays)
data2 = pd.DataFrame(festival_bonus)

# Save to CSV
data.to_csv("employee_master.csv", index=False)
data1.to_csv("holidays.csv", index=False)
data2.to_csv("festival_bonus.csv", index=False)
print("Employee master saved successfully!")
print("Holiday list saved successfully!")
print("festival_bonus list saved successfully!")