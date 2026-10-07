// Use environment variable if set (for local network override without ngrok), otherwise default to the Vite proxy (/api)
import type { BargainPhrase, NegotiationLanguage, ProduceItem, SectorAnalysisResult } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export type QuickCommercePrice = NonNullable<ProduceItem['quickCommercePrice']>;

export interface ScanResultResponse {
  produce_type: string;
  detected_produce_id: string;
  classification_confidence: number;
  freshness_label: string;
  freshness_percent: number;
  freshness_note: string;
  quality_adjustment: number;
  quality_adjustment_label: string;
  wholesale_price: number;
  markup_range: {
    min_pct: number;
    max_pct: number;
  };
  fair_price_range: {
    min: number;
    max: number;
    unit: string;
  };
  data_confidence?: ProduceItem['dataConfidence'];
  price_source?: string;
  quickcommerce_price?: QuickCommercePrice;
  retail_comparison?: any;
  market_context?: ProduceItem['marketContext'];
  session_id?: string;
  needs_additional_observation?: boolean;
  observation_request?: ProduceItem['observationRequest'];
  valuation_uncertainty?: number;
  valuation_confidence?: number;
  quality_uncertainty?: number;
  market_uncertainty?: number;
  market_confidence?: number;
  decision_trace?: ProduceItem['decisionTrace'];
  instrumentation_comparison?: ProduceItem['instrumentationComparison'];
  observation_count?: number;
}

export interface HaggleCheckResponse {
  verdict: ProduceItem['haggleVerdict'];
  suggested_price: number;
  reasoning: string;
  phrases: BargainPhrase[];
  phrases_source: 'gemini' | 'fallback';
  decision: NonNullable<ProduceItem['decision']>;
  severity: ProduceItem['severity'];
  recommendation: ProduceItem['recommendation'];
  alternatives?: ProduceItem['alternatives'];
  starting_offer?: number;
  target_price?: number;
  maximum_reasonable_price?: number;
  potential_saving?: number;
  below_fair_amount?: number;
  quality_context?: ProduceItem['qualityContext'];
}

export async function fetchScanResult(produceId: string, imageBase64?: string): Promise<ScanResultResponse> {
  const response = await fetch(`${API_BASE_URL}/scan-produce`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ produce_type: produceId, image: imageBase64 }),
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch scan result: ${response.statusText}`);
  }
  return response.json() as Promise<ScanResultResponse>;
}

export async function fetchHaggleCheck(
  produceType: string, 
  askingPrice: number, 
  fairPriceMin: number, 
  fairPriceMax: number,
  freshnessLabel?: string,
  quickCommercePrice?: QuickCommercePrice,
  language: NegotiationLanguage = 'hi',
  signal?: AbortSignal
): Promise<HaggleCheckResponse> {
  const response = await fetch(`${API_BASE_URL}/haggle-check`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    signal,
    body: JSON.stringify({
      produce_type: produceType,
      asking_price: askingPrice,
      fair_price_min: fairPriceMin,
      fair_price_max: fairPriceMax,
      freshness_label: freshnessLabel,
      quickcommerce_price: quickCommercePrice,
      language
    }),
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch haggle check: ${response.statusText}`);
  }
  return response.json() as Promise<HaggleCheckResponse>;
}

/** GET /sector-analysis */
export async function fetchSectorAnalysis(
  sector: string,
  component: string,
): Promise<SectorAnalysisResult> {
  const params = new URLSearchParams({ sector, component });
  const response = await fetch(`${API_BASE_URL}/sector-analysis?${params.toString()}`);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const json = await response.json();
      detail = json?.detail || detail;
    } catch (_) { /* ignore */ }
    throw new Error(`Sector analysis failed (${response.status}): ${detail}`);
  }
  return response.json();
}

/** POST /valuation/observe - Add an additional viewpoint to an existing session */
export async function submitAdditionalObservation(
  sessionId: string,
  imageBase64: string,
  viewAngle: string = 'reverse_side'
): Promise<ScanResultResponse> {
  const response = await fetch(`${API_BASE_URL}/valuation/observe`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      image_base64: imageBase64,
      view_angle: viewAngle,
    }),
  });
  if (!response.ok) {
    throw new Error(`Failed to submit additional observation: ${response.statusText}`);
  }
  const session = await response.json();
  
  // Map session response to ScanResultResponse
  const latestQuality = session.current_quality_estimate;
  const latestMarket = session.current_market_estimate;
  const latestValuation = session.latest_valuation;
  const latestDecision = session.latest_decision;
  
  return {
    produce_type: session.commodity,
    detected_produce_id: session.commodity.toLowerCase(),
    classification_confidence: latestQuality?.confidence ?? 0.8,
    freshness_label: latestQuality?.quality_class || 'Fresh',
    freshness_percent: Math.round((latestQuality?.freshness_score ?? 0.8) * 100),
    freshness_note: latestQuality?.defect_notes?.length ? latestQuality.defect_notes.join('. ') : 'Quality re-estimated across multiple viewpoints.',
    quality_adjustment: latestValuation?.quality_adjustment_per_kg ?? 0,
    quality_adjustment_label: `${latestValuation?.quality_adjustment_per_kg >= 0 ? '+' : ''}₹${latestValuation?.quality_adjustment_per_kg ?? 0}/kg adjustment`,
    wholesale_price: latestMarket?.estimated_price_per_kg ?? 30,
    markup_range: {
      min_pct: 15,
      max_pct: 35,
    },
    fair_price_range: {
      min: latestValuation?.fair_min ?? 28,
      max: latestValuation?.fair_max ?? 40,
      unit: 'kg',
    },
    data_confidence: (latestValuation?.confidence ?? 0.8) > 0.75 ? 'High' : (latestValuation?.confidence ?? 0.8) > 0.5 ? 'Medium' : 'Estimated',
    price_source: latestMarket?.sources?.[0]?.source || 'Weighted Market Evidence',
    session_id: session.session_id,
    needs_additional_observation: latestDecision?.decision === 'ACQUIRE_ADDITIONAL_OBSERVATION',
    observation_request: latestDecision?.observation_request,
    valuation_uncertainty: latestValuation?.valuation_uncertainty,
    valuation_confidence: latestValuation?.confidence,
    quality_uncertainty: session.current_quality_uncertainty,
    market_uncertainty: session.current_market_uncertainty,
    market_confidence: latestMarket?.confidence,
    decision_trace: session.decision_trace,
    instrumentation_comparison: session.comparison,
    observation_count: session.observation_count,
  };
}

/** POST /valuation/simulate - Run demonstration benchmark scenario */
export async function runSimulatedScenario(scenarioKey: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/valuation/simulate?scenario_key=${encodeURIComponent(scenarioKey)}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  if (!response.ok) {
    throw new Error(`Failed to run scenario: ${response.statusText}`);
  }
  return response.json();
}

