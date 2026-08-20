export const RUPEE = '\u20B9';

export function formatRupees(value: number | null | undefined): string {
  const amount = Number.isFinite(value) ? Number(value) : 0;
  const rounded = Math.round(amount);
  return `${RUPEE}${rounded}`;
}

export function formatRupeesPerUnit(value: number | null | undefined, unit: string): string {
  return `${formatRupees(value)}/${unit}`;
}

export function formatRelativeDate(timestamp: number, now = Date.now()): string {
  const elapsedMs = Math.max(0, now - timestamp);
  const elapsedDays = Math.floor(elapsedMs / 86_400_000);

  if (elapsedDays === 0) {
    return 'Today';
  }

  if (elapsedDays === 1) {
    return 'Yesterday';
  }

  if (elapsedDays < 7) {
    return `${elapsedDays} days ago`;
  }

  return new Date(timestamp).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  });
}
