import React, { useState, useRef } from 'react';
import { useApp } from '../context/AppContext';

export const AdaptiveValuationCard: React.FC = () => {
  const { selectedProduce, addAdditionalObservation, isScanning, theme } = useApp();
  const [showTrace, setShowTrace] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isTerracotta = theme === 'terracotta';

  const valConf = selectedProduce.valuationConfidence ?? 0.82;
  const valUnc = selectedProduce.valuationUncertainty ?? (1 - valConf);
  const qualUnc = selectedProduce.qualityUncertainty ?? 0.2;
  const mktUnc = selectedProduce.marketUncertainty ?? 0.25;

  const confLabel = valConf >= 0.75 ? 'HIGH CONFIDENCE' : valConf >= 0.5 ? 'MEDIUM CONFIDENCE' : 'LOW CONFIDENCE';
  const confColor =
    valConf >= 0.75
      ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
      : valConf >= 0.5
      ? 'bg-amber-100 text-amber-800 border-amber-300'
      : 'bg-rose-100 text-rose-800 border-rose-300';

  const handleCaptureView = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = reader.result as string;
        addAdditionalObservation(base64, 'reverse_side');
      };
      reader.readAsDataURL(file);
    }
  };

  const comparison = selectedProduce.instrumentationComparison;

  return (
    <div className="w-full bg-white rounded-[20px] p-5 border border-[#e4e2de] shadow-sm flex flex-col gap-4 mt-3">
      {/* Header & Confidence Status Indicator */}
      <div className="flex items-center justify-between pb-3 border-b border-[#f0eee9]">
        <div>
          <span className="text-[10px] font-bold text-[#594238] uppercase tracking-wider block">
            Adaptive Valuation System
          </span>
          <span className="text-[14px] font-bold text-[#1b1c1a]">
            Multi-Source Uncertainty Engine
          </span>
        </div>
        <span
          className={`text-[11px] font-extrabold px-3 py-1 rounded-full border flex items-center gap-1 ${confColor}`}
        >
          <span className="material-symbols-outlined text-[14px]">
            {valConf >= 0.75 ? 'verified' : valConf >= 0.5 ? 'info' : 'warning'}
          </span>
          {confLabel}
        </span>
      </div>

      {/* Uncertainty Breakdown Grid */}
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-[#fbf9f5] rounded-xl p-2.5 border border-[#edebe6] flex flex-col items-center text-center">
          <span className="text-[10px] text-[#594238] font-semibold uppercase">Quality Unc.</span>
          <span className="text-[16px] font-extrabold text-[#1b1c1a] font-display">
            {(qualUnc * 100).toFixed(0)}%
          </span>
          <div className="w-full bg-[#e4e2de] h-1.5 rounded-full mt-1 overflow-hidden">
            <div
              className={`h-full ${qualUnc > 0.4 ? 'bg-amber-500' : 'bg-emerald-500'}`}
              style={{ width: `${Math.min(100, qualUnc * 100)}%` }}
            />
          </div>
        </div>

        <div className="bg-[#fbf9f5] rounded-xl p-2.5 border border-[#edebe6] flex flex-col items-center text-center">
          <span className="text-[10px] text-[#594238] font-semibold uppercase">Market Unc.</span>
          <span className="text-[16px] font-extrabold text-[#1b1c1a] font-display">
            {(mktUnc * 100).toFixed(0)}%
          </span>
          <div className="w-full bg-[#e4e2de] h-1.5 rounded-full mt-1 overflow-hidden">
            <div
              className={`h-full ${mktUnc > 0.4 ? 'bg-amber-500' : 'bg-emerald-500'}`}
              style={{ width: `${Math.min(100, mktUnc * 100)}%` }}
            />
          </div>
        </div>

        <div className="bg-[#fbf9f5] rounded-xl p-2.5 border border-[#edebe6] flex flex-col items-center text-center">
          <span className="text-[10px] text-[#594238] font-semibold uppercase">Valuation Unc.</span>
          <span className="text-[16px] font-extrabold text-[#1b1c1a] font-display">
            {(valUnc * 100).toFixed(0)}%
          </span>
          <div className="w-full bg-[#e4e2de] h-1.5 rounded-full mt-1 overflow-hidden">
            <div
              className={`h-full ${valUnc > 0.35 ? 'bg-rose-500' : 'bg-emerald-500'}`}
              style={{ width: `${Math.min(100, valUnc * 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Before / After Comparison Instrumentation (if multi-observation occurred) */}
      {comparison && comparison.steps && comparison.steps.length > 1 && (
        <div className="bg-emerald-50/70 border border-emerald-200 rounded-xl p-3.5 flex flex-col gap-2">
          <div className="flex items-center gap-1.5 text-emerald-800 text-[12px] font-bold">
            <span className="material-symbols-outlined text-[16px]">trending_down</span>
            Adaptive Fusion: Observation #{comparison.observation_count} Incorporated
          </div>
          <div className="grid grid-cols-2 gap-2 text-[12px] bg-white/80 p-2.5 rounded-lg border border-emerald-100">
            <div>
              <span className="text-gray-500 block text-[10px] uppercase font-semibold">Initial Range (View 1)</span>
              <span className="font-bold text-gray-800">
                ₹{comparison.steps[0].fair_min} – ₹{comparison.steps[0].fair_max}
              </span>
              <span className="text-[10px] text-gray-400 block">
                Width: ₹{comparison.steps[0].range_width.toFixed(1)}
              </span>
            </div>
            <div>
              <span className="text-emerald-700 block text-[10px] uppercase font-semibold">Updated Range (Fused)</span>
              <span className="font-extrabold text-emerald-900">
                ₹{comparison.steps[comparison.steps.length - 1].fair_min} – ₹{comparison.steps[comparison.steps.length - 1].fair_max}
              </span>
              <span className="text-[10px] text-emerald-600 font-bold block">
                Range narrowed by ₹{comparison.range_width_reduction.toFixed(1)}
              </span>
            </div>
          </div>
          <div className="text-[11px] text-emerald-800 font-medium">
            Compound uncertainty reduced by {(comparison.uncertainty_reduction * 100).toFixed(1)}% through active multi-view observation.
          </div>
        </div>
      )}

      {/* Active Observation Request Card */}
      {selectedProduce.needsAdditionalObservation && (
        <div className="bg-amber-50 border-2 border-amber-300 rounded-xl p-4 flex flex-col gap-3">
          <div className="flex items-start gap-2.5">
            <span className="material-symbols-outlined text-amber-600 text-[24px]">photo_camera</span>
            <div>
              <h4 className="font-bold text-[14px] text-amber-900 leading-snug">
                Additional Observation Recommended
              </h4>
              <p className="text-[12px] text-amber-800 mt-0.5 leading-relaxed">
                {selectedProduce.observationRequest?.reason ||
                  'Visual quality uncertainty exceeds acceptable threshold.'}
              </p>
            </div>
          </div>

          <div className="bg-white/90 p-3 rounded-lg border border-amber-200 text-[12px] text-[#594238]">
            <span className="font-bold block text-[#1b1c1a] mb-0.5">Recommended Action:</span>
            {selectedProduce.observationRequest?.user_guidance ||
              'Capture another angle or opposite side of produce to inspect hidden surfaces.'}
          </div>

          <input
            type="file"
            accept="image/*"
            capture="environment"
            ref={fileInputRef}
            onChange={handleCaptureView}
            className="hidden"
          />

          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isScanning}
            className={`w-full py-3 rounded-xl font-bold text-[14px] text-white flex items-center justify-center gap-2 shadow-sm transition-transform active:scale-[0.98] ${
              isTerracotta ? 'bg-[#9e3d00]' : 'bg-[#012d1d]'
            } ${isScanning ? 'opacity-60 cursor-not-allowed' : 'hover:opacity-95'}`}
          >
            <span className="material-symbols-outlined text-[18px]">add_a_photo</span>
            {isScanning ? 'Fusing Observation...' : 'Capture View 2 / Opposite Side'}
          </button>
        </div>
      )}

      {/* Explainable Decision Trace ("Why?") */}
      <div className="border-t border-[#f0eee9] pt-2">
        <button
          onClick={() => setShowTrace(!showTrace)}
          className="w-full flex items-center justify-between text-[12px] font-bold text-[#594238] py-1 hover:text-[#1b1c1a]"
        >
          <span className="flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[16px]">psychology</span>
            Explainable Decision Trace ({selectedProduce.decisionTrace?.length || 0} Steps)
          </span>
          <span className="material-symbols-outlined text-[16px]">
            {showTrace ? 'expand_less' : 'expand_more'}
          </span>
        </button>

        {showTrace && (
          <div className="mt-2 flex flex-col gap-2 bg-[#fbf9f5] p-3 rounded-xl border border-[#edebe6] text-[11px]">
            {selectedProduce.decisionTrace && selectedProduce.decisionTrace.length > 0 ? (
              selectedProduce.decisionTrace.map((trace, idx) => (
                <div key={idx} className="pb-2 border-b border-gray-200 last:border-b-0 last:pb-0">
                  <div className="flex items-center justify-between font-bold text-[#1b1c1a]">
                    <span>{trace.stage.replace(/_/g, ' ')}</span>
                    <span className="text-[10px] text-gray-500 font-mono">
                      {typeof trace.value === 'object' ? JSON.stringify(trace.value) : String(trace.value)}
                    </span>
                  </div>
                  <p className="text-[#594238] mt-0.5 leading-tight">{trace.rationale}</p>
                </div>
              ))
            ) : (
              <p className="text-gray-500">Initial decision trace recorded.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
