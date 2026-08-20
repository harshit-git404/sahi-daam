import assert from 'node:assert/strict';
import test from 'node:test';

import type { ProduceItem } from '../types';
import { formatRelativeDate, formatRupees } from './format.ts';
import {
  calculateFairPrice,
  calculateHistoryStats,
  calculateSavings,
  createPurchaseRecord,
} from './transactions.ts';
import { getPhraseText, getVoiceAvailability, VOICE_LANGUAGE_CONFIG } from './voice.ts';

const tomato: ProduceItem = {
  id: 'tomato',
  name: 'Tomato',
  image: '',
  matchScore: 98,
  qualitySummary: 'Fresh',
  freshness: 'fresh',
  freshnessPercent: 90,
  wholesalePrice: 22,
  markupMinPercent: 30,
  markupMaxPercent: 45,
  retailFairMin: 28,
  retailFairMax: 34,
  typicalVendorAsking: 45,
  suggestedOfferPrice: 30,
  unit: 'kg',
  qualityAdjustment: 0,
  qualityAdjustmentLabel: 'none',
  dataConfidence: 'High',
  category: 'Vegetables',
  bargainPhrases: [],
};

test('createPurchaseRecord stores actual deal data and non-negative savings', () => {
  const record = createPurchaseRecord({
    produce: tomato,
    vendorAskingPrice: 45,
    finalPaidPrice: 29,
    timestamp: 1_800_000_000_000,
  });

  assert.equal(record.produceName, 'Tomato');
  assert.equal(record.vendorAskingPrice, 45);
  assert.equal(record.paidPrice, 29);
  assert.equal(record.fairPrice, 31);
  assert.equal(record.savedAmount, 2);
  assert.equal(record.unit, 'kg');
  assert.equal(record.outcome, 'BOUGHT');
});

test('savings are based on fair price and never become negative', () => {
  assert.equal(calculateFairPrice(tomato), 31);
  assert.equal(calculateSavings(31, 29), 2);
  assert.equal(calculateSavings(31, 40), 0);
});

test('calculateHistoryStats derives totals, weekly changes, and seven-day bars', () => {
  const now = Date.UTC(2026, 7, 20, 12);
  const day = 86_400_000;
  const records = [
    createPurchaseRecord({ produce: tomato, vendorAskingPrice: 45, finalPaidPrice: 29, timestamp: now }),
    createPurchaseRecord({ produce: tomato, vendorAskingPrice: 40, finalPaidPrice: 30, timestamp: now - day }),
    createPurchaseRecord({ produce: tomato, vendorAskingPrice: 35, finalPaidPrice: 29, timestamp: now - 8 * day }),
  ];

  const stats = calculateHistoryStats(records, now);

  assert.equal(stats.totalSavings, 5);
  assert.equal(stats.weeklySavings, 3);
  assert.equal(stats.weeklyDealCount, 2);
  assert.equal(stats.weeklySavingsPctChange, 50);
  assert.deepEqual(stats.weeklyTrend.slice(-2), [1, 2]);
});

test('format helpers render rupees and stable relative dates', () => {
  const now = Date.UTC(2026, 7, 20, 12);

  assert.equal(formatRupees(31.4), '₹31');
  assert.equal(formatRelativeDate(now, now), 'Today');
  assert.equal(formatRelativeDate(now - 86_400_000, now), 'Yesterday');
});

test('voice helpers use the selected phrase language and report unsupported browsers', () => {
  const phrase = {
    hindi: 'Hindi phrase',
    tamil: 'Tamil phrase',
    english: 'English phrase',
    phonetic: 'Hindi phonetic',
  };

  assert.equal(VOICE_LANGUAGE_CONFIG.hi.locale, 'hi-IN');
  assert.equal(VOICE_LANGUAGE_CONFIG.ta.locale, 'ta-IN');
  assert.equal(VOICE_LANGUAGE_CONFIG.en.locale, 'en-IN');
  assert.equal(getPhraseText(phrase, 'hi'), 'Hindi phrase');
  assert.equal(getPhraseText(phrase, 'ta'), 'Tamil phrase');
  assert.equal(getPhraseText(phrase, 'en'), 'English phrase');
  assert.equal(getVoiceAvailability('hi').status, 'unsupported');
});
