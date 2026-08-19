from typing import TypedDict, Literal
from pathlib import Path

import cv2
import numpy as np
from tf_keras.models import load_model


class FreshnessResult(TypedDict):
    freshness_label: Literal["Fresh", "Slightly Aged", "Overripe"]
    freshness_percent: int
    freshness_note: str
    quality_adjustment: int
    quality_adjustment_label: str


MODEL_PATH = Path(__file__).resolve().parent / "models" / "rottenvsfresh98pval.h5"

# The legacy tf_keras loader is required for this older H5 model.
model = load_model(MODEL_PATH, compile=False)

def detect_produce(image: bytes) -> tuple[str, float]:
    """
    Hackathon MVP: A lightweight color-based heuristic to classify 
    the produce as tomato, potato, or onion instead of a heavy CNN.
    Returns (produce_type, confidence_score)
    """
    image_array = np.frombuffer(image, dtype=np.uint8)
    img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if img is None:
        return ("tomato", 0.5)
        
    # Resize to speed up and reduce noise
    img = cv2.resize(img, (50, 50))
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Get median color to avoid background skew
    h, s, v = np.median(hsv[:,:,0]), np.median(hsv[:,:,1]), np.median(hsv[:,:,2])
    
    # Red hue (0-15 or 160-180) -> Tomato
    if (h < 15 or h > 160) and s > 80:
        return ("tomato", 0.92)
    # Brown/Tan/Yellow hue (15-40) -> Potato
    elif 15 <= h <= 40:
        return ("potato", 0.88)
    # Else (Pink/Purple/White) -> Onion
    else:
        return ("onion", 0.85)


def predict_freshness(image: bytes, produce_type: str) -> FreshnessResult:
    """Return the model's freshness assessment for an uploaded produce image."""

    image_array = np.frombuffer(image, dtype=np.uint8)
    img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("The uploaded image could not be read.")

    # Must match the preprocessing used when testing this trained model.
    img = cv2.resize(img, (100, 100))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype("float32") / 255.0
    img = np.expand_dims(img, axis=0)

    # Model convention: 0 = fresh, 1 = not fresh.
    not_fresh_score = float(model.predict(img, verbose=0)[0][0])
    not_fresh_score = max(0.0, min(1.0, not_fresh_score))
    freshness_percent = round((1.0 - not_fresh_score) * 100)

    if not_fresh_score < 0.10:
        return {
            "freshness_label": "Fresh",
            "freshness_percent": freshness_percent,
            "freshness_note": f"{produce_type.capitalize()} appears fresh and suitable for sale.",
            "quality_adjustment": 0,
            "quality_adjustment_label": "No freshness deduction",
        }

    if not_fresh_score < 0.35:
        return {
            "freshness_label": "Slightly Aged",
            "freshness_percent": freshness_percent,
            "freshness_note": (
                f"{produce_type.capitalize()} is still usable but should be consumed soon."
            ),
            "quality_adjustment": -2,
            "quality_adjustment_label": "Slight freshness deduction",
        }

    return {
        "freshness_label": "Overripe",
        "freshness_percent": freshness_percent,
        "freshness_note": (
            f"{produce_type.capitalize()} appears spoiled or severely overripe "
            "and is not fit for sale."
        ),
        "quality_adjustment": -5,
        "quality_adjustment_label": "Spoiled produce — do not buy",
    }