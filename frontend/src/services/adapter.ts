import { ProduceItem, FreshnessLevel, MarketData, PricingData, RetailResult } from '../types';

/**
 * Merge backend /scan-produce response into a ProduceItem for the frontend.
 *
 * Rules:
 * - Backend values take precedence over catalog defaults for ALL price/freshness fields.
 * - If the backend provides no wholesale price (market unavailable), wholesalePrice stays 0
 *   so the frontend can detect and display "Unavailable" rather than showing catalog prices.
 * - Unknown produce (not in catalog) must use backend prices only — never inherit catalog values.
 */
export function mergeProduceData(
  catalogEntry: ProduceItem,
  backendResponse: Record<string, unknown>,
): ProduceItem {
  // Map freshness label to enum
  let mappedFreshness: FreshnessLevel = 'fresh';
  const label = String(backendResponse.freshness_label ?? '').toLowerCase();
  if (label.includes('aged') || label.includes('slightly')) {
    mappedFreshness = 'slightly_aged';
  } else if (label.includes('overripe') || label.includes('spoiled')) {
    mappedFreshness = 'overripe';
  }

  // Parse market block
  const marketBlock = backendResponse.market as MarketData | undefined;
  const pricingBlock = backendResponse.pricing as PricingData | undefined;
  const retailBlock = backendResponse.retail as RetailResult | undefined;

  // Wholesale price — strictly from backend (null / 0 when market is unavailable)
  const wholesalePrice =
    typeof backendResponse.wholesale_price === 'number'
      ? backendResponse.wholesale_price
      : 0;

  // Fair price — from backend pricing block, fall back to fair_price_range
  const fairPriceRange = backendResponse.fair_price_range as { min: number; max: number } | null;
  const retailFairMin = pricingBlock?.fair_price_min ?? fairPriceRange?.min ?? 0;
  const retailFairMax = pricingBlock?.fair_price_max ?? fairPriceRange?.max ?? 0;

  // Market status
  const marketStatus =
    (backendResponse.market_status as 'AVAILABLE' | 'UNAVAILABLE' | undefined) ??
    marketBlock?.status ??
    'UNAVAILABLE';

  // typicalVendorAsking: use catalog entry unchanged; only user input updates this
  const typicalVendorAsking = catalogEntry.typicalVendorAsking;

  // Quick-commerce price
  const qcPrice = backendResponse.quickcommerce_price as
    | { source: string; price: number; unit: string }
    | null
    | undefined;

  return {
    ...catalogEntry,
    // --- ML result ---
    matchScore: typeof backendResponse.produce_confidence === 'number'
      ? backendResponse.produce_confidence
      : catalogEntry.matchScore,
    analysisProvider: (backendResponse.analysis_provider as 'gemini' | 'local_fallback') ??
      catalogEntry.analysisProvider,
    // --- Freshness ---
    freshness: mappedFreshness,
    freshnessPercent:
      typeof backendResponse.freshness_percent === 'number'
        ? backendResponse.freshness_percent
        : catalogEntry.freshnessPercent,
    qualitySummary: typeof backendResponse.freshness_note === 'string'
      ? backendResponse.freshness_note
      : catalogEntry.qualitySummary,
    qualityAdjustment:
      typeof backendResponse.quality_adjustment === 'number'
        ? backendResponse.quality_adjustment
        : catalogEntry.qualityAdjustment,
    qualityAdjustmentLabel: typeof backendResponse.quality_adjustment_label === 'string'
      ? backendResponse.quality_adjustment_label
      : catalogEntry.qualityAdjustmentLabel,
    // --- Market / pricing ---
    wholesalePrice,
    markupMinPercent:
      (backendResponse.markup_range as { min_pct: number } | null)?.min_pct ??
      catalogEntry.markupMinPercent,
    markupMaxPercent:
      (backendResponse.markup_range as { max_pct: number } | null)?.max_pct ??
      catalogEntry.markupMaxPercent,
    retailFairMin,
    retailFairMax,
    typicalVendorAsking,
    // suggestedOfferPrice: 0 until /haggle-check responds; user must enter asking price first
    suggestedOfferPrice: 0,
    dataConfidence: (backendResponse.data_confidence as 'High' | 'Medium' | 'Estimated' | 'Unavailable') ??
      catalogEntry.dataConfidence,
    marketStatus,
    // --- Structured blocks ---
    market: marketBlock,
    pricing: pricingBlock,
    retailComparison: retailBlock,
    onlineReferenceMin: typeof backendResponse.online_reference_min === 'number'
      ? backendResponse.online_reference_min
      : null,
    onlineReferenceMax: typeof backendResponse.online_reference_max === 'number'
      ? backendResponse.online_reference_max
      : null,
    // --- Quick commerce ---
    quickCommercePrice: qcPrice
      ? { source: qcPrice.source, price: qcPrice.price, unit: qcPrice.unit }
      : undefined,
  };
}
