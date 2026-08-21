import React, { useEffect, useRef } from 'react';
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
    fetchHaggle,
    haggleResult,
    isHaggling,
    theme,
  } = useApp();

  const isTerracotta = theme === 'terracotta';
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);


  // Re-fetch haggle when vendor asking price changes (debounced 600ms)
  // Only triggers when the user has entered a price > 0
  const handleAskingPriceChange = (newPrice: number) => {
    setVendorAskingPrice(newPrice);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (newPrice > 0) {
      debounceRef.current = setTimeout(() => {
        fetchHaggle(newPrice);
      }, 600);
    }
  };

  // ------------------------------------------------------------------
  // Display values — prefer backend result; fall back to local calc
  // ------------------------------------------------------------------
  const fairAvg = selectedProduce.retailFairMin > 0 && selectedProduce.retailFairMax > 0
    ? Math.round((selectedProduce.retailFairMin + selectedProduce.retailFairMax) / 2)
    : 0;
  // Only show suggested price after user has entered a price and haggle ran
  const targetOffer = vendorAskingPrice > 0
    ? (haggleResult?.suggested_price ?? selectedProduce.suggestedOfferPrice)
    : null;
  const priceEntered = vendorAskingPrice > 0;

  // Overpriced % — local display calc (not authoritative; haggle verdict is authoritative)
  const overpricePct =
    fairAvg > 0 ? Math.round(((vendorAskingPrice - fairAvg) / fairAvg) * 100) : 0;

  // Haggle verdict from backend
  const verdict = haggleResult?.verdict ?? null;
  const verdictColor =
    verdict === 'HIGH'
      ? 'bg-[#ffdad6] text-[#93000a]'
      : verdict === 'FAIR'
      ? 'bg-[#7bf8a1]/60 text-[#006d37]'
      : verdict === 'LOW'
      ? 'bg-[#e9f8ef] text-[#006d37]'
      : null;
  const verdictLabel =
    verdict === 'HIGH'
      ? `Overpriced by ${haggleResult?.deviation_pct?.toFixed(1) ?? overpricePct}%`
      : verdict === 'FAIR'
      ? 'Near Fair Price Deal'
      : verdict === 'LOW'
      ? 'Below Market Rate'
      : overpricePct > 5
      ? `Overpriced by ${overpricePct}%`
      : 'Near Fair Price';
  const verdictIcon =
    verdict === 'HIGH' ? 'trending_up' : verdict === 'LOW' ? 'trending_down' : 'check_circle';

  const minSlider = Math.max(5, Math.round((selectedProduce.retailFairMin || 15) * 0.6));
  const maxSlider = Math.round((selectedProduce.retailFairMax || 80) * 1.8);

  const handleDecrease = () => {
    const next = Math.max(minSlider, vendorAskingPrice - 5);
    handleAskingPriceChange(next);
    if (navigator.vibrate) navigator.vibrate(20);
  };

  const handleIncrease = () => {
    const next = Math.min(maxSlider, vendorAskingPrice + 5);
    handleAskingPriceChange(next);
    if (navigator.vibrate) navigator.vibrate(20);
  };

  const handleBuy = () => {
    recordPurchase(targetOffer ?? vendorAskingPrice);
    setCurrentScreen('history');
  };

  const marketUnavailable = selectedProduce.marketStatus !== 'AVAILABLE';

  // Retail references for context display
  const blinkit = selectedProduce.retailComparison?.products?.find((p) => p.platform === 'blinkit');
  const zepto = selectedProduce.retailComparison?.products?.find((p) => p.platform === 'zepto');

  return (
    <div className="min-h-screen bg-[#fbf9f5] flex flex-col pb-10 antialiased relative overflow-x-hidden">
      <Header
        title={`${selectedProduce.name} Bargain`}
        showBack
        onBack={() => setCurrentScreen('price_breakdown')}
      />

      {/* Decorative glow */}
      <div
        className={`absolute top-10 right-[-15%] w-72 h-72 rounded-full blur-[90px] opacity-35 pointer-events-none ${
          isTerracotta ? 'bg-[#ffb595]' : 'bg-[#a5d0b9]'
        }`}
      />

      <main className="flex-1 max-w-md mx-auto w-full px-5 py-4 flex flex-col gap-4 relative z-10">

        {/* ── Market unavailable notice ── */}
        {marketUnavailable && (
          <div className="bg-[#fff1e9] border border-[#e0c0b2] rounded-2xl p-4 text-[13px] text-[#7c2d12] flex items-start gap-2">
            <span className="material-symbols-outlined text-[18px] shrink-0">warning</span>
            <span>
              Market price is unavailable. Haggle suggestions are approximate and not based on verified mandi data.
            </span>
          </div>
        )}

        {/* ── Suggestion Card ── */}
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
            {priceEntered
              ? `Vendor asking ₹${vendorAskingPrice}?`
              : 'Enter vendor\'s asking price below'}
          </h2>

          <div className="flex items-baseline gap-2.5 mt-3 mb-1.5">
            <span className="text-[15px] font-medium text-[#594238]">Try offering</span>
            <span
              id="suggested-offer-price-value"
              className={`font-display text-[36px] font-extrabold tracking-tight ${
                isTerracotta ? 'text-[#9e3d00]' : 'text-[#012d1d]'
              }`}
            >
              {!priceEntered ? '—' : isHaggling ? '…' : targetOffer != null ? `₹${targetOffer}` : '—'}
            </span>
          </div>

          {/* Verdict badge */}
          {verdictColor ? (
            <div
              className={`inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full mt-2 font-semibold text-[12px] ${verdictColor}`}
            >
              <span className="material-symbols-outlined text-[16px]">{verdictIcon}</span>
              <span>{verdictLabel}</span>
            </div>
          ) : (
            <div className="inline-flex items-center gap-1.5 bg-[#ffddb9] text-[#663e00] px-3.5 py-1 rounded-full mt-2 font-semibold text-[12px]">
              <span className="material-symbols-outlined text-[16px]">hourglass_empty</span>
              <span>Calculating…</span>
            </div>
          )}

          {/* Explanation from backend */}
          {haggleResult?.explanation && (
            <p className="text-[12px] text-[#594238] mt-2 leading-relaxed">
              {haggleResult.explanation}
            </p>
          )}
        </section>

        {/* ── Reference prices context ── */}
        <section className="bg-[#f5f3ef] rounded-2xl p-4 border border-[#e4e2de]">
          <p className="text-[11px] font-bold uppercase tracking-wider text-[#594238] mb-2">
            Price References
          </p>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="bg-white rounded-xl p-2.5">
              <p className="text-[10px] text-[#8a756b] font-medium">Mandi</p>
              <p className="text-[13px] font-bold text-[#1b1c1a]">
                {selectedProduce.wholesalePrice > 0 ? `₹${selectedProduce.wholesalePrice}` : '—'}
              </p>
            </div>
            <div className="bg-white rounded-xl p-2.5">
              <p className="text-[10px] text-[#8a756b] font-medium">Blinkit</p>
              <p className="text-[13px] font-bold text-[#1b1c1a]">
                {blinkit ? `₹${blinkit.price_per_kg}` : '—'}
              </p>
            </div>
            <div className="bg-white rounded-xl p-2.5">
              <p className="text-[10px] text-[#8a756b] font-medium">Zepto</p>
              <p className="text-[13px] font-bold text-[#1b1c1a]">
                {zepto ? `₹${zepto.price_per_kg}` : '—'}
              </p>
            </div>
          </div>
        </section>

        {/* ── Interactive Stepper & Slider ── */}
        <section
          id="vendor-price-stepper-card"
          className="bg-white rounded-[24px] p-6 shadow-[0px_4px_20px_rgba(211,84,0,0.04)] border border-[#e4e2de]/70 flex flex-col gap-4"
        >
          <label className="font-semibold text-[14px] text-[#1b1c1a] text-center block">
            What is the vendor asking?
          </label>

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
                  onChange={(e) => handleAskingPriceChange(Math.max(1, Number(e.target.value)))}
                  className="w-24 bg-transparent border-none text-center font-display text-[36px] font-extrabold text-[#1b1c1a] focus:ring-0 focus:outline-none p-0"
                />
              </div>
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

          <div className="mt-2 px-1">
            <input
              id="vendor-price-slider"
              aria-label="Price range slider"
              type="range"
              min={minSlider}
              max={maxSlider}
              value={vendorAskingPrice}
              onChange={(e) => handleAskingPriceChange(Number(e.target.value))}
              className="w-full h-2 bg-[#e4e2de] rounded-lg appearance-none cursor-pointer accent-[#9e3d00]"
            />
            <div className="flex justify-between mt-2 text-[12px] font-medium text-[#594238]">
              <span>{fairAvg > 0 ? `Fair avg: ₹${fairAvg}` : 'Enter vendor price'}</span>
              <span className={overpricePct > 15 ? 'text-[#ba1a1a] font-semibold' : 'text-[#006d37]'}>
                {!priceEntered ? 'Slide to set price' : overpricePct > 15 ? 'High Quote' : 'Fair Quote'}
              </span>
            </div>
          </div>
        </section>

        {/* ── Bargain Phrases ── */}
        {selectedProduce.bargainPhrases?.length > 0 && (
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
        )}

        {/* ── Actions ── */}
        <div className="flex flex-col gap-3 mt-2">
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

          <button
            id="i-bought-it-btn"
            onClick={handleBuy}
            disabled={!priceEntered}
            className={`w-full text-white font-display text-[17px] font-bold rounded-2xl py-4 shadow-[0px_8px_24px_rgba(211,84,0,0.22)] active:scale-[0.98] transition-all flex items-center justify-center gap-2 hover:opacity-95 disabled:opacity-40 disabled:cursor-not-allowed ${
              isTerracotta ? 'bg-[#9e3d00]' : 'bg-[#012d1d]'
            }`}
          >
            <span
              className="material-symbols-outlined text-[22px]"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              check_circle
            </span>
            {priceEntered && targetOffer != null
              ? `I Bought It at ₹${targetOffer}`
              : 'Enter price to continue'}
          </button>

          <p className="text-center text-[12px] text-[#594238] font-normal">
            Saves to your purchase history
          </p>
        </div>
      </main>
    </div>
  );
};
