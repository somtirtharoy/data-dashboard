# Serverless — Lambda Excel Processor

## Why AWS Lambda?

**AWS Lambda** (Python 3.12) was chosen over alternatives:

| Option | Pros | Cons |
|---|---|---|
| **Lambda** | Zero servers, auto-scale, pay-per-use, native S3 trigger | Cold starts (mitigated with Provisioned Concurrency if needed) |
| ECS Task / Fargate | More control, no cold starts | Always-on cost, more complex trigger setup |
| Glue ETL | Managed, good for big data | Overkill for single-file uploads, higher latency |
| Step Functions + Lambda | Good for multi-step pipelines | Over-engineered for this use case |

Lambda is the right fit because:
- Uploads are event-driven and infrequent
- Processing a single file takes under 5 minutes
- There is no need for a persistent server

## Runtime & Libraries

| Library | Purpose |
|---|---|
| `pandas` | DataFrame operations, date parsing |
| `openpyxl` | Reading `.xlsx` files |
| `psycopg2-binary` | Direct PostgreSQL inserts |
| `boto3` | S3 file download |

## Configuration

| Setting | Value |
|---|---|
| Runtime | python3.12 |
| Handler | `handler.handler` |
| Timeout | 300 seconds |
| Memory | 512 MB |
| VPC | Yes — private subnets |

## Expected Excel Format

The Lambda is tolerant of column names in any case/spacing. Required columns:

| Excel Column | Normalized to | Required |
|---|---|---|
| Ministry | `ministry` | Yes |
| Program | `program` | Yes |
| Category | `category` | Yes |
| Vendor | `vendor` | No |
| Fiscal Year | `fiscal_year` | Yes |
| Period Start | `period_start` | Yes |
| Period End | `period_end` | Yes |
| Amount | `amount` | Yes |
| Currency | `currency` | No (defaults to CAD) |
| Description | `description` | No |

## Deployment

Lambda is packaged as a ZIP file:

```bash
cd lambda/processor
pip install -r requirements.txt -t dist/ --no-cache-dir
cp handler.py dist/
cd dist && zip -r ../function.zip . -x "*.pyc" -x "__pycache__/*"
```

The CI/CD pipeline (`lambda.yml`) automates this on merge to `main` or `develop`.

## Local Testing

```bash
cd lambda/processor
pytest tests/
```

Use `moto` to mock S3 interactions without real AWS credentials.

## Uploading a File to Trigger Processing

```bash
# Using AWS CLI
aws s3 cp spend_report_q1.xlsx s3://data-dashboard-dev-spend-uploads/

# The Lambda fires automatically within ~1 second
# Check logs:
aws logs tail /aws/lambda/data-dashboard-dev-processor --follow
```

## Monitoring

- CloudWatch Logs: `/aws/lambda/data-dashboard-{env}-processor`
- Metrics to watch: `Errors`, `Duration`, `Throttles`
- Set a CloudWatch alarm on `Errors > 0` for the production function
