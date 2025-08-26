import pandas as pd
from datetime import datetime
import os  # 👈 Add this to handle folders


def log_admin_action(username, emp_id, action_type, description, reason=None):
    log_path = "data/admin_log.csv"

    # ✅ Ensure 'data/' directory exists
    os.makedirs("data", exist_ok=True)

    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "admin_user": username,
        "employee_id": emp_id,
        "action_type": action_type,
        "description": description,
        "reason": reason if reason else "-"
    }

    try:
        df = pd.read_csv(log_path)
        df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    except Exception as e:
        print(f"⚠️ Log file error: {e}")
        df = pd.DataFrame([entry])

    df.to_csv(log_path, index=False)

