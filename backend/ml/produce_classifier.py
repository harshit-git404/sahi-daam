import io
import logging
from typing import TypedDict

import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MODEL_NAME = "jazzmacedo/fruits-and-vegetables-detector-36"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

logger.info("Loading produce classifier %s on %s", MODEL_NAME, DEVICE)
try:
    processor = AutoImageProcessor.from_pretrained(MODEL_NAME)
    model = AutoModelForImageClassification.from_pretrained(MODEL_NAME)
    model.to(DEVICE)
    model.eval()
except Exception as exc:
    raise RuntimeError(f"Produce classifier could not be loaded: {exc}") from exc


class ProduceClassification(TypedDict):
    produce_type: str
    produce_confidence: float


def identify_produce(image_bytes: bytes) -> ProduceClassification:
    """Identify the main fruit or vegetable in encoded image bytes."""

    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image = image.convert("RGB")
    except (OSError, ValueError) as exc:
        raise ValueError("The uploaded image could not be decoded as an image.") from exc

    inputs = processor(images=image, return_tensors="pt")
    inputs = {name: value.to(DEVICE) for name, value in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    probabilities = torch.softmax(outputs.logits, dim=-1)
    confidence, class_id = torch.max(probabilities, dim=-1)
    label = model.config.id2label[class_id.item()]
    produce_type = str(label).strip()
    if not produce_type:
        raise RuntimeError("Produce classifier returned an empty label.")

    produce_confidence = round(float(confidence.item()) * 100, 2)
    logger.info(
        "Produce classifier result: %s | Confidence: %.2f%%",
        produce_type,
        produce_confidence,
    )
    return {
        "produce_type": produce_type,
        "produce_confidence": produce_confidence,
    }
