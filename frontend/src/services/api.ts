const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function fetchScanResult(produceId: string) {
  // Pass produceId if needed in the future, currently backend uses mock
  const response = await fetch(`${API_BASE_URL}/scan-produce`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
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
