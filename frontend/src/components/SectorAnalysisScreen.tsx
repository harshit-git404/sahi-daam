import React, { useEffect, useState } from 'react';
import { Header } from './Header';
import { useApp } from '../context/AppContext';
import { fetchSectorAnalysis } from '../services/api';
import { SectorAnalysisResult } from '../types';

// ------------------------------------------------------------------
// Sparkline SVG chart
// ------------------------------------------------------------------
const Sparkline: React.FC<{ history: { date: string; value: number }[] }> = ({ history }) => {
  if (!history || history.length < 2) return null;
  const W = 280, H = 60;
  const values = history.map((h) => h.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1)) * W;
    const y = H - ((v - min) / range) * (H - 10) - 5;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  return (
    <svg width={W} height={H} className="overflow-visible w-full">
      <polyline
        points={pts.join(' ')}
        fill="none"
        stroke="#0e6c4a"
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      <circle
        cx={pts[pts.length - 1].split(',')[0]}
        cy={pts[pts.length - 1].split(',')[1]}
        r="4"
        fill="#0e6c4a"
      />
    </svg>
  );
};

// ------------------------------------------------------------------
// Trend icon
// ------------------------------------------------------------------
const TrendIcon: React.FC<{ trend: string | undefined }> = ({ trend }) => {
  if (trend === 'UP')
    return <span className="material-symbols-outlined text-[#b91c1c] text-[20px]">trending_up</span>;
  if (trend === 'DOWN')
    return <span className="material-symbols-outlined text-[#006d37] text-[20px]">trending_down</span>;
  if (trend === 'STABLE')
    return <span className="material-symbols-outlined text-[#835100] text-[20px]">trending_flat</span>;
  return null;
};

