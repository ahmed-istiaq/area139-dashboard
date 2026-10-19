"""GA4 connection test - checks Google Analytics directly, without the dashboard.
Run:  python ga_test.py
"""
import json
import os
from pathlib import Path

import common  # noqa: F401  (loads .env)

prop = os.getenv("GA4_PROPERTY_ID", "").strip()
info, source = None, None

secrets = Path(".streamlit/secrets.toml")
if secrets.exists() and "gcp_service_account" in secrets.read_text(encoding="utf-8", errors="ignore"):
    print("WARNING: .streamlit/secrets.toml contains [gcp_service_account] - the dashboard uses it BEFORE anything else!\n")

if os.getenv("GA_CREDENTIALS_JSON"):
    info, source = json.loads(os.environ["GA_CREDENTIALS_JSON"]), "GA_CREDENTIALS_JSON (.env)"
elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    info, source = json.load(open(path, encoding="utf-8")), f"file: {path}"

if not info:
    raise SystemExit("No credentials found. Set GOOGLE_APPLICATION_CREDENTIALS or GA_CREDENTIALS_JSON in .env.")

print("Credential source :", source)
print("Service account   :", info.get("client_email"))
print("Google Cloud proj :", info.get("project_id"))
print("Property ID       :", repr(prop))
if not prop.isdigit():
    print("  -> The Property ID must be digits only (not G-XXXX, no spaces or quotes).")

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, RunReportRequest
from google.oauth2 import service_account

creds = service_account.Credentials.from_service_account_info(
    info, scopes=["https://www.googleapis.com/auth/analytics.readonly"])
client = BetaAnalyticsDataClient(credentials=creds)
try:
    resp = client.run_report(RunReportRequest(
        property=f"properties/{prop}",
        metrics=[Metric(name="activeUsers")],
        date_ranges=[DateRange(start_date="28daysAgo", end_date="today")]))
    users = resp.rows[0].metric_values[0].value if resp.rows else "0"
    print(f"\nOK! Visitors in the last 28 days: {users}")
except Exception as e:
    print("\nFAILED:", e)
    print("\nCheck that this email is listed under GA > Admin > Property access management as a Viewer:")
    print("  ", info.get("client_email"))
