"""
processor.py — Gemini image extraction module
Sends grievance/disciplinary form images to Gemini and returns structured JSON.
Uses the new google.genai package (replaces deprecated google.generativeai).
"""

import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "gemini-3.1-flash-lite-preview"

SYSTEM_PROMPT = """You are an expert legal secretary for a labor union. 
Extract the following fields from this form into a strict JSON format:
- employee_name
- employee_id
- date (in YYYY-MM-DD format if possible)
- case_type (must be one of: Grievance, Discipline, Arbitration, Other)
- article_violated
- description

Rules:
- If handwriting is unclear, provide your best guess
- If a field is completely unreadable or absent, use an empty string ""
- date should be formatted as YYYY-MM-DD when possible
- Only return valid JSON — no preamble, no explanation, no markdown backticks
- The JSON must have exactly these 6 keys

Example output:
{"employee_name": "John Smith", "employee_id": "UPS-00123", "date": "2024-01-15", "case_type": "Grievance", "article_violated": "Article 37", "description": "Employee was forced to work overtime without authorization."}"""


def _get_api_key() -> str:
    """Get Gemini API key from st.secrets or .env."""
    try:
        import streamlit as st
        val = st.secrets.get("GEMINI_API_KEY", None)
        if val:
            return str(val).strip()
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY", "").strip()


def extract_form_data(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """
    Send an image to Gemini and extract structured form data.

    Args:
        image_bytes: Raw image bytes
        mime_type:   MIME type of the image (image/jpeg or image/png)

    Returns:
        dict with keys: employee_name, employee_id, date, case_type,
                        article_violated, description

    Raises:
        ValueError: If API key is not configured
        Exception:  On API or parsing errors
    """
    from google import genai
    from google.genai import types

    api_key = _get_api_key()
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found. "
            "Add it to your .env file or Streamlit secrets."
        )

    client = genai.Client(api_key=api_key)

    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[SYSTEM_PROMPT, image_part],
        config=types.GenerateContentConfig(
            temperature=0.1,
            top_p=0.95,
            max_output_tokens=1024,
        ),
    )

    raw_text = response.text.strip()

    # Strip markdown code fences if present
    raw_text = re.sub(r'^```(?:json)?\s*', '', raw_text)
    raw_text = re.sub(r'\s*```$', '', raw_text)
    raw_text = raw_text.strip()

    # Parse JSON
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            raise ValueError(
                f"Gemini did not return valid JSON. Raw response: {raw_text[:500]}"
            ) from e

    # Ensure all required keys exist
    for key in ["employee_name", "employee_id", "date", "case_type", "article_violated", "description"]:
        if key not in data:
            data[key] = ""

    # Normalize case_type
    valid_types = {"Grievance", "Discipline", "Arbitration", "Other"}
    ct = data.get("case_type", "").strip().title()
    data["case_type"] = ct if ct in valid_types else "Other"

    return data


if __name__ == "__main__":
    import sys
    api_key = _get_api_key()
    print(f"GEMINI_API_KEY: {'✓ Set' if api_key else '✗ NOT SET'}")
    print(f"Model: {MODEL_NAME}")

    if len(sys.argv) >= 2:
        image_path = sys.argv[1]
        mime = "image/png" if image_path.lower().endswith(".png") else "image/jpeg"
        with open(image_path, "rb") as f:
            result = extract_form_data(f.read(), mime)
        print(json.dumps(result, indent=2))
