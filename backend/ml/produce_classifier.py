import io
import logging
from typing import TypedDict

import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

logger = logging.getLogger(__name__)
MODEL_NAME = "jazzmacedo/fruits-and-vegetables-detector-36"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class ProduceClassification(TypedDict):
    produce_type: str
    produce_id: str
    produce_confidence: float


_model = None
_processor = None


def _get_model():
    global _model, _processor
    if _model is None or _processor is None:
        logger.info("Loading produce classifier %s on %s", MODEL_NAME, DEVICE)
        try:
            _processor = AutoImageProcessor.from_pretrained(MODEL_NAME, use_fast=False)
            _model = AutoModelForImageClassification.from_pretrained(MODEL_NAME)
            _model.to(DEVICE)
            _model.eval()
            logger.info("Produce classifier loaded: labels=%s", _model.config.num_labels)
        except Exception as exc:
            _model = None
            _processor = None
            raise RuntimeError(f"Produce classifier could not be loaded: {exc}") from exc
    return _processor, _model


def _to_produce_id(label: str) -> str:
    normalized = " ".join(label.strip().lower().replace("_", " ").split())
    aliases = {
        "bell pepper": "bell_pepper",
        "chilli pepper": "chilli_pepper",
        "jalepeno": "jalapeno",
        "soy beans": "soy_beans",
        "sweetcorn": "sweet_corn",
        "sweet potato": "sweetpotato",
    }
    return aliases.get(normalized, normalized.replace(" ", "_"))


def identify_produce(image_bytes: bytes) -> ProduceClassification:
    """Classify an uploaded fruit or vegetable image with the local HF model."""
    processor, model = _get_model()
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image = image.convert("RGB")
    except (OSError, ValueError) as exc:
        raise ValueError("The uploaded image could not be decoded as an image.") from exc

    try:
        inputs = processor(images=image, return_tensors="pt")
        inputs = {name: value.to(DEVICE) for name, value in inputs.items()}
        with torch.no_grad():
            outputs = model(**inputs)
    except Exception as exc:
        logger.exception("Produce classifier inference failed")
        raise RuntimeError(f"Produce classifier inference failed: {exc}") from exc

    probabilities = torch.softmax(outputs.logits, dim=-1)
    confidence, class_id = torch.max(probabilities, dim=-1)
    label = str(model.config.id2label[int(class_id.item())]).strip()
    if not label:
        raise RuntimeError("Produce classifier returned an empty label.")

    result = {
        "produce_type": label,
        "produce_id": _to_produce_id(label),
        "produce_confidence": round(float(confidence.item()) * 100, 2),
    }
    logger.info("Produce classifier result: %s | confidence=%.2f%%", label, result["produce_confidence"])
    return result


def load_produce_classifier() -> None:
    """Load the classifier during application startup for visible diagnostics."""
    _get_model()
