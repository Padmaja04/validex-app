import streamlit as st
from datetime import datetime
import pandas as pd
import os


def log_feedback(category, department, message, sender="Anonymous", path="data/feedback_raw.csv"):
    new_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "category": category,
        "department": department,
        "sender": sender,
        "message": message,
        "status": "Pending"
    }

    if os.path.exists(path):
        try:
            df_existing = pd.read_csv(path)
            df_updated = pd.concat([df_existing, pd.DataFrame([new_entry])], ignore_index=True)
        except pd.errors.ParserError:
            df_updated = pd.DataFrame([new_entry])
    else:
        df_updated = pd.DataFrame([new_entry])

    df_updated.to_csv(path, index=False)

def sync_feedback_entries(raw_path="data/feedback_insight.csv", reviewed_path="data/feedback_reviewed.csv"):
    # Check if raw feedback exists
    if not os.path.exists(raw_path):
        return  # Nothing to sync

    try:
        raw_df = pd.read_csv(raw_path)
    except pd.errors.ParserError:
        return  # Invalid raw file format

    # Load reviewed feedback or create a new one
    if os.path.exists(reviewed_path):
        try:
            reviewed_df = pd.read_csv(reviewed_path)
        except pd.errors.ParserError:
            reviewed_df = pd.DataFrame(columns=raw_df.columns)
    else:
        reviewed_df = pd.DataFrame(columns=raw_df.columns)

    # Find new entries that aren't yet reviewed
    new_entries = raw_df[~raw_df["timestamp"].isin(reviewed_df["timestamp"])]

    if not new_entries.empty:
        merged_df = pd.concat([reviewed_df, new_entries], ignore_index=True)
        merged_df.to_csv(reviewed_path, index=False)
