import React, { useEffect, useState } from 'react';
import { Header } from './Header';
import { useApp } from '../context/AppContext';
import { fetchSectorAnalysis } from '../services/api';
import {
  FuelDistrictStats,
  FuelTypeAnalytics,
  GenericDistrictStats,
  MetricAnalytics,
  SectorAnalysisResult,
  WastewaterDistrictStats,
  WastewaterMetricAnalytics,
} from '../types';

// ------------------------------------------------------------------
// Generic Sparkline SVG chart for single-metric sectors
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
// 1. District Fuel Bar Chart with Tooltips & 10D Baseline
// ------------------------------------------------------------------
interface DistrictFuelBarChartProps {
  districtName: string;
  stats: FuelDistrictStats;
  fuelType: 'petrol' | 'diesel';
  isCheapest: boolean;
  theme: string;
}

const DistrictFuelBarChart: React.FC<DistrictFuelBarChartProps> = ({
  districtName,
  stats,
  fuelType,
  isCheapest,
  theme,
}) => {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const isTerracotta = theme === 'terracotta';

  const history = stats.history || [];
  const prices = history.map((h) => h.price);
  const minPrice = prices.length ? Math.min(...prices) : 0;
  const maxPrice = prices.length ? Math.max(...prices) : 0;

  const svgWidth = 320;
  const svgHeight = 130;
  const padLeft = 32;
  const padRight = 16;
  const padTop = 26;
  const padBottom = 26;
  const chartWidth = svgWidth - padLeft - padRight;
  const chartHeight = svgHeight - padTop - padBottom;

  let yMin: number;
  let yMax: number;
  if (minPrice === maxPrice) {
    yMin = minPrice - 1.0;
    yMax = maxPrice + 1.0;
  } else {
    const diff = maxPrice - minPrice;
    const pad = Math.max(diff * 0.4, 0.4);
    yMin = Math.floor((minPrice - pad) * 10) / 10;
    yMax = Math.ceil((maxPrice + pad) * 10) / 10;
  }
  const yRange = yMax - yMin || 1;

  const count = history.length;
  const barWidth = 18;
  const gap = count > 1 ? (chartWidth - count * barWidth) / (count - 1) : 0;
  const avgY = padTop + chartHeight - ((stats.average_10_days - yMin) / yRange) * chartHeight;

  const isPetrol = fuelType === 'petrol';
  const barBaseColor = isPetrol
    ? (isTerracotta ? '#d9531e' : '#0e6c4a')
    : (isTerracotta ? '#8a5035' : '#2b6cb0');
  const barHighlightColor = isPetrol ? '#b91c1c' : '#1e3a8a';
  const cheapestGlowColor = '#15803d';

  const hoveredItem = hoveredIdx !== null ? history[hoveredIdx] : null;

  return (
    <div
      className={`rounded-2xl border bg-white p-4 transition-all duration-200 shadow-[0_2px_12px_rgba(0,0,0,0.04)] hover:shadow-[0_4px_16px_rgba(0,0,0,0.08)] ${
        isCheapest
          ? 'border-[#86efac] ring-2 ring-[#22c55e]/20 bg-[#f0fdf4]/30'
          : 'border-[#d8e6dc]'
      }`}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[18px] text-[#0e6c4a]">
            location_on
          </span>
          <h3 className="font-display text-[17px] font-bold text-[#1b1c1a]">
            {districtName}
          </h3>
        </div>
        {isCheapest ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-[#dcfce7] border border-[#86efac] px-2.5 py-0.5 text-[11px] font-bold text-[#15803d]">
            <span className="material-symbols-outlined text-[14px]">verified</span>
            Cheapest in Region
          </span>
        ) : stats.diff_from_cheapest != null && stats.diff_from_cheapest > 0 ? (
          <span className="rounded-full bg-[#f4f3f0] px-2 py-0.5 text-[11px] font-semibold text-[#6b7280]">
            +{stats.diff_from_cheapest.toFixed(2)}/L
          </span>
        ) : null}
      </div>

      <div className="grid grid-cols-3 gap-2 py-2 mb-2 border-y border-[#f0eee9] text-xs">
        <div>
          <p className="text-[11px] text-[#6b7f72]">Current Price</p>
          <p className="font-bold text-[15px] text-[#1b1c1a]">
            ₹{stats.current_price.toFixed(2)}
            <span className="text-[10px] font-normal text-[#8a756b]">/L</span>
          </p>
        </div>
        <div>
          <p className="text-[11px] text-[#6b7f72]">10-Day Avg</p>
          <p className="font-bold text-[14px] text-[#4a5568]">
            ₹{stats.average_10_days.toFixed(2)}
          </p>
        </div>
        <div>
          <p className="text-[11px] text-[#6b7f72]">10D Range</p>
          <p className="font-semibold text-[12px] text-[#4a5568]">
            ₹{stats.low_10_days.toFixed(2)} – {stats.high_10_days.toFixed(2)}
          </p>
        </div>
      </div>

      <div className="relative w-full pt-1">
        {hoveredItem && (
          <div
            className="absolute top-0 left-1/2 -translate-x-1/2 z-10 pointer-events-none transition-all duration-150"
            style={{
              left: `${Math.min(
                Math.max(
                  padLeft + (hoveredIdx ?? 0) * (barWidth + gap) + barWidth / 2,
                  60,
                ),
                svgWidth - 60,
              )}px`,
            }}
          >
            <div className="flex items-center gap-1.5 rounded-lg bg-[#1e293b] text-white px-2.5 py-1 text-[11px] shadow-lg whitespace-nowrap">
              <span className="text-[#94a3b8]">{hoveredItem.display_date}:</span>
              <span className="font-bold text-[#f8fafc]">
                ₹{hoveredItem.price.toFixed(2)}/L
              </span>
              {hoveredItem.price === stats.low_10_days && (
                <span className="text-[#4ade80] text-[10px] font-semibold">
                  (Lowest)
                </span>
              )}
            </div>
          </div>
        )}

        <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-auto overflow-visible select-none">
          <text x={padLeft - 6} y={padTop + 4} textAnchor="end" fontSize="9" fill="#94a3b8" fontWeight="500">
            ₹{yMax.toFixed(1)}
          </text>
          <text x={padLeft - 6} y={padTop + chartHeight} textAnchor="end" fontSize="9" fill="#94a3b8" fontWeight="500">
            ₹{yMin.toFixed(1)}
          </text>

          <line x1={padLeft} y1={padTop} x2={svgWidth - padRight} y2={padTop} stroke="#f1f5f9" strokeWidth="1" />
          <line x1={padLeft} y1={padTop + chartHeight} x2={svgWidth - padRight} y2={padTop + chartHeight} stroke="#e2e8f0" strokeWidth="1" />

          <line x1={padLeft} y1={avgY} x2={svgWidth - padRight} y2={avgY} stroke="#d97706" strokeWidth="1.5" strokeDasharray="4 3" />
          <text x={svgWidth - padRight} y={avgY - 4} textAnchor="end" fontSize="9" fill="#d97706" fontWeight="700">
            10D Avg: ₹{stats.average_10_days.toFixed(2)}
          </text>

          {history.map((entry, idx) => {
            const x = padLeft + idx * (barWidth + gap);
            const normalizedHeight = ((entry.price - yMin) / yRange) * chartHeight;
            const barH = Math.max(normalizedHeight, 4);
            const y = padTop + chartHeight - barH;
            const isHovered = hoveredIdx === idx;
            const isLowestDay = entry.price === stats.low_10_days && stats.low_10_days < stats.high_10_days;

            return (
              <g
                key={entry.date}
                className="cursor-pointer"
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                onClick={() => setHoveredIdx(idx)}
              >
                <rect x={x - 2} y={padTop} width={barWidth + 4} height={chartHeight + padBottom} fill="transparent" />
                <rect
                  x={x}
                  y={y}
                  width={barWidth}
                  height={barH}
                  rx="3"
                  ry="3"
                  fill={isHovered ? barHighlightColor : isLowestDay ? cheapestGlowColor : isCheapest ? '#16a34a' : barBaseColor}
                  opacity={isHovered ? 1 : 0.88}
                  className="transition-all duration-150"
                />
                {isHovered && (
                  <rect x={x - 1.5} y={y - 1.5} width={barWidth + 3} height={barH + 3} rx="4.5" fill="none" stroke={barHighlightColor} strokeWidth="1.5" />
                )}
              </g>
            );
          })}
        </svg>

        <div className="flex justify-between items-center text-[10px] text-[#8a756b] mt-1 px-1">
          <span>{history[0]?.display_date.replace(', 2026', '') || 'Aug 12'}</span>
          <span className="text-[#94a3b8]">10-Day Timeline</span>
          <span className="font-semibold text-[#1b1c1a]">
            {history[history.length - 1]?.display_date.replace(', 2026', '') || 'Aug 21'}
          </span>
        </div>
      </div>
    </div>
  );
};

// ------------------------------------------------------------------
// 2. Generic Multi-Sector District Bar Chart (Wastewater, E-Waste, Chemicals, Construction, Procurement)
// ------------------------------------------------------------------
interface GenericDistrictBarChartProps {
  districtName: string;
  stats: GenericDistrictStats;
  unit: string;
  isHighest: boolean;
  theme: string;
  accentColor?: string;
  highlightColor?: string;
}

const GenericDistrictBarChart: React.FC<GenericDistrictBarChartProps> = ({
  districtName,
  stats,
  unit,
  isHighest,
  theme,
  accentColor = '#0f766e',
  highlightColor = '#0369a1',
}) => {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const isTerracotta = theme === 'terracotta';

  const history = stats.history || [];
  const values = history.map((h) => h.value);
  const minVal = values.length ? Math.min(...values) : 0;
  const maxVal = values.length ? Math.max(...values) : 0;

  const svgWidth = 320;
  const svgHeight = 130;
  const padLeft = 36;
  const padRight = 16;
  const padTop = 26;
  const padBottom = 26;
  const chartWidth = svgWidth - padLeft - padRight;
  const chartHeight = svgHeight - padTop - padBottom;

  let yMin: number;
  let yMax: number;
  if (minVal === maxVal) {
    yMin = Math.max(0, minVal - 1.0);
    yMax = maxVal + 1.0;
  } else {
    const diff = maxVal - minVal;
    const pad = Math.max(diff * 0.35, 0.4);
    yMin = Math.max(0, Math.floor((minVal - pad) * 10) / 10);
    yMax = Math.ceil((maxVal + pad) * 10) / 10;
  }
  const yRange = yMax - yMin || 1;

  const count = history.length;
  const barWidth = 18;
  const gap = count > 1 ? (chartWidth - count * barWidth) / (count - 1) : 0;
  const avgY = padTop + chartHeight - ((stats.average_10_days - yMin) / yRange) * chartHeight;

  const barBaseColor = isTerracotta ? '#9e3d00' : accentColor;
  const barHoverColor = isTerracotta ? '#7c2d12' : highlightColor;
  const peakColor = isTerracotta ? '#ea580c' : '#0284c7';

  const hoveredItem = hoveredIdx !== null ? history[hoveredIdx] : null;

  return (
    <div
      className={`rounded-2xl border bg-white p-4 transition-all duration-200 shadow-[0_2px_12px_rgba(0,0,0,0.04)] hover:shadow-[0_4px_16px_rgba(0,0,0,0.08)] ${
        isHighest
          ? 'border-[#93c5fd] ring-2 ring-[#3b82f6]/20 bg-[#eff6ff]/30'
          : 'border-[#d8e6dc]'
      }`}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[18px] text-[#0f766e]">
            location_on
          </span>
          <h3 className="font-display text-[17px] font-bold text-[#1b1c1a]">
            {districtName}
          </h3>
        </div>
        {isHighest ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-[#dbeafe] border border-[#bfdbfe] px-2.5 py-0.5 text-[11px] font-bold text-[#1d4ed8]">
            <span className="material-symbols-outlined text-[14px]">leaderboard</span>
            Highest in Region
          </span>
        ) : stats.diff_from_highest != null && stats.diff_from_highest > 0 ? (
          <span className="rounded-full bg-[#f4f3f0] px-2 py-0.5 text-[11px] font-semibold text-[#6b7280]">
            -{stats.diff_from_highest.toFixed(1)} {unit} vs Peak
          </span>
        ) : null}
      </div>

      <div className="grid grid-cols-3 gap-2 py-2 mb-2 border-y border-[#f0eee9] text-xs">
        <div>
          <p className="text-[11px] text-[#6b7f72]">Current</p>
          <p className="font-bold text-[15px] text-[#1b1c1a]">
            {stats.current_value.toFixed(1)}
            <span className="text-[10px] font-normal text-[#8a756b]"> {unit}</span>
          </p>
        </div>
        <div>
          <p className="text-[11px] text-[#6b7f72]">10-Day Avg</p>
          <p className="font-bold text-[14px] text-[#4a5568]">
            {stats.average_10_days.toFixed(1)} {unit}
          </p>
        </div>
        <div>
          <p className="text-[11px] text-[#6b7f72]">10D Range</p>
          <p className="font-semibold text-[12px] text-[#4a5568]">
            {stats.low_10_days.toFixed(1)} – {stats.high_10_days.toFixed(1)}
          </p>
        </div>
      </div>

      <div className="relative w-full pt-1">
        {hoveredItem && (
          <div
            className="absolute top-0 left-1/2 -translate-x-1/2 z-10 pointer-events-none transition-all duration-150"
            style={{
              left: `${Math.min(
                Math.max(
                  padLeft + (hoveredIdx ?? 0) * (barWidth + gap) + barWidth / 2,
                  60,
                ),
                svgWidth - 60,
              )}px`,
            }}
          >
            <div className="flex items-center gap-1.5 rounded-lg bg-[#0f172a] text-white px-2.5 py-1 text-[11px] shadow-lg whitespace-nowrap">
              <span className="text-[#94a3b8]">{hoveredItem.display_date}:</span>
              <span className="font-bold text-[#38bdf8]">
                {hoveredItem.value.toFixed(1)} {unit}
              </span>
              {hoveredItem.value === stats.low_10_days && (
                <span className="text-[#fca5a5] text-[10px] font-semibold">
                  (Holiday Dip)
                </span>
              )}
            </div>
          </div>
        )}

        <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-auto overflow-visible select-none">
          <text x={padLeft - 6} y={padTop + 4} textAnchor="end" fontSize="9" fill="#94a3b8" fontWeight="500">
            {yMax.toFixed(1)}
          </text>
          <text x={padLeft - 6} y={padTop + chartHeight} textAnchor="end" fontSize="9" fill="#94a3b8" fontWeight="500">
            {yMin.toFixed(1)}
          </text>

          <line x1={padLeft} y1={padTop} x2={svgWidth - padRight} y2={padTop} stroke="#f1f5f9" strokeWidth="1" />
          <line x1={padLeft} y1={padTop + chartHeight} x2={svgWidth - padRight} y2={padTop + chartHeight} stroke="#e2e8f0" strokeWidth="1" />

          <line x1={padLeft} y1={avgY} x2={svgWidth - padRight} y2={avgY} stroke="#0284c7" strokeWidth="1.5" strokeDasharray="4 3" />
          <text x={svgWidth - padRight} y={avgY - 4} textAnchor="end" fontSize="9" fill="#0284c7" fontWeight="700">
            10D Avg: {stats.average_10_days.toFixed(1)} {unit}
          </text>

          {history.map((entry, idx) => {
            const x = padLeft + idx * (barWidth + gap);
            const normalizedHeight = ((entry.value - yMin) / yRange) * chartHeight;
            const barH = Math.max(normalizedHeight, 4);
            const y = padTop + chartHeight - barH;
            const isHovered = hoveredIdx === idx;
            const isPeak = entry.value === stats.high_10_days;

            return (
              <g
                key={entry.date}
                className="cursor-pointer"
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                onClick={() => setHoveredIdx(idx)}
              >
                <rect x={x - 2} y={padTop} width={barWidth + 4} height={chartHeight + padBottom} fill="transparent" />
                <rect
                  x={x}
                  y={y}
                  width={barWidth}
                  height={barH}
                  rx="3"
                  ry="3"
                  fill={isHovered ? barHoverColor : isPeak ? peakColor : isHighest ? '#2563eb' : barBaseColor}
                  opacity={isHovered ? 1 : 0.88}
                  className="transition-all duration-150"
                />
                {isHovered && (
                  <rect x={x - 1.5} y={y - 1.5} width={barWidth + 3} height={barH + 3} rx="4.5" fill="none" stroke={barHoverColor} strokeWidth="1.5" />
                )}
              </g>
            );
          })}
        </svg>

        <div className="flex justify-between items-center text-[10px] text-[#8a756b] mt-1 px-1">
          <span>{history[0]?.display_date.replace(', 2026', '') || 'Aug 12'}</span>
          <span className="text-[#94a3b8]">Aug 15: Holiday Dip</span>
          <span className="font-semibold text-[#1b1c1a]">
            {history[history.length - 1]?.display_date.replace(', 2026', '') || 'Aug 21'}
          </span>
        </div>
      </div>
    </div>
  );
};

// ------------------------------------------------------------------
// Main SectorAnalysisScreen Component
// ------------------------------------------------------------------
export const SectorAnalysisScreen: React.FC = () => {
  const { selectedSectorName, selectedComponent, setCurrentScreen, theme } = useApp();
  const [result, setResult] = useState<SectorAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeFuel, setActiveFuel] = useState<'petrol' | 'diesel'>('petrol');
  const [activeWastewaterMetric, setActiveWastewaterMetric] = useState<'effluent' | 'treated'>('effluent');
  const [activeGenericMetric, setActiveGenericMetric] = useState<'primary' | 'secondary'>('primary');
  const [showRawRecords, setShowRawRecords] = useState(false);

  const isTerracotta = theme === 'terracotta';

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
  const fuelData = result?.fuel_data;
  const wastewaterData = result?.wastewater_data;
  const analyticsData = result?.analytics_data;

  const isFuelComponent = Boolean(fuelData || selectedComponent === 'Fossil fuels like petrol, diesel, and coal');
  const isWastewaterComponent = Boolean(wastewaterData || selectedComponent === 'Industrial wastewater and factory effluents');
  const isGenericAnalyticsComponent = Boolean(analyticsData);

  const currentFuelAnalytics: FuelTypeAnalytics | undefined = fuelData ? fuelData[activeFuel] : undefined;
  const currentWastewaterAnalytics: WastewaterMetricAnalytics | undefined = wastewaterData ? wastewaterData[activeWastewaterMetric] : undefined;
  const currentGenericAnalytics: MetricAnalytics | undefined = analyticsData ? analyticsData[activeGenericMetric] : undefined;

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
        {/* Back navigation */}
        <button
          onClick={() => setCurrentScreen('component_selection')}
          className="text-sm text-[#594238] mb-4 flex items-center gap-1 transition-colors hover:text-[#9e3d00]"
        >
          <span className="material-symbols-outlined align-middle text-base">
            arrow_back
          </span>
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
          {isFuelComponent || isWastewaterComponent || isGenericAnalyticsComponent
            ? '10-day historical analytics across regional districts.'
            : 'Public data analysis from data.gov.in.'}
        </p>

        {/* Loading skeleton */}
        {loading && (
          <div className="space-y-3 animate-pulse">
            <div className="h-20 rounded-2xl bg-[#e9f8ef]" />
            <div className="grid grid-cols-2 gap-3">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className="h-24 rounded-2xl bg-[#f5f3ef]" />
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
            <p className="mt-1 text-sm text-[#7c2d12] leading-relaxed">
              {result.summary}
            </p>
          </div>
        )}

        {/* 1. Fuel Analytics View */}
        {!loading && result && isAvailable && isFuelComponent && currentFuelAnalytics && (
          <div className="flex flex-col gap-4">
            <div className="rounded-2xl bg-[#f0eee9] p-1.5 flex items-center gap-1.5 shadow-inner">
              <button
                onClick={() => setActiveFuel('petrol')}
                className={`flex-1 py-2.5 px-3 rounded-xl font-display font-bold text-sm flex items-center justify-center gap-1.5 transition-all duration-200 ${
                  activeFuel === 'petrol'
                    ? isTerracotta ? 'bg-[#9e3d00] text-white shadow-md' : 'bg-[#0e6c4a] text-white shadow-md'
                    : 'text-[#594238] hover:bg-white/60'
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">local_gas_station</span>
                Petrol (₹107.74 – ₹109.06)
              </button>

              <button
                onClick={() => setActiveFuel('diesel')}
                className={`flex-1 py-2.5 px-3 rounded-xl font-display font-bold text-sm flex items-center justify-center gap-1.5 transition-all duration-200 ${
                  activeFuel === 'diesel'
                    ? isTerracotta ? 'bg-[#9e3d00] text-white shadow-md' : 'bg-[#0e6c4a] text-white shadow-md'
                    : 'text-[#594238] hover:bg-white/60'
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">oil_barrel</span>
                Diesel (₹99.65 – ₹101.00)
              </button>
            </div>

            <div className="rounded-2xl border border-[#bbf7d0] bg-[#f0fdf4] p-4 flex items-start gap-3 shadow-sm">
              <div className="rounded-xl bg-[#22c55e] text-white p-2 shrink-0">
                <span className="material-symbols-outlined text-[20px]">savings</span>
              </div>
              <div className="text-xs text-[#166534] leading-relaxed">
                <p className="font-bold text-[13px] text-[#14532d] mb-0.5">
                  Best Regional Deal: {currentFuelAnalytics.cheapest_district}
                </p>
                <p>
                  Refuel in <strong>{currentFuelAnalytics.cheapest_district}</strong> at{' '}
                  <strong>₹{currentFuelAnalytics.cheapest_price.toFixed(2)}/L</strong> to save up to{' '}
                  <strong>₹{currentFuelAnalytics.max_savings_per_litre.toFixed(2)} per litre</strong> across the 4 districts.
                </p>
              </div>
            </div>

            <section className="flex flex-col gap-3">
              <div className="flex items-center justify-between px-1">
                <h2 className="font-display font-bold text-[17px] text-[#1b1c1a]">4-District 10-Day Price Graphs</h2>
                <span className="text-[11px] font-semibold text-[#6b7f72]">Hover/tap bars for dates</span>
              </div>

              {Object.entries(currentFuelAnalytics.districts).map(([districtName, stats]) => (
                <DistrictFuelBarChart
                  key={districtName}
                  districtName={districtName}
                  stats={stats}
                  fuelType={activeFuel}
                  isCheapest={stats.is_cheapest ?? false}
                  theme={theme}
                />
              ))}
            </section>

            <section className="rounded-2xl border border-[#d8e6dc] bg-white p-4">
              <h3 className="font-display font-bold text-[15px] text-[#1b1c1a] mb-3">
                Regional Price Matrix ({currentFuelAnalytics.fuel_name})
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="border-b border-[#e2e8f0] text-[#64748b] font-semibold">
                      <th className="pb-2">District</th>
                      <th className="pb-2 text-right">Current</th>
                      <th className="pb-2 text-right">10D Avg</th>
                      <th className="pb-2 text-right">Diff vs Best</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#f1f5f9]">
                    {Object.entries(currentFuelAnalytics.districts)
                      .sort((a, b) => a[1].current_price - b[1].current_price)
                      .map(([districtName, stats]) => (
                        <tr key={districtName} className="hover:bg-[#f8fafc]">
                          <td className="py-2.5 font-medium text-[#1e293b] flex items-center gap-1">
                            {districtName} {stats.is_cheapest && <span className="text-[#16a34a] font-bold">⭐</span>}
                          </td>
                          <td className="py-2.5 text-right font-bold text-[#0f172a]">₹{stats.current_price.toFixed(2)}</td>
                          <td className="py-2.5 text-right text-[#475569]">₹{stats.average_10_days.toFixed(2)}</td>
                          <td className="py-2.5 text-right">
                            {stats.is_cheapest ? (
                              <span className="font-bold text-[#16a34a]">Lowest</span>
                            ) : (
                              <span className="text-[#64748b]">+₹{(stats.diff_from_cheapest ?? 0).toFixed(2)}</span>
                            )}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        )}

        {/* 2. Wastewater & Industrial Effluents View */}
        {!loading && result && isAvailable && isWastewaterComponent && currentWastewaterAnalytics && (
          <div className="flex flex-col gap-4">
            <div className="rounded-2xl bg-[#f0eee9] p-1.5 flex items-center gap-1.5 shadow-inner">
              <button
                onClick={() => setActiveWastewaterMetric('effluent')}
                className={`flex-1 py-2.5 px-3 rounded-xl font-display font-bold text-sm flex items-center justify-center gap-1.5 transition-all duration-200 ${
                  activeWastewaterMetric === 'effluent'
                    ? isTerracotta ? 'bg-[#9e3d00] text-white shadow-md' : 'bg-[#0f766e] text-white shadow-md'
                    : 'text-[#594238] hover:bg-white/60'
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">factory</span>
                Industrial Effluent (MLD)
              </button>

              <button
                onClick={() => setActiveWastewaterMetric('treated')}
                className={`flex-1 py-2.5 px-3 rounded-xl font-display font-bold text-sm flex items-center justify-center gap-1.5 transition-all duration-200 ${
                  activeWastewaterMetric === 'treated'
                    ? isTerracotta ? 'bg-[#9e3d00] text-white shadow-md' : 'bg-[#0284c7] text-white shadow-md'
                    : 'text-[#594238] hover:bg-white/60'
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">water_drop</span>
                Treated Discharge (MLD)
              </button>
            </div>

            <div
              className={`rounded-2xl border p-4 flex items-start gap-3 shadow-sm ${
                activeWastewaterMetric === 'effluent' ? 'border-[#fecaca] bg-[#fff5f5]' : 'border-[#bae6fd] bg-[#f0f9ff]'
              }`}
            >
              <div
                className={`rounded-xl p-2 shrink-0 text-white ${
                  activeWastewaterMetric === 'effluent' ? 'bg-[#dc2626]' : 'bg-[#0284c7]'
                }`}
              >
                <span className="material-symbols-outlined text-[20px]">
                  {activeWastewaterMetric === 'effluent' ? 'warning' : 'verified'}
                </span>
              </div>
              <div className="text-xs leading-relaxed">
                <p className={`font-bold text-[13px] mb-0.5 ${activeWastewaterMetric === 'effluent' ? 'text-[#991b1b]' : 'text-[#0369a1]'}`}>
                  {activeWastewaterMetric === 'effluent'
                    ? `Highest Industrial Load: ${currentWastewaterAnalytics.highest_district}`
                    : `Highest Treatment Output: ${currentWastewaterAnalytics.highest_district}`}
                </p>
                <p className={activeWastewaterMetric === 'effluent' ? 'text-[#7f1d1d]' : 'text-[#075985]'}>
                  {activeWastewaterMetric === 'effluent' ? (
                    <>
                      <strong>{currentWastewaterAnalytics.highest_district}</strong> accounts for{' '}
                      <strong>{currentWastewaterAnalytics.highest_volume.toFixed(1)} MLD</strong> (
                      {Math.round((currentWastewaterAnalytics.highest_volume / currentWastewaterAnalytics.total_regional_volume) * 100)}% of regional discharge).
                    </>
                  ) : (
                    <>
                      <strong>{currentWastewaterAnalytics.highest_district}</strong> leads municipal wastewater treatment with{' '}
                      <strong>{currentWastewaterAnalytics.highest_volume.toFixed(1)} MLD</strong> daily treated effluent output.
                    </>
                  )}
                </p>
              </div>
            </div>

            <section className="flex flex-col gap-3">
              <div className="flex items-center justify-between px-1">
                <h2 className="font-display font-bold text-[17px] text-[#1b1c1a]">4-District 10-Day Discharge Graphs</h2>
                <span className="text-[11px] font-semibold text-[#6b7f72]">Hover/tap bars for dates</span>
              </div>

              {Object.entries(currentWastewaterAnalytics.districts).map(([districtName, stats]) => {
                const genericWwStats: GenericDistrictStats = {
                  current_value: stats.current_volume,
                  average_10_days: stats.average_10_days,
                  high_10_days: stats.high_10_days,
                  low_10_days: stats.low_10_days,
                  percentage_change: stats.percentage_change,
                  trend: stats.trend,
                  history: stats.history.map((h) => ({
                    date: h.date,
                    display_date: h.display_date,
                    value: h.volume,
                  })),
                  periods_available: stats.periods_available,
                  is_highest: stats.is_highest,
                  diff_from_highest: stats.diff_from_highest,
                };
                return (
                  <GenericDistrictBarChart
                    key={districtName}
                    districtName={districtName}
                    stats={genericWwStats}
                    unit={currentWastewaterAnalytics.unit}
                    isHighest={stats.is_highest ?? false}
                    theme={theme}
                    accentColor="#0f766e"
                    highlightColor="#0284c7"
                  />
                );
              })}
            </section>

            <section className="rounded-2xl border border-[#d8e6dc] bg-white p-4">
              <h3 className="font-display font-bold text-[15px] text-[#1b1c1a] mb-3">
                Regional Discharge Matrix ({currentWastewaterAnalytics.metric_name})
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="border-b border-[#e2e8f0] text-[#64748b] font-semibold">
                      <th className="pb-2">District</th>
                      <th className="pb-2 text-right">Current</th>
                      <th className="pb-2 text-right">10D Avg</th>
                      <th className="pb-2 text-right">Regional Share</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#f1f5f9]">
                    {Object.entries(currentWastewaterAnalytics.districts)
                      .sort((a, b) => b[1].current_volume - a[1].current_volume)
                      .map(([districtName, stats]) => {
                        const share = Math.round(
                          (stats.current_volume / currentWastewaterAnalytics.total_regional_volume) * 100,
                        );
                        return (
                          <tr key={districtName} className="hover:bg-[#f8fafc]">
                            <td className="py-2.5 font-medium text-[#1e293b] flex items-center gap-1">
                              {districtName} {stats.is_highest && <span className="text-[#dc2626] font-bold">⚠️</span>}
                            </td>
                            <td className="py-2.5 text-right font-bold text-[#0f172a]">{stats.current_volume.toFixed(1)} MLD</td>
                            <td className="py-2.5 text-right text-[#475569]">{stats.average_10_days.toFixed(1)} MLD</td>
                            <td className="py-2.5 text-right font-medium text-[#0284c7]">{share}%</td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        )}

        {/* 3. Generic Analytics View (E-Waste, Chemicals, Construction, Procurement) */}
        {!loading && result && isAvailable && isGenericAnalyticsComponent && currentGenericAnalytics && analyticsData && (
          <div className="flex flex-col gap-4">
            <div className="rounded-2xl bg-[#f0eee9] p-1.5 flex items-center gap-1.5 shadow-inner">
              <button
                onClick={() => setActiveGenericMetric('primary')}
                className={`flex-1 py-2.5 px-3 rounded-xl font-display font-bold text-sm flex items-center justify-center gap-1.5 transition-all duration-200 ${
                  activeGenericMetric === 'primary'
                    ? isTerracotta ? 'bg-[#9e3d00] text-white shadow-md' : 'bg-[#0f766e] text-white shadow-md'
                    : 'text-[#594238] hover:bg-white/60'
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">analytics</span>
                {analyticsData.primary_label}
              </button>

              <button
                onClick={() => setActiveGenericMetric('secondary')}
                className={`flex-1 py-2.5 px-3 rounded-xl font-display font-bold text-sm flex items-center justify-center gap-1.5 transition-all duration-200 ${
                  activeGenericMetric === 'secondary'
                    ? isTerracotta ? 'bg-[#9e3d00] text-white shadow-md' : 'bg-[#0284c7] text-white shadow-md'
                    : 'text-[#594238] hover:bg-white/60'
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">recycling</span>
                {analyticsData.secondary_label}
              </button>
            </div>

            <div className="rounded-2xl border border-[#bae6fd] bg-[#f0f9ff] p-4 flex items-start gap-3 shadow-sm">
              <div className="rounded-xl p-2 shrink-0 text-white bg-[#0284c7]">
                <span className="material-symbols-outlined text-[20px]">insights</span>
              </div>
              <div className="text-xs text-[#075985] leading-relaxed">
                <p className="font-bold text-[13px] text-[#0369a1] mb-0.5">
                  Regional Leader: {currentGenericAnalytics.highest_district} ({currentGenericAnalytics.highest_value.toFixed(1)} {currentGenericAnalytics.unit})
                </p>
                <p>
                  <strong>{currentGenericAnalytics.highest_district}</strong> accounts for{' '}
                  <strong>
                    {Math.round(
                      (currentGenericAnalytics.highest_value / currentGenericAnalytics.total_regional_volume) * 100,
                    )}%
                  </strong>{' '}
                  of the region's 4-district total. Noticeable downtime and dips observed on Aug 15–16.
                </p>
              </div>
            </div>

            <section className="flex flex-col gap-3">
              <div className="flex items-center justify-between px-1">
                <h2 className="font-display font-bold text-[17px] text-[#1b1c1a]">
                  4-District 10-Day Historical Graphs
                </h2>
                <span className="text-[11px] font-semibold text-[#6b7f72]">Hover/tap bars for dates</span>
              </div>

              {Object.entries(currentGenericAnalytics.districts).map(([districtName, stats]) => (
                <GenericDistrictBarChart
                  key={districtName}
                  districtName={districtName}
                  stats={stats}
                  unit={currentGenericAnalytics.unit}
                  isHighest={stats.is_highest ?? false}
                  theme={theme}
                  accentColor="#0f766e"
                  highlightColor="#0284c7"
                />
              ))}
            </section>

            <section className="rounded-2xl border border-[#d8e6dc] bg-white p-4">
              <h3 className="font-display font-bold text-[15px] text-[#1b1c1a] mb-3">
                Regional Comparison Matrix ({currentGenericAnalytics.metric_name})
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="border-b border-[#e2e8f0] text-[#64748b] font-semibold">
                      <th className="pb-2">District</th>
                      <th className="pb-2 text-right">Current</th>
                      <th className="pb-2 text-right">10D Avg</th>
                      <th className="pb-2 text-right">Regional Share</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#f1f5f9]">
                    {Object.entries(currentGenericAnalytics.districts)
                      .sort((a, b) => b[1].current_value - a[1].current_value)
                      .map(([districtName, stats]) => {
                        const share = Math.round(
                          (stats.current_value / currentGenericAnalytics.total_regional_volume) * 100,
                        );
                        return (
                          <tr key={districtName} className="hover:bg-[#f8fafc]">
                            <td className="py-2.5 font-medium text-[#1e293b] flex items-center gap-1">
                              {districtName} {stats.is_highest && <span className="text-[#0284c7] font-bold">🥇</span>}
                            </td>
                            <td className="py-2.5 text-right font-bold text-[#0f172a]">
                              {stats.current_value.toFixed(1)} {currentGenericAnalytics.unit}
                            </td>
                            <td className="py-2.5 text-right text-[#475569]">
                              {stats.average_10_days.toFixed(1)} {currentGenericAnalytics.unit}
                            </td>
                            <td className="py-2.5 text-right font-medium text-[#0284c7]">{share}%</td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        )}

        {/* Expandable Raw Records Section for all enhanced sectors */}
        {!loading && result && isAvailable && (isFuelComponent || isWastewaterComponent || isGenericAnalyticsComponent) && (
          <div className="rounded-2xl border border-[#d8e6dc] bg-white p-4 mt-4">
            <button
              onClick={() => setShowRawRecords((prev) => !prev)}
              className="w-full flex items-center justify-between text-xs font-bold text-[#315b48]"
            >
              <span>Raw 10-Day Dataset Records ({result.records?.length || 0})</span>
              <span className="material-symbols-outlined text-[18px]">
                {showRawRecords ? 'expand_less' : 'expand_more'}
              </span>
            </button>

            {showRawRecords && result.records && (
              <div className="mt-3 flex flex-col gap-2 max-h-80 overflow-y-auto">
                {result.records.map((record, index) => (
                  <div key={index} className="rounded-xl border border-[#f1f5f9] bg-[#f8fafc] p-3 text-xs">
                    <div className="grid grid-cols-3 gap-2">
                      <div>
                        <p className="text-[10px] text-[#64748b]">Date</p>
                        <p className="font-semibold text-[#0f172a]">
                          {String(record.Formatted_Date || record.Date || '—')}
                        </p>
                      </div>
                      <div>
                        <p className="text-[10px] text-[#64748b]">Category</p>
                        <p className="font-semibold text-[#0f172a]">
                          {String(record.Category || record.Fuel || '—')}
                        </p>
                      </div>
                      <div>
                        <p className="text-[10px] text-[#64748b]">Vellore</p>
                        <p className="font-semibold text-[#0f172a]">
                          {String(record.Vellore || '—')}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Standard Sector Dashboard for other sectors */}
        {!loading && result && isAvailable && !isFuelComponent && !isWastewaterComponent && !isGenericAnalyticsComponent && (
          <div className="flex flex-col gap-4">
            <div className="rounded-2xl bg-[#e9f8ef] p-5">
              <p className="font-display font-bold text-[#1b4332] text-[16px]">
                {metric?.name || 'Analysis'} ready
              </p>
              <p className="text-sm text-[#315b48] mt-1">{result.summary}</p>
            </div>

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

                <div className="col-span-2 rounded-2xl border border-[#d8e6dc] bg-white p-4 flex items-center justify-between">
                  <div>
                    <p className="text-xs text-[#6b7f72] font-medium">Change / trend</p>
                    <p className="mt-1 font-bold text-[#1b1c1a] text-[15px]">
                      {pctLabel ?? '—'}
                      {metric.trend && metric.trend !== 'UNAVAILABLE' && ` · ${metric.trend}`}
                    </p>
                    {periodsLabel && (
                      <p className="text-[11px] text-[#8a756b] mt-0.5">Based on {periodsLabel}</p>
                    )}
                  </div>
                  <TrendIcon trend={metric.trend} />
                </div>
              </section>
            )}

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

            {result.records && result.records.length > 0 && (
              <div className="flex flex-col gap-3">
                {result.records.slice(0, 8).map((record, index) => (
                  <div key={index} className="rounded-2xl border border-[#d8e6dc] bg-white p-4">
                    <div className="grid grid-cols-2 gap-x-3 gap-y-2 text-xs">
                      {Object.entries(record)
                        .slice(0, 8)
                        .map(([key, value]) => (
                          <div key={key}>
                            <p className="text-[#6b7f72] capitalize">{key.replaceAll('_', ' ')}</p>
                            <p className="font-medium text-[#1b1c1a] break-words">{String(value ?? '—')}</p>
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
