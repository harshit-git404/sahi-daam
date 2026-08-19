// Use environment variable if set (for local network override without ngrok), otherwise default to the Vite proxy (/api)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export async function fetchScanResult(imageBase64: string) {
  const response = await fetch(`${API_BASE_URL}/scan-produce`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ image: imageBase64 }),
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch scan result: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchHaggleCheck(askingPrice: number) {
  const response = await fetch(`${API_BASE_URL}/haggle-check`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ asking_price: askingPrice }),
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch haggle check: ${response.statusText}`);
  }
  return response.json();
}
