import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Screen } from '../types';

interface HeaderProps {
  title?: string;
  showBack?: boolean;
  onBack?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ title, showBack, onBack }) => {
  const { currentScreen, setCurrentScreen, setIsDrawerOpen, theme, toggleTheme, selectedLocation } = useApp();
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  const isTerracotta = theme === 'terracotta';

  const handleBack = () => {
    if (onBack) {
      onBack();
      return;
    }
    if (currentScreen === 'bargain') {
      setCurrentScreen('price_breakdown');
    } else if (currentScreen === 'price_breakdown') {
      setCurrentScreen('quality_result');
    } else if (currentScreen === 'quality_result') {
      setCurrentScreen('scan');
    } else if (currentScreen === 'scan') {
      setCurrentScreen('home');
    } else {
      setCurrentScreen('home');
    }
  };

  const getDisplayTitle = () => {
    if (title) return title;
    if (currentScreen === 'home' || currentScreen === 'history') return 'Sahi Daam';
    if (currentScreen === 'quality_result') return 'Sahi Daam';
    if (currentScreen === 'price_breakdown') return 'Tomatoes';
    if (currentScreen === 'bargain') return 'Tomato Bargain';
    return 'Sahi Daam';
  };

  const shouldShowBackButton = showBack ?? (currentScreen !== 'home' && currentScreen !== 'history');

  return (
    <header className="sticky top-0 z-40 w-full bg-[#fbf9f5] border-b border-[#e4e2de]/60 shadow-[0px_4px_20px_rgba(211,84,0,0.06)] transition-colors">
      <div className="max-w-md mx-auto h-16 px-5 flex items-center justify-between">
        {/* Left Action */}
        {shouldShowBackButton ? (
          <button
            id="header-back-button"
            aria-label="Go back"
            onClick={handleBack}
            className={`w-10 h-10 -ml-2 rounded-full flex items-center justify-center transition-all active:scale-90 ${
              isTerracotta
                ? 'text-[#9e3d00] hover:bg-[#ffdbcd]/50'
                : 'text-[#012d1d] hover:bg-[#c1ecd4]/50'
            }`}
          >
            <span className="material-symbols-outlined text-[24px]">arrow_back</span>
          </button>
        ) : (
          <button
            id="header-menu-button"
            aria-label="Open menu"
            onClick={() => setIsDrawerOpen(true)}
            className={`w-10 h-10 -ml-2 rounded-full flex items-center justify-center transition-all active:scale-90 ${
              isTerracotta
                ? 'text-[#594238] hover:bg-[#e4e2de]'
                : 'text-[#414844] hover:bg-[#e2e3df]'
            }`}
          >
            <span className="material-symbols-outlined text-[24px]">menu</span>
          </button>
        )}

        {/* Center Title */}
        <h1
          id="header-app-title"
          onClick={() => setCurrentScreen('home')}
          className={`font-display text-[22px] font-bold tracking-tight cursor-pointer select-none truncate px-2 ${
            isTerracotta ? 'text-[#9e3d00]' : 'text-[#012d1d]'
          }`}
        >
          {getDisplayTitle()}
        </h1>

        {/* Right User Profile */}
        <div className="relative">
          <button
            id="header-profile-button"
            aria-label="User profile"
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className={`w-9 h-9 rounded-full overflow-hidden border-2 transition-transform active:scale-95 flex items-center justify-center ${
              isTerracotta ? 'border-[#ffb595]' : 'border-[#a5d0b9]'
            }`}
          >
            <img
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuCbA12FlcdstUUGVQxGgRA4MDIMmEYiGaMUMZsdBlmmIrhkucPenOSgqR1IIArGWb9mHvh2drqFptrfDExNnHQkIriEANc0KaV3KlIw_Zu6-4mzrhnxQXckY6xFCYIjkOJ3k7Pnl1hJGwzshV0Gu0BCUpkNbrdEI0NjMHbnSGQ6QePC8AAXykcxb2SGtIzOJwKqAUI1sLu-MGqOPpvFRF5bh6KcjlL62_e9S5v6t7wcAd0BH7I89I5evQ"
              alt="Ravi Kumar avatar"
              className="w-full h-full object-cover"
            />
          </button>

          {/* Profile Dropdown */}
          {showProfileMenu && (
            <div className="absolute right-0 mt-2 w-56 rounded-2xl bg-white shadow-xl border border-[#e4e2de] p-3 z-50 animate-in fade-in zoom-in-95 duration-150">
              <div className="flex items-center gap-3 pb-3 border-b border-[#e4e2de]">
                <img
                  src="https://lh3.googleusercontent.com/aida-public/AB6AXuCbA12FlcdstUUGVQxGgRA4MDIMmEYiGaMUMZsdBlmmIrhkucPenOSgqR1IIArGWb9mHvh2drqFptrfDExNnHQkIriEANc0KaV3KlIw_Zu6-4mzrhnxQXckY6xFCYIjkOJ3k7Pnl1hJGwzshV0Gu0BCUpkNbrdEI0NjMHbnSGQ6QePC8AAXykcxb2SGtIzOJwKqAUI1sLu-MGqOPpvFRF5bh6KcjlL62_e9S5v6t7wcAd0BH7I89I5evQ"
                  alt="Ravi"
                  className="w-10 h-10 rounded-full object-cover"
                />
                <div>
                  <p className="font-semibold text-sm text-[#1b1c1a]">Ravi Kumar</p>
                  <p className="text-xs text-[#594238] flex items-center gap-1">
                    <span className="material-symbols-outlined text-[12px]">location_on</span>
                    {selectedLocation.name}
                  </p>
                </div>
              </div>

              <div className="pt-2 space-y-1">
                <button
                  onClick={() => {
                    toggleTheme();
                    setShowProfileMenu(false);
                  }}
                  className="w-full text-left px-2.5 py-2 text-xs font-medium rounded-xl text-[#1b1c1a] hover:bg-[#f5f3ef] flex items-center justify-between"
                >
                  <span className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-[16px]">palette</span>
                    Color Theme
                  </span>
                  <span className="px-2 py-0.5 text-[10px] rounded-full bg-[#ffdbcd] text-[#9e3d00] font-semibold">
                    {isTerracotta ? 'Terracotta' : 'Forest Green'}
                  </span>
                </button>

                <button
                  onClick={() => {
                    setIsDrawerOpen(true);
                    setShowProfileMenu(false);
                  }}
                  className="w-full text-left px-2.5 py-2 text-xs font-medium rounded-xl text-[#1b1c1a] hover:bg-[#f5f3ef] flex items-center gap-2"
                >
                  <span className="material-symbols-outlined text-[16px]">tune</span>
                  Mandi Settings & Location
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
