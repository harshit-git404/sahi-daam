import logging
from typing import TypedDict, Literal
from pathlib import Path

import cv2
import numpy as np
from tf_keras.models import load_model

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class FreshnessResult(TypedDict):
    freshness_label: Literal["Fresh", "Slightly Aged", "Overripe"]
    freshness_percent: int
    freshness_note: str
    quality_adjustment: int
    quality_adjustment_label: str


MODEL_PATH = Path(__file__).resolve().parent / "models" / "rottenvsfresh98pval.h5"
model = None


def _get_model():
    global model
    if model is None:
        if not MODEL_PATH.is_file():
            raise RuntimeError(f"Freshness model not found: {MODEL_PATH}")
        try:
            # The legacy tf_keras loader is required for this older H5 model.
            model = load_model(MODEL_PATH, compile=False)
            logger.info(
                "Freshness model loaded: input_shape=%s output_shape=%s",
                model.input_shape,
                model.output_shape,
            )
        except Exception as exc:
            raise RuntimeError(f"Freshness model could not be loaded: {exc}") from exc
    return model


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
    loaded_model = _get_model()
    not_fresh_score = float(loaded_model.predict(img, verbose=0)[0][0])
    not_fresh_score = max(0.0, min(1.0, not_fresh_score))
    freshness_percent = round((1.0 - not_fresh_score) * 100)
    logger.info("Raw model score: %s", not_fresh_score)
    logger.info("Final freshness percentage: %s%%", freshness_percent)

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