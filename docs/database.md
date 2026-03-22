# Database Design

## Why PostgreSQL?

**Amazon RDS PostgreSQL 15** was chosen over alternatives for these reasons:

| Criterion | PostgreSQL | DynamoDB | Aurora |
|---|---|---|---|
| Data shape | Structured, relational | Flexible, key-value | Structured, relational |
| SQL support | Full | No (PartiQL only) | Full |
| Cost (small dataset) | Low (t3.micro ~$15/mo) | Variable | Higher minimum |
| Analytics queries | GROUP BY, window fns | Limited | Same as PG |
| Local dev | Easy (`docker compose`) | Needs LocalStack | Hard to replicate |

The spend report data is highly structured with known columns, requires GROUP BY aggregations for analytics, and the volume is modest — making RDS PostgreSQL the best fit.

## Schema

### `spend_reports`

| Column | Type | Description |
|---|---|---|
| `id` | `SERIAL PRIMARY KEY` | Auto-incremented ID |
| `source_file` | `VARCHAR(512)` | S3 key of the source Excel file |
| `ministry` | `VARCHAR(256)` | BC Government ministry name |
| `program` | `VARCHAR(256)` | Program within the ministry |
| `category` | `VARCHAR(256)` | Spend category (e.g. IT, Travel) |
| `vendor` | `VARCHAR(512)` | Vendor/supplier name (nullable) |
| `fiscal_year` | `VARCHAR(10)` | e.g. `2024-25` |
| `period_start` | `DATE` | Start of reporting period |
| `period_end` | `DATE` | End of reporting period |
| `amount` | `NUMERIC(18,2)` | Spend amount |
| `currency` | `VARCHAR(3)` | ISO 4217 code (default: `CAD`) |
| `description` | `VARCHAR(1024)` | Optional description |
| `created_at` | `TIMESTAMPTZ` | Row creation time |
| `updated_at` | `TIMESTAMPTZ` | Last update time |

### Indexes

```sql
CREATE INDEX ix_spend_reports_ministry   ON spend_reports (ministry);
CREATE INDEX ix_spend_reports_category   ON spend_reports (category);
CREATE INDEX ix_spend_reports_fiscal_year ON spend_reports (fiscal_year);
```

## Migrations

Alembic is used for schema migrations:

```bash
# Create a new migration
cd backend
alembic revision --autogenerate -m "add vendor index"

# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1
```

Migrations live in `backend/alembic/versions/`.

## Connection

The backend uses SQLAlchemy's async engine with asyncpg:

```
postgresql+asyncpg://<user>:<password>@<host>:5432/<db>
```

In Kubernetes, the `DATABASE_URL` is stored in a Secret and mounted as an environment variable.

## Local Development

```bash
# The database starts automatically with docker compose
docker compose up db

# Connect with psql
docker compose exec db psql -U dashboard -d dashboard
```

## Backup & Recovery

- **Dev**: 1-day automated backup window, no deletion protection
- **Prod**: 7-day automated backups, deletion protection enabled, Multi-AZ standby
- Point-in-time recovery (PITR) available on prod within the 7-day window
