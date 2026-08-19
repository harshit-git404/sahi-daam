import { ProduceItem } from '../types';

export const PRODUCE_DATABASE: ProduceItem[] = [
  {
    id: 'tomato',
    name: 'Tomato',
    hindiName: 'Tamatar (टमाटर)',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDtZtYyEV22IUcPy_tOOxPzAFZIID-VHG4DWQq8_xEcvCdXMJ4BhfwCza_bAnmmc2_vrqDvtXmLOoO3ODWl1SeBUhYeCxkWBCB5MaXfin7GyKt5V9B1Vflq9456Ki2dQuTKsNaYRUKJALrSvJfBAXhlb6pVeFkFceiuX8s1rqnOOxWVclOBgyTzgbjczDeOb0jdIHwF-Py8-KsE1aeu8BiEj4InVqETFUxCZ8UGYBHCTFml9G8fBI5n-A',
    matchScore: 98,
    qualitySummary: 'Slight softness detected — good for immediate use.',
    freshness: 'fresh',
    freshnessPercent: 33, // corresponds to 1/3 progress bar as in mockup
    wholesalePrice: 22,
    markupMinPercent: 30,
    markupMaxPercent: 45,
    retailFairMin: 28,
    retailFairMax: 34,
    typicalVendorAsking: 45,
    suggestedOfferPrice: 32,
    unit: 'kg',
    qualityAdjustment: -1.5,
    qualityAdjustmentLabel: 'slight softness',
    dataConfidence: 'Medium',
    category: 'Vegetables',
    bargainPhrases: [
      {
        hindi: 'भैया, मंडी में ₹22 चल रहा है, ₹32 में दे दो!',
        english: 'Brother, wholesale rate is ₹22, give it for ₹32!',
        phonetic: 'Bhaiya, mandi mein ₹22 chal raha hai, ₹32 mein de do!'
      },
      {
        hindi: 'टमाटर थोड़े नरम हैं, ₹30 लगाओगे तो 2 किलो ले लूँगा।',
        english: 'Tomatoes are a bit soft, if you do ₹30 I will buy 2 kg.',
        phonetic: 'Tamatar thode naram hain, ₹30 lagaoge toh 2 kilo le loonga.'
      },
      {
        hindi: 'पिछली दुकान पर ₹30 दे रहे हैं, सही दाम लगाइए।',
        english: 'Last stall was offering at ₹30, please give a fair price.',
        phonetic: 'Pichhli dukaan par ₹30 de rahe hain, sahi daam lagaiye.'
      }
    ]
  },
  {
    id: 'banana',
    name: 'Banana',
    hindiName: 'Kela (केला)',
    image: 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?auto=format&fit=crop&w=400&q=80',
    matchScore: 95,
    qualitySummary: 'Yellow skin, perfect for consumption.',
    freshness: 'fresh',
    freshnessPercent: 88,
    wholesalePrice: 40,
    markupMinPercent: 15,
    markupMaxPercent: 30,
    retailFairMin: 50,
    retailFairMax: 60,
    typicalVendorAsking: 80,
    suggestedOfferPrice: 55,
    unit: 'dozen',
    qualityAdjustment: 0,
    qualityAdjustmentLabel: 'clean skin',
    dataConfidence: 'High',
    category: 'Fruits',
    bargainPhrases: [
      {
        hindi: 'भैया, केले थोड़े ज्यादा पके लग रहे हैं, ₹50 दर्जन लगा लो।',
        english: 'Brother, bananas look a bit overripe, give for ₹50 a dozen.',
        phonetic: 'Bhaiya, kele thode zyada pake lag rahe hain, ₹50 darjan laga lo.'
      }
    ]
  },
  {
    id: 'onion',
    name: 'Onion',
    hindiName: 'Pyaaz (प्याज़)',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuB1yDJOOmQIRtXaeHyjayaOWgJXbeKH6gG3eP1gPaCJ1Wb3IC0teN8gEaDYknpUOweoYcIN43rY2-0bvppCjjTGgNWqXMK2crUUUoQCQpEjU35BLAgIctb3LQTH7i9xw1mB8Gvzoj5ul4MQJ8reU0dPjgJkaC95tDAdG-Haiuu9hkitSHditEiHcotFUFkXf-rizoUuDF8-hW0jecjTffMyHlo2vUQuw3ndAm8LQOzvMyLoQ33wn1VJuw',
    matchScore: 96,
    qualitySummary: 'Firm outer skin, dry layers — excellent shelf life.',
    freshness: 'fresh',
    freshnessPercent: 25,
    wholesalePrice: 16,
    markupMinPercent: 25,
    markupMaxPercent: 40,
    retailFairMin: 22,
    retailFairMax: 26,
    typicalVendorAsking: 35,
    suggestedOfferPrice: 24,
    unit: 'kg',
    qualityAdjustment: 0,
    qualityAdjustmentLabel: 'dry & firm',
    dataConfidence: 'High',
    category: 'Vegetables',
    bargainPhrases: [
      {
        hindi: 'भैया, ₹20 में दे दो, 3 किलो प्याज लूंगा।',
        english: 'Give it for ₹20, I will take 3 kg onions.',
        phonetic: 'Bhaiya, ₹20 mein de do, 3 kilo pyaaz loonga.'
      },
      {
        hindi: 'नाशिक प्याज का थोक भाव गिरा है, ₹24 सही दाम है।',
        english: 'Nashik onion wholesale rate dropped, ₹24 is the fair price.',
        phonetic: 'Nashik pyaaz ka thok bhav gira hai, ₹24 sahi daam hai.'
      }
    ]
  },
  {
    id: 'potato',
    name: 'Potato',
    hindiName: 'Aloo (आलू)',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuB3E4JhUwpdy8yTWQr6m3TvDWjkR8bNs1yjB89MWQNNgQ4ZpVxbbRixlnbKPwK_GZ3FOLrYwBDC96thespP8Z7-gqYJBKxQH-PKYSrTOSaU2j95qTMaRIlZqdCzRNWIVGV86hY-BALSYWngy0RSZaK-Fx5UkqGpYV6X9l0I5RBFMYhFiGLSjwE0YYKi1jg010Uzl9nwFeGvlbkIx5zkfSmHcq0eH3PbDgJL5EwSJdRDAACavh4VDpmOew',
    matchScore: 99,
    qualitySummary: 'No sprouts, clean skin, solid texture — premium grade.',
    freshness: 'fresh',
    freshnessPercent: 15,
    wholesalePrice: 18,
    markupMinPercent: 20,
    markupMaxPercent: 35,
    retailFairMin: 24,
    retailFairMax: 28,
    typicalVendorAsking: 35,
    suggestedOfferPrice: 26,
    unit: 'kg',
    qualityAdjustment: 0,
    qualityAdjustmentLabel: 'no sprouts',
    dataConfidence: 'High',
    category: 'Vegetables',
    bargainPhrases: [
      {
        hindi: 'आलू ₹25 लगा दो भैया, 5 किलो का थैला बना दो।',
        english: 'Make it ₹25 for potato brother, pack a 5 kg bag.',
        phonetic: 'Aloo ₹25 laga do bhaiya, 5 kilo ka thaila bana do.'
      }
    ]
  },
  {
    id: 'coriander',
    name: 'Coriander',
    hindiName: 'Dhaniya (धनिया)',
    image: 'https://images.unsplash.com/photo-1608686207856-001b95cf60ca?auto=format&fit=crop&w=400&q=80',
    matchScore: 94,
    qualitySummary: 'Crisp green leaves with aromatic stems.',
    freshness: 'fresh',
    freshnessPercent: 20,
    wholesalePrice: 8,
    markupMinPercent: 30,
    markupMaxPercent: 50,
    retailFairMin: 10,
    retailFairMax: 15,
    typicalVendorAsking: 20,
    suggestedOfferPrice: 12,
    unit: 'bunch',
    qualityAdjustment: 0,
    qualityAdjustmentLabel: 'aromatic & fresh',
    dataConfidence: 'High',
    category: 'Leafy',
    bargainPhrases: [
      {
        hindi: 'भैया, सब्जी के साथ थोड़ा धनिया-मिर्ची मुफ्त दे दो ना!',
        english: 'Brother, please throw in some free coriander & chili with the veggies!',
        phonetic: 'Bhaiya, sabzi ke saath thoda dhaniya-mirchi muft de do na!'
      }
    ]
  },
  {
    id: 'ginger',
    name: 'Ginger',
    hindiName: 'Adrak (अदरक)',
    image: 'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?auto=format&fit=crop&w=400&q=80',
    matchScore: 97,
    qualitySummary: 'Juicy fibrous root, clean skin, no moisture mold.',
    freshness: 'fresh',
    freshnessPercent: 30,
    wholesalePrice: 80,
    markupMinPercent: 25,
    markupMaxPercent: 40,
    retailFairMin: 110,
    retailFairMax: 130,
    typicalVendorAsking: 160,
    suggestedOfferPrice: 120,
    unit: 'kg',
    qualityAdjustment: 0,
    qualityAdjustmentLabel: 'firm root',
    dataConfidence: 'Medium',
    category: 'Spices',
    bargainPhrases: [
      {
        hindi: 'अदरक ₹120 किलो लगाइए, 250 ग्राम लेना है।',
        english: 'Price ginger at ₹120/kg, I want 250 grams.',
        phonetic: 'Adrak ₹120 kilo lagaiye, 250 gram lena hai.'
      }
    ]
  }
];

export const INITIAL_PURCHASE_HISTORY = [
  {
    id: 'rec-1',
    produceId: 'tomato',
    produceName: 'Tomato',
    paidPrice: 32,
    fairPrice: 30,
    savedAmount: 2,
    date: 'Today',
    timestamp: Date.now() - 3600000 * 2,
    iconType: 'tomato' as const
  },
  {
    id: 'rec-2',
    produceId: 'onion',
    produceName: 'Onion',
    paidPrice: 20,
    fairPrice: 25,
    savedAmount: 5,
    date: 'Yesterday',
    timestamp: Date.now() - 86400000,
    iconType: 'onion' as const
  }
];
