import type { ProduceItem, PurchaseRecord } from '../types';

const PURCHASE_HISTORY_STORAGE_KEY = 'sahi-daam.purchase-history.v1';

export interface TransactionInput {
  produce: ProduceItem;
  vendorAskingPrice: number;
  finalPaidPrice: number;
  timestamp?: number;
}

export interface HistoryStats {
  totalSavings: number;
  dealCount: number;
  weeklySavings: number;
  weeklyDealCount: number;
  weeklySavingsPctChange: number;
  weeklyTrend: number[];
}

export function calculateFairPrice(produce: ProduceItem): number {
  return Math.round((produce.retailFairMin + produce.retailFairMax) / 2);
}

export function calculateSavings(fairPrice: number, finalPaidPrice: number): number {
  return Math.max(0, Math.round(fairPrice - finalPaidPrice));
}

export function createPurchaseRecord({
  produce,
  vendorAskingPrice,
  finalPaidPrice,
  timestamp = Date.now(),
}: TransactionInput): PurchaseRecord {
  const fairPrice = calculateFairPrice(produce);
  const iconType =
    produce.id === 'tomato' || produce.id === 'onion' || produce.id === 'potato'
      ? produce.id
      : produce.category === 'Leafy'
        ? 'leaf'
        : 'general';

  return {
    id: `rec-${timestamp}`,
    produceId: produce.id,
    produceName: produce.name,
    vendorAskingPrice: Math.round(vendorAskingPrice),
    paidPrice: Math.round(finalPaidPrice),
    fairPrice,
    savedAmount: calculateSavings(fairPrice, finalPaidPrice),
    unit: produce.unit,
    timestamp,
    decision: produce.decision,
    outcome: 'BOUGHT',
    iconType,
  };
}

export function calculateHistoryStats(records: PurchaseRecord[], now = Date.now()): HistoryStats {
  const totalSavings = records.reduce((sum, record) => sum + record.savedAmount, 0);
  const sevenDaysAgo = now - 7 * 86_400_000;
  const fourteenDaysAgo = now - 14 * 86_400_000;
  const currentWeek = records.filter((record) => record.timestamp >= sevenDaysAgo);
  const previousWeek = records.filter(
    (record) => record.timestamp >= fourteenDaysAgo && record.timestamp < sevenDaysAgo
  );
  const weeklySavings = currentWeek.reduce((sum, record) => sum + record.savedAmount, 0);
  const previousWeeklySavings = previousWeek.reduce((sum, record) => sum + record.savedAmount, 0);
  const weeklySavingsPctChange =
    previousWeeklySavings > 0
      ? Math.round(((weeklySavings - previousWeeklySavings) / previousWeeklySavings) * 100)
      : weeklySavings > 0
        ? 100
        : 0;
  const weeklyTrend = Array.from({ length: 7 }, (_, index) => {
    const dayStart = new Date(now);
    dayStart.setHours(0, 0, 0, 0);
    dayStart.setDate(dayStart.getDate() - (6 - index));
    const startMs = dayStart.getTime();
    const endMs = startMs + 86_400_000;
    return records
      .filter((record) => record.timestamp >= startMs && record.timestamp < endMs)
      .reduce((sum, record) => sum + record.savedAmount, 0);
  });

  return {
    totalSavings,
    dealCount: records.length,
    weeklySavings,
    weeklyDealCount: currentWeek.length,
    weeklySavingsPctChange,
    weeklyTrend,
  };
}

export function loadPurchaseHistory(): PurchaseRecord[] {
  if (typeof window === 'undefined') {
    return [];
  }

  try {
    const raw = window.localStorage.getItem(PURCHASE_HISTORY_STORAGE_KEY);
    if (!raw) {
      return [];
    }

    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed.filter(isPurchaseRecord);
  } catch {
    return [];
  }
}

export function savePurchaseHistory(records: PurchaseRecord[]): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(PURCHASE_HISTORY_STORAGE_KEY, JSON.stringify(records));
}

function isPurchaseRecord(value: unknown): value is PurchaseRecord {
  if (!value || typeof value !== 'object') {
    return false;
  }

  const record = value as Partial<PurchaseRecord>;
  return (
    typeof record.id === 'string' &&
    typeof record.produceId === 'string' &&
    typeof record.produceName === 'string' &&
    typeof record.vendorAskingPrice === 'number' &&
    typeof record.paidPrice === 'number' &&
    typeof record.fairPrice === 'number' &&
    typeof record.savedAmount === 'number' &&
    typeof record.unit === 'string' &&
    typeof record.timestamp === 'number'
  );
}
