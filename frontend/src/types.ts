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
  metric?: {
    name: string;
    unit: string;
    current_value: number | null;
    average_10_days: number | null;
    high_10_days: number | null;
    low_10_days: number | null;
    percentage_change: number | null;
    trend: string;
    history: { date: string; value: number }[];
    periods_available?: number;
  };
}

export interface RetailProduct {
  platform: string;
  commodity: string;
  product_name: string;
  variant: string;
  quantity: string;
  quantity_kg: number;
  price: number;
  mrp: number | null;
  price_per_kg: number;
  location?: string;
  location_note?: string;
  collected_at?: string;
}

export interface RetailResult {
  status: 'AVAILABLE' | 'UNAVAILABLE';
  commodity: string;
  location?: string;
  products: RetailProduct[];
  best_price_per_kg?: number;
  best_platform?: string;
  collected_at?: string;
  /** Cache age in hours — null if cannot be calculated */
  cache_age_hours?: number | null;
  /** 'cached_snapshot' | 'live' — always 'cached_snapshot' for now */
  data_source_type?: string;
  message?: string;
  source?: string;
}

export type FreshnessLevel = 'fresh' | 'slightly_aged' | 'overripe';

/** Market history block returned from /scan-produce */
export interface MarketData {
  status: 'AVAILABLE' | 'UNAVAILABLE';
  today_price: number | null;
  unit: string;
  date?: string;
  market_name?: string;
  district?: string;
  current_value: number | null;
  average_10_days: number | null;
  high_10_days: number | null;
  low_10_days: number | null;
  percentage_change: number | null;
  trend: 'UP' | 'DOWN' | 'STABLE' | 'UNAVAILABLE';
  history: { date: string; value: number }[];
  periods_available: number;
  error?: string;
}

export interface PricingData {
  fair_price_min: number;
  fair_price_max: number;
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
  unit: string;
  qualityAdjustment: number;
  qualityAdjustmentLabel: string;
  dataConfidence: 'High' | 'Medium' | 'Estimated' | 'Unavailable';
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
  retailComparison?: RetailResult;
  /** Full market history block from backend */
  market?: MarketData;
  /** Calculated fair price range from backend */
  pricing?: PricingData;
  /** Online retail reference bounds for haggle context */
  onlineReferenceMin?: number | null;
  onlineReferenceMax?: number | null;
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
  /** Display name of the mandi */
  mandiName: string;
  /** District extracted from the name (used for API calls) */
  district?: string;
  active: boolean;
}

export type AppTheme = 'terracotta' | 'forest_green';

export type PurchaseType = 'street_vendor' | 'supermarket_online';
