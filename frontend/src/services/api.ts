import { SectorAnalysisResult } from '../types';

// Use environment variable if set (for local network override without ngrok), otherwise default to the Vite proxy (/api)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export async function fetchScanResult(produceId: string, imageBase64?: string, options?: { state?: string; district?: string; market?: string; purchase_type?: string }) {
  const response = await fetch(`${API_BASE_URL}/scan-produce`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ produce_type: produceId, image: imageBase64, ...options }),
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch scan result: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchHaggleCheck(askingPrice: number, fairPriceMin: number, fairPriceMax: number) {
  const response = await fetch(`${API_BASE_URL}/haggle-check`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ asking_price: askingPrice, fair_price_min: fairPriceMin, fair_price_max: fairPriceMax }),
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch haggle check: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchSectorAnalysis(sector: string, component: string): Promise<SectorAnalysisResult> {
  const params = new URLSearchParams({ sector, component });
  const response = await fetch(`${API_BASE_URL}/sector-analysis?${params.toString()}`);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || `Failed to fetch sector analysis: ${response.statusText}`);
  }
  return response.json();
}
