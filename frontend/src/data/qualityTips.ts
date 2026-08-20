import { FreshnessLevel } from '../types';

type ProduceTips = {
  [key in FreshnessLevel]: string;
};

type QualityTips = {
  [produceId: string]: ProduceTips;
};

export const QUALITY_TIPS: QualityTips = {
  tomato: {
    fresh: 'Great raw — salads, sandwiches',
    slightly_aged: 'Best cooked — curries, chutney',
    overripe: 'Perfect for sauce or puree today'
  },
  onion: {
    fresh: 'Crunchy raw — garnishes, salads',
    slightly_aged: 'Ideal for sautéing — bases, gravies',
    overripe: 'Caramelize for a deep, rich flavor'
  },
  potato: {
    fresh: 'Perfect for boiling, mashing, or fries',
    slightly_aged: 'Great for roasting or thick curries',
    overripe: 'Use immediately in stews or hash'
  }
};

export function getQualityTip(produceId: string, freshness: FreshnessLevel): string {
  const tips = QUALITY_TIPS[produceId.toLowerCase()];
  if (tips) {
    return tips[freshness];
  }
  // Fallback for general items
  switch (freshness) {
    case 'fresh': return 'Enjoy fresh or store properly to maintain quality.';
    case 'slightly_aged': return 'Best cooked or used in hot dishes soon.';
    case 'overripe': return 'Use immediately in purees, sauces, or soups.';
    default: return '';
  }
}
