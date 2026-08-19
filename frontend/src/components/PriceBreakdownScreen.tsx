import React from 'react';
import { useApp } from '../context/AppContext';
import { Header } from './Header';

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
            FAIR PRICE RANGE
          </h2>

          <div
            id="fair-price-range-value"
            className={`font-display text-[36px] font-extrabold mb-1 tracking-tight ${
              isTerracotta ? 'text-[#9e3d00]' : 'text-[#012d1d]'
            }`}
          >
            ₹{selectedProduce.retailFairMin}–{selectedProduce.retailFairMax}/{selectedProduce.unit}
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
            <span>Verified Fair Deal</span>
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
            Price Breakdown
          </h3>

          <ul className="flex flex-col gap-3.5">
            {/* Wholesale Price */}
            <li className="flex justify-between items-start border-b border-[#e5e0d8] pb-3">
              <div className="flex flex-col">
                <span className="text-[15px] font-medium text-[#1b1c1a]">
                  Today's wholesale price
                </span>
                <span className="text-[12px] text-[#594238]">
                  {selectedLocation.mandiName}
                </span>
              </div>
              <span className="font-semibold text-[15px] text-[#1b1c1a]">
                ₹{selectedProduce.wholesalePrice}/{selectedProduce.unit}
              </span>
            </li>

            {/* Local Markup */}
            <li className="flex justify-between items-start border-b border-[#e5e0d8] pb-3">
              <div className="flex flex-col">
                <span className="text-[15px] font-medium text-[#1b1c1a]">
                  Typical local markup
                </span>
                <span className="text-[12px] text-[#594238]">
                  (+{selectedProduce.markupMinPercent}-{selectedProduce.markupMaxPercent}%)
                </span>
              </div>
              <span className="font-semibold text-[15px] text-[#1b1c1a]">
                ₹29–32/{selectedProduce.unit}
              </span>
            </li>

            {/* Quality Adjustment */}
            <li className="flex justify-between items-start pb-1">
              <div className="flex flex-col">
                <span className="text-[15px] font-medium text-[#1b1c1a]">
                  Quality adjustment
                </span>
                <span className="text-[12px] text-[#594238]">
                  ({selectedProduce.qualityAdjustmentLabel})
                </span>
              </div>
              <span
                className={`font-semibold text-[15px] ${
                  isTerracotta ? 'text-[#9e3d00]' : 'text-[#012d1d]'
                }`}
              >
                -₹1 to -2
              </span>
            </li>
          </ul>

          {/* Status Confidence Indicator */}
          <div className="mt-5 pt-3.5 border-t border-[#c1c8c2]/50 flex items-center justify-between">
            <div className="flex items-center gap-1.5 bg-[#a46700]/15 text-[#835100] px-3 py-1.5 rounded-full text-[12px] font-semibold">
              <span className="material-symbols-outlined text-[16px]">info</span>
              Data confidence: {selectedProduce.dataConfidence}
            </div>
            <span className="text-[11px] text-[#594238]">Updated 6:30 AM</span>
          </div>
        </section>

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
      </main>
    </div>
  );
};
