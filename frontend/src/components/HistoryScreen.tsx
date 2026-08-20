import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Header } from './Header';
import { formatRelativeDate, formatRupees } from '../services/format';
import { calculateHistoryStats } from '../services/transactions';

export const HistoryScreen: React.FC = () => {
  const { purchaseHistory, totalSavings, theme, triggerCelebration } = useApp();
  const [showAll, setShowAll] = useState(false);
  const isTerracotta = theme === 'terracotta';

  const visibleHistory = showAll ? purchaseHistory : purchaseHistory.slice(0, 5);
  const stats = React.useMemo(() => calculateHistoryStats(purchaseHistory), [purchaseHistory]);
  const maxTrendValue = Math.max(1, ...stats.weeklyTrend);
  const weeklyTrendText =
    stats.weeklyDealCount === 0
      ? 'No deals this week'
      : stats.weeklySavingsPctChange === 0
        ? `${formatRupees(stats.weeklySavings)} saved this week`
        : `${stats.weeklySavingsPctChange > 0 ? 'Up' : 'Down'} ${Math.abs(stats.weeklySavingsPctChange)}% this week`;
  const weeklyTrendIcon =
    stats.weeklyDealCount === 0
      ? 'savings'
      : stats.weeklySavingsPctChange < 0
        ? 'trending_down'
        : 'trending_up';

  return (
    <div className="min-h-screen bg-[#fbf9f5] flex flex-col pb-[110px] antialiased">
      {/* TopAppBar */}
      <Header title="Sahi Daam" />

      {/* Main Container */}
      <main className="max-w-md mx-auto w-full px-5 pt-4 flex flex-col gap-4">
        {/* Total Savings Summary Card */}
        <section
          id="savings-summary-card"
          onClick={triggerCelebration}
          className="relative bg-white rounded-2xl p-6 shadow-[0px_4px_24px_rgba(211,84,0,0.08)] border border-[#e4e2de]/70 overflow-hidden flex flex-col items-center justify-center text-center cursor-pointer transition-transform active:scale-[0.99]"
        >
          {/* Decorative Confetti Layer */}
          <div aria-hidden="true" className="absolute inset-0 pointer-events-none overflow-hidden">
            <div
              className="confetti-piece w-2 h-2"
              style={{
                left: '12%',
                backgroundColor: isTerracotta ? '#7bf8a1' : '#a0f4c8',
                animationDelay: '0s'
              }}
            />
            <div
              className="confetti-piece w-1.5 h-1.5"
              style={{
                left: '32%',
                backgroundColor: isTerracotta ? '#ffb595' : '#a5d0b9',
                animationDelay: '1.2s'
              }}
            />
            <div
              className="confetti-piece w-2.5 h-2.5"
              style={{
                left: '52%',
                backgroundColor: isTerracotta ? '#7bf8a1' : '#a0f4c8',
                animationDelay: '2.4s'
              }}
            />
            <div
              className="confetti-piece w-2 h-2"
              style={{
                left: '74%',
                backgroundColor: isTerracotta ? '#ffb595' : '#a5d0b9',
                animationDelay: '0.8s'
              }}
            />
            <div
              className="confetti-piece w-1.5 h-1.5"
              style={{
                left: '88%',
                backgroundColor: isTerracotta ? '#7bf8a1' : '#a0f4c8',
                animationDelay: '3s'
              }}
            />
          </div>

          <p className="text-[13px] font-semibold text-[#594238] mb-1">Total Savings</p>

          <h2
            id="total-savings-number"
            className={`font-display text-[44px] font-extrabold tracking-tight mb-4 ${
              isTerracotta ? 'text-[#9e3d00]' : 'text-[#012d1d]'
            }`}
          >
            {formatRupees(totalSavings)}
          </h2>

          {/* Weekly Trend Line */}
          <div className="w-full max-w-[240px] h-12 relative flex items-end justify-between px-2 opacity-90 my-1">
            {stats.weeklyTrend.map((daySavings, index) => {
              const heightPct = daySavings === 0 ? 12 : Math.max(18, Math.round((daySavings / maxTrendValue) * 100));
              const isLatest = index === stats.weeklyTrend.length - 1;

              return (
                <div
                  key={index}
                  className={`w-1/6 rounded-t-sm transition-all ${
                    isLatest
                      ? isTerracotta
                        ? 'bg-[#006d37] shadow-[0_0_12px_rgba(0,109,55,0.45)]'
                        : 'bg-[#0e6c4a] shadow-[0_0_12px_rgba(14,108,74,0.45)]'
                      : isTerracotta
                        ? 'bg-[#7bf8a1]'
                        : 'bg-[#a0f4c8]'
                  }`}
                  style={{ height: `${heightPct}%`, opacity: daySavings === 0 ? 0.35 : 1 }}
                  aria-label={`${formatRupees(daySavings)} saved`}
                />
              );
            })}
          </div>

          <p
            className={`text-[12px] font-semibold mt-3 flex items-center gap-1 ${
              isTerracotta ? 'text-[#006d37]' : 'text-[#0e6c4a]'
            }`}
          >
            <span
              className="material-symbols-outlined text-[16px]"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              {weeklyTrendIcon}
            </span>
            {weeklyTrendText} - Tap for confetti
          </p>
        </section>

        {/* Recent History List */}
        <section id="recent-history-section" className="flex flex-col gap-3">
          <div className="flex items-center justify-between px-1">
            <h3 className="font-display text-[18px] font-bold text-[#1b1c1a]">
              Recent History
            </h3>
            <span className="text-[12px] text-[#594238]">
              {stats.dealCount} deals tracked
            </span>
          </div>

          {purchaseHistory.length === 0 ? (
            <div className="bg-white rounded-2xl p-5 border border-[#e4e2de]/70 text-center shadow-[0px_4px_20px_rgba(211,84,0,0.04)]">
              <span className="material-symbols-outlined text-[28px] text-[#594238] mb-2">
                receipt_long
              </span>
              <p className="font-display text-[16px] font-bold text-[#1b1c1a]">
                No completed deals yet
              </p>
              <p className="text-[12px] text-[#594238] mt-1">
                Bought items will appear here after you confirm the final haggle price.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {visibleHistory.map((item) => {
                const isTomato = item.iconType === 'tomato' || item.produceName.toLowerCase().includes('tomato');
                const isOnion = item.iconType === 'onion' || item.produceName.toLowerCase().includes('onion');

                return (
                  <article
                    key={item.id}
                    className="bg-white rounded-2xl p-4 shadow-[0px_4px_20px_rgba(211,84,0,0.06)] flex items-center gap-4 border border-[#e4e2de]/60 transition-all hover:bg-[#fbf9f5] active:scale-[0.98]"
                  >
                    {/* Category Circle Icon */}
                    <div
                      className={`w-12 h-12 rounded-full flex items-center justify-center shrink-0 ${
                        isTomato
                          ? 'bg-[#ffdad6] text-[#93000a]'
                          : isOnion
                          ? 'bg-[#ffddb9] text-[#663e00]'
                          : isTerracotta
                          ? 'bg-[#ffdbcd] text-[#9e3d00]'
                          : 'bg-[#c1ecd4] text-[#012d1d]'
                      }`}
                    >
                      <span
                        className="material-symbols-outlined text-[24px]"
                        style={{ fontVariationSettings: "'FILL' 1" }}
                      >
                        {isTomato ? 'local_florist' : isOnion ? 'spa' : 'eco'}
                      </span>
                    </div>

                    {/* Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-start mb-1">
                        <h4 className="font-display text-[16px] font-bold text-[#1b1c1a] truncate">
                          {item.produceName}
                        </h4>
                        <span className="text-[12px] font-medium text-[#594238] shrink-0 ml-2">
                          {formatRelativeDate(item.timestamp)}
                        </span>
                      </div>

                      <div className="flex justify-between items-center">
                        <div className="flex flex-col">
                          <span className="text-[14px] font-medium text-[#1b1c1a]">
                            Paid: {formatRupees(item.paidPrice)}/{item.unit}
                          </span>
                          <span className="text-[12px] text-[#8c7166]">
                            Asked: {formatRupees(item.vendorAskingPrice)} - Fair: {formatRupees(item.fairPrice)}
                          </span>
                        </div>

                        {/* Savings Badge */}
                        <div
                          className={`px-3 py-1 rounded-full text-[13px] font-bold flex items-center gap-1 shadow-2xs ${
                            isOnion && !isTomato
                              ? isTerracotta
                                ? 'bg-[#006d37] text-white'
                                : 'bg-[#0e6c4a] text-white'
                              : isTerracotta
                              ? 'bg-[#7bf8a1] text-[#007239]'
                              : 'bg-[#a0f4c8] text-[#19724f]'
                          }`}
                        >
                          <span
                            className="material-symbols-outlined text-[14px]"
                            style={{ fontVariationSettings: "'FILL' 1" }}
                          >
                            savings
                          </span>
                          {formatRupees(item.savedAmount)}
                        </div>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          )}

          {/* Load More Button */}
          {purchaseHistory.length > 5 && (
            <div className="flex justify-center mt-2">
              <button
                id="load-more-history-btn"
                onClick={() => setShowAll(!showAll)}
                className={`text-[14px] font-semibold py-2 px-4 rounded-full transition-colors flex items-center gap-1.5 active:scale-95 ${
                  isTerracotta
                    ? 'text-[#9e3d00] hover:bg-[#ffdbcd]/50'
                    : 'text-[#012d1d] hover:bg-[#c1ecd4]/50'
                }`}
              >
                {showAll ? 'Show Less' : 'Load More'}
                <span
                  className={`material-symbols-outlined text-[18px] transition-transform ${
                    showAll ? 'rotate-180' : ''
                  }`}
                >
                  expand_more
                </span>
              </button>
            </div>
          )}
        </section>
      </main>
    </div>
  );
};
