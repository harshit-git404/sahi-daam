import React from 'react';
import { useApp } from '../context/AppContext';
import { Header } from './Header';
import { MarketData } from '../types';

// ------------------------------------------------------------------
// Helper: trend chip
// ------------------------------------------------------------------
const TrendChip: React.FC<{ trend: string; isTerracotta: boolean }> = ({ trend, isTerracotta }) => {
  const color = isTerracotta ? '#9e3d00' : '#012d1d';
  if (trend === 'UP') return (
    <span className="inline-flex items-center gap-1 text-[#b91c1c] font-semibold text-[12px]">
      <span className="material-symbols-outlined text-[16px]">trending_up</span> Rising
    </span>
  );
  if (trend === 'DOWN') return (
    <span className="inline-flex items-center gap-1 text-[#006d37] font-semibold text-[12px]">
      <span className="material-symbols-outlined text-[16px]">trending_down</span> Falling
    </span>
  );
  if (trend === 'STABLE') return (
    <span className="inline-flex items-center gap-1 font-semibold text-[12px]" style={{ color }}>
      <span className="material-symbols-outlined text-[16px]">trending_flat</span> Stable
    </span>
  );
  return <span className="text-[12px] text-[#594238]">—</span>;
};

// ------------------------------------------------------------------
// Helper: sparkline mini chart (SVG)
// ------------------------------------------------------------------
const Sparkline: React.FC<{ history: { date: string; value: number }[]; isTerracotta: boolean }> = ({
  history,
  isTerracotta,
}) => {
  if (!history || history.length < 2) return null;
  const W = 220, H = 48;
  const values = history.map((h) => h.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1)) * W;
    const y = H - ((v - min) / range) * (H - 8) - 4;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const stroke = isTerracotta ? '#9e3d00' : '#012d1d';
  return (
    <svg width={W} height={H} className="overflow-visible">
      <polyline
        points={pts.join(' ')}
        fill="none"
        stroke={stroke}
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {values.map((_, i) => {
        const [x, y] = pts[i].split(',').map(Number);
        return (
          <circle key={i} cx={x} cy={y} r="3" fill={stroke} />
        );
      })}
    </svg>
  );
};

// ------------------------------------------------------------------
// Helper: market stats row
// ------------------------------------------------------------------
const StatRow: React.FC<{ label: string; value: string | null }> = ({ label, value }) => (
  <div className="flex justify-between items-center py-1.5 border-b border-[#e5e0d8] last:border-0">
    <span className="text-[13px] text-[#594238]">{label}</span>
    <span className="text-[13px] font-semibold text-[#1b1c1a]">{value ?? '—'}</span>
  </div>
);

