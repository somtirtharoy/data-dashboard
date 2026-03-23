from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.models.spend_report import SpendReport


@pytest.fixture
async def sample_report(db_session):
    report = SpendReport(
        source_file="test.xlsx",
        ministry="Finance",
        program="Operations",
        category="IT",
        fiscal_year="2024-25",
        period_start="2024-04-01",
        period_end="2024-06-30",
        amount=Decimal("50000.00"),
    )
    db_session.add(report)
    await db_session.commit()
    await db_session.refresh(report)
    return report


async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_list_reports_empty(client: AsyncClient):
    response = await client.get("/api/v1/reports")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


async def test_list_reports_with_data(client: AsyncClient, sample_report: SpendReport):
    response = await client.get("/api/v1/reports")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["ministry"] == "Finance"


async def test_get_report_not_found(client: AsyncClient):
    response = await client.get("/api/v1/reports/99999")
    assert response.status_code == 404


async def test_get_report(client: AsyncClient, sample_report: SpendReport):
    response = await client.get(f"/api/v1/reports/{sample_report.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_report.id
    assert data["category"] == "IT"


async def test_analytics_summary(client: AsyncClient, sample_report: SpendReport):
    response = await client.get("/api/v1/reports/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "by_category" in data
    assert "total_spend" in data
    assert float(data["total_spend"]) > 0
