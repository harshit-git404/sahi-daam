import json
import os
from typing import Any, List, Optional, TypedDict

from dotenv import load_dotenv

load_dotenv()


class Phrase(TypedDict):
    hindi: str
    tamil: str
    english: str
    phonetic: str


DECISION_STATES = (
    "OVERPRICED",
    "SLIGHTLY_HIGH",
    "FAIR_PRICE",
    "GOOD_DEAL",
    "UNUSUALLY_CHEAP",
)

LEGACY_VERDICT_TO_DECISION = {
    "Overpriced": "OVERPRICED",
    "Fair Price": "FAIR_PRICE",
    "Suspiciously Cheap": "UNUSUALLY_CHEAP",
}

REQUIRED_PHRASE_FIELDS = ("hindi", "tamil", "english", "phonetic")


def _normalise_decision(verdict_or_decision: str, decision: Optional[str] = None) -> str:
    if decision in DECISION_STATES:
        return decision
    if verdict_or_decision in DECISION_STATES:
        return verdict_or_decision
    return LEGACY_VERDICT_TO_DECISION.get(verdict_or_decision, "FAIR_PRICE")


def _format_amount(value: Optional[float]) -> Optional[str]:
    if value is None:
        return None

    rounded = round(value)
    if abs(value - rounded) < 0.01:
        return str(int(rounded))

    return f"{value:.1f}".rstrip("0").rstrip(".")


def _offer_phrase(amount: Optional[str], language: str) -> str:
    if language == "hindi":
        return f"{amount} रुपये" if amount else "सही दाम"
    if language == "tamil":
        return f"{amount} ரூபாய்" if amount else "சரியான விலை"
    return f"₹{amount}" if amount else "a fair price"


def get_fallback_phrases(
    verdict_or_decision: str,
    suggested_price: Optional[float] = None,
    decision: Optional[str] = None,
) -> List[Phrase]:
    resolved_decision = _normalise_decision(verdict_or_decision, decision)
    amount = _format_amount(suggested_price)
    hindi_offer = _offer_phrase(amount, "hindi")
    tamil_offer = _offer_phrase(amount, "tamil")
    english_offer = _offer_phrase(amount, "english")
    phonetic_offer = f"{amount} rupaye" if amount else "sahi daam"

    fallback_phrases: dict[str, List[Phrase]] = {
        "OVERPRICED": [
            {
                "hindi": f"भैया, {hindi_offer} में दे दीजिए।",
                "tamil": f"அண்ணா, {tamil_offer}க்கு கொடுங்கள்.",
                "english": f"Could you make it {english_offer}?",
                "phonetic": f"Bhaiya, {phonetic_offer} mein de dijiye.",
            },
            {
                "hindi": "बाजार में इससे कम मिल रहा है, थोड़ा कम कीजिए।",
                "tamil": "மார்க்கெட்டில் இதைவிட குறைவாக கிடைக்கிறது, கொஞ்சம் குறையுங்கள்.",
                "english": "It is cheaper in the market. Please reduce it a bit.",
                "phonetic": "Bazaar mein isse kam mil raha hai, thoda kam kijiye.",
            },
        ],
        "SLIGHTLY_HIGH": [
            {
                "hindi": f"भैया, थोड़ा कम कर दीजिए, {hindi_offer} ठीक रहेगा।",
                "tamil": f"அண்ணா, கொஞ்சம் குறையுங்கள், {tamil_offer} சரியாக இருக்கும்.",
                "english": f"Could you reduce it a little? {english_offer} would be fair.",
                "phonetic": f"Bhaiya, thoda kam kar dijiye, {phonetic_offer} theek rahega.",
            },
            {
                "hindi": "दाम बस थोड़ा ज्यादा है, सही रेट लगा दीजिए।",
                "tamil": "விலை கொஞ்சம் அதிகமாக இருக்கிறது, சரியான விலை சொல்லுங்கள்.",
                "english": "The price is just a little high. Please quote the fair rate.",
                "phonetic": "Daam bas thoda zyada hai, sahi rate laga dijiye.",
            },
        ],
        "FAIR_PRICE": [
            {
                "hindi": "ठीक है भैया, यही सही दाम है।",
                "tamil": "சரி அண்ணா, இதுதான் சரியான விலை.",
                "english": "Alright, that sounds fair.",
                "phonetic": "Theek hai bhaiya, yahi sahi daam hai.",
            },
            {
                "hindi": "दाम ठीक है, दे दीजिए।",
                "tamil": "விலை சரியாக இருக்கிறது, கொடுங்கள்.",
                "english": "The price is fair. Please give it.",
                "phonetic": "Daam theek hai, de dijiye.",
            },
        ],
        "GOOD_DEAL": [
            {
                "hindi": "ठीक है, मैं ले लेता हूँ।",
                "tamil": "சரி, நான் எடுத்துக்கொள்கிறேன்.",
                "english": "Alright, I'll take it.",
                "phonetic": "Theek hai, main le leta hoon.",
            },
            {
                "hindi": "अच्छा दाम है, पैक कर दीजिए।",
                "tamil": "நல்ல விலை, பேக் செய்து கொடுங்கள்.",
                "english": "That is a good price. Please pack it.",
                "phonetic": "Achha daam hai, pack kar dijiye.",
            },
        ],
        "UNUSUALLY_CHEAP": [
            {
                "hindi": "भैया, माल ठीक है ना?",
                "tamil": "அண்ணா, காய்கறி நல்லா இருக்கா?",
                "english": "Is the produce in good condition?",
                "phonetic": "Bhaiya, maal theek hai na?",
            },
            {
                "hindi": "इतना कम दाम क्यों है, क्वालिटी ठीक है?",
                "tamil": "இவ்வளவு குறைந்த விலை ஏன், தரம் சரியாக இருக்கிறதா?",
                "english": "Why is it priced so low? Is the quality okay?",
                "phonetic": "Itna kam daam kyon hai, quality theek hai?",
            },
        ],
    }

    return fallback_phrases[resolved_decision]


