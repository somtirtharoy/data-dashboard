# Data Dashboard

A full-stack data analytics platform for processing Excel spend reports. Uploads to S3 trigger a Lambda function that parses the spreadsheet and persists data to PostgreSQL. A React frontend visualizes the data via tables, pie charts, and histograms.

## Architecture Overview

```
Excel Upload → S3 Bucket → Lambda (Python) → RDS PostgreSQL
                                                     ↑
                                          FastAPI Backend (EKS)
                                                     ↑
                                          React Frontend (EKS)
```

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript, Recharts, TanStack Table |
| Backend | FastAPI (Python 3.12), SQLAlchemy, Alembic |
| Data Ingestion | AWS Lambda (Python), pandas, openpyxl |
| Database | Amazon RDS PostgreSQL 15 |
| Storage | Amazon S3 |
| Container Orchestration | AWS EKS + Helm 3 |
| Infrastructure as Code | Terraform 1.x |
| CI/CD | GitHub Actions |

## Repository Structure

```
data-dashboard/
├── backend/              # FastAPI application
├── frontend/             # React + TypeScript SPA
├── lambda/               # S3-triggered Excel processor
├── infra/
│   ├── terraform/        # All AWS resource definitions
│   └── helm/             # Kubernetes Helm charts
├── .github/workflows/    # CI/CD pipelines
├── docs/                 # Architecture and setup docs
├── docker-compose.yml    # Local development
└── Makefile              # Common dev commands
```

## Quick Start (Local)

### Prerequisites
- Docker + Docker Compose
- Node 20+
- Python 3.12+
- AWS CLI (for deploying)

### Run Locally

```bash
# Clone and start all services
git clone <repo-url>
cd data-dashboard

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Start all services
make dev

# Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Documentation

- [Architecture](docs/architecture.md)
- [Database Design](docs/database.md)
- [Serverless / Lambda](docs/serverless.md)
- [Infrastructure Setup](docs/infrastructure.md)
- [CI/CD Setup](docs/cicd.md)
- [Getting Started](docs/getting-started.md)

## Development

```bash
make lint        # Run all linters
make test        # Run all tests
make build       # Build all Docker images
make deploy-dev  # Deploy to dev environment
```

## License

Copyright © Province of British Columbia. See [LICENSE](LICENSE).
