import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { fetchLocalities, fetchMandis, fetchMandiRecommendation } from '../services/api';
import { LocalityDTO, MandiDTO, MandiRecommendation } from '../types';

export const LocalityModal: React.FC = () => {
  const {
    isLocalityModalOpen,
    setIsLocalityModalOpen,
    selectedLocality,
    setSelectedLocality,
    selectedMandi,
    setSelectedMandi,
    theme,
  } = useApp();

  const [pincode, setPincode] = useState<string>(selectedLocality?.pincode || '632014');
  const [localities, setLocalities] = useState<LocalityDTO[]>([]);
  const [allMandis, setAllMandis] = useState<MandiDTO[]>([]);
  const [recommendation, setRecommendation] = useState<MandiRecommendation | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const isTerracotta = theme === 'terracotta';

  // Load initial localities and mandis on modal open
  useEffect(() => {
    if (isLocalityModalOpen) {
      loadLocalities(pincode);
      fetchMandis().then(setAllMandis).catch(() => {});
    }
  }, [isLocalityModalOpen]);

  // When selected locality changes, fetch mandi recommendation
  useEffect(() => {
    if (selectedLocality) {
      fetchMandiRecommendation(selectedLocality.id)
        .then((rec) => {
          setRecommendation(rec);
          if (rec.suggested_mandi && !selectedMandi) {
            setSelectedMandi(rec.suggested_mandi);
          }
        })
        .catch(() => setRecommendation(null));
    }
  }, [selectedLocality]);

  const loadLocalities = async (pin: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchLocalities(pin.trim() ? pin.trim() : undefined);
      setLocalities(data);
      if (data.length > 0 && (!selectedLocality || !data.some((l) => l.id === selectedLocality.id))) {
        setSelectedLocality(data[0]);
      }
    } catch (err: any) {
      setError(err?.message || 'Could not load localities.');
    } finally {
      setLoading(false);
    }
  };

  const handlePincodeSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadLocalities(pincode);
  };

  if (!isLocalityModalOpen) return null;

  return (
    <div className="fixed inset-0 z-[120] bg-black/60 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4 animate-in fade-in duration-200">
      <div className="bg-[#fbf9f5] w-full max-w-lg rounded-t-3xl sm:rounded-3xl p-6 shadow-2xl flex flex-col max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[#e4e2de]">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isTerracotta ? 'bg-[#9e3d00]/10 text-[#9e3d00]' : 'bg-[#1b4332]/10 text-[#1b4332]'}`}>
              <span className="material-symbols-outlined text-[24px]">location_on</span>
            </div>
            <div>
              <h2 className="font-display text-[18px] font-bold text-[#1b1c1a]">Select Locality & Mandi</h2>
              <p className="text-[12px] text-[#594238]">Locality-aware transport & market pricing</p>
            </div>
          </div>
          <button
            onClick={() => setIsLocalityModalOpen(false)}
            className="w-8 h-8 rounded-full bg-[#f0eee9] hover:bg-[#e4e2de] flex items-center justify-center text-[#594238]"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>

        {/* Step 1: Pincode Lookup */}
        <div className="mt-5">
          <label className="block text-[13px] font-semibold text-[#1b1c1a] mb-1.5">
            1. Enter Pincode (Postal Code)
          </label>
          <form onSubmit={handlePincodeSearch} className="flex gap-2">
            <div className="relative flex-1">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[18px] text-[#85736b]">
                search
              </span>
              <input
                type="text"
                value={pincode}
                onChange={(e) => setPincode(e.target.value)}
                placeholder="e.g. 632014, 632006, 560034"
                maxLength={6}
                className="w-full pl-9 pr-3 py-2.5 rounded-xl border border-[#d5cfc7] bg-white text-[14px] text-[#1b1c1a] focus:outline-none focus:ring-2 focus:ring-[#9e3d00]"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className={`px-4 py-2.5 rounded-xl text-white text-[13px] font-semibold transition-all ${
                isTerracotta ? 'bg-[#9e3d00] hover:bg-[#7e3100]' : 'bg-[#1b4332] hover:bg-[#143326]'
              }`}
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </form>
          {error && <p className="text-red-600 text-[12px] mt-1.5">{error}</p>}
        </div>

        {/* Step 2: Matching Localities */}
        <div className="mt-4">
          <label className="block text-[13px] font-semibold text-[#1b1c1a] mb-1.5">
            2. Choose Your Locality
          </label>
          {localities.length === 0 ? (
            <p className="text-[13px] text-[#85736b] py-2">No localities found for this pincode. Showing demo defaults.</p>
          ) : (
            <div className="grid grid-cols-2 gap-2 max-h-36 overflow-y-auto p-1">
              {localities.map((loc) => {
                const isSelected = selectedLocality?.id === loc.id;
                return (
                  <button
                    key={loc.id}
                    onClick={() => setSelectedLocality(loc)}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      isSelected
                        ? isTerracotta
                          ? 'border-[#9e3d00] bg-[#9e3d00]/5 text-[#9e3d00] font-semibold ring-1 ring-[#9e3d00]'
                          : 'border-[#1b4332] bg-[#1b4332]/5 text-[#1b4332] font-semibold ring-1 ring-[#1b4332]'
                        : 'border-[#e4e2de] bg-white text-[#1b1c1a] hover:bg-[#f5f2eb]'
                    }`}
                  >
                    <div className="text-[14px] font-bold">{loc.name}</div>
                    <div className="text-[11px] text-[#85736b]">
                      {loc.district}, {loc.pincode}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Step 3: Suggested & Override Mandi */}
        <div className="mt-5 p-4 rounded-2xl bg-white border border-[#e4e2de]">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[13px] font-bold text-[#1b1c1a] flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[18px] text-[#9e3d00]">storefront</span>
              3. Suggested Wholesale Mandi
            </span>
            {recommendation?.confidence && (
              <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                recommendation.confidence === 'high' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
              }`}>
                {recommendation.confidence === 'high' ? 'Verified Distance' : 'Provisional'}
              </span>
            )}
          </div>

          {recommendation?.reason && (
            <p className="text-[12px] text-[#594238] bg-[#fbf9f5] p-2.5 rounded-xl border border-[#ece8e1] mb-3 leading-relaxed">
              {recommendation.reason}
            </p>
          )}

          {/* Mandi Override Dropdown */}
          <div className="mt-2">
            <label className="block text-[11px] uppercase tracking-wider font-semibold text-[#85736b] mb-1">
              Active Mandi (Tap to Override)
            </label>
            <select
              value={selectedMandi?.id || ''}
              onChange={(e) => {
                const found = allMandis.find((m) => m.id === e.target.value);
                if (found) setSelectedMandi(found);
              }}
              className="w-full px-3 py-2.5 rounded-xl border border-[#d5cfc7] bg-white text-[13px] text-[#1b1c1a] focus:outline-none focus:ring-2 focus:ring-[#9e3d00]"
            >
              {allMandis.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.market_name} ({m.district}) {m.distance_km_reference ? `— ${m.distance_km_reference} km` : ''}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Footer info & Confirmation */}
        <div className="mt-5 pt-3 border-t border-[#e4e2de] flex items-center justify-between">
          <span className="text-[11px] text-[#85736b] flex items-center gap-1">
            <span className="material-symbols-outlined text-[14px]">info</span>
            Seeded regional demonstration data
          </span>
          <button
            onClick={() => setIsLocalityModalOpen(false)}
            className={`px-5 py-2.5 rounded-xl text-white text-[13px] font-bold transition-all shadow-md active:scale-95 ${
              isTerracotta ? 'bg-[#9e3d00] hover:bg-[#7e3100]' : 'bg-[#1b4332] hover:bg-[#143326]'
            }`}
          >
            Apply & Close
          </button>
        </div>
      </div>
    </div>
  );
};
