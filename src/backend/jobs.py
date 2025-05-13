import pandas as pd
from datetime import datetime
import os

FILENAME = "jobs.xlsx"

# Initialize Excel file if it doesn't exist
def init_excel():
    if not os.path.exists(FILENAME):
        df = pd.DataFrame(columns=["Company", "Role", "URL", "Status", "Applied Date", "Notes"])
        df.to_excel(FILENAME, index=False)

def add_job(company, role, url="", status="Applied", notes=""):
    init_excel()
    df = pd.read_excel(FILENAME)
    new_row = {
        "Company": company,
        "Role": role,
        "URL": url,
        "Status": status,
        "Applied Date": datetime.today().strftime("%Y-%m-%d"),
        "Notes": notes
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_excel(FILENAME, index=False)
    return f"✅ Job at {company} for {role} added."

def list_jobs():
    init_excel()
    df = pd.read_excel(FILENAME)
    if df.empty:
        return "📭 No jobs added yet."
    jobs = df.tail(10)  # Show only last 10 entries
    return "\n".join([
        f"{row.Company} | {row.Role} | {row.Status} | {row['Applied Date']}\n🔗 {row.URL or 'No Link'}"
        for _, row in jobs.iterrows()
    ])
