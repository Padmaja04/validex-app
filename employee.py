import pandas as pd

employee_data={
     "employee_id": [1, 2, 3, 4],
    "employee_name": ["sunil", "shivaji", "vaishali", "prashant"],
    "start_datetime":["23/06/2025 9:30:01","23/06/2025 9:28:12","23/06/2025 9:25:10","23/06/2025 9:29:15"],
    "exit_datetime":["23/06/2025 7:36:01","23/06/2025 7:37:05","23/06/2025 7:30:01","23/06/2025 7:38:01"],
     "year_month":["25/06","25/06","25/06","25/06"],
    "date_only":[24,24,24,24]
}

data = pd.DataFrame(employee_data)
data.to_csv("employee_data.csv", index=False)
print("data saved successfully!")
