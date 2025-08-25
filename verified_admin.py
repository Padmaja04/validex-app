import pandas as pd


verified_admins ={
    "admin_user":[]
}

data1 = pd.DataFrame(verified_admins)
data1.to_csv("verified_admins.csv",index=False)
print("verifiedd admin successfully")