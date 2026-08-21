import io
import logging
from pathlib import Path
from typing import Literal, TypedDict

import numpy as np
from PIL import Image

try:
    from tf_keras.models import load_model
except ImportError:
    try:
        from tensorflow.keras.models import load_model
    except ImportError:
        try:
            from keras.models import load_model
        except ImportError:
            load_model = None

logger = logging.getLogger(__name__)
MODEL_PATH = Path(__file__).resolve().parent / "models" / "rottenvsfresh98pval.h5"
_model = None


class FreshnessResult(TypedDict):
    freshness_label: Literal["Fresh", "Slightly Aged", "Overripe"]
    freshness_percent: int
    freshness_note: str
    quality_adjustment: int
    quality_adjustment_label: str


def _get_model():
    global _model
    if _model is None:
        if load_model is None:
            raise RuntimeError("Keras / tf_keras is not installed; freshness model is unavailable.")
        if not MODEL_PATH.is_file():
            raise RuntimeError(f"Freshness model not found: {MODEL_PATH}")
        try:
            _model = load_model(MODEL_PATH, compile=False)
            if _model.input_shape[-3:] != (100, 100, 3) or _model.output_shape[-1] != 1:
                raise RuntimeError(
                    f"Unexpected freshness model shape: input={_model.input_shape}, output={_model.output_shape}"
                )
            logger.info("Freshness model loaded: input_shape=%s output_shape=%s", _model.input_shape, _model.output_shape)
        except Exception as exc:
            _model = None
            raise RuntimeError(f"Freshness model could not be loaded: {exc}") from exc
    return _model


def predict_freshness(image_bytes: bytes, produce_type: str) -> FreshnessResult:
    """Run the H5 model. Its documented convention is 0=fresh and 1=not fresh."""
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image = image.convert("RGB").resize((100, 100))
            image_array = np.asarray(image, dtype=np.float32) / 255.0
    except (OSError, ValueError) as exc:
        raise ValueError("The uploaded image could not be decoded as an image.") from exc

    input_batch = np.expand_dims(image_array, axis=0)
    loaded_model = _get_model()
    try:
        raw_output = loaded_model.predict(input_batch, verbose=0)
        not_fresh_score = float(raw_output[0][0])
    except Exception as exc:
        logger.exception("Freshness model inference failed")
        raise RuntimeError(f"Freshness model inference failed: {exc}") from exc

    logger.info("Freshness raw model output: %s", raw_output.tolist())
    not_fresh_score = max(0.0, min(1.0, not_fresh_score))
    freshness_percent = round((1.0 - not_fresh_score) * 100)
    logger.info("Freshness result: %s | score=%d%%", produce_type, freshness_percent)

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
            "freshness_note": f"{produce_type.capitalize()} is still usable but should be consumed soon.",
            "quality_adjustment": -2,
            "quality_adjustment_label": "Slight freshness deduction",
        }
    return {
        "freshness_label": "Overripe",
        "freshness_percent": freshness_percent,
        "freshness_note": f"{produce_type.capitalize()} appears spoiled or severely overripe and is not fit for sale.",
        "quality_adjustment": -5,
            "quality_adjustment_label": "Spoiled produce - do not buy",
    }


def load_freshness_model() -> None:
    """Load the H5 model during application startup for visible diagnostics."""
    _get_model()
