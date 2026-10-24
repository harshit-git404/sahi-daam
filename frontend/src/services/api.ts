import {
  RetailResult,
  SectorAnalysisResult,
  LocalityDTO,
  MandiDTO,
  MandiRecommendation,
  CalculationRecordSummary,
  LedgerVerificationResult,
  CommunitySubmissionInput,
  ScenarioSummaryDTO,
  ExperimentRunResult,
  ManifestRunEntry,
} from '../types';

// Use environment variable if set, otherwise default to the Vite proxy (/api)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

/**
 * POST /scan-produce
 *
 * @param produceId   - known produce ID hint (optional; backend identifies via ML)
 * @param imageBase64 - base64-encoded image (required for ML analysis)
 * @param options     - structured location fields & locality/mandi selection
 */
export async function fetchScanResult(
  produceId: string,
  imageBase64?: string,
  options?: {
    state?: string;
    district?: string;
    market?: string;
    purchase_type?: string;
    locality_id?: string;
    pincode?: string;
    mandi_id?: string;
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
  if (options?.locality_id) body.locality_id = options.locality_id;
  if (options?.pincode) body.pincode = options.pincode;
  if (options?.mandi_id) body.mandi_id = options.mandi_id;

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
    } catch { /* ignore */ }
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
    } catch { /* ignore */ }
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
    } catch { /* ignore */ }
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

/** GET /localities */
export async function fetchLocalities(pincode?: string): Promise<LocalityDTO[]> {
  const url = pincode ? `${API_BASE_URL}/localities?pincode=${encodeURIComponent(pincode.trim())}` : `${API_BASE_URL}/localities`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch localities (${res.status})`);
  return res.json();
}

/** GET /mandis */
export async function fetchMandis(district?: string): Promise<MandiDTO[]> {
  const url = district ? `${API_BASE_URL}/mandis?district=${encodeURIComponent(district.trim())}` : `${API_BASE_URL}/mandis`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch mandis (${res.status})`);
  return res.json();
}

/** GET /mandis/recommendation */
export async function fetchMandiRecommendation(
  localityId: string,
  commodityId?: string,
): Promise<MandiRecommendation> {
  const params = new URLSearchParams({ locality_id: localityId });
  if (commodityId) params.set('commodity_id', commodityId);
  const res = await fetch(`${API_BASE_URL}/mandis/recommendation?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to get mandi recommendation (${res.status})`);
  return res.json();
}

/** POST /community-prices */
export async function submitCommunityPrice(payload: CommunitySubmissionInput): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/community-prices`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const errJson = await res.json();
      detail = errJson?.detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

/** GET /community-prices */
export async function fetchCommunityPrices(params?: {
  commodity_id?: string;
  locality_id?: string;
  window_days?: number;
}): Promise<any> {
  const q = new URLSearchParams();
  if (params?.commodity_id) q.set('commodity_id', params.commodity_id);
  if (params?.locality_id) q.set('locality_id', params.locality_id);
  if (params?.window_days) q.set('window_days', String(params.window_days));
  const res = await fetch(`${API_BASE_URL}/community-prices?${q.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch community prices (${res.status})`);
  return res.json();
}

/** GET /calculations */
export async function fetchCalculations(
  limit: number = 50,
  offset: number = 0,
): Promise<{ calculations: CalculationRecordSummary[]; total_count: number }> {
  const res = await fetch(`${API_BASE_URL}/calculations?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error(`Failed to fetch calculations (${res.status})`);
  return res.json();
}

/** GET /calculations/{id} */
export async function fetchCalculationDetail(id: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/calculations/${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error(`Calculation not found (${res.status})`);
  return res.json();
}

/** GET /calculations/{id}/export */
export async function downloadCalculationExport(id: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/calculations/${encodeURIComponent(id)}/export`);
  if (!res.ok) throw new Error(`Failed to export calculation (${res.status})`);
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `sahi_daam_${id}.json`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

/** GET /ledger/verify */
export async function verifyLedger(): Promise<LedgerVerificationResult> {
  const res = await fetch(`${API_BASE_URL}/ledger/verify`);
  if (!res.ok) throw new Error(`Failed to verify ledger (${res.status})`);
  return res.json();
}

/** ---------------------------------------------------------------------------
 * Experiment Lab API Functions
 * --------------------------------------------------------------------------- */

/** GET /experiments/scenarios */
export async function fetchExperimentScenarios(): Promise<ScenarioSummaryDTO[]> {
  const res = await fetch(`${API_BASE_URL}/experiments/scenarios`);
  if (!res.ok) throw new Error(`Failed to fetch scenarios (${res.status})`);
  return res.json();
}

/** POST /experiments/run/{scenarioId} */
export async function runExperimentScenario(scenarioId: string): Promise<ExperimentRunResult> {
  const res = await fetch(`${API_BASE_URL}/experiments/run/${encodeURIComponent(scenarioId)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const err = await res.json();
      detail = err?.detail || detail;
    } catch {}
    throw new Error(`Scenario run failed: ${detail}`);
  }
  return res.json();
}

/** POST /experiments/run-all */
export async function runAllExperimentScenarios(): Promise<{
  total_scenarios: number;
  executed_count: number;
  all_passed: boolean;
  report_path: string;
}> {
  const res = await fetch(`${API_BASE_URL}/experiments/run-all`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) throw new Error(`Batch execution failed (${res.status})`);
  return res.json();
}

/** GET /experiments/runs */
export async function fetchExperimentRuns(): Promise<ManifestRunEntry[]> {
  const res = await fetch(`${API_BASE_URL}/experiments/runs`);
  if (!res.ok) throw new Error(`Failed to fetch runs (${res.status})`);
  return res.json();
}

/** GET /experiments/runs/{runId} */
export async function fetchExperimentRunDetail(runId: string): Promise<ExperimentRunResult> {
  const res = await fetch(`${API_BASE_URL}/experiments/runs/${encodeURIComponent(runId)}`);
  if (!res.ok) throw new Error(`Run detail not found (${res.status})`);
  return res.json();
}

/** GET /experiments/runs/{runId}/export */
export async function downloadExperimentExport(runId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/experiments/runs/${encodeURIComponent(runId)}/export`);
  if (!res.ok) throw new Error(`Failed to export run (${res.status})`);
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${runId}.json`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

/** GET /experiments/manifest */
export async function fetchExperimentManifest(): Promise<{
  total_runs: number;
  runs: ManifestRunEntry[];
}> {
  const res = await fetch(`${API_BASE_URL}/experiments/manifest`);
  if (!res.ok) throw new Error(`Failed to fetch manifest (${res.status})`);
  return res.json();
}
