"""
database.py — Google Sheets + Cloudinary integration
Handles: connect, append rows, fetch records as DataFrame, upload images to Cloudinary.
Works on both local (.env) and Streamlit Cloud (st.secrets).
"""

import os
import io
import json
import pandas as pd
import gspread
import cloudinary
import cloudinary.uploader
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

# ── Config ─────────────────────────────────────────────────────────────────────
SHEET_NAME = "Union_Records"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

COLUMN_HEADERS = [
    "timestamp",
    "employee_name",
    "employee_id",
    "date",
    "case_type",
    "article_violated",
    "description",
    "source_file",
    "image_url",
]


# ── Secret helpers ─────────────────────────────────────────────────────────────
def _get_secret(key: str, default: str = "") -> str:
    """
    Read a secret from st.secrets (Streamlit Cloud) or os.getenv (local .env).
    Streamlit Cloud takes priority; falls back to .env for local development.
    """
    try:
        import streamlit as st
        val = st.secrets.get(key, None)
        if val:
            return str(val).strip()
    except Exception:
        pass
    return os.getenv(key, default).strip()


# ── Google credentials ─────────────────────────────────────────────────────────
def _get_credentials() -> Credentials:
    creds_json = _get_secret("GOOGLE_SERVICE_ACCOUNT_JSON")
    if creds_json:
        try:
            creds_dict = json.loads(creds_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON: {e}")
        return Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

    creds_file = _get_secret("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
    if os.path.exists(creds_file):
        return Credentials.from_service_account_file(creds_file, scopes=SCOPES)

    raise ValueError(
        "No Google credentials found. Set either:\n"
        "  GOOGLE_SERVICE_ACCOUNT_JSON (full JSON string)\n"
        "  GOOGLE_SERVICE_ACCOUNT_FILE (path to JSON file)"
    )


def _get_gspread_client() -> gspread.Client:
    return gspread.authorize(_get_credentials())


# ── Cloudinary image upload ────────────────────────────────────────────────────
def _configure_cloudinary():
    cloud_name = _get_secret("CLOUDINARY_CLOUD_NAME")
    api_key    = _get_secret("CLOUDINARY_API_KEY")
    api_secret = _get_secret("CLOUDINARY_API_SECRET")

    if not all([cloud_name, api_key, api_secret]):
        raise ValueError(
            "Cloudinary credentials missing. Add to .env or Streamlit secrets:\n"
            "  CLOUDINARY_CLOUD_NAME\n"
            "  CLOUDINARY_API_KEY\n"
            "  CLOUDINARY_API_SECRET"
        )

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True,
    )


def upload_image_to_cloudinary(image_bytes: bytes, filename: str, mime_type: str = "image/jpeg") -> str | None:
    """
    Upload a form image to Cloudinary under the union_grievances/ folder.

    Args:
        image_bytes: Raw image bytes
        filename:    Original filename — used to build the Cloudinary public_id
        mime_type:   MIME type (image/jpeg or image/png)

    Returns:
        Secure HTTPS URL on success, None on failure.
    """
    try:
        _configure_cloudinary()

        base = filename.rsplit(".", 1)[0]
        public_id = f"union_grievances/{base}"

        result = cloudinary.uploader.upload(
            io.BytesIO(image_bytes),
            public_id=public_id,
            resource_type="image",
            overwrite=False,
        )
        return result.get("secure_url")

    except Exception as e:
        print(f"[database.py] upload_image_to_cloudinary error: {e}")
        return None


# ── Google Sheets ──────────────────────────────────────────────────────────────
def _get_or_create_sheet() -> gspread.Worksheet:
    """Open Union_Records sheet, creating it with headers if needed."""
    client = _get_gspread_client()

    try:
        spreadsheet = client.open(SHEET_NAME)
    except gspread.SpreadsheetNotFound:
        spreadsheet = client.create(SHEET_NAME)
        spreadsheet.share(None, perm_type="anyone", role="writer")
        print(f"Created new spreadsheet: {SHEET_NAME}")

    worksheet = spreadsheet.sheet1
    existing = worksheet.get_all_values()

    if not existing:
        worksheet.append_row(COLUMN_HEADERS, value_input_option="RAW")
    elif existing[0] != COLUMN_HEADERS:
        worksheet.delete_rows(1)
        worksheet.insert_row(COLUMN_HEADERS, index=1)

    return worksheet


def append_record(record: dict) -> bool:
    """
    Append a validated record as a new row in the Google Sheet.
    image_url is optional — defaults to empty string if not provided.
    """
    try:
        worksheet = _get_or_create_sheet()
        row = [str(record.get(col, "")) for col in COLUMN_HEADERS]
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        print(f"[database.py] append_record error: {e}")
        return False


def get_all_records() -> pd.DataFrame | None:
    """Fetch all records as a DataFrame, sorted newest first."""
    try:
        worksheet = _get_or_create_sheet()
        data = worksheet.get_all_records(expected_headers=COLUMN_HEADERS)

        if not data:
            return pd.DataFrame(columns=COLUMN_HEADERS)

        df = pd.DataFrame(data)
        for col in COLUMN_HEADERS:
            if col not in df.columns:
                df[col] = ""

        if "timestamp" in df.columns:
            df = df.sort_values("timestamp", ascending=False).reset_index(drop=True)

        return df[COLUMN_HEADERS]

    except Exception as e:
        print(f"[database.py] get_all_records error: {e}")
        return None


def search_records(query: str, search_fields: list | None = None) -> pd.DataFrame | None:
    """Filter records by query string across specified fields."""
    if search_fields is None:
        search_fields = ["employee_name", "employee_id"]

    df = get_all_records()
    if df is None or df.empty:
        return df

    query = query.strip().lower()
    if not query:
        return df

    mask = pd.Series(False, index=df.index)
    for field in search_fields:
        if field in df.columns:
            mask |= df[field].str.lower().str.contains(query, na=False)

    return df[mask].reset_index(drop=True)


def delete_record_by_employee_id(employee_id: str) -> int:
    """Delete all sheet rows matching a given employee_id. Returns count deleted."""
    try:
        worksheet = _get_or_create_sheet()
        all_values = worksheet.get_all_values()
        headers = all_values[0] if all_values else []

        try:
            id_col_idx = headers.index("employee_id") + 1
        except ValueError:
            return 0

        rows_to_delete = []
        for i, row in enumerate(all_values[1:], start=2):
            if len(row) >= id_col_idx and row[id_col_idx - 1].strip() == employee_id.strip():
                rows_to_delete.append(i)

        for row_idx in sorted(rows_to_delete, reverse=True):
            worksheet.delete_rows(row_idx)

        return len(rows_to_delete)

    except Exception as e:
        print(f"[database.py] delete_record error: {e}")
        return 0


# ── CLI test ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Google Sheets + Cloudinary connection...\n")

    try:
        worksheet = _get_or_create_sheet()
        print(f"✓ Sheets connected: {worksheet.spreadsheet.title}")
    except Exception as e:
        print(f"✗ Sheets failed: {e}")

    try:
        import base64
        tiny_png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg=="
        )
        url = upload_image_to_cloudinary(tiny_png, "test_upload.png", "image/png")
        if url:
            print(f"✓ Cloudinary upload: {url}")
        else:
            print("✗ Cloudinary upload returned None")
    except Exception as e:
        print(f"✗ Cloudinary failed: {e}")
