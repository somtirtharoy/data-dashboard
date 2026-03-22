import io
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from handler import _normalize_df, process_file


def make_excel_bytes(data: dict) -> bytes:
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    return buf.read()


VALID_DATA = {
    "Ministry": ["Finance", "Health"],
    "Program": ["Operations", "Acute Care"],
    "Category": ["IT", "Medical Supplies"],
    "Vendor": ["Acme Corp", None],
    "Fiscal Year": ["2024-25", "2024-25"],
    "Period Start": ["2024-04-01", "2024-04-01"],
    "Period End": ["2024-06-30", "2024-06-30"],
    "Amount": [50000.00, 120000.50],
    "Currency": ["CAD", "CAD"],
}


def test_normalize_df_happy_path():
    df = pd.DataFrame(VALID_DATA)
    result = _normalize_df(df)
    assert len(result) == 2
    assert "ministry" in result.columns
    assert isinstance(result.iloc[0]["amount"], Decimal)


def test_normalize_df_missing_column():
    df = pd.DataFrame({"Ministry": ["Finance"], "Program": ["Ops"]})
    with pytest.raises(ValueError, match="Missing required columns"):
        _normalize_df(df)


def test_normalize_df_drops_null_ministry():
    data = VALID_DATA.copy()
    data["Ministry"] = [None, "Health"]
    df = pd.DataFrame(data)
    result = _normalize_df(df)
    assert len(result) == 1
    assert result.iloc[0]["ministry"] == "Health"


@patch("handler._download_file")
@patch("handler._get_db_conn")
def test_process_file(mock_conn, mock_download, tmp_path):
    excel_path = tmp_path / "test.xlsx"
    excel_bytes = make_excel_bytes(VALID_DATA)
    excel_path.write_bytes(excel_bytes)

    mock_download.return_value = str(excel_path)

    mock_cursor = MagicMock()
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)

    mock_conn_obj = MagicMock()
    mock_conn_obj.__enter__ = lambda s: s
    mock_conn_obj.__exit__ = MagicMock(return_value=False)
    mock_conn_obj.cursor.return_value = mock_cursor
    mock_conn.return_value = mock_conn_obj

    count = process_file("my-bucket", "uploads/test.xlsx")
    assert count == 2
