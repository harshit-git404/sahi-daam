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

# Load MobileNetV2 for real object classification
from tf_keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
classification_model = MobileNetV2(weights='imagenet')

def detect_produce(image: bytes) -> tuple[str, float]:
    """
    Uses MobileNetV2 to classify the object.
    """
    image_array = np.frombuffer(image, dtype=np.uint8)
    img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if img is None:
        return ("tomato", 0.5)
        
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (224, 224))
    img = np.expand_dims(img, axis=0)
    img = preprocess_input(img)
    
    preds = classification_model.predict(img, verbose=0)
    results = decode_predictions(preds, top=5)[0]
    
    # Check top predictions for keywords
    top_labels = [res[1].lower() for res in results]
    confidence = float(results[0][2])
    
    for label in top_labels:
        if 'banana' in label: return ('banana', confidence)
        if 'apple' in label or 'granny_smith' in label: return ('apple', confidence)
        if 'orange' in label or 'lemon' in label: return ('orange', confidence)
        if 'bell_pepper' in label or 'strawberry' in label or 'tomato' in label: return ('tomato', confidence) # ImageNet has weird tomato mappings
        if 'onion' in label or 'garlic' in label: return ('onion', confidence)
        if 'potato' in label or 'squash' in label: return ('potato', confidence)

    # Fallback to the top ImageNet label if it's something weird (like laptop)
    return (top_labels[0], confidence)


def predict_freshness(image: bytes, produce_type: str) -> FreshnessResult:
    """Return the model's freshness assessment for an uploaded produce image."""
    
    # Bypassing the .h5 model for unsupported fruits because it's only trained on tomatoes/onions/potatoes!
    if produce_type not in ['tomato', 'onion', 'potato']:
        # Mock freshness for other fruits so the progress bar isn't 0%
        return {
            "freshness_label": "Fresh",
            "freshness_percent": 88,
            "freshness_note": f"{produce_type.capitalize()} appears fresh. (Freshness simulated for demo)",
            "quality_adjustment": 0,
            "quality_adjustment_label": "No freshness deduction",
        }

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