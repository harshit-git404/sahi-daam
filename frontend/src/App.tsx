import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { HomeScreen } from './components/HomeScreen';
import { SectorSelectionScreen } from './components/SectorSelectionScreen';
import { ComponentSelectionScreen } from './components/ComponentSelectionScreen';
import { SectorAnalysisScreen } from './components/SectorAnalysisScreen';
import { ScanScreen } from './components/ScanScreen';
import { QualityResultScreen } from './components/QualityResultScreen';
import { PriceBreakdownScreen } from './components/PriceBreakdownScreen';
import { BargainScreen } from './components/BargainScreen';
import { HistoryScreen } from './components/HistoryScreen';
import { BottomNav } from './components/BottomNav';
import { DrawerMenu } from './components/DrawerMenu';
import { AudioHaggleModal } from './components/AudioHaggleModal';

const LOADING_MESSAGES = [
  "Analyzing produce visuals...",
  "Running vision ensemble models...",
  "Assessing freshness levels...",
  "Fetching live Mandi rates...",
  "Finalizing analysis..."
];

const AppContent: React.FC = () => {
  const { currentScreen, isScanning, apiError, setApiError } = useApp();
  const [loadingTextIdx, setLoadingTextIdx] = React.useState(0);

  React.useEffect(() => {
    if (isScanning) {
      setLoadingTextIdx(0);
      const interval = setInterval(() => {
        setLoadingTextIdx((prev) => (prev + 1) % LOADING_MESSAGES.length);
      }, 1500);
      return () => clearInterval(interval);
    }
  }, [isScanning]);

  return (
    <div className="min-h-screen bg-[#fbf9f5] flex flex-col justify-between font-body text-[#1b1c1a] antialiased">
      {/* Screen Router */}
      <div key={currentScreen} className="flex-1 animate-in fade-in slide-in-from-bottom-2 duration-300 ease-out">
        {currentScreen === 'home' && <HomeScreen />}
        {currentScreen === 'sector_selection' && <SectorSelectionScreen />}
        {currentScreen === 'component_selection' && <ComponentSelectionScreen />}
        {currentScreen === 'sector_analysis' && <SectorAnalysisScreen />}
        {currentScreen === 'scan' && <ScanScreen />}
        {currentScreen === 'quality_result' && <QualityResultScreen />}
        {currentScreen === 'price_breakdown' && <PriceBreakdownScreen />}
        {currentScreen === 'bargain' && <BargainScreen />}
        {currentScreen === 'history' && <HistoryScreen />}
      </div>

      {/* Global Navigation Shell */}
      <BottomNav />

      {/* Side Menu Drawer */}
      <DrawerMenu />

      {/* Audio Bargaining Modal */}
      <AudioHaggleModal />

      {/* Global Branded Loading Overlay */}
      {isScanning && (
        <div className="fixed inset-0 z-[100] bg-[#fbf9f5] flex flex-col items-center justify-center animate-in fade-in duration-200">
          <div className="w-24 h-24 relative flex items-center justify-center">
             <div className="absolute inset-0 rounded-full border-[6px] border-[#e4e2de]"></div>
             <div className="absolute inset-0 rounded-full border-[6px] border-t-[#9e3d00] animate-spin"></div>
             <span className="material-symbols-outlined text-[40px] text-[#9e3d00] animate-pulse">center_focus_strong</span>
          </div>
          <p className="mt-6 font-display text-[18px] font-semibold text-[#1b1c1a] animate-pulse transition-all duration-300">
            {LOADING_MESSAGES[loadingTextIdx]}
          </p>
        </div>
      )}

      {/* Global API Error Overlay */}
      {apiError && (
        <div className="fixed inset-0 z-[110] bg-black/60 backdrop-blur-sm flex items-center justify-center p-5 animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl p-6 w-full max-w-sm shadow-2xl flex flex-col items-center text-center">
            <div className="w-16 h-16 rounded-full bg-red-100 text-red-600 flex items-center justify-center mb-4">
              <span className="material-symbols-outlined text-[32px]">error</span>
            </div>
            <h3 className="font-display text-[20px] font-bold text-[#1b1c1a] mb-2">Connection Error</h3>
            <p className="text-[14px] text-[#594238] mb-6">{apiError}</p>
            <div className="flex gap-3 w-full">
              <button
                onClick={() => setApiError(null)}
                className="flex-1 py-3.5 rounded-2xl border border-[#e4e2de] text-[#1b1c1a] font-semibold active:scale-95 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setApiError(null);
                  // Allow user to try scanning again from home
                }}
                className="flex-1 py-3.5 rounded-2xl bg-[#9e3d00] text-white font-semibold active:scale-95 transition-all shadow-md"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}
