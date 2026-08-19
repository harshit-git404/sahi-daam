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
  const { currentScreen } = useApp();

  return (
    <div className="min-h-screen bg-[#fbf9f5] flex flex-col justify-between font-body text-[#1b1c1a] antialiased">
      {/* Screen Router */}
      <div className="flex-1">
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
