import React from 'react';
import { useApp } from '../context/AppContext';
import { Header } from './Header';

// ── Helper: freshness level label ─────────────────────────────────────────────
function freshnessLevelLabel(freshness: string): string {
  if (freshness === 'slightly_aged') return 'Slightly Aged';
  if (freshness === 'overripe') return 'Overripe';
  return 'Fresh';
}

// ── Helper: freshness colour ──────────────────────────────────────────────────
function freshnessColor(freshness: string, isTerracotta: boolean): string {
  if (freshness === 'overripe') return '#b91c1c';
  if (freshness === 'slightly_aged') return isTerracotta ? '#9e3d00' : '#835100';
  return isTerracotta ? '#006d37' : '#0e6c4a';
}

export const QualityResultScreen: React.FC = () => {
  const { setCurrentScreen, selectedProduce, capturedImage, theme } = useApp();
  const isTerracotta = theme === 'terracotta';

  const accentColor = isTerracotta ? '#9e3d00' : '#012d1d';
  const greenColor = isTerracotta ? '#006d37' : '#0e6c4a';

  // ── Freshness values ──────────────────────────────────────────────────────
  const freshnessScore = selectedProduce.freshnessPercent; // 0–100 numeric
  const freshnessLevel = freshnessLevelLabel(selectedProduce.freshness);
  const fColor = freshnessColor(selectedProduce.freshness, isTerracotta);

  // ── Market / price preview ────────────────────────────────────────────────
  const market = selectedProduce.market;
  const marketAvailable = market?.status === 'AVAILABLE';
  const todayPrice = marketAvailable && market?.today_price != null
    ? `₹${market.today_price}/${selectedProduce.unit}`
    : null;
  const fairMin = selectedProduce.retailFairMin;
  const fairMax = selectedProduce.retailFairMax;
  const fairPriceText = marketAvailable && fairMin > 0 && fairMax > 0
    ? `₹${fairMin}–${fairMax}/${selectedProduce.unit}`
    : null;

  // ── Quality adjustment label ──────────────────────────────────────────────
  const qAdj = selectedProduce.qualityAdjustment;
  const qAdjLabel = selectedProduce.qualityAdjustmentLabel || 'none';
  const qAdjText = qAdj < 0
    ? `-₹${Math.abs(qAdj)} (${qAdjLabel})`
    : qAdj > 0
    ? `+₹${qAdj} (${qAdjLabel})`
    : `₹0 (${qAdjLabel})`;

  return (
    <div className="min-h-screen bg-[#fbf9f5] flex flex-col pb-[110px] antialiased">
      <Header title="Scan Result" showBack onBack={() => setCurrentScreen('scan')} />

      <main className="flex-1 max-w-md mx-auto w-full px-5 py-4 flex flex-col gap-4">

        {/* ── Result Card ── */}
        <div
          id="quality-result-card"
          className="w-full bg-white rounded-[24px] shadow-[0px_4px_20px_rgba(211,84,0,0.08)] p-6 flex flex-col items-center border border-[#e4e2de]/60"
        >
          {/* Thumbnail */}
          <div className="w-44 h-44 rounded-[20px] overflow-hidden mb-5 relative shadow-inner bg-[#f5f3ef]">
            <img
              src={capturedImage || selectedProduce.image}
              alt={selectedProduce.name}
              className="w-full h-full object-cover"
            />
            {/* Match Badge */}
            <div
              id="match-score-badge"
              className="absolute top-2.5 right-2.5 font-semibold text-[12px] px-2.5 py-1 rounded-full flex items-center gap-1 shadow-sm bg-[#7bf8a1] text-[#007239]"
            >
              <span
                className="material-symbols-outlined text-[14px]"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                check_circle
              </span>
              {selectedProduce.matchScore}% Match
            </div>
          </div>

          {/* Produce name */}
          <h2
            id="scanned-produce-title"
            className="font-display text-[30px] font-bold text-[#1b1c1a] mb-1 text-center tracking-tight"
          >
            {selectedProduce.name}
          </h2>

          {/* Quality description from Gemini/ML */}
          {selectedProduce.qualitySummary ? (
            <p
              id="quality-summary-text"
              className="text-[14px] text-[#594238] text-center mb-5 px-2 leading-relaxed"
            >
              {selectedProduce.qualitySummary}
            </p>
          ) : null}

          {/* ── Freshness Score + Level row ── */}
          <div
            id="freshness-score-row"
            className="w-full flex items-center justify-between bg-[#f5f3ef] rounded-2xl px-4 py-3 mb-4 border border-[#e4e2de]"
          >
            <div className="flex items-center gap-2">
              <span
                className="material-symbols-outlined text-[20px]"
                style={{ color: fColor, fontVariationSettings: "'FILL' 1" }}
              >
                {selectedProduce.freshness === 'fresh' ? 'eco' : selectedProduce.freshness === 'overripe' ? 'compost' : 'hourglass_empty'}
              </span>
              <div>
                <p
                  id="freshness-level-label"
                  className="text-[14px] font-bold"
                  style={{ color: fColor }}
                >
                  {freshnessLevel}
                </p>
                <p className="text-[11px] text-[#8a756b]">Freshness Level</p>
              </div>
            </div>
            <div className="text-right">
              <p
                id="freshness-score-numeric"
                className="font-display text-[28px] font-extrabold tracking-tight"
                style={{ color: fColor }}
              >
                {freshnessScore}
              </p>
              <p className="text-[11px] text-[#8a756b]">/ 100</p>
            </div>
          </div>

          {/* ── Freshness Gauge bar ── */}
          <div id="freshness-gauge" className="w-full mb-4">
            <div className="flex justify-between items-end mb-1.5 px-0.5">
              {(['fresh', 'slightly_aged', 'overripe'] as const).map((level) => (
                <span
                  key={level}
                  className="text-[11px] font-medium transition-colors duration-300"
                  style={{
                    fontWeight: selectedProduce.freshness === level ? 700 : 400,
                    color: selectedProduce.freshness === level ? fColor : '#8a756b',
                    fontSize: selectedProduce.freshness === level ? '12px' : '11px',
                  }}
                >
                  {freshnessLevelLabel(level)}
                </span>
              ))}
            </div>
            <div className="h-3 bg-[#e4e2de] rounded-full w-full relative overflow-hidden">
              <div
                className="absolute left-0 top-0 h-full rounded-full transition-all duration-700 ease-out"
                style={{
                  width: `${freshnessScore}%`,
                  backgroundColor: fColor,
                }}
              />
            </div>
            {/* Tick marks at 33% and 66% */}
            <div className="relative w-full h-1.5 mt-0.5 px-0">
              <div className="absolute left-1/3 top-0 w-px h-1.5 bg-[#c8c0b8] -ml-px" />
              <div className="absolute left-2/3 top-0 w-px h-1.5 bg-[#c8c0b8] -ml-px" />
            </div>
          </div>

          {/* ── Quality adjustment ── */}
          <div className="w-full flex items-center justify-between px-1 text-[12px] text-[#594238]">
            <span>Freshness price adjustment</span>
            <span
              className={`font-semibold ${qAdj < 0 ? 'text-[#b91c1c]' : qAdj > 0 ? 'text-[#006d37]' : 'text-[#594238]'}`}
            >
              {qAdjText}
            </span>
          </div>
        </div>

        {/* ── Compact Price Preview ── */}
        <div
          id="price-preview-card"
          className={`w-full rounded-[20px] p-4 border ${
            marketAvailable
              ? 'bg-[#e9f8ef] border-[#d8e6dc]'
              : 'bg-[#f5f3ef] border-[#e4e2de]'
          }`}
        >
          <p className="text-[11px] font-bold uppercase tracking-widest text-[#594238] mb-3">
            {marketAvailable ? 'Price Preview · Agmarknet' : 'Market Data'}
          </p>
          <div className="grid grid-cols-2 gap-3">
            {/* Today's Market Price */}
            <div className="bg-white rounded-xl p-3 flex flex-col gap-0.5 shadow-2xs">
              <p className="text-[10px] font-medium text-[#8a756b] uppercase tracking-wider">
                Today's Mandi Price
              </p>
              <p
                id="today-market-price-preview"
                className="font-display text-[18px] font-bold"
                style={{ color: marketAvailable ? accentColor : '#8a756b' }}
              >
                {todayPrice ?? 'Unavailable'}
              </p>
            </div>
            {/* Fair Price Range */}
            <div className="bg-white rounded-xl p-3 flex flex-col gap-0.5 shadow-2xs">
              <p className="text-[10px] font-medium text-[#8a756b] uppercase tracking-wider">
                Fair Price Range
              </p>
              <p
                id="fair-price-range-preview"
                className="font-display text-[18px] font-bold"
                style={{ color: marketAvailable ? greenColor : '#8a756b' }}
              >
                {fairPriceText ?? 'Unavailable'}
              </p>
            </div>
          </div>
          {!marketAvailable && (
            <p className="text-[11px] text-[#8a756b] mt-2.5 text-center">
              Market price unavailable — see full breakdown for details.
            </p>
          )}
          {marketAvailable && market?.date && (
            <p className="text-[10px] text-[#8a756b] mt-2 text-right">
              Agmarknet · {market.date}
            </p>
          )}
        </div>

        {/* ── AI Insight pill ── */}
        <div className="w-full bg-[#f5f3ef] rounded-2xl p-3.5 border border-[#e4e2de] text-xs text-[#594238] flex items-center gap-2.5">
          <span className="material-symbols-outlined text-[20px]" style={{ color: greenColor }}>
            verified
          </span>
          <span>
            {selectedProduce.analysisProvider === 'gemini'
              ? 'Analyzed with Gemini Flash.'
              : 'Analyzed with local ML fallback.'}{' '}
            {marketAvailable
              ? 'Market benchmark loaded from Agmarknet.'
              : 'Market price is currently unavailable for this location.'}
          </span>
        </div>
      </main>

      {/* ── Sticky CTA ── */}
      <div className="fixed bottom-[74px] w-full px-5 z-30 max-w-md mx-auto left-0 right-0">
        <button
          id="continue-to-price-analysis-button"
          onClick={() => setCurrentScreen('purchase_type')}
          className={`w-full text-white font-display text-[17px] font-semibold py-4 rounded-[16px] shadow-[0px_8px_24px_rgba(211,84,0,0.18)] active:scale-[0.98] transition-all flex justify-center items-center gap-2 hover:opacity-95 ${
            isTerracotta ? 'bg-[#9e3d00]' : 'bg-[#012d1d]'
          }`}
        >
          Continue to Price Analysis
          <span className="material-symbols-outlined text-[20px]">arrow_forward</span>
        </button>
      </div>
    </div>
  );
};
