import pytest
from pydantic import ValidationError

from routers.haggle import HaggleRequest


def make_request(**overrides):
    payload = {
        "produce_type": "tomato",
        "asking_price": 45,
        "fair_price_min": 28,
        "fair_price_max": 34,
    }
    payload.update(overrides)
    return HaggleRequest(**payload)


def test_haggle_request_defaults_to_hindi_language():
    request = make_request()

    assert request.language == "hi"


@pytest.mark.parametrize("language", ["hi", "ta", "en"])
def test_haggle_request_accepts_supported_languages(language):
    request = make_request(language=language)

    assert request.language == language


def test_haggle_request_rejects_unsupported_language():
    with pytest.raises(ValidationError):
        make_request(language="fr")
