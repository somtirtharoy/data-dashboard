from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.spend_report import (
    AnalyticsSummary,
    SpendReportListResponse,
    SpendReportRead,
)
from app.services.report_service import ReportService

router = APIRouter()


@router.get("", response_model=SpendReportListResponse)
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    ministry: str | None = None,
    category: str | None = None,
    fiscal_year: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    return await service.list_reports(
        page=page,
        page_size=page_size,
        ministry=ministry,
        category=category,
        fiscal_year=fiscal_year,
    )


@router.get("/analytics/summary", response_model=AnalyticsSummary)
async def analytics_summary(
    fiscal_year: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    return await service.get_analytics_summary(fiscal_year=fiscal_year)


@router.get("/{report_id}", response_model=SpendReportRead)
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    service = ReportService(db)
    return await service.get_report(report_id)
