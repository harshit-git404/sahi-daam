import React from 'react';
import { useApp } from '../context/AppContext';

export const BottomNav: React.FC = () => {
  const { currentScreen, setCurrentScreen, theme } = useApp();

  // Don't show bottom nav when inside full-screen camera scanning mode
  if (currentScreen === 'scan') {
    return null;
  }

  const isTerracotta = theme === 'terracotta';
  const isHomeActive = currentScreen === 'home';
  const isHistoryActive = currentScreen === 'history';
  const isScanActive = currentScreen === 'quality_result' || currentScreen === 'price_breakdown' || currentScreen === 'bargain';

  return (
    <nav
      id="bottom-navigation-bar"
      className="fixed bottom-0 left-0 w-full z-40 bg-[#fbf9f5] border-t border-[#e4e2de]/80 shadow-[0px_-4px_24px_rgba(211,84,0,0.06)] select-none"
    >
      <div className="max-w-md mx-auto flex items-center justify-around px-5 pt-2 pb-[calc(1.25rem+env(safe-area-inset-bottom))]">
        {/* Home */}
        <button
          id="nav-home-btn"
          aria-label="Home"
          onClick={() => setCurrentScreen('home')}
          className={`flex flex-col items-center justify-center transition-all duration-200 active:scale-90 ${
            isHomeActive
              ? isTerracotta
                ? 'bg-[#7bf8a1] text-[#007239] font-semibold rounded-full px-5 py-1 shadow-sm'
                : 'bg-[#a0f4c8] text-[#19724f] font-semibold rounded-full px-5 py-1 shadow-sm'
              : 'text-[#594238] px-3 py-1 hover:text-[#1b1c1a]'
          }`}
        >
          <span
            className="material-symbols-outlined text-[24px]"
            style={{ fontVariationSettings: isHomeActive ? "'FILL' 1, 'wght' 600" : "'FILL' 0, 'wght' 400" }}
          >
            home
          </span>
          <span className="text-[12px] font-medium leading-tight mt-0.5">Home</span>
        </button>

        {/* Scan */}
        <button
          id="nav-scan-btn"
          aria-label="Scan Produce"
          onClick={() => setCurrentScreen('scan')}
          className={`flex flex-col items-center justify-center transition-all duration-200 active:scale-90 ${
            isScanActive
              ? isTerracotta
                ? 'bg-[#7bf8a1] text-[#007239] font-semibold rounded-full px-5 py-1 shadow-sm'
                : 'bg-[#a0f4c8] text-[#19724f] font-semibold rounded-full px-5 py-1 shadow-sm'
              : 'text-[#594238] px-3 py-1 hover:text-[#1b1c1a]'
          }`}
        >
          <span
            className="material-symbols-outlined text-[24px]"
            style={{ fontVariationSettings: isScanActive ? "'FILL' 1, 'wght' 600" : "'FILL' 0, 'wght' 400" }}
          >
            center_focus_strong
          </span>
          <span className="text-[12px] font-medium leading-tight mt-0.5">Scan</span>
        </button>

        {/* History */}
        <button
          id="nav-history-btn"
          aria-label="Savings History"
          onClick={() => setCurrentScreen('history')}
          className={`flex flex-col items-center justify-center transition-all duration-200 active:scale-90 ${
            isHistoryActive
              ? isTerracotta
                ? 'bg-[#7bf8a1] text-[#007239] font-semibold rounded-full px-5 py-1 shadow-sm'
                : 'bg-[#a0f4c8] text-[#19724f] font-semibold rounded-full px-5 py-1 shadow-sm'
              : 'text-[#594238] px-3 py-1 hover:text-[#1b1c1a]'
          }`}
        >
          <span
            className="material-symbols-outlined text-[24px]"
            style={{ fontVariationSettings: isHistoryActive ? "'FILL' 1, 'wght' 600" : "'FILL' 0, 'wght' 400" }}
          >
            history
          </span>
          <span className="text-[12px] font-medium leading-tight mt-0.5">History</span>
        </button>
      </div>
    </nav>
  );
};