// ------------------------------------------------------------------
// Main screen
// ------------------------------------------------------------------
export const SectorAnalysisScreen: React.FC = () => {
  const { selectedSectorName, selectedComponent, setCurrentScreen } = useApp();
  const [result, setResult] = useState<SectorAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!selectedComponent) return;
    setResult(null);
    setError(null);
    setLoading(true);
    fetchSectorAnalysis(selectedSectorName, selectedComponent)
      .then((data) => {
        setResult(data);
      })
      .catch((err: Error) => {
        setError(err.message);
      })
      .finally(() => setLoading(false));
  }, [selectedSectorName, selectedComponent]);

  const metric = result?.metric;
  const isAvailable = result?.status === 'API_AVAILABLE';
  const pct = metric?.percentage_change;
  const pctLabel = pct != null ? `${pct > 0 ? '+' : ''}${pct.toFixed(1)}%` : null;
  const periodsLabel =
    metric?.periods_available != null
      ? `${metric.periods_available} distinct period${metric.periods_available !== 1 ? 's' : ''}`
      : null;

  return (
    <div className="min-h-screen bg-[#fbf9f5] pb-[90px]">
      <Header />
      <main className="max-w-md mx-auto w-full px-5 pt-5">

        {/* Back nav */}
        <button
          onClick={() => setCurrentScreen('component_selection')}
          className="text-sm text-[#594238] mb-4 flex items-center gap-1"
        >
          <span className="material-symbols-outlined align-middle text-base">arrow_back</span>
          Components
        </button>

        {/* Title */}
        <p className="text-xs uppercase tracking-[0.16em] text-[#0e6c4a] font-semibold">
          {selectedSectorName}
        </p>
        <h1 className="font-display text-[26px] font-bold leading-tight text-[#1b1c1a] mt-2">
          {selectedComponent}
        </h1>
        <p className="text-sm text-[#594238] mt-2 mb-5">
          Public data analysis from data.gov.in.
        </p>

        {/* Loading skeleton */}
        {loading && (
          <div className="space-y-3 animate-pulse">
            <div className="h-20 rounded-2xl bg-[#e9f8ef]" />
            <div className="grid grid-cols-2 gap-3">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className="h-16 rounded-2xl bg-[#f5f3ef]" />
              ))}
            </div>
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <div className="rounded-2xl bg-[#fff1e9] border border-[#e0c0b2] p-5 text-sm text-[#7c2d12]">
            {error}
          </div>
        )}

        {/* Not available */}
        {!loading && result && !isAvailable && (
          <div className="rounded-2xl border border-[#e0c0b2] bg-[#fff1e9] p-5">
            <p className="font-display font-bold text-[#7c2d12] text-[16px]">
              {result.status === 'API_UNAVAILABLE'
                ? 'Coming soon — API unavailable'
                : 'No verified data source'}
            </p>
            <p className="mt-1 text-sm text-[#7c2d12] leading-relaxed">{result.summary}</p>
          </div>
        )}

        {/* Available — full dashboard */}
        {!loading && result && isAvailable && (
          <div className="flex flex-col gap-4">

            {/* Summary */}
            <div className="rounded-2xl bg-[#e9f8ef] p-5">
              <p className="font-display font-bold text-[#1b4332] text-[16px]">
                {metric?.name || 'Analysis'} ready
              </p>
              <p className="text-sm text-[#315b48] mt-1">{result.summary}</p>
            </div>

            {/* Stats grid */}
            {metric && (
              <section className="grid grid-cols-2 gap-3">
                {[
                  { label: 'Current', value: metric.current_value, suffix: metric.unit },
                  { label: `${periodsLabel ?? '10-period'} avg`, value: metric.average_10_days, suffix: metric.unit },
                  { label: 'High', value: metric.high_10_days, suffix: metric.unit },
                  { label: 'Low', value: metric.low_10_days, suffix: metric.unit },
                ].map(({ label, value, suffix }) => (
                  <div key={label} className="rounded-2xl border border-[#d8e6dc] bg-white p-4">
                    <p className="text-xs text-[#6b7f72] font-medium">{label}</p>
                    <p className="mt-1 font-display text-xl font-bold text-[#1b1c1a]">
                      {value == null ? '—' : `${value} ${suffix}`}
                    </p>
                  </div>
                ))}

                {/* Change + trend spanning full width */}
                <div className="col-span-2 rounded-2xl border border-[#d8e6dc] bg-white p-4 flex items-center justify-between">
                  <div>
                    <p className="text-xs text-[#6b7f72] font-medium">Change / trend</p>
                    <p className="mt-1 font-bold text-[#1b1c1a] text-[15px]">
                      {pctLabel ?? '—'}
                      {metric.trend && metric.trend !== 'UNAVAILABLE' && ` · ${metric.trend}`}
                    </p>
                    {periodsLabel && (
                      <p className="text-[11px] text-[#8a756b] mt-0.5">
                        Based on {periodsLabel}
                      </p>
                    )}
                  </div>
                  <TrendIcon trend={metric.trend} />
                </div>
              </section>
            )}

            {/* Sparkline chart */}
            {metric?.history && metric.history.length >= 2 && (
              <section className="rounded-2xl bg-white border border-[#d8e6dc] p-4">
                <p className="text-xs font-bold uppercase tracking-wider text-[#315b48] mb-3">
                  Historical trend
                </p>
                <Sparkline history={metric.history} />
                <div className="flex justify-between text-[10px] text-[#8a756b] mt-1.5 px-1">
                  <span>{metric.history[0]?.date}</span>
                  <span>{metric.history[metric.history.length - 1]?.date}</span>
                </div>
              </section>
            )}

            {/* Historical records list */}
            {result.records && result.records.length > 0 && (
              <div className="flex flex-col gap-3">
                {result.records.slice(0, 8).map((record, index) => (
                  <div key={index} className="rounded-2xl border border-[#d8e6dc] bg-white p-4">
                    <div className="grid grid-cols-2 gap-x-3 gap-y-2 text-xs">
                      {Object.entries(record)
                        .slice(0, 8)
                        .map(([key, value]) => (
                          <div key={key}>
                            <p className="text-[#6b7f72] capitalize">
                              {key.replaceAll('_', ' ')}
                            </p>
                            <p className="font-medium text-[#1b1c1a] break-words">
                              {String(value ?? '—')}
                            </p>
                          </div>
                        ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};
