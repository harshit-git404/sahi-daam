import React from 'react';
import { useApp } from '../context/AppContext';
import { Header } from './Header';
import { formatRupees, formatRupeesPerUnit } from '../services/format';

export const PriceBreakdownScreen: React.FC = () => {
  const { setCurrentScreen, selectedProduce, selectedLocation, theme } = useApp();
  const isTerracotta = theme === 'terracotta';

  return (
    <div className="min-h-screen bg-[#fbf9f5] flex flex-col pb-[100px] antialiased">
      {/* TopAppBar */}
      <Header
        title={selectedProduce.name === 'Tomato' ? 'Tomatoes' : selectedProduce.name}
        showBack
        onBack={() => setCurrentScreen('quality_result')}
      />

      {/* Main Content */}
      <main className="flex-1 max-w-md mx-auto w-full px-5 py-4 flex flex-col gap-4">
        {/* Breadcrumb Context Tag */}
        <div
          onClick={() => setCurrentScreen('quality_result')}
          className="flex items-center gap-1.5 text-[#594238] cursor-pointer hover:opacity-80 active:opacity-60 transition-opacity"
        >
          <span
            className={`material-symbols-outlined text-[20px] ${
              isTerracotta ? 'text-[#9e3d00]' : 'text-[#012d1d]'
            }`}
          >
            arrow_back
          </span>
          <span className="font-semibold text-[14px] text-[#1b1c1a]">
            {selectedProduce.name === 'Tomato' ? 'Tomatoes' : selectedProduce.name}
          </span>
        </div>

        {/* Big Hero Number Card */}
        <section
          id="hero-price-range-card"
          className="bg-white rounded-[24px] p-6 shadow-[0px_4px_20px_rgba(211,84,0,0.08)] text-center relative overflow-hidden border border-[#e4e2de]/60"
        >
          {/* Decorative blur circle in top right */}
          <div
            className={`absolute -top-10 -right-10 w-32 h-32 rounded-full opacity-20 blur-2xl pointer-events-none ${
              isTerracotta ? 'bg-[#ffb595]' : 'bg-[#a5d0b9]'
            }`}
          />

          <h2 className="text-[13px] font-bold text-[#594238] mb-2 uppercase tracking-widest">
            WHAT SHOULD IT COST?
          </h2>

          <div
            id="fair-price-range-value"
            className={`font-display text-[36px] font-extrabold mb-1 tracking-tight ${
              isTerracotta ? 'text-[#9e3d00]' : 'text-[#012d1d]'
            }`}
          >
            {formatRupees(selectedProduce.retailFairMin)}-{formatRupeesPerUnit(selectedProduce.retailFairMax, selectedProduce.unit)}
          </div>

          <div
            className={`flex items-center justify-center gap-1.5 text-[13px] font-semibold ${
              isTerracotta ? 'text-[#006d37]' : 'text-[#0e6c4a]'
            }`}
          >
            <span
              className="material-symbols-outlined text-[18px]"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              energy_savings_leaf
            </span>
            <span>Estimated Fair Range</span>
          </div>
        </section>

        {/* Receipt Style Breakdown */}
        <section
          id="receipt-price-breakdown-card"
          className="bg-[#efeeea] rounded-[24px] p-6 relative border border-[#e0c0b2]/30 shadow-xs"
        >
          {/* Scalloped edge */}
          <div
            className="absolute -top-2 left-0 w-full h-4 bg-[#efeeea]"
            style={{
              maskImage: 'radial-gradient(circle at 10px 0, transparent 8px, black 9px)',
              WebkitMaskImage: 'radial-gradient(circle at 10px 0, transparent 8px, black 9px)',
              maskSize: '20px 20px',
              WebkitMaskSize: '20px 20px',
              maskRepeat: 'repeat-x',
              WebkitMaskRepeat: 'repeat-x'
            }}
          />

          <h3 className="font-display text-[18px] font-bold text-[#1b1c1a] mb-5 border-b border-[#c1c8c2]/50 pb-3">
            How We Got This
          </h3>

          <ul className="flex flex-col gap-3.5">
            {/* Wholesale Price */}
            <li className="flex justify-between items-start border-b border-[#e5e0d8] pb-3">
              <div className="flex flex-col">
                <span className="text-[15px] font-medium text-[#1b1c1a]">
                  Local wholesale benchmark
                </span>
              </div>
              <span className="font-semibold text-[15px] text-[#1b1c1a]">
                {formatRupeesPerUnit(selectedProduce.wholesalePrice, selectedProduce.unit)}
              </span>
            </li>

            {/* Local Markup */}
            <li className="flex justify-between items-start border-b border-[#e5e0d8] pb-3">
              <div className="flex flex-col">
                <span className="text-[15px] font-medium text-[#1b1c1a]">
                  Typical retail markup
                </span>
                <span className="text-[12px] text-[#594238]">
                  (+{selectedProduce.markupMinPercent}-{selectedProduce.markupMaxPercent}%)
                </span>
              </div>
              <span className="font-semibold text-[15px] text-[#1b1c1a]">
                +{formatRupees(Math.round(selectedProduce.wholesalePrice * (selectedProduce.markupMinPercent / 100)))}-{formatRupees(Math.round(selectedProduce.wholesalePrice * (selectedProduce.markupMaxPercent / 100)))}
              </span>
            </li>

            {/* Quality Adjustment */}
            <li className="flex justify-between items-start pb-1">
              <div className="flex flex-col">
                <span className="text-[15px] font-medium text-[#1b1c1a]">
                  Quality adjustment
                </span>
                <span className="text-[12px] text-[#594238]">
                  {selectedProduce.qualityAdjustment === 0 ? '(No quality adjustment applied)' : `(${selectedProduce.qualityAdjustmentLabel})`}
                </span>
              </div>
              <span
                className={`font-semibold text-[15px] ${
                  isTerracotta ? 'text-[#9e3d00]' : 'text-[#012d1d]'
                }`}
              >
                {selectedProduce.qualityAdjustment < 0 ? `-${formatRupees(Math.abs(selectedProduce.qualityAdjustment))}` : selectedProduce.qualityAdjustment > 0 ? `+${formatRupees(selectedProduce.qualityAdjustment)}` : formatRupees(0)}
              </span>
            </li>
          </ul>

          {/* Status Confidence Indicator / Data Source */}
          <div className="mt-5 pt-4 border-t border-[#c1c8c2]/50 flex flex-col gap-2.5">
            <h4 className="text-[11px] font-bold text-[#594238] uppercase tracking-widest flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[15px]">database</span>
              Data Source
            </h4>
            <div className="flex flex-col gap-2">
              <div className="flex items-start justify-between">
                <span className="text-[13px] font-medium text-[#1b1c1a]">Market Reference</span>
                <span className="text-[13px] text-[#594238] font-medium text-right max-w-[60%] leading-tight">
                  {selectedProduce.priceSource ? selectedProduce.priceSource.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') : 'Local Data'}
                  <br/>
                  <span className="text-[11.5px] opacity-80">{selectedLocation.mandiName}</span>
                </span>
              </div>
              
              <div className="flex items-start justify-between">
                <span className="text-[13px] font-medium text-[#1b1c1a]">Data Confidence</span>
                <div className="flex flex-col items-end gap-1">
                  <div className={`flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold inline-block ${
                    selectedProduce.dataConfidence === 'High' ? 'bg-[#7bf8a1]/20 text-[#006d37]' :
                    selectedProduce.dataConfidence === 'Medium' ? 'bg-[#ffb595]/20 text-[#9e3d00]' :
                    'bg-[#a46700]/15 text-[#835100]'
                  }`}>
                    {selectedProduce.dataConfidence}
                  </div>
                  <span className="text-[11px] text-[#594238] italic text-right leading-tight max-w-[150px]">
                    {selectedProduce.dataConfidence === 'High' ? 'Based on highly localized, recent data.' :
                     selectedProduce.dataConfidence === 'Medium' ? 'Based on available regional data.' :
                     'Limited data — use as a rough estimate.'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── MARKET TODAY ── */}
        {selectedProduce.marketContext && (
          <section id="market-context-card" className="bg-white rounded-[24px] p-5 border border-[#e4e2de] shadow-xs">
            <h3 className="text-[11px] font-bold text-[#594238] mb-3 uppercase tracking-widest flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[15px]">trending_up</span>
              Market Today
            </h3>

            {selectedProduce.marketContext.trend === 'INSUFFICIENT_DATA' ? (
              <div className="flex items-start gap-2">
                <span className="material-symbols-outlined text-[18px] text-[#594238] mt-0.5 flex-shrink-0">info</span>
                <p className="text-[13px] text-[#594238] leading-snug">
                  Not enough recent market history to determine a price trend. Using today's single observation.
                </p>
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {/* Main price + trend indicator */}
                <div className="flex items-end justify-between">
                  <div>
                    <p className="text-[28px] font-extrabold text-[#1b1c1a] font-display leading-none">
                      {formatRupees(selectedProduce.marketContext.current_price)}
                      <span className="text-[14px] font-medium text-[#594238] ml-1">/{selectedProduce.unit}</span>
                    </p>
                    <p className="text-[12px] text-[#594238] mt-0.5">Today's local wholesale reference</p>
                  </div>
                  <div className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-[13px] font-bold ${
                    selectedProduce.marketContext.trend === 'UP' 
                      ? 'bg-[#fef2f2] text-[#b91c1c]' 
                      : selectedProduce.marketContext.trend === 'DOWN' 
                        ? 'bg-[#f0fdf4] text-[#15803d]'
                        : 'bg-[#f5f3ef] text-[#594238]'
                  }`}>
                    <span className="material-symbols-outlined text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                      {selectedProduce.marketContext.trend === 'UP' ? 'trending_up' : selectedProduce.marketContext.trend === 'DOWN' ? 'trending_down' : 'trending_flat'}
                    </span>
                    {selectedProduce.marketContext.change_pct > 0 ? '+' : ''}{selectedProduce.marketContext.change_pct}% vs avg
                  </div>
                </div>

                {/* Details grid */}
                <div className="grid grid-cols-2 gap-2 mt-1">
                  <div className="bg-[#f5f3ef] rounded-xl p-3">
                    <p className="text-[10px] font-bold text-[#594238] uppercase tracking-wider mb-0.5">Recent Average</p>
                    <p className="text-[16px] font-bold text-[#1b1c1a]">{formatRupeesPerUnit(selectedProduce.marketContext.recent_average, selectedProduce.unit)}</p>
                  </div>
                  <div className="bg-[#f5f3ef] rounded-xl p-3">
                    <p className="text-[10px] font-bold text-[#594238] uppercase tracking-wider mb-0.5">History</p>
                    <p className="text-[16px] font-bold text-[#1b1c1a]">{selectedProduce.marketContext.history_days} days</p>
                    <p className="text-[10px] text-[#594238]">{selectedProduce.marketContext.observation_count} observations</p>
                  </div>
                </div>

                <p className="text-[11px] text-[#594238] text-center">
                  Trend confidence: {selectedProduce.marketContext.confidence}
                </p>
              </div>
            )}
          </section>
        )}

        {/* Location Context */}
        <div className="flex items-center justify-center gap-1.5 text-[#594238] text-[13px] font-medium my-1">
          <span className="material-symbols-outlined text-[18px] text-[#9e3d00]">
            location_on
          </span>
          <span>{selectedLocation.name} · Today</span>
        </div>

        {/* Primary Action Button */}
        <button
          id="start-haggling-button"
          onClick={() => setCurrentScreen('bargain')}
          className={`w-full text-white font-display text-[16px] font-semibold py-4 rounded-2xl shadow-[0px_8px_24px_rgba(211,84,0,0.18)] active:scale-[0.98] transition-all flex justify-center items-center gap-2 hover:opacity-95 mt-1 ${
            isTerracotta ? 'bg-[#9e3d00]' : 'bg-[#012d1d]'
          }`}
        >
          <span className="material-symbols-outlined text-[20px]">forum</span>
          Start Haggling
        </button>

        {/* Secondary Action Button */}
        <button
          onClick={() => setCurrentScreen('supermarket')}
          className={`w-full font-display text-[15px] font-semibold py-3.5 rounded-2xl border active:scale-[0.98] transition-all flex justify-center items-center gap-2 hover:bg-gray-50 mt-1 mb-4 ${
            isTerracotta ? 'text-[#9e3d00] border-[#9e3d00]/30' : 'text-[#012d1d] border-[#012d1d]/30'
          }`}
        >
          <span className="material-symbols-outlined text-[18px]">storefront</span>
          Compare with quick-commerce
        </button>
      </main>
    </div>
  );
};
