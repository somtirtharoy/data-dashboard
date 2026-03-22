.PHONY: dev lint test build clean deploy-dev deploy-prod

# ─── Local Development ────────────────────────────────────────────────────────

dev:
	docker compose up --build

dev-down:
	docker compose down -v

# ─── Linting ──────────────────────────────────────────────────────────────────

lint: lint-backend lint-frontend lint-lambda lint-terraform

lint-backend:
	cd backend && ruff check . && mypy app/

lint-frontend:
	cd frontend && npm run lint

lint-lambda:
	cd lambda/processor && ruff check . && mypy .

lint-terraform:
	cd infra/terraform && terraform fmt -check -recursive

# ─── Testing ──────────────────────────────────────────────────────────────────

test: test-backend test-frontend test-lambda

test-backend:
	cd backend && pytest --cov=app --cov-report=term-missing

test-frontend:
	cd frontend && npm test -- --run

test-lambda:
	cd lambda/processor && pytest

# ─── Build ────────────────────────────────────────────────────────────────────

build: build-backend build-frontend build-lambda

build-backend:
	docker build -t data-dashboard-backend:latest ./backend

build-frontend:
	docker build -t data-dashboard-frontend:latest ./frontend

build-lambda:
	cd lambda/processor && pip install -r requirements.txt -t dist/ && \
	  cp handler.py dist/ && \
	  cd dist && zip -r ../function.zip .

# ─── Infrastructure ───────────────────────────────────────────────────────────

tf-init-%:
	cd infra/terraform/environments/$* && terraform init

tf-plan-%:
	cd infra/terraform/environments/$* && terraform plan -var="db_password=$(DB_PASSWORD)"

tf-apply-%:
	cd infra/terraform/environments/$* && terraform apply -var="db_password=$(DB_PASSWORD)"

tf-destroy-dev:
	cd infra/terraform/environments/dev && terraform destroy -var="db_password=$(DB_PASSWORD)"

# ─── Helm / Kubernetes ────────────────────────────────────────────────────────

helm-lint:
	helm lint infra/helm/backend
	helm lint infra/helm/frontend

# helm-deploy-<env>  e.g. make helm-deploy-dev  make helm-deploy-stage  make helm-deploy-prod
helm-deploy-%:
	helm upgrade --install backend infra/helm/backend \
	  --namespace data-dashboard --create-namespace \
	  -f infra/helm/backend/values-$*.yaml
	helm upgrade --install frontend infra/helm/frontend \
	  --namespace data-dashboard \
	  -f infra/helm/frontend/values-$*.yaml

# ─── Database ─────────────────────────────────────────────────────────────────

db-migrate:
	cd backend && alembic upgrade head

db-rollback:
	cd backend && alembic downgrade -1

# ─── E2E Tests ────────────────────────────────────────────────────────────────

e2e-install:
	pip install -r e2e/requirements.txt
	cd e2e && npm install --save-dev @playwright/test && npx playwright install chromium

e2e-lambda-db:
	# Layer 1+2: Lambda handler → DB → API (no browser)
	pytest e2e/test_lambda_to_db.py e2e/test_api.py -v

e2e-browser:
	# Layer 3: Full browser tests via Playwright
	cd e2e && npx playwright test test_frontend.spec.ts

e2e: e2e-lambda-db e2e-browser

# ─── Utilities ────────────────────────────────────────────────────────────────

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -name "*.pyc" -delete
	cd frontend && rm -rf dist node_modules/.cache
