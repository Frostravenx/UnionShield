"""
processor.py — Gemini 1.5 Flash image extraction module
Sends grievance/disciplinary form images to Gemini and returns structured JSON.
"""

import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# ── Configure Gemini ───────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

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


def extract_form_data(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """
    Send an image to Gemini 1.5 Flash and extract structured form data.
    
    Args:
        image_bytes: Raw image bytes
        mime_type: MIME type of the image (image/jpeg or image/png)
    
    Returns:
        dict with keys: employee_name, employee_id, date, case_type,
                        article_violated, description
    
    Raises:
        ValueError: If API key is not configured
        Exception: On API or parsing errors
    """
    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY not found in environment. "
            "Please add it to your .env file."
        )

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config={
            "temperature": 0.1,   # Low temp for more deterministic extraction
            "top_p": 0.95,
            "max_output_tokens": 1024,
        }
    )

    # Build the content parts — image + instruction
    image_part = {
        "mime_type": mime_type,
        "data": image_bytes
    }

    response = model.generate_content(
        [SYSTEM_PROMPT, image_part],
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
        # Attempt to extract JSON object from text
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            raise ValueError(f"Gemini did not return valid JSON. Raw response: {raw_text[:500]}") from e

    # Ensure all required keys exist
    required_keys = ["employee_name", "employee_id", "date", "case_type", "article_violated", "description"]
    for key in required_keys:
        if key not in data:
            data[key] = ""

    # Normalize case_type
    valid_types = {"Grievance", "Discipline", "Arbitration", "Other"}
    ct = data.get("case_type", "").strip().title()
    data["case_type"] = ct if ct in valid_types else "Other"

    return data


def test_extraction():
    """Quick test using a sample image path. Run directly: python processor.py"""
    import sys
    if len(sys.argv) < 2:
        print("Usage: python processor.py <image_path>")
        print("\nEnvironment check:")
        print(f"  GEMINI_API_KEY: {'✓ Set' if GEMINI_API_KEY else '✗ NOT SET — add to .env'}")
        return

    image_path = sys.argv[1]
    print(f"Processing: {image_path}")

    mime = "image/png" if image_path.lower().endswith(".png") else "image/jpeg"
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    result = extract_form_data(image_bytes, mime)
    print("\nExtracted data:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    test_extraction()
