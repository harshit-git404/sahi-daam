import React from 'react';
import { useApp } from '../context/AppContext';
import { Header } from './Header';

export const QualityResultScreen: React.FC = () => {
  const { setCurrentScreen, selectedProduce, capturedImage, theme } = useApp();
  const isTerracotta = theme === 'terracotta';

  return (
    <div className="min-h-screen bg-[#fbf9f5] flex flex-col pb-[100px] antialiased">
      {/* TopAppBar */}
      <Header title="Sahi Daam" showBack onBack={() => setCurrentScreen('scan')} />

      {/* Main Content */}
      <main className="flex-1 max-w-md mx-auto w-full px-5 py-4 flex flex-col items-center">
        {/* Result Card */}
        <div
          id="quality-result-card"
          className="w-full bg-white rounded-[24px] shadow-[0px_4px_20px_rgba(211,84,0,0.08)] p-6 flex flex-col items-center border border-[#e4e2de]/60 mt-1"
        >
          {/* Thumbnail Image */}
          <div className="w-48 h-48 rounded-[24px] overflow-hidden mb-6 relative shadow-inner bg-[#f5f3ef]">
            <img
              src={capturedImage || selectedProduce.image}
              alt={selectedProduce.name}
              className="w-full h-full object-cover"
            />
            {/* Match Badge */}
            <div
              id="match-score-badge"
              className={`absolute top-3 right-3 font-medium text-[12px] px-2.5 py-1 rounded-full flex items-center gap-1 shadow-sm ${
                isTerracotta
                  ? 'bg-[#7bf8a1] text-[#007239]'
                  : 'bg-[#a0f4c8] text-[#19724f]'
              }`}
            >
              <span
                className="material-symbols-outlined text-[16px]"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                check_circle
              </span>
              {selectedProduce.matchScore}% Match
            </div>
          </div>

          {/* Subject Text */}
          <h2
            id="scanned-produce-title"
            className="font-display text-[32px] font-bold text-[#1b1c1a] mb-2 text-center tracking-tight"
          >
            {selectedProduce.name}
          </h2>

          {/* Description */}
          <p
            id="quality-summary-text"
            className="text-[16px] text-[#594238] text-center mb-8 px-2 leading-relaxed"
          >
            {selectedProduce.qualitySummary}
          </p>

          {/* Freshness Gauge */}
          <div id="freshness-gauge" className="w-full mb-3">
            <div className="flex justify-between items-end mb-2 px-1">
              <span
                className={`transition-colors duration-300 ${
                  selectedProduce.freshness === 'fresh'
                    ? `font-semibold text-[14px] ${isTerracotta ? 'text-[#006d37]' : 'text-[#0e6c4a]'}`
                    : 'text-[12px] font-medium text-[#594238]'
                }`}
              >
                Fresh
              </span>
              <span
                className={`transition-colors duration-300 ${
                  selectedProduce.freshness === 'slightly_aged'
                    ? `font-semibold text-[14px] ${isTerracotta ? 'text-[#9e3d00]' : 'text-[#0e6c4a]'}`
                    : 'text-[12px] font-medium text-[#594238]'
                }`}
              >
                Slightly Aged
              </span>
              <span
                className={`transition-colors duration-300 ${
                  selectedProduce.freshness === 'overripe'
                    ? `font-semibold text-[14px] ${isTerracotta ? 'text-[#9e3d00]' : 'text-[#0e6c4a]'}`
                    : 'text-[12px] font-medium text-[#594238]'
                }`}
              >
                Overripe
              </span>
            </div>

            {/* Gauge Track */}
            <div className="h-4 bg-[#e4e2de] rounded-full w-full relative overflow-hidden">
              {/* Progress Bar (Active segment) */}
              <div
                className={`absolute left-0 top-0 h-full rounded-full transition-all duration-500 ease-in-out ${
                  isTerracotta ? 'bg-[#006d37]' : 'bg-[#0e6c4a]'
                }`}
                style={{ width: `${selectedProduce.freshnessPercent}%` }}
              />
            </div>

            {/* Markers */}
            <div className="relative w-full h-2 mt-1 px-1">
              <div className="absolute left-1/3 top-0 w-1 h-2 bg-[#e0c0b2] -ml-[2px] rounded-full" />
              <div className="absolute left-2/3 top-0 w-1 h-2 bg-[#e0c0b2] -ml-[2px] rounded-full" />
            </div>
          </div>
        </div>

        {/* AI Insight Pill */}
        <div className="w-full mt-4 bg-[#f5f3ef] rounded-2xl p-3.5 border border-[#e4e2de] text-xs text-[#594238] flex items-center gap-2.5">
          <span className="material-symbols-outlined text-[20px] text-[#006d37]">
            verified
          </span>
          <span>
            {selectedProduce.analysisProvider === 'gemini' ? 'Analyzed with Gemini Flash.' : 'Analyzed with local fallback models.'}{' '}
            {selectedProduce.marketStatus === 'AVAILABLE' ? 'Price benchmark loaded from the local market data.' : 'Market price is currently unavailable.'}
          </span>
        </div>
      </main>

      {/* Sticky Bottom Action Area */}
      <div className="fixed bottom-[74px] w-full px-5 z-30 max-w-md mx-auto left-0 right-0">
        <button
          id="see-fair-price-button"
          onClick={() => setCurrentScreen('purchase_type')}
          className={`w-full text-white font-display text-[18px] font-semibold py-4 rounded-[16px] shadow-[0px_8px_24px_rgba(211,84,0,0.18)] active:scale-[0.98] transition-all flex justify-center items-center gap-2 hover:opacity-95 ${
            isTerracotta ? 'bg-[#9e3d00]' : 'bg-[#012d1d]'
          }`}
        >
          See Fair Price
          <span className="material-symbols-outlined text-[20px]">arrow_forward</span>
        </button>
      </div>
    </div>
  );
};
