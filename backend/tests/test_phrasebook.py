import sys
from types import ModuleType

import pytest

from pricing.phrasebook import (
    DECISION_STATES,
    generate_bargain_phrases,
    get_fallback_phrases,
)


REQUIRED_FIELDS = ("hindi", "tamil", "english", "phonetic")


def assert_multilingual_phrase(phrase: dict) -> None:
    for field in REQUIRED_FIELDS:
        assert field in phrase
        assert isinstance(phrase[field], str)
        assert phrase[field].strip()


@pytest.mark.parametrize("decision", DECISION_STATES)
def test_fallback_phrases_cover_all_decision_states(decision):
    phrases = get_fallback_phrases(decision, suggested_price=30, decision=decision)

    assert len(phrases) >= 1
    for phrase in phrases:
        assert_multilingual_phrase(phrase)


@pytest.mark.parametrize(
    ("legacy_verdict", "decision"),
    [
        ("Overpriced", "OVERPRICED"),
        ("Overpriced", "SLIGHTLY_HIGH"),
        ("Fair Price", "FAIR_PRICE"),
        ("Fair Price", "GOOD_DEAL"),
        ("Suspiciously Cheap", "UNUSUALLY_CHEAP"),
    ],
)
def test_generate_bargain_phrases_falls_back_without_gemini(monkeypatch, legacy_verdict, decision):
    monkeypatch.setenv("GEMINI_API_KEY", "")

    phrases, source = generate_bargain_phrases(
        produce_type="tomato",
        verdict=legacy_verdict,
        suggested_price=30,
        decision=decision,
    )

    assert source == "fallback"
    assert len(phrases) >= 1
    for phrase in phrases:
        assert_multilingual_phrase(phrase)


def test_generate_bargain_phrases_falls_back_when_gemini_payload_is_incomplete(monkeypatch):
    class FakeResponse:
        text = '[{"hindi": "भैया, कम कर दीजिए।", "english": "Please reduce it.", "phonetic": "Bhaiya, kam kar dijiye."}]'

    class FakeModels:
        @staticmethod
        def generate_content(model, contents):
            return FakeResponse()

    class FakeClient:
        def __init__(self, api_key):
            self.models = FakeModels()

    fake_genai = ModuleType("google.genai")
    fake_genai.Client = FakeClient
    fake_google = ModuleType("google")
    fake_google.genai = fake_genai

    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setitem(sys.modules, "google", fake_google)
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)

    phrases, source = generate_bargain_phrases(
        produce_type="tomato",
        verdict="Overpriced",
        suggested_price=30,
        decision="OVERPRICED",
    )

    assert source == "fallback"
    for phrase in phrases:
        assert_multilingual_phrase(phrase)


def test_generate_bargain_phrases_sends_selected_language_to_gemini(monkeypatch):
    captured_prompts = []

    class FakeResponse:
        text = """
        [
          {
            "hindi": "Hindi phrase",
            "tamil": "Tamil phrase",
            "english": "English phrase",
            "phonetic": "Hindi phonetic"
          }
        ]
        """

    class FakeModels:
        @staticmethod
        def generate_content(model, contents):
            captured_prompts.append(contents[0])
            return FakeResponse()

    class FakeClient:
        def __init__(self, api_key):
            self.models = FakeModels()

    fake_genai = ModuleType("google.genai")
    fake_genai.Client = FakeClient
    fake_google = ModuleType("google")
    fake_google.genai = fake_genai

    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setitem(sys.modules, "google", fake_google)
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)

    phrases, source = generate_bargain_phrases(
        produce_type="tomato",
        verdict="Overpriced",
        suggested_price=30,
        decision="OVERPRICED",
        language="ta",
    )

    assert source == "gemini"
    assert captured_prompts
    assert "selected negotiation language is Tamil" in captured_prompts[0]
    for phrase in phrases:
        assert_multilingual_phrase(phrase)
