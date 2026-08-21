import React from 'react';
import { Header } from './Header';
import { useApp } from '../context/AppContext';
import { FOOD_SECTOR_ID, FRESH_PRODUCE_COMPONENT, SECTOR_OPTIONS } from '../data/sectorData';

export const ComponentSelectionScreen: React.FC = () => {
  const { selectedSectorId, selectComponent, setCurrentScreen, theme } = useApp();
  const sector = SECTOR_OPTIONS.find((option) => option.id === selectedSectorId) || SECTOR_OPTIONS[0];
  const isTerracotta = theme === 'terracotta';

  return (
    <div className="min-h-screen bg-[#fbf9f5] pb-[90px]">
      <Header />
      <main className="max-w-md mx-auto w-full px-5 pt-5">
        <button onClick={() => setCurrentScreen('sector_selection')} className="text-sm text-[#594238] mb-4">
          <span className="material-symbols-outlined align-middle text-base">arrow_back</span> Sectors
        </button>
        <p className="text-xs uppercase tracking-[0.16em] text-[#9e3d00] font-semibold">{sector.name}</p>
        <h1 className="font-display text-[28px] font-bold leading-tight text-[#1b1c1a] mt-2">Choose a component</h1>
        <p className="text-sm text-[#594238] mt-2 mb-5">{selectedSectorId === FOOD_SECTOR_ID ? 'Photos are available only for fresh fruits and vegetables.' : 'This analysis uses sector data from data.gov.in.'}</p>
        <div className="flex flex-col gap-3">
          {sector.components.map((component) => {
            const isPhotoFlow = sector.id === FOOD_SECTOR_ID && component === FRESH_PRODUCE_COMPONENT;
            return (
              <button
                key={component}
                onClick={() => selectComponent(component)}
                className={`text-left rounded-2xl border p-4 flex items-center gap-3 transition-transform active:scale-[0.98] ${
                  isTerracotta ? 'border-[#e0c0b2] hover:bg-[#fff1e9]' : 'border-[#b9d9ca] hover:bg-[#e9f8ef]'
                }`}
              >
                <span className={`material-symbols-outlined ${isPhotoFlow ? 'text-[#9e3d00]' : 'text-[#0e6c4a]'}`}>{isPhotoFlow ? 'photo_camera' : 'analytics'}</span>
                <span className="flex-1">
                  <span className="block font-medium text-[#1b1c1a]">{component}</span>
                  <span className="block text-xs text-[#594238] mt-1">{isPhotoFlow ? 'Photo analysis and freshness score' : 'Sector-specific public data analysis'}</span>
                </span>
                <span className="material-symbols-outlined text-[#8a756b]">chevron_right</span>
              </button>
            );
          })}
        </div>
      </main>
    </div>
  );
};
