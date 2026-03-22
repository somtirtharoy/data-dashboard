"""
E2E test fixtures.

Requires the full docker compose stack to be running:
  docker compose up -d

Environment can be overridden:
  DB_URL      - direct postgres connection (default: local compose)
  API_URL     - backend base URL          (default: http://localhost:8000)
  FRONTEND_URL- frontend base URL         (default: http://localhost:3000)
"""

import io
import os

import psycopg2
import pytest
import pandas as pd

DB_DSN = os.getenv(
    "DB_URL",
    "postgresql://dashboard:dashboard@localhost:5432/dashboard",
)
API_URL = os.getenv("API_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@pytest.fixture(scope="session")
def db():
    """Return a raw psycopg2 connection to the test database."""
    conn = psycopg2.connect(DB_DSN)
    conn.autocommit = False
    yield conn
    conn.close()


@pytest.fixture(autouse=True)
def clean_db(db):
    """Wipe spend_reports rows inserted during a test after it finishes."""
    yield
    with db.cursor() as cur:
        cur.execute("DELETE FROM spend_reports WHERE source_file LIKE 'e2e/%'")
    db.commit()


@pytest.fixture(scope="session")
def sample_excel(tmp_path_factory) -> str:
    """Write a minimal valid Excel file; return its path."""
    tmp = tmp_path_factory.mktemp("excel")
    path = tmp / "spend_report_e2e.xlsx"

    df = pd.DataFrame(
        {
            "Ministry": ["Finance", "Health", "Finance"],
            "Program": ["Digital Services", "Acute Care", "Operations"],
            "Category": ["IT", "Medical Supplies", "Travel"],
            "Vendor": ["Acme Corp", None, "BC Ferries"],
            "Fiscal Year": ["2024-25", "2024-25", "2024-25"],
            "Period Start": ["2024-04-01", "2024-04-01", "2024-07-01"],
            "Period End": ["2024-06-30", "2024-06-30", "2024-09-30"],
            "Amount": [125_000.00, 75_500.50, 8_200.00],
            "Currency": ["CAD", "CAD", "CAD"],
            "Description": ["Cloud hosting Q1", None, "Staff travel Q2"],
        }
    )
    df.to_excel(path, index=False, engine="openpyxl")
    return str(path)