// ------------------------------------------------------------------
// Main component
// ------------------------------------------------------------------
export const PriceBreakdownScreen: React.FC = () => {
  const { setCurrentScreen, selectedProduce, selectedLocation, theme, purchaseType } = useApp();
  const isTerracotta = theme === 'terracotta';

  const market: MarketData | undefined = selectedProduce.market;
  const marketAvailable = market?.status === 'AVAILABLE';
  const retail = selectedProduce.retailComparison;
  const retailAvailable = retail?.status === 'AVAILABLE' && (retail?.products?.length ?? 0) > 0;

  const displayFairMin = selectedProduce.retailFairMin;
  const displayFairMax = selectedProduce.retailFairMax;
  const displayUnit = selectedProduce.unit;

  const pct = market?.percentage_change;
  const pctLabel = pct != null ? `${pct > 0 ? '+' : ''}${pct.toFixed(1)}%` : null;
  const periodsLabel =
    market?.periods_available != null
      ? `Based on ${market.periods_available} distinct market days`
      : null;

  // Blinkit and Zepto prices
  const blinkitPrices = retail?.products?.filter((p) => p.platform === 'blinkit') ?? [];
  const zeptoPrices = retail?.products?.filter((p) => p.platform === 'zepto') ?? [];
  const bestBlinkit = blinkitPrices.length > 0 ? blinkitPrices[0] : null;
  const bestZepto = zeptoPrices.length > 0 ? zeptoPrices[0] : null;

  // Street vendor path requires market; supermarket path requires retail
  const canHaggle = purchaseType === 'street_vendor' && marketAvailable;

  return (
    <div className="min-h-screen bg-[#fbf9f5] flex flex-col pb-[100px] antialiased">
      {/* Header */}
      <Header
        title={selectedProduce.name === 'Tomato' ? 'Tomatoes' : selectedProduce.name}
        showBack
        onBack={() => setCurrentScreen('quality_result')}
      />

      <main className="flex-1 max-w-md mx-auto w-full px-5 py-4 flex flex-col gap-4">

        {/* ── Hero Fair Price Card ── */}
        <section
          id="hero-price-range-card"
          className="bg-white rounded-[24px] p-6 shadow-[0px_4px_20px_rgba(211,84,0,0.08)] text-center relative overflow-hidden border border-[#e4e2de]/60"
        >
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
            {!marketAvailable
              ? 'Unavailable'
              : displayFairMin > 0
              ? `₹${displayFairMin}–${displayFairMax}/${displayUnit}`
              : 'Unavailable'}
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
            <span>{marketAvailable ? 'Agmarknet Verified' : 'Market Data Unavailable'}</span>
          </div>
        </section>

        {/* ── Price Breakdown Receipt ── */}
        <section
          id="receipt-price-breakdown-card"
          className="bg-[#efeeea] rounded-[24px] p-6 relative border border-[#e0c0b2]/30 shadow-xs"
        >
          <h3 className="font-display text-[18px] font-bold text-[#1b1c1a] mb-4 border-b border-[#c1c8c2]/50 pb-3">
            Price Breakdown
          </h3>
          <ul className="flex flex-col gap-0">
            <StatRow
              label={`Today's mandi price · ${selectedLocation.mandiName}`}
              value={
                marketAvailable && market?.today_price != null
                  ? `₹${market.today_price}/${displayUnit}`
                  : 'Unavailable'
              }
            />
            <StatRow
              label={`Typical local markup (+${selectedProduce.markupMinPercent}–${selectedProduce.markupMaxPercent}%)`}
              value={
                marketAvailable && selectedProduce.wholesalePrice > 0
                  ? `₹${Math.round(selectedProduce.wholesalePrice * (1 + selectedProduce.markupMinPercent / 100))}–${Math.round(selectedProduce.wholesalePrice * (1 + selectedProduce.markupMaxPercent / 100))}/${displayUnit}`
                  : 'Unavailable'
              }
            />
            <StatRow
              label={`Freshness adjustment (${selectedProduce.qualityAdjustmentLabel || 'none'})`}
              value={
                selectedProduce.qualityAdjustment < 0
                  ? `-₹${Math.abs(selectedProduce.qualityAdjustment)}`
                  : selectedProduce.qualityAdjustment > 0
                  ? `+₹${selectedProduce.qualityAdjustment}`
                  : '₹0'
              }
            />
          </ul>

          {/* Data confidence */}
          <div className="mt-4 pt-3 border-t border-[#c1c8c2]/50 flex items-center justify-between">
            <div className="flex items-center gap-1.5 bg-[#a46700]/15 text-[#835100] px-3 py-1.5 rounded-full text-[12px] font-semibold">
              <span className="material-symbols-outlined text-[16px]">info</span>
              Data: {selectedProduce.dataConfidence}
            </div>
            <span className="text-[11px] text-[#594238]">
              {market?.date
                ? `Agmarknet · ${market.date}`
                : 'Agmarknet · unavailable'}
            </span>
          </div>
        </section>

        {/* ── 10-Day Market History ── */}
        {marketAvailable && market && (
          <section className="bg-white rounded-[24px] p-5 border border-[#d8e6dc] shadow-xs">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-display text-[16px] font-bold text-[#1b1c1a]">
                Market History
              </h3>
              {market.trend && market.trend !== 'UNAVAILABLE' && (
                <TrendChip trend={market.trend} isTerracotta={isTerracotta} />
              )}
            </div>

            {/* Sparkline */}
            {market.history && market.history.length >= 2 && (
              <div className="flex justify-center mb-3">
                <Sparkline history={market.history} isTerracotta={isTerracotta} />
              </div>
            )}

            {/* Stats grid */}
            <div className="grid grid-cols-2 gap-2 mb-3">
              {[
                ['Current', market.current_value != null ? `₹${market.current_value}/kg` : null],
                ['Avg', market.average_10_days != null ? `₹${market.average_10_days}/kg` : null],
                ['High', market.high_10_days != null ? `₹${market.high_10_days}/kg` : null],
                ['Low', market.low_10_days != null ? `₹${market.low_10_days}/kg` : null],
              ].map(([label, value]) => (
                <div
                  key={label}
                  className="bg-[#f5f3ef] rounded-xl p-3 flex flex-col gap-0.5"
                >
                  <span className="text-[11px] text-[#594238] uppercase tracking-wider font-semibold">
                    {label}
                  </span>
                  <span className="text-[15px] font-bold text-[#1b1c1a]">
                    {value ?? '—'}
                  </span>
                </div>
              ))}
            </div>

            {/* Change row */}
            {pctLabel && (
              <div className="flex items-center justify-between text-[12px] text-[#594238] px-1">
                <span>10-day change</span>
                <span
                  className={`font-semibold ${
                    (market.percentage_change ?? 0) > 0 ? 'text-[#b91c1c]' : 'text-[#006d37]'
                  }`}
                >
                  {pctLabel}
                </span>
              </div>
            )}
            {periodsLabel && (
              <p className="text-[11px] text-[#8a756b] mt-1.5 px-1">{periodsLabel}</p>
            )}
          </section>
        )}

        {/* ── Online Retail Reference (contextual) ── */}
        {retailAvailable && (
          <section className="rounded-2xl border border-[#d8e6dc] bg-[#e9f8ef] p-4">
            <p className="text-xs font-bold uppercase tracking-wider text-[#315b48] mb-3">
              Online Retail Reference
            </p>
            <div className="flex flex-col gap-2">
              {bestBlinkit && (
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold capitalize text-[#315b48]">Blinkit</span>
                    <span className="text-[11px] text-[#6b7f72]">{bestBlinkit.quantity}</span>
                  </div>
                  <span className="font-semibold text-[#1b4332]">₹{bestBlinkit.price_per_kg}/kg</span>
                </div>
              )}
              {bestZepto && (
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold capitalize text-[#315b48]">Zepto</span>
                    <span className="text-[11px] text-[#6b7f72]">{bestZepto.quantity}</span>
                  </div>
                  <span className="font-semibold text-[#1b4332]">₹{bestZepto.price_per_kg}/kg</span>
                </div>
              )}
            </div>
            <p className="text-[11px] text-[#6b7f72] mt-2">
              Retail reference — not used to calculate fair price.
              {retail?.collected_at && ` Data from ${new Date(retail.collected_at).toLocaleDateString('en-IN')}.`}
            </p>
          </section>
        )}

        {/* ── Location pill ── */}
        <div className="flex items-center justify-center gap-1.5 text-[#594238] text-[13px] font-medium my-1">
          <span className="material-symbols-outlined text-[18px] text-[#9e3d00]">location_on</span>
          <span>
            {marketAvailable
              ? `${selectedLocation.name} · Today`
              : 'Market price unavailable'}
          </span>
        </div>

        {/* ── Primary action ── */}
        {purchaseType === 'street_vendor' ? (
          <button
            id="start-haggling-button"
            onClick={() => setCurrentScreen('bargain')}
            disabled={!canHaggle}
            className={`w-full text-white font-display text-[16px] font-semibold py-4 rounded-2xl shadow-[0px_8px_24px_rgba(211,84,0,0.18)] active:scale-[0.98] transition-all flex justify-center items-center gap-2 hover:opacity-95 mt-1 disabled:opacity-50 disabled:cursor-not-allowed ${
              isTerracotta ? 'bg-[#9e3d00]' : 'bg-[#012d1d]'
            }`}
          >
            <span className="material-symbols-outlined text-[20px]">forum</span>
            {canHaggle ? 'Start Haggling' : 'Market price unavailable'}
          </button>
        ) : (
          <button
            id="back-to-purchase-type-btn"
            onClick={() => setCurrentScreen('purchase_type')}
            className="w-full text-[#594238] font-display text-[16px] font-semibold py-4 rounded-2xl border border-[#e0c0b2] bg-white active:scale-[0.98] transition-all mt-1"
          >
            Change buying context
          </button>
        )}
      </main>
    </div>
  );
};
