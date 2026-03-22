# CI/CD Setup

## Pipeline Overview

Four GitHub Actions workflows handle separate concerns:

| Workflow | File | Triggers |
|---|---|---|
| Backend | `.github/workflows/backend.yml` | Push/PR to `backend/**` |
| Frontend | `.github/workflows/frontend.yml` | Push/PR to `frontend/**` |
| Lambda | `.github/workflows/lambda.yml` | Push/PR to `lambda/**` |
| Infrastructure | `.github/workflows/infra.yml` | Push/PR to `infra/terraform/**` |

## Branch Strategy

```
main     ──────────────────────────────→  Production deploy (after gate)
develop  ──────────────────────────────→  Dev deploy (automatic)
feature/* ─→ PR → develop
```

- All merges require passing CI
- `main` deploys require a GitHub Environment approval gate

## Required GitHub Secrets

Set these in **Settings → Secrets and variables → Actions**:

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM key for the CI/CD deploy role |
| `AWS_SECRET_ACCESS_KEY` | IAM secret for the CI/CD deploy role |
| `AWS_ACCOUNT_ID` | 12-digit AWS account ID (used to build ECR URI) |
| `DB_PASSWORD` | RDS master password (used by Terraform) |

## Backend Pipeline Stages

```
lint → test → build+push image to ECR → helm deploy to EKS
```

1. **lint**: `ruff check` + `mypy`
2. **test**: pytest against a real PostgreSQL service container (not mocked)
3. **build-push**: multi-stage Docker build, tagged with `git sha` + `latest`/`dev`
4. **deploy**: `helm upgrade --install` with `--wait`, rolls back on failure

## Frontend Pipeline Stages

```
lint+typecheck → test → build+push image to ECR → helm deploy to EKS
```

1. **lint**: ESLint with zero warnings allowed
2. **typecheck**: `tsc --noEmit`
3. **test**: Vitest with jsdom
4. **build-push**: nginx-served production build
5. **deploy**: same Helm pattern as backend

## Lambda Pipeline Stages

```
lint+test → package zip → aws lambda update-function-code
```

No Docker image — Lambda uses a ZIP package. The deploy step calls `update-function-code` directly.

## Infrastructure Pipeline Stages

```
fmt check → init → validate → plan → [manual gate] → apply
```

- `apply` only runs on `main` and requires the `production` GitHub environment to approve
- The plan artifact is saved and reused in the apply step to prevent drift

## Setting Up the Production Gate

1. In GitHub, go to **Settings → Environments → New environment**
2. Name it `production`
3. Add **Required reviewers** (at least one team member)
4. The `terraform-apply` and backend/frontend `deploy` jobs use `environment: production`

## Local Testing of CI Steps

```bash
# Simulate backend lint+test
make lint-backend
make test-backend

# Simulate Lambda packaging
make build-lambda

# Simulate Helm render (dry run)
helm template backend infra/helm/backend -f infra/helm/backend/values-dev.yaml
```

## Image Tagging Strategy

- `<sha>` — immutable, every build
- `dev` — latest build on `develop` branch
- `latest` — latest build on `main` branch

Helm deploys always use the `<sha>` tag for precision; the mutable tags are for convenience.

## Rollback

```bash
# Roll back a Helm release to the previous revision
helm rollback backend 0 --namespace data-dashboard

# Or re-deploy a specific image tag
helm upgrade backend infra/helm/backend \
  --namespace data-dashboard \
  --set image.tag=<previous-sha> \
  -f infra/helm/backend/values-prod.yaml
```
