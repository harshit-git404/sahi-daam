export type Screen = 
  | 'home'
  | 'sector_selection'
  | 'component_selection'
  | 'sector_analysis'
  | 'scan'
  | 'quality_result'
  | 'purchase_type'
  | 'supermarket'
  | 'price_breakdown'
  | 'bargain'
  | 'history';

export interface SectorAnalysisResult {
  summary: string;
  records: Record<string, unknown>[];
  status?: 'API_AVAILABLE' | 'API_UNAVAILABLE' | 'NO_SUITABLE_DATA_SOURCE';
}

export type FreshnessLevel = 'fresh' | 'slightly_aged' | 'overripe';

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
  unit: string;
  qualityAdjustment: number;
  qualityAdjustmentLabel: string;
  dataConfidence: 'High' | 'Medium' | 'Estimated';
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
  marketStatus?: 'AVAILABLE' | 'UNAVAILABLE';
  analysisProvider?: 'gemini' | 'local_fallback';
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

export type PurchaseType = 'street_vendor' | 'supermarket_online';
