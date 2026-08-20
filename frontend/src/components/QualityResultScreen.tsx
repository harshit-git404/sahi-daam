import React from 'react';
import { useApp } from '../context/AppContext';
import { Header } from './Header';
import { getQualityTip } from '../data/qualityTips';

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

          {/* Subject Text & Header */}
          <div className="w-full text-left mb-2 px-1">
            <h3 className="text-[11px] font-bold text-[#594238] mb-1 uppercase tracking-widest">
              What Did We Find?
            </h3>
            <h2
              id="scanned-produce-title"
              className="font-display text-[32px] font-bold text-[#1b1c1a] tracking-tight leading-tight"
            >
              {selectedProduce.name}
            </h2>
          </div>

          {/* Freshness Stats */}
          <div className="w-full flex items-center justify-between px-4 mb-4 bg-[#f5f3ef] rounded-xl p-3 border border-[#e4e2de]/60">
             <div className="flex flex-col">
               <span className="text-[11px] font-bold text-[#594238] uppercase tracking-wider">Freshness</span>
               <span className="font-display text-[24px] font-extrabold text-[#1b1c1a]">{selectedProduce.freshnessPercent}%</span>
             </div>
             <div className="w-[1px] h-10 bg-[#e4e2de]"></div>
             <div className="flex flex-col text-right">
               <span className="text-[11px] font-bold text-[#594238] uppercase tracking-wider">Label</span>
               <span className={`font-display text-[20px] font-bold ${
                 selectedProduce.freshness === 'fresh' ? (isTerracotta ? 'text-[#006d37]' : 'text-[#0e6c4a]') :
                 selectedProduce.freshness === 'slightly_aged' ? 'text-[#9e3d00]' : 'text-[#806b00]'
               }`}>
                 {selectedProduce.freshness === 'fresh' ? 'Fresh' : selectedProduce.freshness === 'slightly_aged' ? 'Slightly Aged' : 'Overripe'}
               </span>
             </div>
          </div>

          {/* Concise Interpretation */}
          <div className="w-full mb-6 px-1">
            <p
              id="quality-summary-text"
              className="text-[15px] font-medium text-[#1b1c1a] leading-relaxed border-l-[3px] border-[#e0c0b2] pl-3 py-0.5"
            >
              {selectedProduce.qualitySummary}
            </p>
          </div>

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
          
          {/* Best Used For Tip */}
          {getQualityTip(selectedProduce.id, selectedProduce.freshness) && (
            <div className="w-full bg-[#fdfaf5] rounded-xl p-3 border border-[#e4e2de] text-[13px] text-[#594238] flex items-start gap-2.5 mt-1">
              <span className={`material-symbols-outlined text-[18px] mt-0.5 ${isTerracotta ? 'text-[#9e3d00]' : 'text-[#012d1d]'}`}>
                lightbulb
              </span>
              <div>
                <span className="font-semibold block mb-0.5 text-[#1b1c1a]">Best used for:</span>
                <span>{getQualityTip(selectedProduce.id, selectedProduce.freshness)}</span>
              </div>
            </div>
          )}
        </div>

        {/* AI Insight Pill */}
        <div className="w-full mt-4 bg-[#f5f3ef] rounded-2xl p-3.5 border border-[#e4e2de] text-xs text-[#594238] flex items-center gap-2.5">
          <span className="material-symbols-outlined text-[20px] text-[#006d37]">
            verified
          </span>
          <span>
            Quality verified via Visual AI. Price benchmark adjusted for local Mandi rate.
          </span>
        </div>
      </main>

      {/* Sticky Bottom Action Area */}
      <div className="fixed bottom-[74px] w-full px-5 z-30 max-w-md mx-auto left-0 right-0">
        <button
          id="see-fair-price-button"
          onClick={() => setCurrentScreen('price_breakdown')}
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
