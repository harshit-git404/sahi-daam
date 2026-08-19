from typing import TypedDict, Literal
from pathlib import Path

import os
import json
from typing import TypedDict, Literal
from dotenv import load_dotenv

# Load environment variables (GEMINI_API_KEY)
load_dotenv()

class FreshnessResult(TypedDict):
    freshness_label: Literal["Fresh", "Slightly Aged", "Overripe"]
    freshness_percent: int
    freshness_note: str
    quality_adjustment: int
    quality_adjustment_label: str

def analyze_produce_with_gemini(image_bytes: bytes) -> tuple[str, FreshnessResult]:
    """
    Sends the image to Gemini Vision API to detect the produce and assess freshness.
    Returns (detected_produce_id, FreshnessResult).
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        # MOCK FALLBACK for hackathon if no API key is provided
        return ("coconut", {
            "freshness_label": "Fresh",
            "freshness_percent": 90,
            "freshness_note": "Mocked by AI: The coconut husk looks intact with no visible cracks or mold. (Add your Gemini API Key in .env for real analysis!)",
            "quality_adjustment": 0,
            "quality_adjustment_label": "Intact husk"
        })

    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=api_key)
        
        prompt = """
        Analyze this image of produce.
        Return ONLY a raw JSON object with the following structure (no markdown tags):
        {
          "detected_produce_id": "apple|banana|tomato|onion|potato|coconut|etc...",
          "freshness_label": "Fresh|Slightly Aged|Overripe",
          "freshness_percent": <number 0-100>,
          "freshness_note": "<A short 1-sentence observation on its visual quality>",
          "quality_adjustment": <number 0 to -10 depending on damage>,
          "quality_adjustment_label": "<short 2-3 word reason for deduction, e.g. 'Bruised skin'>"
        }
        """
        
        # We need to upload or pass the raw bytes. With GenAI SDK we can pass bytes directly.
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'),
                prompt
            ]
        )
        
        # Clean the JSON response (strip markdown blocks if Gemini returns them)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
            
        data = json.loads(text)
        
        result: FreshnessResult = {
            "freshness_label": data.get("freshness_label", "Fresh"),
            "freshness_percent": data.get("freshness_percent", 85),
            "freshness_note": data.get("freshness_note", "Visual analysis complete."),
            "quality_adjustment": data.get("quality_adjustment", 0),
            "quality_adjustment_label": data.get("quality_adjustment_label", "No deductions")
        }
        
        return (data.get("detected_produce_id", "unknown").lower(), result)

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return ("unknown", {
            "freshness_label": "Fresh",
            "freshness_percent": 85,
            "freshness_note": "Failed to analyze image due to API error.",
            "quality_adjustment": 0,
            "quality_adjustment_label": "API Error"
        })