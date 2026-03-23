"""
S3-triggered Lambda: parse Excel spend report → insert rows into PostgreSQL.

Expected Excel columns (case-insensitive, whitespace-stripped):
  Ministry | Program | Category | Vendor | Fiscal Year |
  Period Start | Period End | Amount | Currency | Description
"""

import json
import logging
import os
import tempfile
from datetime import date
from decimal import Decimal

import boto3
import pandas as pd
import psycopg2
import psycopg2.extras
from urllib.parse import unquote_plus

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]

_s3_kwargs = {}
if os.environ.get("AWS_ENDPOINT_URL"):
    _s3_kwargs["endpoint_url"] = os.environ["AWS_ENDPOINT_URL"]

s3_client = boto3.client("s3", **_s3_kwargs)

COLUMN_MAP = {
    "ministry": "ministry",
    "program": "program",
    "category": "category",
    "vendor": "vendor",
    "fiscal year": "fiscal_year",
    "fiscal_year": "fiscal_year",
    "period start": "period_start",
    "period_start": "period_start",
    "period end": "period_end",
    "period_end": "period_end",
    "amount": "amount",
    "currency": "currency",
    "description": "description",
}

INSERT_SQL = """
INSERT INTO spend_reports
  (source_file, ministry, program, category, vendor, fiscal_year,
   period_start, period_end, amount, currency, description)
VALUES %s
ON CONFLICT DO NOTHING
"""


def _get_db_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=10,
    )


def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip().lower() for c in df.columns]
    df = df.rename(columns=COLUMN_MAP)

    required = {"ministry", "program", "category", "fiscal_year", "period_start", "period_end", "amount"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["period_start"] = pd.to_datetime(df["period_start"]).dt.date
    df["period_end"] = pd.to_datetime(df["period_end"]).dt.date
    df["amount"] = df["amount"].apply(lambda x: Decimal(str(x)))
    df["currency"] = df.get("currency", "CAD").fillna("CAD")
    df["vendor"] = df.get("vendor", pd.NA)
    df["description"] = df.get("description", pd.NA)

    df = df.dropna(subset=["ministry", "program", "category", "amount"])
    return df


def _download_file(bucket: str, key: str) -> str:
    suffix = ".xlsx" if key.endswith(".xlsx") else ".xls"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    s3_client.download_fileobj(bucket, key, tmp)
    tmp.flush()
    return tmp.name


def process_file(bucket: str, key: str) -> int:
    local_path = _download_file(bucket, key)

    df = pd.read_excel(local_path, engine="openpyxl")
    df = _normalize_df(df)

    rows = [
        (
            key,
            row["ministry"],
            row["program"],
            row["category"],
            row.get("vendor") if pd.notna(row.get("vendor")) else None,
            row["fiscal_year"],
            row["period_start"],
            row["period_end"],
            row["amount"],
            row["currency"],
            row.get("description") if pd.notna(row.get("description")) else None,
        )
        for _, row in df.iterrows()
    ]

    with _get_db_conn() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(cur, INSERT_SQL, rows)
        conn.commit()

    logger.info("Inserted %d rows from s3://%s/%s", len(rows), bucket, key)
    return len(rows)


def handler(event: dict, context) -> dict:
    records = event.get("Records", [])
    total_inserted = 0

    for record in records:
        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])
        logger.info("Processing s3://%s/%s", bucket, key)

        try:
            n = process_file(bucket, key)
            total_inserted += n
        except Exception:
            logger.exception("Failed to process s3://%s/%s", bucket, key)
            raise

    return {"statusCode": 200, "body": json.dumps({"inserted": total_inserted})}
