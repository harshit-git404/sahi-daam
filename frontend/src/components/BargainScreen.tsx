import React from 'react';
import { useApp } from '../context/AppContext';
import { Header } from './Header';

export const BargainScreen: React.FC = () => {
  const {
    setCurrentScreen,
    selectedProduce,
    vendorAskingPrice,
    setVendorAskingPrice,
    recordPurchase,
    setIsAudioModalOpen,
    theme
  } = useApp();

  const isTerracotta = theme === 'terracotta';

  // Dynamic calculations
  const fairAvg = Math.round((selectedProduce.retailFairMin + selectedProduce.retailFairMax) / 2);
  
  // Calculate suggested counter offer: slightly above wholesale, fair middle
  const targetOffer = Math.max(
    selectedProduce.wholesalePrice + 5,
    Math.round(fairAvg + (vendorAskingPrice > fairAvg ? (fairAvg * 0.05) : 0))
  );

  // Overpriced percentage calculation
  const overpricePct = Math.round(((vendorAskingPrice - fairAvg) / fairAvg) * 100);

  const handleDecrease = () => {
    setVendorAskingPrice(prev => Math.max(selectedProduce.wholesalePrice, prev - 5));
    if (navigator.vibrate) navigator.vibrate(20);
  };

  const handleIncrease = () => {
    setVendorAskingPrice(prev => Math.min(150, prev + 5));
    if (navigator.vibrate) navigator.vibrate(20);
  };

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setVendorAskingPrice(Number(e.target.value));
  };

  const handleBuy = () => {
    recordPurchase(targetOffer);
    setCurrentScreen('history');
  };

  // Slider percentage calculation (min 15, max 80 for scale)
  const minSlider = 15;
  const maxSlider = 80;
  const sliderPercent = Math.min(
    100,
    Math.max(0, ((vendorAskingPrice - minSlider) / (maxSlider - minSlider)) * 100)
  );

  return (
    <div className="min-h-screen bg-[#fbf9f5] flex flex-col pb-10 antialiased relative overflow-hidden">
      {/* TopAppBar */}
      <Header
        title={`${selectedProduce.name} Bargain`}
        showBack
        onBack={() => setCurrentScreen('price_breakdown')}
      />

      {/* Decorative Warm Backdrop Glow */}
      <div
        className={`absolute top-10 right-[-15%] w-72 h-72 rounded-full blur-[90px] opacity-35 pointer-events-none ${
          isTerracotta ? 'bg-[#ffb595]' : 'bg-[#a5d0b9]'
        }`}
      />

      {/* Main Content */}
      <main className="flex-1 max-w-md mx-auto w-full px-5 py-4 flex flex-col gap-4 relative z-10">
        {/* Suggestion Card (Glassmorphism) */}
        <section
          id="market-analysis-suggestion-card"
          className="glass-card rounded-[24px] p-6 shadow-[0px_4px_24px_rgba(211,84,0,0.06)] relative overflow-hidden border border-[#e4e2de]"
        >
          <div className="absolute top-4 right-4">
            <span
              className={`material-symbols-outlined text-[32px] ${
                isTerracotta ? 'text-[#006d37]' : 'text-[#0e6c4a]'
              }`}
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              eco
            </span>
          </div>

          <p className="text-[12px] font-bold text-[#594238] mb-1.5 uppercase tracking-wider">
            MARKET ANALYSIS
          </p>

          <h2
            id="vendor-asking-heading"
            className="font-display text-[24px] font-bold text-[#1b1c1a] mb-1 tracking-tight"
          >
            Vendor asking ₹{vendorAskingPrice}?
          </h2>

          <div className="flex items-baseline gap-2.5 mt-3 mb-1.5">
            <span className="text-[15px] font-medium text-[#594238]">
              Try offering
            </span>
            <span
              id="suggested-offer-price-value"
              className={`font-display text-[36px] font-extrabold tracking-tight ${
                isTerracotta ? 'text-[#9e3d00]' : 'text-[#012d1d]'
              }`}
            >
              ₹{targetOffer}
            </span>
          </div>

          {/* Overprice badge or Fair badge */}
          {overpricePct > 5 ? (
            <div className="inline-flex items-center gap-1.5 bg-[#ffdad6] text-[#93000a] px-3.5 py-1 rounded-full mt-2 font-semibold text-[12px]">
              <span className="material-symbols-outlined text-[16px]">trending_up</span>
              <span>Overpriced by {overpricePct}%</span>
            </div>
          ) : (
            <div className="inline-flex items-center gap-1.5 bg-[#7bf8a1]/60 text-[#006d37] px-3.5 py-1 rounded-full mt-2 font-semibold text-[12px]">
              <span className="material-symbols-outlined text-[16px]">check_circle</span>
              <span>Near Fair Price Deal</span>
            </div>
          )}
        </section>

        {/* Interactive Stepper & Slider Card */}
        <section
          id="vendor-price-stepper-card"
          className="bg-white rounded-[24px] p-6 shadow-[0px_4px_20px_rgba(211,84,0,0.04)] border border-[#e4e2de]/70 flex flex-col gap-4"
        >
          <label className="font-semibold text-[14px] text-[#1b1c1a] text-center block">
            What is the vendor asking?
          </label>

          {/* Stepper controls */}
          <div className="flex items-center justify-between gap-4">
            <button
              id="decrease-price-btn"
              aria-label="Decrease price"
              onClick={handleDecrease}
              className="w-14 h-14 rounded-full bg-[#f5f3ef] flex items-center justify-center text-[#1b1c1a] hover:bg-[#eae8e4] active:scale-90 transition-all shadow-xs border border-[#e0c0b2]/40"
            >
              <span className="material-symbols-outlined text-[24px]">remove</span>
            </button>

            <div className="flex-1 relative text-center">
              <div className="flex items-center justify-center">
                <span className="text-[24px] font-bold text-[#594238] mr-1">₹</span>
                <input
                  id="vendor-price-input"
                  aria-label="Vendor asking price"
                  type="number"
                  value={vendorAskingPrice}
                  onChange={(e) => setVendorAskingPrice(Math.max(1, Number(e.target.value)))}
                  className="w-24 bg-transparent border-none text-center font-display text-[36px] font-extrabold text-[#1b1c1a] focus:ring-0 focus:outline-none p-0"
                />
              </div>
              {/* Visual active underline */}
              <div className="w-full h-[2px] bg-[#e4e2de] rounded-full mt-1 relative overflow-hidden">
                <div
                  className={`h-full mx-auto w-2/3 rounded-full transition-all duration-300 ${
                    isTerracotta ? 'bg-[#9e3d00]' : 'bg-[#012d1d]'
                  }`}
                />
              </div>
            </div>

            <button
              id="increase-price-btn"
              aria-label="Increase price"
              onClick={handleIncrease}
              className="w-14 h-14 rounded-full bg-[#f5f3ef] flex items-center justify-center text-[#1b1c1a] hover:bg-[#eae8e4] active:scale-90 transition-all shadow-xs border border-[#e0c0b2]/40"
            >
              <span className="material-symbols-outlined text-[24px]">add</span>
            </button>
          </div>

          {/* Tactile Range Slider */}
          <div className="mt-2 px-1">
            <div className="relative flex items-center">
              <input
                id="vendor-price-slider"
                aria-label="Price range slider"
                type="range"
                min={minSlider}
                max={maxSlider}
                value={vendorAskingPrice}
                onChange={handleSliderChange}
                className="w-full h-2 bg-[#e4e2de] rounded-lg appearance-none cursor-pointer accent-[#9e3d00]"
              />
            </div>

            <div className="flex justify-between mt-2 text-[12px] font-medium text-[#594238]">
              <span>Avg: ₹{fairAvg}</span>
              <span className={overpricePct > 15 ? 'text-[#ba1a1a] font-semibold' : 'text-[#006d37]'}>
                {overpricePct > 15 ? 'High Quote' : 'Fair Quote'}
              </span>
            </div>
          </div>
        </section>

        {/* Suggested Verbal Bargaining Counter */}
        <section className="bg-[#f5f3ef] rounded-2xl p-4 border border-[#e4e2de] shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[12px] font-bold uppercase tracking-wider text-[#594238] flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px] text-[#9e3d00]">record_voice_over</span>
              Suggested Dialogue
            </span>
            <span className="text-[11px] text-[#594238]">Hindi & English</span>
          </div>

          <div className="space-y-2">
            {selectedProduce.bargainPhrases.slice(0, 2).map((phrase, idx) => (
              <div
                key={idx}
                className="p-2.5 rounded-xl bg-white border border-[#e4e2de]/80 text-xs shadow-2xs"
              >
                <p className="font-semibold text-[#1b1c1a]">"{phrase.hindi}"</p>
                <p className="text-[11px] text-[#594238] italic mt-0.5">"{phrase.english}"</p>
              </div>
            ))}
          </div>
        </section>

        {/* Action Area */}
        <div className="flex flex-col gap-3 mt-2">
          {/* Mic Assistant Button */}
          <button
            id="start-haggle-assistant-btn"
            onClick={() => setIsAudioModalOpen(true)}
            className="relative w-full bg-[#efeeea] border border-[#e4e2de] rounded-2xl py-3.5 px-4 flex items-center justify-center gap-3 overflow-hidden hover:bg-[#eae8e4] active:scale-[0.98] transition-all shadow-xs group"
          >
            <div className="absolute top-2 right-3 bg-[#ffddb9] text-[#663e00] px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider">
              COMING SOON
            </div>

            <div
              className={`w-11 h-11 rounded-full flex items-center justify-center text-white shadow-md group-hover:scale-105 transition-transform ${
                isTerracotta ? 'bg-[#c64f00]' : 'bg-[#1b4332]'
              }`}
            >
              <span
                className="material-symbols-outlined text-[22px]"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                mic
              </span>
            </div>

            <span className="font-display font-semibold text-[15px] text-[#1b1c1a]">
              Start Haggle Assistant
            </span>
          </button>

          {/* Primary Purchase Confirmation CTA */}
          <button
            id="i-bought-it-btn"
            onClick={handleBuy}
            className={`w-full text-white font-display text-[17px] font-bold rounded-2xl py-4 shadow-[0px_8px_24px_rgba(211,84,0,0.22)] active:scale-[0.98] transition-all flex items-center justify-center gap-2 hover:opacity-95 ${
              isTerracotta ? 'bg-[#9e3d00]' : 'bg-[#012d1d]'
            }`}
          >
            <span
              className="material-symbols-outlined text-[22px]"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              check_circle
            </span>
            I Bought It at ₹{targetOffer}
          </button>

          <p className="text-center text-[12px] text-[#594238] font-normal">
            Saves to your purchase history
          </p>
        </div>
      </main>
    </div>
  );
};
