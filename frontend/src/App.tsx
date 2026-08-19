import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { HomeScreen } from './components/HomeScreen';
import { ScanScreen } from './components/ScanScreen';
import { QualityResultScreen } from './components/QualityResultScreen';
import { PriceBreakdownScreen } from './components/PriceBreakdownScreen';
import { BargainScreen } from './components/BargainScreen';
import { HistoryScreen } from './components/HistoryScreen';
import { BottomNav } from './components/BottomNav';
import { DrawerMenu } from './components/DrawerMenu';
import { AudioHaggleModal } from './components/AudioHaggleModal';

const AppContent: React.FC = () => {
  const { currentScreen, isScanning } = useApp();

  return (
    <div className="min-h-screen bg-[#fbf9f5] flex flex-col justify-between font-body text-[#1b1c1a] antialiased">
      {/* Screen Router */}
      <div key={currentScreen} className="flex-1 animate-in fade-in slide-in-from-bottom-2 duration-300 ease-out">
        {currentScreen === 'home' && <HomeScreen />}
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
        <div className="fixed inset-0 z-[100] bg-[#fbf9f5]/90 backdrop-blur-sm flex flex-col items-center justify-center animate-in fade-in duration-200">
          <div className="w-20 h-20 relative flex items-center justify-center">
             <div className="absolute inset-0 rounded-full border-4 border-[#e4e2de]"></div>
             <div className="absolute inset-0 rounded-full border-4 border-t-[#9e3d00] animate-spin"></div>
             <span className="material-symbols-outlined text-[32px] text-[#9e3d00] animate-pulse">center_focus_strong</span>
          </div>
          <p className="mt-4 font-display font-semibold text-[#1b1c1a] animate-pulse">Scanning Produce...</p>
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
