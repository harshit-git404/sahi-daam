export type Screen = 
  | 'home'
  | 'scan'
  | 'quality_result'
  | 'price_breakdown'
  | 'bargain'
  | 'history';

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
  haggleVerdict?: 'Fair Price' | 'Overpriced' | 'Suspiciously Cheap';
  haggleReasoning?: string;
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
