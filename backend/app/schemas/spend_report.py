from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SpendReportBase(BaseModel):
    ministry: str
    program: str
    category: str
    vendor: str | None = None
    fiscal_year: str
    period_start: date
    period_end: date
    amount: Decimal
    currency: str = "CAD"
    description: str | None = None


class SpendReportCreate(SpendReportBase):
    source_file: str


class SpendReportRead(SpendReportBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_file: str
    created_at: datetime
    updated_at: datetime


class SpendReportListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[SpendReportRead]


class AnalyticsSummary(BaseModel):
    by_category: list[dict]
    by_ministry: list[dict]
    by_fiscal_year: list[dict]
    total_spend: Decimal
