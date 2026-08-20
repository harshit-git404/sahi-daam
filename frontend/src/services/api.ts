// Use environment variable if set (for local network override without ngrok), otherwise default to the Vite proxy (/api)
import type { BargainPhrase, NegotiationLanguage, ProduceItem } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export type QuickCommercePrice = NonNullable<ProduceItem['quickCommercePrice']>;

export interface ScanResultResponse {
  detected_produce_id?: string;
  produce_type?: string;
  freshness_label?: string;
  freshness_percent?: number;
  freshness_note?: string;
  wholesale_price?: number;
  markup_range?: {
    min_pct?: number;
    max_pct?: number;
  };
  quality_adjustment?: number;
  quality_adjustment_label?: string;
  fair_price_range?: {
    min?: number;
    max?: number;
    unit?: string;
  };
  data_confidence?: ProduceItem['dataConfidence'];
  price_source?: string;
  quickcommerce_price?: QuickCommercePrice;
  market_context?: ProduceItem['marketContext'];
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
