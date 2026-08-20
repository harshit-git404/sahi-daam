import re
from typing import List

def classify_variants(name: str, variant_keywords: List[str]) -> List[str]:
    name_lower = name.lower()
    variants = []
    for kw in variant_keywords:
        if kw in name_lower:
            variants.append(kw)
    if not variants:
        variants.append("regular")
    return variants

COMMODITY_RULES = {
    "tomato": {
        "search_term": "Tomato",
        "keywords": ["tomato", "thakkali"],
        "exclusions": ["ketchup", "sauce", "puree", "pickle", "sun dried", "dried", "juice", "pasta", "pizza", "chopped", "peeled", "oil", "canned", "tin", "preserve"],
        "variant_keywords": ["cherry", "organic", "hybrid", "desi"]
    },
    "potato": {
        "search_term": "Potato",
        "keywords": ["potato", "aloo"],
        "exclusions": ["chips", "wafers", "crisps", "snack", "snacks", "frozen", "fries", "french fries", "hash brown", "hashbrown", "mashed", "flakes", "powder", "starch", "flour", "mix", "instant", "namkeen", "cracker", "crackers", "papad", "fry"],
        "variant_keywords": ["baby", "organic", "red"]
    },
    "onion": {
        "search_term": "Onion",
        "keywords": ["onion", "onions", "pyaz", "pyaaz"],
        "exclusions": ["powder", "flakes", "fried", "paste", "soup", "seasoning", "chutney", "pickle", "rings", "frozen", "crisps", "chips", "snack", "sauce", "oil"],
        "variant_keywords": ["red", "white", "pearl", "baby", "organic", "spring"]
    },
    "carrot": {
        "search_term": "Carrot",
        "keywords": ["carrot", "carrots", "gajar"],
        "exclusions": ["juice", "cake", "halwa", "powder", "pickle", "soup", "frozen", "dried", "puree", "jam", "spread", "snack"],
        "variant_keywords": ["baby", "red", "organic"]
    },
    "cucumber": {
        "search_term": "Cucumber",
        "keywords": ["cucumber", "cucumbers", "kheera"],
        "exclusions": ["pickle", "pickled", "juice", "dressing", "sauce", "powder", "frozen", "dried", "snack"],
        "variant_keywords": ["english", "mini", "organic"]
    },
    "brinjal": {
        "search_term": "Brinjal",
        "keywords": ["brinjal", "eggplant", "baingan", "aubergine"],
        "exclusions": ["pickle", "chips", "crisps", "powder", "paste", "curry", "frozen", "dried", "snack", "ready to eat"],
        "variant_keywords": ["green", "purple", "long", "round", "organic", "striped"]
    },
    "cauliflower": {
        "search_term": "Cauliflower",
        "keywords": ["cauliflower", "gobi", "gobhi"],
        "exclusions": ["rice", "pizza", "soup", "powder", "frozen", "chips", "crisps", "snack", "snacks", "ready to eat", "mix", "pickled"],
        "variant_keywords": ["organic", "florets"]
    },
    "cabbage": {
        "search_term": "Cabbage",
        "keywords": ["cabbage", "patta gobi", "patta gobhi"],
        "exclusions": ["soup", "juice", "powder", "kimchi", "pickle", "pickled", "fermented", "frozen", "chips", "snack", "sauce"],
        "variant_keywords": ["green", "red", "napa", "organic"]
    },
    "banana": {
        "search_term": "Banana",
        "keywords": ["banana", "bananas", "kela"],
        "exclusions": ["chips", "wafers", "shake", "powder", "bread", "cake", "puree", "juice", "flavour", "flavored", "snack", "cookies", "biscuit", "ice cream", "leaf", "blossom", "stem"],
        "variant_keywords": ["robusta", "yelakki", "nendran", "raw", "organic", "red"]
    },
    "papaya": {
        "search_term": "Papaya",
        "keywords": ["papaya", "papita"],
        "exclusions": ["juice", "powder", "jam", "candy", "dried", "extract", "capsule", "tablet", "supplement", "snack", "shake", "flavour", "face", "wash", "soap", "cream", "lotion"],
        "variant_keywords": ["raw", "organic"]
    }
}

def normalize_quantity(quantity_str: str) -> float:
    """
    Parses a string like '500 g' or '1 kg' and returns the kg value.
    Returns None if parsing fails.
    """
    if not quantity_str:
        return None
        
    qs = quantity_str.lower().strip()
    match = re.search(r'([0-9]*\.?[0-9]+)', qs)
    if not match:
        return None
        
    val = float(match.group(1))
    
    if "kg" in qs or "kgs" in qs:
        return val
    elif "g" in qs or "gm" in qs or "grams" in qs:
        return val / 1000.0
    
    return None
