import pandas as pd

resignation_log = {
        "employee_id": [],
        "employee_name": [],
        "department": [],
        "notice_issued_date": [],
        "notice_period_days": [],
        "resignation_date": [],

        "status": []

}

data = pd.DataFrame(resignation_log)
data.to_csv("resignation_log.csv", index=False)
print("resignation_log saved successfully!")