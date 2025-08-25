import pandas as pd

leave_balance_df ={
"employee_id":[],
    "total_allocated":[],
    "leaves_taken":[]

}

data = pd.DataFrame(leave_balance_df)
data.to_csv("leave_balance_df.csv", index=False)
print("leave_balance saved successfully!")

leave_balance_df = pd.read_csv("leave_balance_df.csv")
print(leave_balance_df)