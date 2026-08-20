import React from 'react';
import { Header } from './Header';
import { useApp } from '../context/AppContext';

export const SupermarketScreen: React.FC = () => {
  const { selectedProduce, setCurrentScreen, theme } = useApp();
  const isTerracotta = theme === 'terracotta';

  return (
    <div className="min-h-screen bg-[#fbf9f5] pb-[90px]">
      <Header title="Store comparison" showBack onBack={() => setCurrentScreen('purchase_type')} />
      <main className="max-w-md mx-auto w-full px-5 pt-6">
        <div className={`rounded-3xl border p-6 ${isTerracotta ? 'border-[#e0c0b2] bg-[#fff1e9]' : 'border-[#b9d9ca] bg-[#e9f8ef]'}`}>
          <span className="material-symbols-outlined text-[38px] text-[#0e6c4a]">shopping_bag</span>
          <p className="mt-5 text-xs font-bold uppercase tracking-[0.16em] text-[#0e6c4a]">{selectedProduce.name}</p>
          <h1 className="font-display text-[26px] font-bold text-[#1b1c1a] mt-2">Online comparison unavailable</h1>
          <p className="text-sm leading-relaxed text-[#315b48] mt-2">A connected supermarket or online-price service is not configured yet. No retailer price has been estimated.</p>
        </div>
        <button onClick={() => setCurrentScreen('purchase_type')} className="mt-5 w-full rounded-2xl border border-[#e0c0b2] bg-white py-4 font-display font-semibold text-[#9e3d00]">Choose another buying context</button>
      </main>
    </div>
  );
};
