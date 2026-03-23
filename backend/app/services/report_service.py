from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.spend_report import SpendReport
from app.schemas.spend_report import AnalyticsSummary, SpendReportListResponse


class ReportService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_reports(
        self,
        page: int,
        page_size: int,
        ministry: str | None,
        category: str | None,
        fiscal_year: str | None,
    ) -> SpendReportListResponse:
        query = select(SpendReport)
        count_query = select(func.count()).select_from(SpendReport)

        if ministry:
            query = query.where(SpendReport.ministry == ministry)
            count_query = count_query.where(SpendReport.ministry == ministry)
        if category:
            query = query.where(SpendReport.category == category)
            count_query = count_query.where(SpendReport.category == category)
        if fiscal_year:
            query = query.where(SpendReport.fiscal_year == fiscal_year)
            count_query = count_query.where(SpendReport.fiscal_year == fiscal_year)

        total = (await self.db.execute(count_query)).scalar_one()
        offset = (page - 1) * page_size
        result = await self.db.execute(query.offset(offset).limit(page_size))
        items = result.scalars().all()

        return SpendReportListResponse(
            total=total, page=page, page_size=page_size, items=list(items)
        )

    async def get_report(self, report_id: int) -> SpendReport:
        result = await self.db.execute(
            select(SpendReport).where(SpendReport.id == report_id)
        )
        report = result.scalar_one_or_none()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return report

    async def get_analytics_summary(
        self, fiscal_year: str | None
    ) -> AnalyticsSummary:
        base_filter = []
        if fiscal_year:
            base_filter.append(SpendReport.fiscal_year == fiscal_year)

        async def _agg(group_col):
            q = (
                select(group_col, func.sum(SpendReport.amount).label("total"))
                .where(*base_filter)
                .group_by(group_col)
                .order_by(func.sum(SpendReport.amount).desc())
            )
            rows = (await self.db.execute(q)).all()
            return [{"name": r[0], "total": float(r[1])} for r in rows]

        by_category = await _agg(SpendReport.category)
        by_ministry = await _agg(SpendReport.ministry)
        by_fiscal_year = await _agg(SpendReport.fiscal_year)

        total_q = select(func.sum(SpendReport.amount)).where(*base_filter)
        total = (await self.db.execute(total_q)).scalar_one() or Decimal("0")

        return AnalyticsSummary(
            by_category=by_category,
            by_ministry=by_ministry,
            by_fiscal_year=by_fiscal_year,
            total_spend=total,
        )
