import { ProduceItem, FreshnessLevel } from '../types';

export function mergeProduceData(catalogEntry: ProduceItem, backendResponse: any): ProduceItem {
  // Map freshness label to enum
  let mappedFreshness: FreshnessLevel = 'fresh';
  const label = backendResponse.freshness_label?.toLowerCase() || '';
  if (label.includes('aged')) {
    mappedFreshness = 'slightly_aged';
  } else if (label.includes('overripe')) {
    mappedFreshness = 'overripe';
  }

  return {
    ...catalogEntry,
    matchScore: backendResponse.produce_confidence ?? catalogEntry.matchScore,
    freshness: mappedFreshness,
    freshnessPercent: backendResponse.freshness_percent ?? catalogEntry.freshnessPercent,
    qualitySummary: backendResponse.freshness_note ?? catalogEntry.qualitySummary,
    wholesalePrice: backendResponse.wholesale_price ?? 0,
    markupMinPercent: backendResponse.markup_range?.min_pct ?? catalogEntry.markupMinPercent,
    markupMaxPercent: backendResponse.markup_range?.max_pct ?? catalogEntry.markupMaxPercent,
    retailFairMin: backendResponse.fair_price_range?.min ?? 0,
    retailFairMax: backendResponse.fair_price_range?.max ?? 0,
    qualityAdjustment: backendResponse.quality_adjustment ?? catalogEntry.qualityAdjustment,
    qualityAdjustmentLabel: backendResponse.quality_adjustment_label ?? catalogEntry.qualityAdjustmentLabel,
    dataConfidence: backendResponse.data_confidence ?? catalogEntry.dataConfidence,
    quickCommercePrice: backendResponse.quickcommerce_price ? {
      source: backendResponse.quickcommerce_price.source,
      price: backendResponse.quickcommerce_price.price,
      unit: backendResponse.quickcommerce_price.unit,
    } : undefined,
    marketStatus: backendResponse.market_status,
    analysisProvider: backendResponse.analysis_provider,
  };
}
