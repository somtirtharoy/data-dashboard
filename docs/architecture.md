# Architecture

## System Overview

```
                    ┌─────────────┐
  User uploads      │             │
  .xlsx file ──────▶│  S3 Bucket  │
                    │  (uploads/) │
                    └──────┬──────┘
                           │ S3 ObjectCreated event
                           ▼
                    ┌─────────────┐
                    │   Lambda    │  Python 3.12
                    │  Processor  │  pandas + openpyxl
                    └──────┬──────┘
                           │ INSERT rows
                           ▼
                    ┌─────────────┐
                    │  RDS (PG)   │  PostgreSQL 15
                    │  (private   │  Multi-AZ (prod)
                    │   subnet)   │
                    └──────┬──────┘
                           │ SQL queries
                           ▼
                    ┌─────────────┐
                    │  FastAPI    │  Python 3.12
                    │  Backend    │  SQLAlchemy async
                    │  (EKS Pod)  │  Alembic migrations
                    └──────┬──────┘
                           │ REST JSON
                           ▼
                    ┌─────────────┐
                    │   React     │  TypeScript
                    │  Frontend   │  Recharts
                    │  (EKS Pod)  │  TanStack Query
                    └─────────────┘
```

## Component Responsibilities

### S3 Bucket
- Receives raw Excel (.xlsx) uploads
- Bucket notifications trigger Lambda on `s3:ObjectCreated:*`
- All objects encrypted at rest (AES-256)
- Versioning enabled

### Lambda Processor
- Runtime: **Python 3.12**
- Trigger: S3 event notification (filter: `*.xlsx`)
- Libraries: `pandas`, `openpyxl`, `psycopg2`
- Normalizes column names, validates required fields, inserts rows into `spend_reports`
- Runs inside the VPC private subnets to reach RDS
- Timeout: 5 minutes, Memory: 512 MB

### RDS PostgreSQL
- Engine: **PostgreSQL 15**
- Single-AZ in dev, Multi-AZ in prod
- Placed in private subnets — not publicly accessible
- Accessed from: Lambda (via SG) and EKS pods (via SG)
- Automated backups: 1 day (dev), 7 days (prod)

### FastAPI Backend
- Async SQLAlchemy + asyncpg driver
- OpenAPI docs at `/docs`
- Key endpoints:
  - `GET /api/v1/reports` — paginated list with filters
  - `GET /api/v1/reports/{id}` — single record
  - `GET /api/v1/reports/analytics/summary` — aggregated stats
- Database credentials injected via Kubernetes Secret

### React Frontend
- Vite + React 18 + TypeScript
- TanStack Query for server state
- Recharts for pie/bar charts
- nginx serves static assets and proxies `/api` to backend

## Network Design

```
VPC 10.0.0.0/16
├── Public Subnets (10.0.101.0/24, 10.0.102.0/24)
│   └── NAT Gateway, ALB
└── Private Subnets (10.0.1.0/24, 10.0.2.0/24)
    ├── EKS Node Group
    ├── RDS PostgreSQL
    └── Lambda ENIs
```

## Security

- All inter-service communication within VPC
- Security groups allow only the minimum required ports
- Secrets stored in AWS Secrets Manager, mounted as Kubernetes Secrets
- ECR images scanned on push
- Lambda and EKS IAM roles follow least privilege
- RDS encrypted at rest and in transit

## Scalability

| Component | Dev | Prod |
|---|---|---|
| EKS nodes | 1 × t3.medium | 2–6 × t3.medium |
| Backend replicas | 1 | 2–6 (HPA) |
| Frontend replicas | 1 | 2–6 (HPA) |
| RDS | db.t3.micro, single-AZ | db.t3.small, Multi-AZ |
| Lambda concurrency | default | reserved concurrency as needed |
