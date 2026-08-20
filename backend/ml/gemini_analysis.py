import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
from pathlib import Path
from PIL import Image
import io

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

logger = logging.getLogger(__name__)


class GeminiUnavailable(RuntimeError):
    pass


def analyze_with_gemini(image_bytes: bytes) -> dict[str, Any]:
    """Use Gemini Flash for produce identification and freshness when configured."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        raise GeminiUnavailable("GEMINI_API_KEY is not configured.")

    try:
        from google import genai
        from google.genai import types

        with Image.open(io.BytesIO(image_bytes)) as image:
            format_name = (image.format or "JPEG").lower()
        mime_type = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(format_name, "image/jpeg")

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                """Analyze this fruit or vegetable image. Return only JSON with keys:
                produce_type (string), produce_confidence (number 0-100),
                freshness_percent (number 0-100), freshness_label (Fresh, Slightly Aged, or Overripe),
                freshness_note (string), quality_adjustment (integer, usually 0, -2, or -5),
                quality_adjustment_label (string). Do not add markdown.""",
            ],
        )
        text = (response.text or "").strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        result = json.loads(text)
        required = ("produce_type", "produce_confidence", "freshness_percent", "freshness_label", "freshness_note")
        if any(key not in result for key in required):
            raise ValueError("Gemini response omitted required analysis fields.")
        result["analysis_provider"] = "gemini"
        return result
    except GeminiUnavailable:
        raise
    except Exception as exc:
        logger.exception("Gemini produce analysis failed")
        raise GeminiUnavailable(f"Gemini analysis failed: {exc}") from exc
