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
  | 'history'
  | 'ledger_audit'
  | 'experiment_lab';

export interface ScenarioSummaryDTO {
  scenario_id: string;
  scenario_name: string;
  category: string;
  description: string;
  commodity_id: string;
  wholesale_price?: number | null;
  transport_cost?: number | null;
  transport_status: string;
  markup_range: string;
  quality_adjustment: number;
  raw_observations_count: number;
  is_mock: boolean;
}

export interface CalculationStepDTO {
  step_number: number;
  title: string;
  formula: string;
  inputs: Record<string, any>;
  substitutions: string;
  result_label: string;
  result_value: string;
  unit: string;
  status: string;
  explanation: string;
}

export interface ExpectedBehaviorCheckDTO {
  check_name: string;
  expected: string;
  actual: string;
  passed: boolean;
  explanation: string;
}

export interface ExperimentRunResult {
  schema_version: string;
  experiment: {
    run_id: string;
    scenario_id: string;
    scenario_name: string;
    category: string;
    description: string;
    timestamp_utc: string;
    status: string;
    is_mock: boolean;
    deterministic: boolean;
  };
  configuration: {
    fixture_version: string;
    algorithm_version: string;
    policy: Record<string, any>;
    reference_clock_utc: string;
  };
  inputs: {
    commodity_id: string;
    wholesale_price_per_kg?: number | null;
    transport_cost_per_kg?: number | null;
    transport_status: string;
    transport_method?: string | null;
    quality_adjustment: number;
    quality_adjustment_meaning: string;
    markup_min_pct: number;
    markup_max_pct: number;
    total_community_observations_count: number;
    community_observations: Array<{
      price: number;
      unit: string;
      is_duplicate: boolean;
      observed_at?: string | null;
    }>;
  };
  eligible_community_observations: {
    total_found: number;
    eligible_count: number;
    excluded_duplicates_count: number;
    excluded_stale_count: number;
    excluded_non_weight_unit_count: number;
    excluded_invalid_count: number;
    eligible_prices: number[];
    community_median?: number | null;
    community_mean?: number | null;
    community_min?: number | null;
    community_max?: number | null;
  };
  calculation_steps: CalculationStepDTO[];
  actual_output: {
    commodity_id: string;
    locality_id?: string | null;
    calculation_status: string;
    wholesale_price_per_kg?: number | null;
    transport_cost_per_kg?: number | null;
    transport_status: string;
    transport_method?: string | null;
    cost_basis_per_kg?: number | null;
    is_provisional_wholesale_only: boolean;
    markup_min_pct: number;
    markup_max_pct: number;
    quality_adjustment: number;
    quality_adjustment_meaning: string;
    baseline_range?: { min: number; max: number; mid: number; unit: string } | null;
    community_sample_size: number;
    community_estimate?: number | null;
    reconciliation_weight_alpha: number;
    is_sample_sufficient: boolean;
    reconciled_range?: { min: number; max: number; mid: number; unit: string } | null;
    suggested_price?: number | null;
    warnings: string[];
    notes: string[];
  };
  sub_runs?: Array<{
    sub_id: string;
    label: string;
    quality_adjustment: number;
    meaning: string;
    cost_basis_per_kg?: number | null;
    baseline_min?: number | null;
    baseline_max?: number | null;
    difference_from_fresh: number;
  }>;
  expected_behavior_checks: ExpectedBehaviorCheckDTO[];
  warnings: string[];
  notes: string[];
  missing_inputs: string[];
  persistence: {
    saved: boolean;
    relative_path?: string | null;
    file_size_bytes: number;
    sha256_hash?: string | null;
  };
  integrity: {
    normal_ledger_record_id?: string | null;
    normal_ledger_sequence?: number | null;
    normal_ledger_hash?: string | null;
    notes: string;
  };
}

export interface ManifestRunEntry {
  run_id: string;
  scenario_id: string;
  scenario_name: string;
  category: string;
  timestamp_utc: string;
  status: string;
  calculation_status: string;
  relative_path: string;
  all_checks_passed: boolean;
  checks_passed_count: number;
  checks_total_count: number;
  algorithm_version: string;
  sha256_hash: string;
  is_mock: boolean;
}

export interface LocalityDTO {
  id: string;
  name: string;
  pincode?: string | null;
  district: string;
  state: string;
}

export interface MandiDTO {
  id: string;
  market_name: string;
  district: string;
  state: string;
  distance_km_reference?: number | null;
  provenance_note?: string | null;
  is_mock: boolean;
}

export interface MandiRecommendation {
  suggested_mandi?: MandiDTO | null;
  locality: LocalityDTO;
  has_recommendation: boolean;
  confidence: 'high' | 'provisional' | 'unavailable';
  distance_km?: number | null;
  reason: string;
  available_mandis: MandiDTO[];
}

export interface PricingBreakdown {
  commodity_id?: string;
  locality_id?: string | null;
  calculation_status?: string;
  wholesale_price_per_kg?: number | null;
  transport_cost_per_kg?: number | null;
  transport_status?: string;
  transport_method?: string | null;
  cost_basis_per_kg?: number | null;
  is_provisional_wholesale_only?: boolean;
  markup_min_pct?: number;
  markup_max_pct?: number;
  quality_adjustment?: number;
  quality_adjustment_meaning?: string;
  baseline_range?: { min: number; max: number; mid: number; unit: string } | null;
  community_sample_size?: number;
  community_estimate?: number | null;
  reconciliation_weight_alpha?: number;
  is_sample_sufficient?: boolean;
  reconciled_range?: { min: number; max: number; mid: number; unit: string } | null;
  suggested_price?: number | null;
  warnings?: string[];
  notes?: string[];
  observation_breakdown?: {
    total_found: number;
    eligible_count: number;
    excluded_duplicates_count: number;
    excluded_stale_count: number;
    excluded_non_weight_unit_count: number;
    excluded_invalid_count: number;
    community_median?: number | null;
    community_mean?: number | null;
    community_min?: number | null;
    community_max?: number | null;
  };
}

export interface CalculationRecordSummary {
  id: string;
  sequence_number: number;
  commodity_id: string;
  locality_id?: string | null;
  status: string;
  algorithm_version: string;
  schema_version: string;
  previous_record_hash: string;
  current_record_hash: string;
  is_mock: boolean;
  created_at: string;
}

export interface LedgerVerificationResult {
  is_valid: boolean;
  total_records: number;
  last_sequence_number?: number | null;
  last_record_hash?: string | null;
  tampered_sequences: number[];
  errors: string[];
  checkpoint_verified?: boolean;
  verified_at: string;
}

export interface CommunitySubmissionInput {
  commodity_id: string;
  price: number;
  unit: string;
  locality_id: string;
  source_type: 'customer' | 'vendor';
  contributor_id?: string;
  observed_at?: string;
}

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
  /** Additive explainable pricing breakdown from backend */
  pricingBreakdown?: PricingBreakdown;
  calculationId?: string | null;
  sequenceNumber?: number | null;
  recordHash?: string | null;
  calculationStatus?: string;
  isMock?: boolean;
  localityId?: string | null;
  mandiId?: string | null;
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
