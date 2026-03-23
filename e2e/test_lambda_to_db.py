"""
Layer 1 — Lambda handler → PostgreSQL

Calls handler.process_file() directly with a local Excel file and a real DB.
No S3 or Lambda runtime needed: this tests the core ETL logic end-to-end.
"""

import os
import sys

import pytest

# Make the lambda processor importable without installing it as a package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambda", "processor"))

DB_DSN = os.getenv(
    "DB_URL",
    "postgresql://dashboard:dashboard@localhost:5432/dashboard",
)


@pytest.fixture(autouse=True)
def patch_db_env(monkeypatch):
    """Point the Lambda handler at the local test database."""
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "dashboard")
    monkeypatch.setenv("DB_USER", "dashboard")
    monkeypatch.setenv("DB_PASSWORD", "dashboard")


def test_process_file_inserts_rows(sample_excel, db, monkeypatch):
    """
    Given a valid Excel file,
    when process_file() is called,
    then all non-null rows are inserted into spend_reports.
    """
    from handler import process_file

    # Bypass S3 download — return the local file path directly
    monkeypatch.setattr("handler._download_file", lambda bucket, key: sample_excel)

    inserted = process_file("test-bucket", "e2e/spend_report_e2e.xlsx")

    assert inserted == 3, f"Expected 3 rows inserted, got {inserted}"


def test_inserted_rows_are_queryable(sample_excel, db, monkeypatch):
    """
    After process_file(), the rows should be visible in the DB
    with correct field values.
    """
    from handler import process_file

    monkeypatch.setattr("handler._download_file", lambda bucket, key: sample_excel)
    process_file("test-bucket", "e2e/spend_report_e2e.xlsx")

    with db.cursor() as cur:
        cur.execute(
            "SELECT ministry, category, amount FROM spend_reports "
            "WHERE source_file = 'e2e/spend_report_e2e.xlsx' "
            "ORDER BY amount DESC"
        )
        rows = cur.fetchall()

    assert len(rows) == 3
    assert rows[0] == ("Finance", "IT", 125_000), f"Unexpected first row: {rows[0]}"
    assert rows[1][0] == "Health"


def test_idempotent_reprocessing(sample_excel, db, monkeypatch):
    """
    Processing the same file twice should not duplicate rows
    (ON CONFLICT DO NOTHING in the INSERT).
    """
    from handler import process_file

    monkeypatch.setattr("handler._download_file", lambda bucket, key: sample_excel)

    process_file("test-bucket", "e2e/spend_report_e2e.xlsx")
    process_file("test-bucket", "e2e/spend_report_e2e.xlsx")

    with db.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM spend_reports "
            "WHERE source_file = 'e2e/spend_report_e2e.xlsx'"
        )
        count = cur.fetchone()[0]

    assert count == 3, f"Expected 3 (not doubled), got {count}"


def test_missing_required_column_raises(tmp_path, db, monkeypatch):
    """
    An Excel file missing a required column should raise ValueError
    and insert nothing.
    """
    import pandas as pd
    from handler import process_file

    bad_path = tmp_path / "bad.xlsx"
    pd.DataFrame({"Ministry": ["Finance"], "Amount": [1000]}).to_excel(
        bad_path, index=False
    )

    monkeypatch.setattr("handler._download_file", lambda bucket, key: str(bad_path))

    with pytest.raises(ValueError, match="Missing required columns"):
        process_file("test-bucket", "e2e/bad.xlsx")

    with db.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM spend_reports WHERE source_file = 'e2e/bad.xlsx'"
        )
        assert cur.fetchone()[0] == 0
