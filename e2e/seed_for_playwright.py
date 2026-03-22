"""
Seed script called by Playwright's beforeAll hook.
Invokes the Lambda handler directly to insert test data
before browser tests run.
"""

import io
import os
import sys
import tempfile

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambda", "processor"))

os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "dashboard")
os.environ.setdefault("DB_USER", "dashboard")
os.environ.setdefault("DB_PASSWORD", "dashboard")

from handler import process_file  # noqa: E402 (env must be set first)

DATA = {
    "Ministry": ["Finance", "Health", "Finance"],
    "Program": ["Digital Services", "Acute Care", "Operations"],
    "Category": ["IT", "Medical Supplies", "Travel"],
    "Vendor": ["Acme Corp", None, "BC Ferries"],
    "Fiscal Year": ["2024-25", "2024-25", "2024-25"],
    "Period Start": ["2024-04-01", "2024-04-01", "2024-07-01"],
    "Period End": ["2024-06-30", "2024-06-30", "2024-09-30"],
    "Amount": [125_000.00, 75_500.50, 8_200.00],
    "Currency": ["CAD", "CAD", "CAD"],
}


def main():
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        pd.DataFrame(DATA).to_excel(tmp.name, index=False, engine="openpyxl")
        excel_path = tmp.name

    # Monkey-patch _download_file so handler skips S3
    import handler as h

    h._download_file = lambda bucket, key: excel_path  # type: ignore[attr-defined]

    n = process_file("test-bucket", "e2e/playwright_seed.xlsx")
    print(f"[seed] Inserted {n} rows for Playwright tests")


if __name__ == "__main__":
    main()
