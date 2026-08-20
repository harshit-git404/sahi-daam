export type Screen = 
  | 'home'
  | 'scan'
  | 'quality_result'
  | 'price_breakdown'
  | 'bargain'
  | 'history';

export type FreshnessLevel = 'fresh' | 'slightly_aged' | 'overripe';

export interface BargainPhrase {
  hindi: string;
  english: string;
  phonetic: string;
}

export type PriceTrend = 'UP' | 'DOWN' | 'STABLE' | 'INSUFFICIENT_DATA';

export interface MarketContext {
  current_price: number;
  recent_average: number;
  change_pct: number;
  trend: PriceTrend;
  history_days: number;
  observation_count: number;
  confidence: 'High' | 'Medium' | 'Low';
}

export interface ProduceItem {
  id: string;
  name: string;
  hindiName?: string;
  image: string;
  matchScore: number;
  qualitySummary: string;
  freshness: FreshnessLevel;
  freshnessPercent: number; // 0 to 100
  wholesalePrice: number;
  markupMinPercent: number;
  markupMaxPercent: number;
  retailFairMin: number;
  retailFairMax: number;
  typicalVendorAsking: number;
  suggestedOfferPrice: number;
  decision?: 'GOOD_DEAL' | 'FAIR_PRICE' | 'SLIGHTLY_HIGH' | 'OVERPRICED' | 'UNUSUALLY_CHEAP';
  severity?: 'NONE' | 'SLIGHT' | 'MODERATE' | 'SIGNIFICANT';
  recommendation?: {
    action: string;
    headline: string;
    explanation: string;
  };
  startingOffer?: number;
  targetPrice?: number;
  maximumReasonablePrice?: number;
  potentialSaving?: number;
  belowFairAmount?: number;
  qualityContext?: {
    freshness_label: string | null;
    caution: string | null;
  };
  haggleVerdict?: 'Fair Price' | 'Overpriced' | 'Suspiciously Cheap';
  haggleReasoning?: string;
  hagglePhrases?: BargainPhrase[];
  unit: string;
  qualityAdjustment: number;
  qualityAdjustmentLabel: string;
  dataConfidence: 'High' | 'Medium' | 'Estimated';
  priceSource?: string;
  category: 'Vegetables' | 'Fruits' | 'Leafy' | 'Spices';
  bargainPhrases: {
    hindi: string;
    english: string;
    phonetic: string;
  }[];
  quickCommercePrice?: {
    source: string;
    price: number;
    unit: string;
  };
  alternatives?: {
    quickcommerce?: {
      source: string;
      price: number;
      unit: string;
    };
  };
  marketContext?: MarketContext;
}

export interface PurchaseRecord {
  id: string;
  produceId: string;
  produceName: string;
  paidPrice: number;
  fairPrice: number;
  savedAmount: number;
  date: string; // e.g. "Today", "Yesterday", "3 days ago"
  timestamp: number;
  iconType: 'tomato' | 'onion' | 'potato' | 'leaf' | 'general';
}

export interface MandiLocation {
  id: string;
  name: string;
  state: string;
  mandiName: string;
  active: boolean;
}

export type AppTheme = 'terracotta' | 'forest_green';
