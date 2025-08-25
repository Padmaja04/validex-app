import pandas as pd

appraisal_history = {
       "employee_id": [],
       "reviewer_id": [],
       "rating": [],
       "hike_percent": [],
       "notes": [],
       "appraisal_date": [],
       "new_salary": []

 }
data = pd.DataFrame(appraisal_history)
data.to_csv("appraisal_history.csv", index=False)
print("appraisal history saved successfully!")