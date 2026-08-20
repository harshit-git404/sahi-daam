import { RetailResult, SectorAnalysisResult } from '../types';

// Use environment variable if set, otherwise default to the Vite proxy (/api)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

/**
 * POST /scan-produce
 *
 * @param produceId   - known produce ID hint (optional; backend identifies via ML)
 * @param imageBase64 - base64-encoded image (required for ML analysis)
 * @param options     - structured location fields (state, district, market, purchase_type)
 */
export async function fetchScanResult(
  produceId: string,
  imageBase64?: string,
  options?: {
    state?: string;
    district?: string;
    market?: string;
    purchase_type?: string;
  },
) {
  const body: Record<string, unknown> = {
    produce_type: produceId,
    image: imageBase64,
  };
  if (options?.state) body.state = options.state;
  if (options?.district) body.district = options.district;
  if (options?.market) body.market = options.market;
  if (options?.purchase_type) body.purchase_type = options.purchase_type;

  const response = await fetch(`${API_BASE_URL}/scan-produce`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const json = await response.json();
      detail = json?.detail || detail;
    } catch (_) { /* ignore */ }
    throw new Error(`Scan failed (${response.status}): ${detail}`);
  }
  return response.json();
}

/**
 * POST /haggle-check
 *
 * Must only be called for street_vendor purchase type.
 */
export async function fetchHaggleCheck(
  askingPrice: number,
  fairPriceMin: number,
  fairPriceMax: number,
  options?: {
    purchase_type?: string;
    market_reference?: number;
    online_reference_min?: number;
    online_reference_max?: number;
  },
) {
  const body: Record<string, unknown> = {
    asking_price: askingPrice,
    fair_price_min: fairPriceMin,
    fair_price_max: fairPriceMax,
    purchase_type: options?.purchase_type ?? 'street_vendor',
  };
  if (options?.market_reference != null) body.market_reference = options.market_reference;
  if (options?.online_reference_min != null) body.online_reference_min = options.online_reference_min;
  if (options?.online_reference_max != null) body.online_reference_max = options.online_reference_max;

  const response = await fetch(`${API_BASE_URL}/haggle-check`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const json = await response.json();
      detail = json?.detail || detail;
    } catch (_) { /* ignore */ }
    throw new Error(`Haggle check failed (${response.status}): ${detail}`);
  }
  return response.json();
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

/** GET /retail-prices */
export async function fetchRetailPrices(
  commodity: string,
  location?: string,
): Promise<RetailResult> {
  const params = new URLSearchParams({ commodity });
  if (location) params.set('location', location);
  const response = await fetch(`${API_BASE_URL}/retail-prices?${params.toString()}`);
  if (!response.ok) {
    return {
      status: 'UNAVAILABLE',
      commodity,
      products: [],
      message: `Retail prices unavailable (${response.status}: ${response.statusText}).`,
    };
  }
  return response.json();
}
