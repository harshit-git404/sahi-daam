export type Screen = 
  | 'home'
  | 'scan'
  | 'quality_result'
  | 'price_breakdown'
  | 'bargain'
  | 'history'
  | 'sector_selection'
  | 'component_selection'
  | 'purchase_type'
  | 'supermarket'
  | 'sector_analysis';

export type FreshnessLevel = 'fresh' | 'slightly_aged' | 'overripe';
export type NegotiationLanguage = 'hi' | 'ta' | 'en';
export type HaggleStatus = 'idle' | 'listening' | 'processing' | 'ready' | 'timeout' | 'error';

export interface RetailProduct {
  platform: string;
  product_name: string;
  price_per_kg: number;
  quantity: string;
  variant: string;
  mrp: number;
  location_note: string;
}

export interface RetailComparison {
  status: string; // 'AVAILABLE'
  products: RetailProduct[];
  best_platform: string;
  best_price_per_kg: number;
  collected_at: string;
  source: string;
  cache_age_hours?: number;
  data_source_type?: string;
}

export interface BargainPhrase {
  hindi: string;
  tamil?: string;
  english: string;
  phonetic: string;
}

export interface NegotiationState {
  status: HaggleStatus;
  language: NegotiationLanguage;
  vendorAskingPrice: number;
  latestVendorCounterOffer: number | null;
  userCurrentOffer: number | null;
  recommendedNextOffer: number | null;
  error: string | null;
  lastUpdatedAt: number | null;
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
  bargainPhrases: BargainPhrase[];
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
  retailComparison?: RetailComparison;
  marketContext?: MarketContext;
}

export interface PurchaseRecord {
  id: string;
  produceId: string;
  produceName: string;
  vendorAskingPrice: number;
  paidPrice: number;
  fairPrice: number;
  savedAmount: number;
  unit: string;
  timestamp: number;
  decision?: ProduceItem['decision'];
  outcome?: 'BOUGHT' | 'SKIPPED';
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

export interface FuelHistoryItem {
  date: string;
  display_date: string;
  price: number;
}

export interface FuelDistrictStats {
  current_price: number;
  average_10_days: number;
  high_10_days: number;
  low_10_days: number;
  percentage_change: number;
  trend: 'UP' | 'DOWN' | 'STABLE';
  history: FuelHistoryItem[];
  periods_available: number;
  is_cheapest?: boolean;
  diff_from_cheapest?: number;
}

export interface FuelTypeAnalytics {
  fuel_type: 'petrol' | 'diesel';
  fuel_name: string;
  unit: string;
  cheapest_district: string;
  cheapest_price: number;
  cheapest_avg_district: string;
  max_savings_per_litre: number;
  districts: Record<string, FuelDistrictStats>;
}

export interface FuelAnalysisData {
  status: string;
  petrol: FuelTypeAnalytics;
  diesel: FuelTypeAnalytics;
  districts: string[];
  records: Record<string, unknown>[];
  total_records: number;
  source: string;
  summary: string;
}

export interface WastewaterHistoryItem {
  date: string;
  display_date: string;
  volume: number;
}

export interface WastewaterDistrictStats {
  current_volume: number;
  average_10_days: number;
  high_10_days: number;
  low_10_days: number;
  percentage_change: number;
  trend: 'UP' | 'DOWN' | 'STABLE';
  history: WastewaterHistoryItem[];
  periods_available: number;
  is_highest?: boolean;
  diff_from_highest?: number;
}

export interface WastewaterMetricAnalytics {
  metric_type: 'effluent' | 'treated';
  metric_name: string;
  unit: string;
  highest_district: string;
  highest_volume: number;
  highest_avg_district: string;
  lowest_volume: number;
  total_regional_volume: number;
  districts: Record<string, WastewaterDistrictStats>;
}

export interface WastewaterAnalysisData {
  status: string;
  effluent: WastewaterMetricAnalytics;
  treated: WastewaterMetricAnalytics;
  districts: string[];
  records: Record<string, unknown>[];
  total_records: number;
  source: string;
  summary: string;
}

export interface GenericHistoryItem {
  date: string;
  display_date: string;
  value: number;
}

export interface GenericDistrictStats {
  current_value: number;
  average_10_days: number;
  high_10_days: number;
  low_10_days: number;
  percentage_change: number;
  trend: 'UP' | 'DOWN' | 'STABLE';
  history: GenericHistoryItem[];
  periods_available: number;
  is_highest?: boolean;
  diff_from_highest?: number;
}

export interface MetricAnalytics {
  metric_type: string;
  metric_name: string;
  unit: string;
  highest_district: string;
  highest_value: number;
  highest_avg_district: string;
  lowest_volume: number;
  total_regional_volume: number;
  districts: Record<string, GenericDistrictStats>;
}

export interface SectorAnalyticsPayload {
  status: string;
  primary: MetricAnalytics;
  secondary: MetricAnalytics;
  primary_label: string;
  secondary_label: string;
  districts: string[];
  records: Record<string, unknown>[];
  total_records: number;
  source: string;
  summary: string;
}

export interface SectorAnalysisResult {
  summary: string;
  records: Record<string, unknown>[];
  status?: 'API_AVAILABLE' | 'API_UNAVAILABLE' | 'NO_SUITABLE_DATA_SOURCE';
  fuel_data?: FuelAnalysisData;
  wastewater_data?: WastewaterAnalysisData;
  analytics_data?: SectorAnalyticsPayload;
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
