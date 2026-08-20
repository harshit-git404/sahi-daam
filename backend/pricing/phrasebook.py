import os
import json
from typing import TypedDict, List
from dotenv import load_dotenv

load_dotenv()

class Phrase(TypedDict):
    hindi: str
    english: str
    phonetic: str

def get_fallback_phrases(verdict: str) -> List[Phrase]:
    if verdict == "Overpriced":
        return [
            {"hindi": "भैया, यह तो बहुत महंगा है। थोड़ा कम कीजिए।", "english": "Brother, this is too expensive. Please reduce the price a bit.", "phonetic": "Bhaiya, yeh toh bahut mehanga hai. Thoda kam kijiye."},
            {"hindi": "बाजार में तो यह सस्ता मिल रहा है। सही दाम लगाइए।", "english": "It's available cheaper in the market. Give a fair price.", "phonetic": "Bazaar mein toh yeh sasta mil raha hai. Sahi daam lagaiye."}
        ]
    elif verdict == "Suspiciously Cheap":
        return [
            {"hindi": "दाम तो कम है, पर क्वालिटी ठीक है ना?", "english": "The price is low, but is the quality okay?", "phonetic": "Daam toh kam hai, par quality theek hai na?"},
            {"hindi": "क्या इसमें कोई खराबी है?", "english": "Is there any defect in this?", "phonetic": "Kya isme koi kharabi hai?"}
        ]
    else: # Fair Price
        return [
            {"hindi": "दाम सही है, दे दीजिए।", "english": "The price is fair, please pack it.", "phonetic": "Daam sahi hai, de dijiye."},
            {"hindi": "ठीक है, एक किलो तोल दीजिए।", "english": "Alright, weigh one kilo.", "phonetic": "Theek hai, ek kilo tol dijiye."}
        ]

def generate_bargain_phrases(produce_type: str, verdict: str, suggested_price: float) -> tuple[List[Phrase], str]:
    """
    Generates 2-3 bargain phrases dynamically using Gemini based on context.
    Returns (phrases, source) where source is 'gemini' or 'fallback'.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return (get_fallback_phrases(verdict), "fallback")

    try:
        from google import genai
        
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        Act as an expert Indian haggler in a local vegetable market. 
        The user is trying to buy {produce_type}.
        The market analysis verdict is "{verdict}", and the target suggested price is ₹{suggested_price}.
        Generate exactly 2 polite but firm bargaining phrases the user can say to the vendor in Hindi.
        
        Return ONLY a raw JSON array of objects with the following keys (no markdown blocks):
        - "hindi": The phrase in Devanagari Hindi.
        - "english": The English translation.
        - "phonetic": The Hinglish (Latin alphabet) pronunciation of the Hindi phrase.
        
        Keep them short, conversational, and culturally accurate for an Indian sabzi mandi.
        """
        
        fallback_models = ['gemini-3.7-flash', 'gemini-3.5-flash', 'gemini-2.5-flash']
        response = None
        last_error = None
        
        for model_name in fallback_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[prompt]
                )
                break
            except Exception as e:
                last_error = e
                continue
                
        if not response:
            raise last_error
        
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
            
        data = json.loads(text)
        return (data, "gemini")

    except Exception as e:
        print(f"Gemini API Error generating phrases: {e}")
        return (get_fallback_phrases(verdict), "fallback")
