import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { submitCommunityPrice } from '../services/api';

const SUPPORTED_UNITS = [
  { value: 'kg', label: 'Per Kilogram (₹/kg)' },
  { value: '500g', label: '500 Grams' },
  { value: '250g', label: '250 Grams' },
  { value: '100g', label: '100 Grams' },
  { value: 'piece', label: 'Per Piece' },
  { value: 'bunch', label: 'Per Bunch' },
];

export const CommunityPriceModal: React.FC = () => {
  const {
    isCommunityModalOpen,
    setIsCommunityModalOpen,
    selectedProduce,
    selectedLocality,
    theme,
  } = useApp();

  const [commodityId, setCommodityId] = useState<string>(selectedProduce?.id || 'tomato');
  const [price, setPrice] = useState<string>('');
  const [unit, setUnit] = useState<string>('kg');
  const [sourceType, setSourceType] = useState<'customer' | 'vendor'>('customer');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [result, setResult] = useState<any | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isTerracotta = theme === 'terracotta';

  if (!isCommunityModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setResult(null);

    const numPrice = parseFloat(price);
    if (isNaN(numPrice) || numPrice <= 0) {
      setErrorMessage('Please enter a valid positive price.');
      return;
    }

    if (!selectedLocality?.id) {
      setErrorMessage('Please select a locality before submitting.');
      return;
    }

    setSubmitting(true);
    try {
      const res = await submitCommunityPrice({
        commodity_id: commodityId,
        price: numPrice,
        unit: unit,
        locality_id: selectedLocality.id,
        source_type: sourceType,
        contributor_id: `demo_${sourceType}_${Math.floor(Math.random() * 900 + 100)}`,
        observed_at: new Date().toISOString(),
      });
      setResult(res);
      setPrice('');
    } catch (err: any) {
      setErrorMessage(err?.message || 'Submission failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    setIsCommunityModalOpen(false);
    setResult(null);
    setErrorMessage(null);
  };

  return (
    <div className="fixed inset-0 z-[120] bg-black/60 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4 animate-in fade-in duration-200">
      <div className="bg-[#fbf9f5] w-full max-w-lg rounded-t-3xl sm:rounded-3xl p-6 shadow-2xl flex flex-col max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[#e4e2de]">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isTerracotta ? 'bg-[#9e3d00]/10 text-[#9e3d00]' : 'bg-[#1b4332]/10 text-[#1b4332]'}`}>
              <span className="material-symbols-outlined text-[24px]">groups</span>
            </div>
            <div>
              <h2 className="font-display text-[18px] font-bold text-[#1b1c1a]">Report Community Price</h2>
              <p className="text-[12px] text-[#594238]">Help neighbours discover fair local prices</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="w-8 h-8 rounded-full bg-[#f0eee9] hover:bg-[#e4e2de] flex items-center justify-center text-[#594238]"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>

        {/* Feedback Alert */}
        {result && (
          <div className="mt-4 p-4 rounded-2xl bg-white border border-[#d5cfc7] shadow-sm">
            <div className="flex items-center gap-2 mb-2 text-green-700 font-bold text-[14px]">
              <span className="material-symbols-outlined text-[20px]">check_circle</span>
              Report Successfully Recorded!
            </div>
            <p className="text-[12px] text-[#594238] leading-relaxed">
              Price: ₹{result?.observation?.price} / {result?.observation?.unit}
              {result?.normalized_price_per_kg && ` (₹${result.normalized_price_per_kg.toFixed(1)}/kg)`}
            </p>

            {result?.is_duplicate && (
              <div className="mt-2 p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-[12px]">
                <span className="font-semibold">Notice:</span> This report was flagged as a potential duplicate. It has been preserved for auditing records, but will not inflate the independent sample count.
              </div>
            )}
            <button
              onClick={() => setResult(null)}
              className="mt-3 text-[12px] text-[#9e3d00] font-semibold underline"
            >
              Submit Another Observation
            </button>
          </div>
        )}

        {!result && (
          <form onSubmit={handleSubmit} className="mt-4 space-y-4">
            {/* Commodity */}
            <div>
              <label className="block text-[12px] font-semibold text-[#1b1c1a] mb-1">
                Commodity / Produce
              </label>
              <select
                value={commodityId}
                onChange={(e) => setCommodityId(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl border border-[#d5cfc7] bg-white text-[13px] text-[#1b1c1a] focus:outline-none focus:ring-2 focus:ring-[#9e3d00]"
              >
                <option value="tomato">Tomato (Tamatar)</option>
                <option value="potato">Potato (Aaloo)</option>
                <option value="onion">Onion (Pyaaz)</option>
                <option value="spinach">Spinach (Palak)</option>
                <option value="coriander">Coriander (Dhaniya)</option>
                <option value="ginger">Ginger (Adrak)</option>
              </select>
            </div>

            {/* Price & Unit */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[12px] font-semibold text-[#1b1c1a] mb-1">
                  Price Paid / Offered (₹)
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="1"
                  max="500"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  placeholder="e.g. 30"
                  required
                  className="w-full px-3 py-2.5 rounded-xl border border-[#d5cfc7] bg-white text-[14px] text-[#1b1c1a] focus:outline-none focus:ring-2 focus:ring-[#9e3d00]"
                />
              </div>
              <div>
                <label className="block text-[12px] font-semibold text-[#1b1c1a] mb-1">
                  Unit
                </label>
                <select
                  value={unit}
                  onChange={(e) => setUnit(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl border border-[#d5cfc7] bg-white text-[13px] text-[#1b1c1a] focus:outline-none focus:ring-2 focus:ring-[#9e3d00]"
                >
                  {SUPPORTED_UNITS.map((u) => (
                    <option key={u.value} value={u.value}>
                      {u.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Locality */}
            <div>
              <label className="block text-[12px] font-semibold text-[#1b1c1a] mb-1">
                Locality (Area)
              </label>
              <div className="px-3 py-2.5 rounded-xl border border-[#d5cfc7] bg-[#f0eee9] text-[13px] text-[#1b1c1a] flex items-center justify-between">
                <span>{selectedLocality?.name || 'Vellore'} ({selectedLocality?.district || 'Vellore'}, {selectedLocality?.pincode || '632014'})</span>
                <span className="text-[11px] text-[#85736b]">From Active Profile</span>
              </div>
            </div>

            {/* Source Type / Experience Role */}
            <div>
              <label className="block text-[12px] font-semibold text-[#1b1c1a] mb-1.5">
                Reporting As
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setSourceType('customer')}
                  className={`py-2 px-3 rounded-xl border text-[13px] font-semibold flex items-center justify-center gap-1.5 transition-all ${
                    sourceType === 'customer'
                      ? 'border-[#9e3d00] bg-[#9e3d00]/10 text-[#9e3d00]'
                      : 'border-[#e4e2de] bg-white text-[#594238]'
                  }`}
                >
                  <span className="material-symbols-outlined text-[18px]">shopping_bag</span>
                  Customer Buyer
                </button>
                <button
                  type="button"
                  onClick={() => setSourceType('vendor')}
                  className={`py-2 px-3 rounded-xl border text-[13px] font-semibold flex items-center justify-center gap-1.5 transition-all ${
                    sourceType === 'vendor'
                      ? 'border-[#9e3d00] bg-[#9e3d00]/10 text-[#9e3d00]'
                      : 'border-[#e4e2de] bg-white text-[#594238]'
                  }`}
                >
                  <span className="material-symbols-outlined text-[18px]">store</span>
                  Street Vendor
                </button>
              </div>
            </div>

            {errorMessage && (
              <p className="text-red-600 text-[12px]">{errorMessage}</p>
            )}

            {/* Policy Explainer */}
            <div className="p-3 rounded-xl bg-white border border-[#e4e2de] text-[11px] text-[#85736b] leading-relaxed">
              <span className="font-semibold text-[#1b1c1a]">Reconciliation Rule:</span> Reports enter a 2-day rolling window. 
              At least 10 independent reports are required before community observations adjust the price baseline. Flagged duplicates do not count toward the sample size.
            </div>

            {/* Submit Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={submitting}
                className={`w-full py-3.5 rounded-2xl text-white font-bold text-[14px] shadow-lg transition-all active:scale-98 flex items-center justify-center gap-2 ${
                  isTerracotta ? 'bg-[#9e3d00] hover:bg-[#7e3100]' : 'bg-[#1b4332] hover:bg-[#143326]'
                }`}
              >
                {submitting ? (
                  <span>Recording...</span>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-[20px]">send</span>
                    Submit Price Report
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
