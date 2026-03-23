# Infrastructure Setup on AWS

## Overview

All AWS resources are managed with **Terraform** and deployed to **ca-central-1** (Canada Central).

```
AWS Account
└── ca-central-1
    ├── VPC (10.0.0.0/16)
    │   ├── Public Subnets  → NAT Gateway, ALB
    │   └── Private Subnets → EKS nodes, RDS, Lambda
    ├── EKS Cluster
    ├── RDS PostgreSQL
    ├── S3 Bucket (uploads)
    ├── Lambda Function
    ├── ECR Repositories (backend, frontend)
    └── Secrets Manager
```

## Prerequisites

1. AWS CLI v2 installed and configured
2. Terraform >= 1.6 installed
3. `kubectl` installed
4. `helm` 3.x installed
5. An S3 bucket and DynamoDB table for Terraform state (bootstrap once):

```bash
# Create state bucket
aws s3api create-bucket \
  --bucket bcgov-data-dashboard-tfstate \
  --region ca-central-1 \
  --create-bucket-configuration LocationConstraint=ca-central-1

aws s3api put-bucket-versioning \
  --bucket bcgov-data-dashboard-tfstate \
  --versioning-configuration Status=Enabled

# Create DynamoDB lock table
aws dynamodb create-table \
  --table-name bcgov-data-dashboard-tflock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ca-central-1
```

## IAM Permissions Required

The deploying IAM user/role needs permissions for:
- `ec2:*` (VPC, subnets, security groups)
- `eks:*`
- `rds:*`
- `s3:*`
- `lambda:*`
- `iam:CreateRole`, `iam:AttachRolePolicy`, `iam:PassRole`
- `ecr:*`
- `secretsmanager:*`

For least privilege, create a dedicated deployment role with a boundary policy.

## First-Time Deployment

### 1. Create ECR repositories

```bash
aws ecr create-repository --repository-name data-dashboard-backend --region ca-central-1
aws ecr create-repository --repository-name data-dashboard-frontend --region ca-central-1
```

### 2. Store secrets in AWS Secrets Manager

```bash
aws secretsmanager create-secret \
  --name data-dashboard/dev/db-password \
  --secret-string "your-strong-password" \
  --region ca-central-1
```

### 3. Run Terraform

```bash
cd infra/terraform/environments/dev

terraform init
terraform plan -var="db_password=your-strong-password"
terraform apply -var="db_password=your-strong-password"
```

Terraform will output:
- `cluster_name` — EKS cluster name
- `rds_endpoint` — RDS hostname
- `s3_bucket` — Upload bucket name

### 4. Configure kubectl

```bash
aws eks update-kubeconfig \
  --name data-dashboard-dev \
  --region ca-central-1
kubectl get nodes  # verify connectivity
```

### 5. Create Kubernetes Secrets

```bash
kubectl create namespace data-dashboard

kubectl create secret generic backend-secrets \
  --namespace data-dashboard \
  --from-literal=DATABASE_URL="postgresql+asyncpg://dashboard:<password>@<rds-endpoint>:5432/dashboard"
```

### 6. Deploy Helm charts

```bash
make helm-deploy-dev
```

### 7. Run database migrations

```bash
kubectl exec -n data-dashboard \
  deploy/backend-backend \
  -- alembic upgrade head
```

## Production Differences

- `single_nat_gateway = false` → one NAT GW per AZ
- RDS: `multi_az = true`, `deletion_protection = true`, 7-day backups
- EKS: `min_size = 2`, `desired_size = 2`
- GitHub Actions `production` environment gate requires manual approval before `terraform apply`

## Updating Infrastructure

```bash
# After editing Terraform files:
cd infra/terraform/environments/dev
terraform plan
terraform apply
```

Changes to EKS node groups or VPCs may require draining pods first.

## Destroying (Dev Only)

```bash
cd infra/terraform/environments/dev
terraform destroy -var="db_password=your-password"
```

Note: Production has `deletion_protection = true` on RDS and will block `terraform destroy`.

## Cost Estimates (dev, ca-central-1, ~730 hrs/month)

| Resource | Approx. Monthly Cost |
|---|---|
| EKS cluster endpoint | ~$73 |
| 1× t3.medium node | ~$40 |
| RDS db.t3.micro | ~$18 |
| NAT Gateway | ~$35 |
| S3 (< 1 GB) | < $1 |
| Lambda (event-driven) | < $1 |
| **Total** | **~$167/month** |
