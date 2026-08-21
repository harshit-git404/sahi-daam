import React from 'react';
import { Header } from './Header';
import { useApp } from '../context/AppContext';
import { PurchaseType } from '../types';

export const PurchaseTypeScreen: React.FC = () => {
  const { selectedProduce, setCurrentScreen, theme } = useApp();
  const isTerracotta = theme === 'terracotta';

  const choose = (type: string) => {
    setCurrentScreen(type === 'street_vendor' ? 'scan' : 'supermarket');
  };

  return (
    <div className="min-h-screen bg-[#fbf9f5] pb-[90px]">
      <Header title="Buying context" showBack onBack={() => setCurrentScreen('quality_result')} />
      <main className="max-w-md mx-auto w-full px-5 pt-6">
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-[#9e3d00]">{selectedProduce.name}</p>
        <h1 className="font-display text-[30px] font-bold leading-tight text-[#1b1c1a] mt-2">Where are you buying this?</h1>
        <p className="text-sm text-[#594238] mt-2 mb-6">Choose the path that matches your purchase so the comparison stays relevant.</p>
        <div className="flex flex-col gap-3">
          <button onClick={() => choose('street_vendor')} className={`rounded-2xl border p-5 text-left flex items-center gap-4 active:scale-[0.98] transition-transform ${isTerracotta ? 'border-[#e0c0b2] hover:bg-[#fff1e9]' : 'border-[#b9d9ca] hover:bg-[#e9f8ef]'}`}>
            <span className="material-symbols-outlined text-[30px] text-[#9e3d00]">storefront</span>
            <span className="flex-1"><span className="block font-display font-bold text-[#1b1c1a]">Street Vendor / Local Seller</span><span className="block text-xs text-[#594238] mt-1">Mandi reference price, fair range, and haggle analysis</span></span>
            <span className="material-symbols-outlined text-[#8a756b]">chevron_right</span>
          </button>
          <button onClick={() => choose('supermarket_online')} className={`rounded-2xl border p-5 text-left flex items-center gap-4 active:scale-[0.98] transition-transform ${isTerracotta ? 'border-[#e0c0b2] hover:bg-[#fff1e9]' : 'border-[#b9d9ca] hover:bg-[#e9f8ef]'}`}>
            <span className="material-symbols-outlined text-[30px] text-[#0e6c4a]">shopping_bag</span>
            <span className="flex-1"><span className="block font-display font-bold text-[#1b1c1a]">Supermarket / Online</span><span className="block text-xs text-[#594238] mt-1">Compare connected store prices when the service is available</span></span>
            <span className="material-symbols-outlined text-[#8a756b]">chevron_right</span>
          </button>
        </div>
      </main>
    </div>
  );
};
