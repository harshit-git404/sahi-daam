import React from 'react';
import { useApp } from '../context/AppContext';
import { Header } from './Header';

export const HomeScreen: React.FC = () => {
  const { setCurrentScreen, selectProduceById, totalSavings, theme } = useApp();
  const isTerracotta = theme === 'terracotta';

  const handleSelectProduce = (id: string) => {
    selectProduceById(id);
  };

  return (
    <div className="min-h-screen bg-[#fbf9f5] flex flex-col pb-[90px] antialiased">
      {/* Top Header */}
      <Header />

      {/* Main Container */}
      <main className="max-w-md mx-auto w-full px-5 pt-4 flex flex-col gap-4">
        {/* Welcome & Tagline */}
        <section id="home-welcome-section" className="mb-1">
          <h2 className="font-display text-[32px] font-bold text-[#1b1c1a] leading-tight tracking-tight">
            Hello, Ravi
          </h2>
          <p className="text-[16px] text-[#594238] mt-1 font-normal">
            Know the fair price before you pay.
          </p>
        </section>

        {/* Primary Action: Scan Produce */}
        <section id="home-scan-action-section">
          <button
            id="home-scan-produce-button"
            onClick={() => setCurrentScreen('scan')}
            className={`w-full text-white rounded-[24px] py-6 px-5 flex flex-col items-center justify-center gap-3 transition-all duration-200 active:scale-[0.97] hover:opacity-95 ${
              isTerracotta
                ? 'bg-[#9e3d00] shadow-[0px_8px_24px_rgba(158,61,0,0.22)]'
                : 'bg-[#012d1d] shadow-[0px_8px_24px_rgba(1,45,29,0.22)]'
            }`}
          >
            <span
              className="material-symbols-outlined text-[48px]"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              camera_alt
            </span>
            <span className="font-display text-[24px] font-semibold tracking-tight">
              Scan Produce
            </span>
          </button>
        </section>

        {/* Savings Card */}
        <section id="home-savings-card-section">
          <div
            id="home-savings-widget"
            onClick={() => setCurrentScreen('history')}
            className="bg-[#f5f3ef] rounded-2xl p-3.5 flex items-center justify-between shadow-[0px_4px_20px_rgba(211,84,0,0.06)] border border-[#e4e2de]/60 cursor-pointer transition-transform active:scale-[0.98] hover:bg-[#eae8e4]"
          >
            <div className="flex items-center gap-3.5">
              <div
                className={`w-12 h-12 rounded-full flex items-center justify-center shrink-0 ${
                  isTerracotta
                    ? 'bg-[#7bf8a1] text-[#007239]'
                    : 'bg-[#a0f4c8] text-[#19724f]'
                }`}
              >
                <span
                  className="material-symbols-outlined text-[24px]"
                  style={{ fontVariationSettings: "'FILL' 1" }}
                >
                  savings
                </span>
              </div>
              <div>
                <p className="text-[12px] font-medium text-[#594238]">Today's Savings</p>
                <p className="font-display text-[20px] font-bold text-[#1b1c1a] leading-snug">
                  ₹{totalSavings}{' '}
                  <span className="text-[15px] font-normal text-[#594238]">
                    saved this month
                  </span>
                </p>
              </div>
            </div>
            <span className="material-symbols-outlined text-[#594238] text-[20px] mr-1">
              chevron_right
            </span>
          </div>
        </section>

        {/* Quick Selection */}
        <section id="home-quick-manual-entry-section">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-display text-[15px] font-semibold text-[#1b1c1a]">
              Quick Manual Entry
            </h3>
            <span className="text-[12px] text-[#594238]">Instant Price</span>
          </div>

          <div className="grid grid-cols-3 gap-3">
            {/* Tomato */}
            <button
              id="quick-produce-tomato"
              onClick={() => handleSelectProduce('tomato')}
              className="bg-[#efeeea] rounded-2xl p-3 flex flex-col items-center justify-center gap-2 active:scale-95 transition-all hover:bg-[#eae8e4] border border-[#e0c0b2]/40 shadow-xs group"
            >
              <div className="w-14 h-14 overflow-hidden rounded-xl flex items-center justify-center bg-white/60 p-1">
                <img
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuD05BYbHvfA19lD1DMhlsKrJ_ukzfzhVfg_mJl9HGFbkJSsryxUOp19SBN4soqTiKcJCCq0FjQVjA_vPHD9ITf7vbkBg9n40ejzyVZ-FXiPWO78itPXsH6JqQQsArIZyXQ5ZcRUuEOaicfydUiiCLq45ph9w2vrY_4igiTwOmFO7WJPeQID_zzCmkxpo2H0Kt_WdH98fSR_-4mwgWSmcxSTXdbAY_2jkZ1zJX_MKFVaw0RTPP2paH6xOQ"
                  alt="Tomato"
                  className="w-full h-full object-contain group-hover:scale-110 transition-transform duration-200"
                />
              </div>
              <span className="text-[13px] font-medium text-[#1b1c1a]">Tomato</span>
            </button>

            {/* Onion */}
            <button
              id="quick-produce-onion"
              onClick={() => handleSelectProduce('onion')}
              className="bg-[#efeeea] rounded-2xl p-3 flex flex-col items-center justify-center gap-2 active:scale-95 transition-all hover:bg-[#eae8e4] border border-[#e0c0b2]/40 shadow-xs group"
            >
              <div className="w-14 h-14 overflow-hidden rounded-xl flex items-center justify-center bg-white/60 p-1">
                <img
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuB1yDJOOmQIRtXaeHyjayaOWgJXbeKH6gG3eP1gPaCJ1Wb3IC0teN8gEaDYknpUOweoYcIN43rY2-0bvppCjjTGgNWqXMK2crUUUoQCQpEjU35BLAgIctb3LQTH7i9xw1mB8Gvzoj5ul4MQJ8reU0dPjgJkaC95tDAdG-Haiuu9hkitSHditEiHcotFUFkXf-rizoUuDF8-hW0jecjTffMyHlo2vUQuw3ndAm8LQOzvMyLoQ33wn1VJuw"
                  alt="Onion"
                  className="w-full h-full object-contain group-hover:scale-110 transition-transform duration-200"
                />
              </div>
              <span className="text-[13px] font-medium text-[#1b1c1a]">Onion</span>
            </button>

            {/* Potato */}
            <button
              id="quick-produce-potato"
              onClick={() => handleSelectProduce('potato')}
              className="bg-[#efeeea] rounded-2xl p-3 flex flex-col items-center justify-center gap-2 active:scale-95 transition-all hover:bg-[#eae8e4] border border-[#e0c0b2]/40 shadow-xs group"
            >
              <div className="w-14 h-14 overflow-hidden rounded-xl flex items-center justify-center bg-white/60 p-1">
                <img
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuB3E4JhUwpdy8yTWQr6m3TvDWjkR8bNs1yjB89MWQNNgQ4ZpVxbbRixlnbKPwK_GZ3FOLrYwBDC96thespP8Z7-gqYJBKxQH-PKYSrTOSaU2j95qTMaRIlZqdCzRNWIVGV86hY-BALSYWngy0RSZaK-Fx5UkqGpYV6X9l0I5RBFMYhFiGLSjwE0YYKi1jg010Uzl9nwFeGvlbkIx5zkfSmHcq0eH3PbDgJL5EwSJdRDAACavh4VDpmOew"
                  alt="Potato"
                  className="w-full h-full object-contain group-hover:scale-110 transition-transform duration-200"
                />
              </div>
              <span className="text-[13px] font-medium text-[#1b1c1a]">Potato</span>
            </button>
          </div>
        </section>

        {/* Live Mandi Ticker / Tip */}
        <section className="bg-white/80 rounded-2xl p-4 border border-[#e4e2de] shadow-xs text-xs text-[#594238] flex items-center gap-3">
          <span className="text-xl">💡</span>
          <div>
            <span className="font-semibold text-[#1b1c1a]">Mandi Bargain Rule:</span> Wholesale prices updated this morning. Always offer 20-30% below initial vendor quote for high volume produce.
          </div>
        </section>
      </main>
    </div>
  );
};
