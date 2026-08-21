import React from 'react';
import { Header } from './Header';
import { useApp } from '../context/AppContext';
import { RetailProduct } from '../types';

const PlatformCard: React.FC<{
  platform: string;
  products: RetailProduct[];
  isBest: boolean;
  isTerracotta: boolean;
}> = ({ platform, products, isBest, isTerracotta }) => {
  const best = products[0]; // already sorted by price_per_kg ascending
  if (!best) return null;
  const accent = isTerracotta ? '#9e3d00' : '#0e6c4a';

  return (
    <div
      className={`rounded-2xl border p-4 ${
        isBest ? 'border-[#006d37] bg-[#e9f8ef]' : 'border-[#e4e2de] bg-white'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-display font-bold text-[15px] capitalize text-[#1b1c1a]">
          {platform}
        </span>
        {isBest && (
          <span className="text-[10px] font-bold text-[#006d37] bg-[#7bf8a1]/60 px-2 py-0.5 rounded-full uppercase tracking-wide">
            Best Price
          </span>
        )}
      </div>

      {products.map((p) => (
        <div
          key={`${p.platform}-${p.product_name}-${p.price_per_kg}`}
          className="flex items-center justify-between py-1.5 border-b border-[#e5e0d8] last:border-0"
        >
          <div>
            <p className="text-[13px] font-medium text-[#1b1c1a]">{p.product_name}</p>
            <p className="text-[11px] text-[#8a756b]">
              {p.quantity} · {p.variant !== 'regular' ? p.variant : 'standard'}
            </p>
          </div>
          <div className="text-right">
            <p className="text-[14px] font-bold" style={{ color: accent }}>
              ₹{p.price_per_kg}/kg
            </p>
            {p.mrp != null && p.mrp > p.price_per_kg && (
              <p className="text-[10px] text-[#8a756b] line-through">MRP ₹{p.mrp}</p>
            )}
          </div>
        </div>
      ))}

      {best.location_note && (
        <p className="text-[10px] text-[#8a756b] mt-2 italic">{best.location_note}</p>
      )}
    </div>
  );
};

export const SupermarketScreen: React.FC = () => {
  const { selectedProduce, setCurrentScreen, theme } = useApp();
  const isTerracotta = theme === 'terracotta';
  const retail = selectedProduce.retailComparison;
  const isAvailable = retail?.status === 'AVAILABLE' && (retail?.products?.length ?? 0) > 0;

  // Group products by platform
  const byPlatform: Record<string, RetailProduct[]> = {};
  if (isAvailable && retail?.products) {
    for (const p of retail.products) {
      if (!byPlatform[p.platform]) byPlatform[p.platform] = [];
      byPlatform[p.platform].push(p);
    }
  }

  const bestPlatform = retail?.best_platform ?? null;

  // Google Maps search link for nearby store
  const mapsQuery = encodeURIComponent(
    `${selectedProduce.name} near me supermarket`,
  );
  const mapsUrl = `https://www.google.com/maps/search/${mapsQuery}`;

  return (
    <div className="min-h-screen bg-[#fbf9f5] pb-[90px]">
      <Header
        title="Store comparison"
        showBack
        onBack={() => setCurrentScreen('purchase_type')}
      />

      <main className="max-w-md mx-auto w-full px-5 pt-6 flex flex-col gap-4">

        {/* Produce + freshness summary */}
        <div className="flex items-center gap-3 bg-white rounded-2xl p-4 border border-[#e4e2de]">
          <img
            src={selectedProduce.image}
            alt={selectedProduce.name}
            className="w-14 h-14 rounded-xl object-cover"
          />
          <div>
            <p className="font-display font-bold text-[16px] text-[#1b1c1a]">
              {selectedProduce.name}
            </p>
            <p className="text-[12px] text-[#594238] mt-0.5">
              Freshness: {selectedProduce.freshnessPercent}% · {selectedProduce.freshness.replace('_', ' ')}
            </p>
            {selectedProduce.analysisProvider && (
              <p className="text-[11px] text-[#8a756b] mt-0.5">
                Analyzed by{' '}
                {selectedProduce.analysisProvider === 'gemini' ? 'Gemini Flash' : 'Local ML fallback'}
              </p>
            )}
          </div>
        </div>

        {/* Retailer comparison */}
        {isAvailable ? (
          <>
            <div className="flex items-center justify-between">
              <p className="text-xs font-bold uppercase tracking-wider text-[#315b48]">
                Retailer comparison
              </p>
              {retail?.collected_at && (
                <p className="text-[10px] text-[#8a756b]">
                  Data from {new Date(retail.collected_at).toLocaleDateString('en-IN')}
                </p>
              )}
            </div>

            {Object.entries(byPlatform).map(([platform, products]) => (
              <PlatformCard
                key={platform}
                platform={platform}
                products={products}
                isBest={platform === bestPlatform}
                isTerracotta={isTerracotta}
              />
            ))}

            {retail?.best_price_per_kg != null && (
              <div
                className={`rounded-2xl p-4 ${
                  isTerracotta ? 'bg-[#fff1e9] border border-[#e0c0b2]' : 'bg-[#e9f8ef] border border-[#d8e6dc]'
                }`}
              >
                <div className="flex items-start justify-between">
                  <p className="text-[13px] font-bold text-[#1b1c1a]">
                    Best available retail price
                  </p>
                  {retail?.cache_age_hours != null && (
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold inline-block ${
                      retail.cache_age_hours < 24 ? 'bg-[#7bf8a1]/20 text-[#006d37]' :
                      retail.cache_age_hours <= 72 ? 'bg-[#ffb595]/20 text-[#9e3d00]' :
                      'bg-[#a46700]/15 text-[#835100]'
                    }`}>
                      {retail.cache_age_hours > 72 
                        ? `Updated ${Math.floor(retail.cache_age_hours / 24)}d ago` 
                        : `Updated ${Math.round(retail.cache_age_hours)}h ago`}
                    </span>
                  )}
                </div>
                <p
                  className={`font-display text-[28px] font-extrabold mt-1 ${
                    isTerracotta ? 'text-[#9e3d00]' : 'text-[#0e6c4a]'
                  }`}
                >
                  ₹{retail.best_price_per_kg}/kg
                </p>
                <p className="text-[11px] text-[#594238] mt-0.5 capitalize">
                  via {retail.best_platform}
                </p>
                <p className="text-[11px] text-[#8a756b] mt-1">
                  {retail.source}
                </p>
              </div>
            )}
          </>
        ) : (
          <div className="rounded-2xl border border-[#e0c0b2] bg-[#fff1e9] p-5">
            <span className="material-symbols-outlined text-[32px] text-[#9e3d00]">shopping_bag</span>
            <p className="mt-2 font-display font-bold text-[#7c2d12] text-[18px]">
              Online comparison unavailable
            </p>
            <p className="text-sm text-[#594238] mt-1 leading-relaxed">
              {retail?.message ||
                'Retail comparison is not yet available for this produce. ' +
                  'Try again later or check nearby stores on the map.'}
            </p>
          </div>
        )}

        {/* NO HAGGLE NOTICE */}
        <div className="flex items-center gap-2 rounded-xl bg-[#f5f3ef] border border-[#e4e2de] p-3 text-[12px] text-[#594238]">
          <span className="material-symbols-outlined text-[18px] text-[#8a756b]">info</span>
          <span>Haggling is not applicable for supermarket / online purchases.</span>
        </div>

        {/* Nearby stores map link */}
        <div className="rounded-2xl border border-[#d8e6dc] bg-[#e9f8ef] p-4">
          <p className="text-xs font-bold uppercase tracking-wider text-[#315b48] mb-2">
            Find nearby stores
          </p>
          <a
            href={mapsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={`inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-white text-[13px] font-semibold active:scale-[0.98] transition-all ${
              isTerracotta ? 'bg-[#9e3d00]' : 'bg-[#0e6c4a]'
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">map</span>
            Open in Maps
          </a>
          <p className="text-[10px] text-[#8a756b] mt-2">
            Opens Google Maps search for nearby stores.
          </p>
        </div>

        <button
          onClick={() => setCurrentScreen('purchase_type')}
          className="mt-1 w-full rounded-2xl border border-[#e0c0b2] bg-white py-4 font-display font-semibold text-[#9e3d00] active:scale-[0.98] transition-all"
        >
          Choose another buying context
        </button>
      </main>
    </div>
  );
};
