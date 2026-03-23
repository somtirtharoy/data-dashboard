"""
Layer 2 — API

Verifies the FastAPI backend returns the rows inserted by the Lambda layer.
Requires the backend service to be running (docker compose up backend).
"""

import os
import sys

import pytest
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambda", "processor"))

API_URL = os.getenv("API_URL", "http://localhost:8000")


@pytest.fixture(scope="module", autouse=True)
def seed_data(sample_excel, monkeypatch):
    """Insert rows via the Lambda handler before any API test runs."""
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "dashboard")
    monkeypatch.setenv("DB_USER", "dashboard")
    monkeypatch.setenv("DB_PASSWORD", "dashboard")

    from handler import process_file

    monkeypatch.setattr("handler._download_file", lambda bucket, key: sample_excel)
    process_file("test-bucket", "e2e/spend_report_e2e.xlsx")


def test_health():
    r = requests.get(f"{API_URL}/health", timeout=5)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_reports_returns_inserted_rows():
    r = requests.get(f"{API_URL}/api/v1/reports", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 3

    ministries = {item["ministry"] for item in data["items"]}
    assert "Finance" in ministries
    assert "Health" in ministries


def test_filter_by_ministry():
    r = requests.get(
        f"{API_URL}/api/v1/reports", params={"ministry": "Finance"}, timeout=5
    )
    assert r.status_code == 200
    data = r.json()
    assert all(item["ministry"] == "Finance" for item in data["items"])


def test_filter_by_fiscal_year():
    r = requests.get(
        f"{API_URL}/api/v1/reports", params={"fiscal_year": "2024-25"}, timeout=5
    )
    assert r.status_code == 200
    assert r.json()["total"] >= 3


def test_analytics_summary():
    r = requests.get(
        f"{API_URL}/api/v1/reports/analytics/summary",
        params={"fiscal_year": "2024-25"},
        timeout=5,
    )
    assert r.status_code == 200
    data = r.json()

    assert float(data["total_spend"]) > 0

    category_names = {item["name"] for item in data["by_category"]}
    assert "IT" in category_names

    ministry_names = {item["name"] for item in data["by_ministry"]}
    assert "Finance" in ministry_names
    assert "Health" in ministry_names


def test_get_single_report():
    # Get first report ID from list
    r = requests.get(f"{API_URL}/api/v1/reports", timeout=5)
    first_id = r.json()["items"][0]["id"]

    r2 = requests.get(f"{API_URL}/api/v1/reports/{first_id}", timeout=5)
    assert r2.status_code == 200
    assert r2.json()["id"] == first_id


def test_get_nonexistent_report():
    r = requests.get(f"{API_URL}/api/v1/reports/999999999", timeout=5)
    assert r.status_code == 404


def test_pagination():
    r = requests.get(
        f"{API_URL}/api/v1/reports",
        params={"page": 1, "page_size": 2},
        timeout=5,
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) <= 2
    assert data["page"] == 1
    assert data["page_size"] == 2