def _strip_json_fences(text: str) -> str:
    clean_text = text.strip()
    if clean_text.startswith("```json"):
        return clean_text[7:-3].strip()
    if clean_text.startswith("```"):
        return clean_text[3:-3].strip()
    return clean_text


def _validate_phrases(data: Any) -> List[Phrase]:
    if not isinstance(data, list):
        raise ValueError("Gemini phrase response must be a JSON array.")

    phrases: List[Phrase] = []

    for item in data[:3]:
        if not isinstance(item, dict):
            raise ValueError("Each Gemini phrase must be an object.")

        phrase: Phrase = {
            "hindi": "",
            "tamil": "",
            "english": "",
            "phonetic": "",
        }

        for field in REQUIRED_PHRASE_FIELDS:
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Gemini phrase is missing '{field}'.")
            phrase[field] = value.strip()

        phrases.append(phrase)

    if not phrases:
        raise ValueError("Gemini phrase response did not contain any phrases.")

    return phrases


def generate_bargain_phrases(
    produce_type: str,
    verdict: str,
    suggested_price: float,
    decision: Optional[str] = None,
) -> tuple[List[Phrase], str]:
    """
    Generates 2-3 bargain phrases dynamically using Gemini based on context.
    Returns (phrases, source) where source is 'gemini' or 'fallback'.
    """
    resolved_decision = _normalise_decision(verdict, decision)
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key or api_key == "your_gemini_api_key_here":
        return (get_fallback_phrases(verdict, suggested_price, resolved_decision), "fallback")

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        prompt = f"""
        Act as an expert Indian haggler in a local vegetable market.
        The user is trying to buy {produce_type}.
        The market analysis verdict is "{verdict}".
        The machine decision state is "{resolved_decision}".
        The target suggested price is ₹{suggested_price}.

        Generate exactly 2 short, polite, practical phrases the user can say to the vendor.
        The phrase intent must match the decision state:
        - OVERPRICED: politely negotiate down toward the suggested price.
        - SLIGHTLY_HIGH: ask for a small reduction without sounding aggressive.
        - FAIR_PRICE: accept that the price is fair.
        - GOOD_DEAL: accept the deal naturally.
        - UNUSUALLY_CHEAP: ask the vendor to confirm freshness or quality.

        Return ONLY a raw JSON array of objects with these exact keys:
        - "hindi": Native-script Hindi in Devanagari.
        - "tamil": Native-script Tamil.
        - "english": Natural English meaning, not word-for-word translation.
        - "phonetic": Hinglish pronunciation for the Hindi phrase only.

        Do not put Tamil transliteration in "phonetic".
        Keep every phrase conversational and suitable for an Indian sabzi mandi.
        """

        fallback_models = ["gemini-3.7-flash", "gemini-3.5-flash", "gemini-2.5-flash"]
        response = None
        last_error = None

        for model_name in fallback_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[prompt],
                )
                break
            except Exception as e:
                last_error = e
                continue

        if not response:
            raise last_error

        text = _strip_json_fences(response.text or "")
        data = json.loads(text)
        return (_validate_phrases(data), "gemini")

    except Exception as e:
        print(f"Gemini API Error generating phrases: {e}")
        return (get_fallback_phrases(verdict, suggested_price, resolved_decision), "fallback")
