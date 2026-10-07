"""
export_results.py
Exports SQLite audit logs and simulation metrics into publication packages.
"""

import os
import sqlite3
import pandas as pd
import json


def export_all():
    os.makedirs("evidence/exports", exist_ok=True)

    # 1. Export SQLite Audit Database to CSV
    db_path = "evidence/inspection_audit.db"
    if os.path.exists(db_path):
        with sqlite3.connect(db_path) as conn:
            audit_df = pd.read_sql_query("SELECT * FROM inspection_steps", conn)
            audit_df.to_csv("evidence/exports/complete_audit_trail_export.csv", index=False)
            print(f"Exported {len(audit_df)} audit steps to evidence/exports/complete_audit_trail_export.csv")

    # 2. Package Summary JSON
    summary_path = "evidence/results/validation_summary.json"
    if os.path.exists(summary_path):
        with open(summary_path, "r") as f:
            data = json.load(f)
        with open("evidence/exports/executive_summary.json", "w") as f:
            json.dump(data, f, indent=2)
        print("Exported executive summary to evidence/exports/executive_summary.json")


if __name__ == "__main__":
    export_all()
