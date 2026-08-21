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
