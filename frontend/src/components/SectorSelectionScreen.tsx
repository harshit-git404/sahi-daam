import React from 'react';
import { Header } from './Header';
import { useApp } from '../context/AppContext';
import { FOOD_SECTOR_ID, SECTOR_OPTIONS } from '../data/sectorData';

export const SectorSelectionScreen: React.FC = () => {
  const { selectSector, theme } = useApp();
  const isTerracotta = theme === 'terracotta';
  const featuredSector = SECTOR_OPTIONS.find((sector) => sector.id === FOOD_SECTOR_ID);
  const otherSectors = SECTOR_OPTIONS.filter((sector) => sector.id !== FOOD_SECTOR_ID);

  return (
    <div className="min-h-screen bg-[#fbf9f5] pb-[90px]">
      <Header />
      <main className="max-w-md mx-auto w-full px-5 pt-6">
        <button onClick={() => window.history.back()} className="mb-6 flex items-center gap-1 text-sm font-medium text-[#594238] transition-colors hover:text-[#9e3d00]">
          <span className="material-symbols-outlined align-middle text-base">arrow_back</span> Back
        </button>
        <section className="mb-6">
          <p className="mb-2 text-xs font-bold uppercase tracking-[0.18em] text-[#9e3d00]">Start an analysis</p>
          <h1 className="font-display text-[32px] font-bold leading-[1.08] tracking-tight text-[#1b1c1a]">What do you want to analyze?</h1>
          <p className="mt-3 max-w-sm text-[15px] leading-relaxed text-[#594238]">Choose a sector to explore public data, or check fresh produce with our photo-based AI analysis.</p>
        </section>

        {featuredSector && (
          <button
            key={featuredSector.id}
            onClick={() => selectSector(featuredSector.id)}
            className={`group relative mb-7 w-full overflow-hidden rounded-[26px] border p-5 text-left shadow-[0px_12px_28px_rgba(158,61,0,0.12)] transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0px_16px_32px_rgba(158,61,0,0.18)] active:translate-y-0 active:scale-[0.985] ${
              isTerracotta ? 'border-[#e0a58d] bg-[#fff0e8]' : 'border-[#b9d9ca] bg-[#e9f8ef] shadow-[0px_12px_28px_rgba(14,108,74,0.12)]'
            }`}
          >
            <div className="absolute -right-8 -top-10 h-32 w-32 rounded-full bg-white/30" />
            <div className="relative flex items-start justify-between gap-4">
              <div className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl ${isTerracotta ? 'bg-[#9e3d00] text-white' : 'bg-[#0e6c4a] text-white'}`}>
                <span className="material-symbols-outlined text-[30px]">{featuredSector.icon}</span>
              </div>
              <span className={`flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.08em] ${isTerracotta ? 'bg-white/75 text-[#9e3d00]' : 'bg-white/75 text-[#0e6c4a]'}`}>
                <span className="material-symbols-outlined text-[14px]">auto_awesome</span>
                Photo + AI analysis available
              </span>
            </div>
            <div className="relative mt-5 pr-8">
              <h2 className="font-display text-[21px] font-bold text-[#1b1c1a]">{featuredSector.name}</h2>
              <p className="mt-1.5 text-[13px] leading-relaxed text-[#594238]">{featuredSector.description}</p>
              <p className={`mt-4 text-xs font-bold ${isTerracotta ? 'text-[#9e3d00]' : 'text-[#0e6c4a]'}`}>Freshness scoring for fruits & vegetables</p>
            </div>
            <span className="material-symbols-outlined absolute bottom-5 right-5 text-[#8a756b] transition-transform group-hover:translate-x-1">arrow_forward</span>
          </button>
        )}

        <section>
          <div className="mb-3 flex items-end justify-between">
            <div>
              <p className="font-display text-[18px] font-bold text-[#1b1c1a]">Explore other sectors</p>
              <p className="mt-1 text-xs text-[#594238]">Data-powered insights across everyday systems</p>
            </div>
            <span className="rounded-full bg-[#f0eeea] px-2.5 py-1 text-[11px] font-semibold text-[#594238]">{otherSectors.length} more</span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {otherSectors.map((sector) => (
            <button
              key={sector.id}
              onClick={() => selectSector(sector.id)}
              className={`group relative min-h-[166px] rounded-2xl border p-4 text-left shadow-[0px_4px_16px_rgba(70,50,40,0.05)] transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0px_8px_20px_rgba(70,50,40,0.1)] active:scale-[0.97] ${
                isTerracotta ? 'border-[#e7d5cd] bg-white hover:border-[#e0a58d] hover:bg-[#fffaf7]' : 'border-[#d8e6dc] bg-white hover:border-[#a5d0b9] hover:bg-[#f7fcf8]'
              }`}
            >
              <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${isTerracotta ? 'bg-[#fff0e8] text-[#9e3d00]' : 'bg-[#e9f8ef] text-[#0e6c4a]'}`}>
                <span className="material-symbols-outlined text-[22px]">{sector.icon}</span>
              </span>
              <span className="mt-3 block pr-2">
                <span className="block font-display text-[14px] font-bold leading-tight text-[#1b1c1a]">{sector.name}</span>
                <span className="mt-1.5 block text-[11px] leading-[1.35] text-[#594238]">{sector.description}</span>
              </span>
              <span className="absolute bottom-3 right-3 flex items-center gap-0.5 text-[10px] font-semibold text-[#8a756b]">
                {sector.components.length} components
                <span className="material-symbols-outlined text-[16px] transition-transform group-hover:translate-x-0.5">chevron_right</span>
              </span>
            </button>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
};
