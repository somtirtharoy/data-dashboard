# Getting Started

## Local Development

### Prerequisites

- Docker Desktop (with compose)
- Python 3.12+ (for running tests/lint outside Docker)
- Node 20+
- AWS CLI v2
- Terraform >= 1.6
- kubectl + Helm 3

### 1. Clone and start

```bash
git clone <repo-url>
cd data-dashboard

cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

make dev
```

Services:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API docs**: http://localhost:8000/docs
- **LocalStack** (S3/Lambda sim): http://localhost:4566

### 2. Seed test data (optional)

```bash
# Connect to the API and POST directly, or create a seed script:
docker compose exec backend python -c "
from app.database import AsyncSessionLocal
from app.models.spend_report import SpendReport
import asyncio
from decimal import Decimal
from datetime import date

async def seed():
    async with AsyncSessionLocal() as db:
        db.add(SpendReport(
            source_file='seed.xlsx',
            ministry='Finance',
            program='Digital Services',
            category='IT',
            fiscal_year='2024-25',
            period_start=date(2024, 4, 1),
            period_end=date(2024, 6, 30),
            amount=Decimal('125000.00'),
        ))
        await db.commit()
        print('Seeded!')

asyncio.run(seed())
"
```

### 3. Simulate an Excel upload (LocalStack)

```bash
# Create a local S3 bucket in LocalStack
aws --endpoint-url http://localhost:4566 s3 mb s3://data-dashboard-dev-spend-uploads

# Upload a test file
aws --endpoint-url http://localhost:4566 s3 cp my_report.xlsx s3://data-dashboard-dev-spend-uploads/
```

## Running Tests

```bash
make test          # all tests
make test-backend  # backend only (pytest)
make test-frontend # frontend only (vitest)
make test-lambda   # lambda only (pytest)
```

## Linting

```bash
make lint          # all linters
make lint-backend  # ruff + mypy
make lint-frontend # eslint + tsc
```

## Adding a New Field to the Report

1. Add column to `backend/app/models/spend_report.py`
2. Add field to `backend/app/schemas/spend_report.py`
3. Generate Alembic migration: `cd backend && alembic revision --autogenerate -m "add new field"`
4. Update `lambda/processor/handler.py` → `COLUMN_MAP` and `INSERT_SQL`
5. Update the frontend table in `frontend/src/pages/ReportsPage.tsx`

## Project Conventions

- **Python**: ruff for lint, mypy strict for type checking, pytest for tests
- **TypeScript**: ESLint with zero warnings, strict mode, vitest for tests
- **Commits**: Conventional Commits (`feat:`, `fix:`, `chore:`, etc.)
- **Branches**: `feature/<ticket>-description`, `fix/<ticket>-description`
- **PRs**: require passing CI and one reviewer approval before merge
