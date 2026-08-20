import React from 'react';
import { useApp } from '../context/AppContext';
import { MANDI_LOCATIONS } from '../data/mandiLocations';
import { formatRupees } from '../services/format';

export const DrawerMenu: React.FC = () => {
  const {
    isDrawerOpen,
    setIsDrawerOpen,
    selectedLocation,
    setSelectedLocation,
    theme,
    toggleTheme,
    totalSavings,
    setCurrentScreen,
    selectProduceById
  } = useApp();

  if (!isDrawerOpen) return null;

  const isTerracotta = theme === 'terracotta';

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-xs transition-opacity animate-in fade-in duration-200"
        onClick={() => setIsDrawerOpen(false)}
      />

      {/* Drawer Panel */}
      <div className="relative w-4/5 max-w-xs bg-[#fbf9f5] h-full shadow-2xl flex flex-col z-10 animate-in slide-in-from-left duration-200 border-r border-[#e4e2de]">
        {/* Header */}
        <div className={`p-5 border-b border-[#e4e2de] ${isTerracotta ? 'bg-[#ffdbcd]/30' : 'bg-[#c1ecd4]/30'}`}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className={`material-symbols-outlined text-[28px] ${isTerracotta ? 'text-[#9e3d00]' : 'text-[#012d1d]'}`}>
                storefront
              </span>
              <span className={`font-display font-bold text-xl ${isTerracotta ? 'text-[#9e3d00]' : 'text-[#012d1d]'}`}>
                Sahi Daam
              </span>
            </div>
            <button
              onClick={() => setIsDrawerOpen(false)}
              className="p-1 rounded-full text-[#594238] hover:bg-[#e4e2de]"
            >
              <span className="material-symbols-outlined text-[20px]">close</span>
            </button>
          </div>
          <p className="text-xs text-[#594238]">
            AI-driven fair price & freshness guide for Indian Mandis.
          </p>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {/* Quick Stats */}
          <div className="p-3.5 rounded-2xl bg-white border border-[#e4e2de] shadow-xs">
            <p className="text-xs text-[#594238] font-medium">Your Total Savings</p>
            <p className={`font-display text-2xl font-bold mt-0.5 ${isTerracotta ? 'text-[#9e3d00]' : 'text-[#012d1d]'}`}>
              {formatRupees(totalSavings)}
            </p>
          </div>

          {/* Location Selector */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-[#594238] mb-2 block">
              Active Mandi & Location
            </label>
            <div className="space-y-1.5">
              {MANDI_LOCATIONS.map((loc) => {
                const isSelected = selectedLocation.id === loc.id;
                return (
                  <button
                    key={loc.id}
                    onClick={() => {
                      setSelectedLocation(loc);
                    }}
                    className={`w-full text-left p-2.5 rounded-xl text-xs flex items-center justify-between border transition-all ${
                      isSelected
                        ? isTerracotta
                          ? 'bg-[#ffdbcd]/60 border-[#9e3d00] text-[#9e3d00] font-semibold'
                          : 'bg-[#c1ecd4]/60 border-[#012d1d] text-[#012d1d] font-semibold'
                        : 'bg-white border-[#e4e2de] text-[#1b1c1a] hover:bg-[#f5f3ef]'
                    }`}
                  >
                    <div>
                      <p>{loc.name}</p>
                      <p className="text-[10px] text-[#594238] font-normal">{loc.mandiName}</p>
                    </div>
                    {isSelected && (
                      <span className="material-symbols-outlined text-[16px]">check</span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Appearance Switch */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-[#594238] mb-2 block">
              Color Aesthetic
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => {
                  if (theme !== 'terracotta') toggleTheme();
                }}
                className={`p-2.5 rounded-xl border text-xs flex items-center justify-center gap-2 font-medium ${
                  isTerracotta
                    ? 'border-[#9e3d00] bg-[#ffdbcd]/50 text-[#9e3d00]'
                    : 'border-[#e4e2de] bg-white text-[#1b1c1a]'
                }`}
              >
                <div className="w-3.5 h-3.5 rounded-full bg-[#9e3d00]" />
                Terracotta
              </button>
              <button
                onClick={() => {
                  if (theme !== 'forest_green') toggleTheme();
                }}
                className={`p-2.5 rounded-xl border text-xs flex items-center justify-center gap-2 font-medium ${
                  !isTerracotta
                    ? 'border-[#012d1d] bg-[#c1ecd4]/50 text-[#012d1d]'
                    : 'border-[#e4e2de] bg-white text-[#1b1c1a]'
                }`}
              >
                <div className="w-3.5 h-3.5 rounded-full bg-[#012d1d]" />
                Forest Green
              </button>
            </div>
          </div>

          {/* Sample Produce Fast-Switch */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-[#594238] mb-2 block">
              Quick Produce Inspection
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: 'tomato', name: 'Tomato', emoji: '🍅' },
                { id: 'onion', name: 'Onion', emoji: '🧅' },
                { id: 'potato', name: 'Potato', emoji: '🥔' }
              ].map((p) => (
                <button
                  key={p.id}
                  onClick={() => {
                    selectProduceById(p.id);
                    setCurrentScreen('quality_result');
                    setIsDrawerOpen(false);
                  }}
                  className="p-2 rounded-xl bg-white border border-[#e4e2de] hover:bg-[#f5f3ef] text-center text-xs"
                >
                  <span className="text-lg block">{p.emoji}</span>
                  <span className="font-medium text-[#1b1c1a]">{p.name}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#e4e2de] text-center text-[11px] text-[#594238]">
          Sahi Daam v1.0 · Indian Mandi Data Engine
        </div>
      </div>
    </div>
  );
};
