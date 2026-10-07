import React from 'react';
import { useApp } from '../context/AppContext';

interface DemoScenarioModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DEMO_SCENARIOS = [
  {
    key: 'scenario_1',
    title: '1. High Quality Image & Confident Valuation',
    desc: 'Crisp image, tight market consensus. Controller finalizes valuation without asking for view 2.',
    badge: 'Finalizes View 1',
  },
  {
    key: 'scenario_2',
    title: '2. Poor Image / High Uncertainty Request',
    desc: 'Image blur and ambiguity trigger an active request for View 2 (EVI > Cost).',
    badge: 'Requests View 2',
  },
  {
    key: 'scenario_3',
    title: '3. Agreeing Observations Reduce Range Width',
    desc: 'Observation 1 + Observation 2 agree, reducing uncertainty and narrowing the fair-price interval.',
    badge: 'Range Narrows',
  },
  {
    key: 'scenario_4',
    title: '4. Conflicting Views Retain Defect & Uncertainty',
    desc: 'View 1 looks fresh but View 2 reveals hidden bruising. System preserves defect and holds caution.',
    badge: 'Defect Preserved',
  },
  {
    key: 'scenario_5',
    title: '5. Divergent Market Sources Elevate Uncertainty',
    desc: 'High price variance across regional mandis expands market uncertainty score.',
    badge: 'Market Disagreement',
  },
  {
    key: 'scenario_6',
    title: '6. Stale Market Data Decays Reliability',
    desc: 'Older mandi reporting lowers evidence weight and increases temporal uncertainty penalty.',
    badge: 'Recency Decay',
  },
  {
    key: 'scenario_7',
    title: '7. High Asking Price with High Confidence',
    desc: 'Confident fair estimate triggers definitive OVERPRICED verdict with targeted bargaining targets.',
    badge: 'Assertive Deal Check',
  },
  {
    key: 'scenario_8',
    title: '8. High Uncertainty Guard Withholds Overpriced Claim',
    desc: 'When valuation is uncertain, system guards against false overpricing claims and outputs INSUFFICIENT_CONFIDENCE.',
    badge: 'Uncertainty Guard',
  },
];

export const DemoScenarioModal: React.FC<DemoScenarioModalProps> = ({ isOpen, onClose }) => {
  const { runDemoScenario, isScanning, theme } = useApp();
  const isTerracotta = theme === 'terracotta';

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
      <div className="bg-white rounded-3xl max-w-lg w-full max-h-[85vh] flex flex-col overflow-hidden shadow-2xl border border-gray-200">
        <div className="p-5 border-b border-gray-100 flex items-center justify-between bg-[#fbf9f5]">
          <div>
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-amber-600">science</span>
              <h3 className="font-bold text-[17px] text-gray-900">
                Validation & Demonstration Mode
              </h3>
            </div>
            <p className="text-[12px] text-gray-500 mt-0.5">
              Simulate patent benchmark scenarios with deterministic evidence propagation
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-gray-200 text-gray-700 flex items-center justify-center hover:bg-gray-300"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>

        <div className="p-4 overflow-y-auto flex flex-col gap-2.5">
          {DEMO_SCENARIOS.map((sc) => (
            <div
              key={sc.key}
              onClick={() => {
                runDemoScenario(sc.key);
                onClose();
              }}
              className="p-3.5 rounded-2xl border border-gray-200 hover:border-amber-400 hover:bg-amber-50/50 cursor-pointer transition-all flex flex-col gap-1 text-left"
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-[14px] text-gray-900">{sc.title}</span>
                <span className="text-[10px] font-extrabold px-2 py-0.5 rounded-md bg-amber-100 text-amber-800">
                  {sc.badge}
                </span>
              </div>
              <p className="text-[12px] text-gray-600 leading-snug">{sc.desc}</p>
            </div>
          ))}
        </div>

        <div className="p-4 bg-gray-50 border-t border-gray-200 text-center text-[11px] text-gray-500">
          This mode executes the deterministic test harness under benchmark conditions without fabricating live API responses.
        </div>
      </div>
    </div>
  );
};
