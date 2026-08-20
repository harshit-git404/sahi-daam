import React, { useEffect, useState } from 'react';
import { Header } from './Header';
import { useApp } from '../context/AppContext';
import { fetchSectorAnalysis } from '../services/api';

export const SectorAnalysisScreen: React.FC = () => {
  const { selectedSectorName, selectedComponent, setCurrentScreen } = useApp();
  const [result, setResult] = useState<{ summary: string; records: Record<string, unknown>[]; status?: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedComponent) return;
    setResult(null);
    setError(null);
    fetchSectorAnalysis(selectedSectorName, selectedComponent)
      .then(setResult)
      .catch((requestError: Error) => setError(requestError.message));
  }, [selectedSectorName, selectedComponent]);

  return (
    <div className="min-h-screen bg-[#fbf9f5] pb-[90px]">
      <Header />
      <main className="max-w-md mx-auto w-full px-5 pt-5">
        <button onClick={() => setCurrentScreen('component_selection')} className="text-sm text-[#594238] mb-4">
          <span className="material-symbols-outlined align-middle text-base">arrow_back</span> Components
        </button>
        <p className="text-xs uppercase tracking-[0.16em] text-[#0e6c4a] font-semibold">{selectedSectorName}</p>
        <h1 className="font-display text-[26px] font-bold leading-tight text-[#1b1c1a] mt-2">{selectedComponent}</h1>
        <p className="text-sm text-[#594238] mt-2 mb-5">Public data analysis from data.gov.in.</p>
        {!result && !error && <div className="rounded-2xl bg-[#e9f8ef] p-5 text-sm text-[#1b4332]">Fetching the latest available records...</div>}
        {error && <div className="rounded-2xl bg-[#fff1e9] border border-[#e0c0b2] p-5 text-sm text-[#7c2d12]">{error}</div>}
        {result && result.status !== 'API_AVAILABLE' && (
          <div className="rounded-2xl border border-[#e0c0b2] bg-[#fff1e9] p-5">
            <p className="font-display font-bold text-[#7c2d12]">{result.status === 'API_UNAVAILABLE' ? 'Coming soon' : 'No verified data source'}</p>
            <p className="mt-1 text-sm text-[#7c2d12]">{result.summary}</p>
          </div>
        )}
        {result && result.status === 'API_AVAILABLE' && (
          <>
            <div className="rounded-2xl bg-[#e9f8ef] p-5 mb-4">
              <p className="font-display font-bold text-[#1b4332]">Analysis ready</p>
              <p className="text-sm text-[#315b48] mt-1">{result.summary}</p>
            </div>
            <div className="flex flex-col gap-3">
              {result.records.slice(0, 10).map((record, index) => (
                <div key={index} className="rounded-2xl border border-[#d8e6dc] bg-white p-4">
                  <p className="text-xs text-[#6b7f72] mb-2">Record {index + 1}</p>
                  <div className="grid grid-cols-2 gap-x-3 gap-y-2 text-xs">
                    {Object.entries(record).slice(0, 8).map(([key, value]) => (
                      <div key={key}>
                        <p className="text-[#6b7f72] capitalize">{key.replaceAll('_', ' ')}</p>
                        <p className="font-medium text-[#1b1c1a] break-words">{String(value ?? 'N/A')}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
};
