import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import {
  ScenarioSummaryDTO,
  ExperimentRunResult,
  ManifestRunEntry,
} from '../types';
import {
  fetchExperimentScenarios,
  runExperimentScenario,
  runAllExperimentScenarios,
  fetchExperimentRuns,
  fetchExperimentRunDetail,
  downloadExperimentExport,
} from '../services/api';

export const ExperimentLabScreen: React.FC = () => {
  const { setCurrentScreen, theme } = useApp();
  const isTerracotta = theme === 'terracotta';

  // State
  const [scenarios, setScenarios] = useState<ScenarioSummaryDTO[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('transport_available');
  const [activeCategory, setActiveCategory] = useState<string>('All');
  const [_loading, setLoading] = useState<boolean>(true);
  const [running, setRunning] = useState<boolean>(false);
  const [batchRunning, setBatchRunning] = useState<boolean>(false);
  const [currentRun, setCurrentRun] = useState<ExperimentRunResult | null>(null);
  const [historyRuns, setHistoryRuns] = useState<ManifestRunEntry[]>([]);
  const [showHistory, setShowHistory] = useState<boolean>(false);
  const [showRawJson, setShowRawJson] = useState<boolean>(false);
  const [copySuccess, setCopySuccess] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [scList, runsList] = await Promise.all([
        fetchExperimentScenarios(),
        fetchExperimentRuns().catch(() => []),
      ]);
      setScenarios(scList);
      setHistoryRuns(runsList);

      // If there are runs, auto-load the latest or run default
      if (runsList.length > 0) {
        const latestDetail = await fetchExperimentRunDetail(runsList[runsList.length - 1].run_id);
        setCurrentRun(latestDetail);
        setSelectedScenarioId(latestDetail.experiment.scenario_id);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to initialize Experiment Lab');
    } finally {
      setLoading(false);
    }
  };

  const handleRunScenario = async (scenarioId: string) => {
    setRunning(true);
    setError(null);
    try {
      const result = await runExperimentScenario(scenarioId);
      setCurrentRun(result);
      setSelectedScenarioId(scenarioId);
      // Refresh runs history
      const updatedRuns = await fetchExperimentRuns();
      setHistoryRuns(updatedRuns);
    } catch (err: any) {
      setError(err?.message || 'Scenario execution failed');
    } finally {
      setRunning(false);
    }
  };

  const handleRunAll = async () => {
    setBatchRunning(true);
    setError(null);
    try {
      await runAllExperimentScenarios();
      const updatedRuns = await fetchExperimentRuns();
      setHistoryRuns(updatedRuns);
      if (updatedRuns.length > 0) {
        const latest = await fetchExperimentRunDetail(updatedRuns[updatedRuns.length - 1].run_id);
        setCurrentRun(latest);
      }
    } catch (err: any) {
      setError(err?.message || 'Batch execution failed');
    } finally {
      setBatchRunning(false);
    }
  };

  const handleSelectHistoryRun = async (runId: string) => {
    try {
      setRunning(true);
      const detail = await fetchExperimentRunDetail(runId);
      setCurrentRun(detail);
      setSelectedScenarioId(detail.experiment.scenario_id);
      setShowHistory(false);
    } catch {
      setError(`Failed to load run ${runId}`);
    } finally {
      setRunning(false);
    }
  };

  const handleCopySummary = () => {
    if (!currentRun) return;
    const summary = `Sahi Daam Experiment Summary\nScenario: ${currentRun.experiment.scenario_name}\nRun ID: ${currentRun.experiment.run_id}\nStatus: ${currentRun.actual_output.calculation_status}\nCost Basis: ₹${currentRun.actual_output.cost_basis_per_kg}/kg\nBaseline Range: ₹${currentRun.actual_output.baseline_range?.min}–₹${currentRun.actual_output.baseline_range?.max}/kg\nReconciled Range: ₹${currentRun.actual_output.reconciled_range?.min}–₹${currentRun.actual_output.reconciled_range?.max}/kg\nCommunity Alpha: ${currentRun.actual_output.reconciliation_weight_alpha}\nAll Checks Passed: ${currentRun.expected_behavior_checks.every(c => c.passed)}`;
    navigator.clipboard.writeText(summary);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };

  const selectedSpec = scenarios.find((s) => s.scenario_id === selectedScenarioId);
  const categories = ['All', ...Array.from(new Set(scenarios.map((s) => s.category)))];
  const filteredScenarios = activeCategory === 'All'
    ? scenarios
    : scenarios.filter((s) => s.category === activeCategory);

  return (
    <div className="min-h-screen bg-[#fbf9f5] pb-24 text-[#1b1c1a]">
      {/* Top App Bar */}
      <header className="sticky top-0 z-40 bg-[#fbf9f5]/90 backdrop-blur-md border-b border-[#e4e2de] px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentScreen('home')}
            className="w-10 h-10 rounded-full flex items-center justify-center text-[#594238] hover:bg-[#ece8e1] transition-all"
            aria-label="Back"
          >
            <span className="material-symbols-outlined text-[24px]">arrow_back</span>
          </button>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[20px] text-[#9e3d00]">science</span>
              <h1 className="font-display text-[18px] font-bold text-[#1b1c1a]">Experiment Lab</h1>
            </div>
            <p className="text-[11px] text-[#594238]">Deterministic Pricing & Reconciliation Simulator</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowHistory(true)}
            className="px-3 py-1.5 rounded-xl border border-[#e4e2de] bg-white hover:bg-[#f5f3ef] text-[#594238] text-xs font-semibold flex items-center gap-1 transition-all"
            title="View Past Run Manifest"
          >
            <span className="material-symbols-outlined text-[16px]">history</span>
            History ({historyRuns.length})
          </button>
          <button
            onClick={handleRunAll}
            disabled={batchRunning}
            className={`px-3 py-1.5 rounded-xl text-white text-xs font-bold flex items-center gap-1 transition-all ${
              isTerracotta ? 'bg-[#9e3d00] hover:bg-[#853400]' : 'bg-[#012d1d] hover:bg-[#02442c]'
            } disabled:opacity-50`}
          >
            <span className={`material-symbols-outlined text-[16px] ${batchRunning ? 'animate-spin' : ''}`}>
              play_circle
            </span>
            {batchRunning ? 'Running...' : 'Run All (13)'}
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-3xl mx-auto px-4 pt-4 space-y-6">
        {/* Error Alert */}
        {error && (
          <div className="p-3.5 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[18px]">error</span>
              <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-red-900 font-bold">×</button>
          </div>
        )}

        {/* ── Category Filter Pills ── */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition-all ${
                activeCategory === cat
                  ? isTerracotta
                    ? 'bg-[#9e3d00] text-white shadow-xs'
                    : 'bg-[#012d1d] text-white shadow-xs'
                  : 'bg-white border border-[#e4e2de] text-[#594238] hover:bg-[#f5f3ef]'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* ── Scenario Selection Cards Carousel / Grid ── */}
        <section className="space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#594238]">
              Select Scenario ({filteredScenarios.length})
            </h2>
            <span className="text-[11px] text-[#85736b]">Pure deterministic fixtures</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {filteredScenarios.map((sc) => {
              const isSelected = sc.scenario_id === selectedScenarioId;
              return (
                <div
                  key={sc.scenario_id}
                  onClick={() => setSelectedScenarioId(sc.scenario_id)}
                  className={`p-3.5 rounded-2xl border text-left cursor-pointer transition-all ${
                    isSelected
                      ? isTerracotta
                        ? 'bg-amber-50/70 border-[#9e3d00] shadow-sm'
                        : 'bg-emerald-50/70 border-[#012d1d] shadow-sm'
                      : 'bg-white border-[#e4e2de] hover:border-[#cfc9c1] hover:bg-[#faf8f5]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-white border border-[#e4e2de] text-[#594238]">
                      {sc.category}
                    </span>
                    {isSelected && (
                      <span className="material-symbols-outlined text-[16px] text-green-700">check_circle</span>
                    )}
                  </div>
                  <h3 className="font-display text-[14px] font-bold text-[#1b1c1a] leading-tight mb-1">
                    {sc.scenario_name}
                  </h3>
                  <p className="text-[11px] text-[#594238] line-clamp-2 leading-relaxed">
                    {sc.description}
                  </p>
                </div>
              );
            })}
          </div>
        </section>

        {/* ── Input Parameters Preview & Action Bar ── */}
        {selectedSpec && (
          <section className="p-4 rounded-3xl bg-white border border-[#e4e2de] shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#9e3d00]">Input Preview</span>
                <h3 className="font-display text-[15px] font-bold text-[#1b1c1a]">
                  {selectedSpec.scenario_name}
                </h3>
              </div>
              <button
                onClick={() => handleRunScenario(selectedSpec.scenario_id)}
                disabled={running}
                className={`px-4 py-2.5 rounded-2xl text-white font-display text-sm font-bold flex items-center gap-2 shadow-sm transition-all active:scale-95 ${
                  isTerracotta ? 'bg-[#9e3d00] hover:bg-[#853400]' : 'bg-[#012d1d] hover:bg-[#02442c]'
                } disabled:opacity-50`}
              >
                <span className={`material-symbols-outlined text-[18px] ${running ? 'animate-spin' : ''}`}>
                  {running ? 'hourglass_top' : 'play_arrow'}
                </span>
                {running ? 'Executing...' : 'Run Experiment'}
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div className="p-2.5 rounded-xl bg-[#fbf9f5] border border-[#f0eee9]">
                <span className="text-[10px] text-[#594238] block">Wholesale Price</span>
                <span className="font-bold text-[#1b1c1a]">
                  {selectedSpec.wholesale_price != null ? `₹${selectedSpec.wholesale_price}/kg` : 'Unavailable (None)'}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-[#fbf9f5] border border-[#f0eee9]">
                <span className="text-[10px] text-[#594238] block">Freight / Transport</span>
                <span className="font-bold text-[#1b1c1a]">
                  {selectedSpec.transport_status === 'available' ? `₹${selectedSpec.transport_cost}/kg` : 'Unavailable'}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-[#fbf9f5] border border-[#f0eee9]">
                <span className="text-[10px] text-[#594238] block">Markup Range</span>
                <span className="font-bold text-[#1b1c1a]">{selectedSpec.markup_range}</span>
              </div>
              <div className="p-2.5 rounded-xl bg-[#fbf9f5] border border-[#f0eee9]">
                <span className="text-[10px] text-[#594238] block">Community Submissions</span>
                <span className="font-bold text-[#1b1c1a]">{selectedSpec.raw_observations_count} reports</span>
              </div>
            </div>
          </section>
        )}

        {/* ── EXECUTION RESULTS CONTAINER ── */}
        {currentRun && (
          <div className="space-y-6 pt-2 animate-in fade-in duration-300">
            {/* -----------------------------------------------------------
                SECTION 1: Experiment Identification
               ----------------------------------------------------------- */}
            <section className="p-5 rounded-3xl bg-white border border-[#e4e2de] shadow-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#594238]">
                  Section 1 · Identification
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-100 text-amber-800 border border-amber-200">
                  Mock Experiment Data
                </span>
              </div>
              <h2 className="font-display text-[18px] font-bold text-[#1b1c1a]">
                {currentRun.experiment.scenario_name}
              </h2>
              <p className="text-xs text-[#594238] leading-relaxed">
                {currentRun.experiment.description}
              </p>

              <div className="pt-2 border-t border-[#f0eee9] flex flex-wrap items-center justify-between gap-2 text-[11px] text-[#85736b] font-mono">
                <span>Run ID: {currentRun.experiment.run_id}</span>
                <span>Time: {new Date(currentRun.experiment.timestamp_utc).toLocaleString('en-IN')}</span>
                <span>Algorithm: {currentRun.configuration.algorithm_version}</span>
              </div>
            </section>

            {/* -----------------------------------------------------------
                SECTION 2: Input Parameters Table
               ----------------------------------------------------------- */}
            <section className="p-5 rounded-3xl bg-white border border-[#e4e2de] shadow-xs space-y-3">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#594238] block">
                Section 2 · Input Parameters Table
              </span>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-[#e4e2de] text-[#85736b]">
                      <th className="py-2 pr-3 font-semibold">Parameter</th>
                      <th className="py-2 px-3 font-semibold">Input Value</th>
                      <th className="py-2 px-3 font-semibold">Unit</th>
                      <th className="py-2 pl-3 font-semibold">Source</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#f0eee9]">
                    <tr>
                      <td className="py-2 pr-3 font-medium text-[#1b1c1a]">Commodity</td>
                      <td className="py-2 px-3">{currentRun.inputs.commodity_id.toUpperCase()}</td>
                      <td className="py-2 px-3">—</td>
                      <td className="py-2 pl-3 text-[#594238]">Simulated Fixture</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-3 font-medium text-[#1b1c1a]">Wholesale Price</td>
                      <td className="py-2 px-3 font-bold">
                        {currentRun.inputs.wholesale_price_per_kg != null ? `₹${currentRun.inputs.wholesale_price_per_kg}` : 'Unavailable'}
                      </td>
                      <td className="py-2 px-3">₹/kg</td>
                      <td className="py-2 pl-3 text-[#594238]">Mandi Modal Quote</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-3 font-medium text-[#1b1c1a]">Transport Cost</td>
                      <td className="py-2 px-3">
                        {currentRun.inputs.transport_status === 'available'
                          ? `₹${currentRun.inputs.transport_cost_per_kg}`
                          : 'Unavailable (Missing)'}
                      </td>
                      <td className="py-2 px-3">₹/kg</td>
                      <td className="py-2 pl-3 text-[#594238]">{currentRun.inputs.transport_method || 'Unconfigured'}</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-3 font-medium text-[#1b1c1a]">Retail Markup Range</td>
                      <td className="py-2 px-3">+{currentRun.inputs.markup_min_pct}% to +{currentRun.inputs.markup_max_pct}%</td>
                      <td className="py-2 px-3">%</td>
                      <td className="py-2 pl-3 text-[#594238]">Pricing Policy</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-3 font-medium text-[#1b1c1a]">Freshness Deduction</td>
                      <td className="py-2 px-3">
                        {currentRun.inputs.quality_adjustment > 0
                          ? `+${currentRun.inputs.quality_adjustment}`
                          : currentRun.inputs.quality_adjustment}
                      </td>
                      <td className="py-2 px-3">₹/kg</td>
                      <td className="py-2 pl-3 text-[#594238]">{currentRun.inputs.quality_adjustment_meaning}</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-3 font-medium text-[#1b1c1a]">Eligible Independent Reports</td>
                      <td className="py-2 px-3 font-bold">{currentRun.actual_output.community_sample_size}</td>
                      <td className="py-2 px-3">reports</td>
                      <td className="py-2 pl-3 text-[#594238]">
                        Excludes {currentRun.eligible_community_observations.excluded_duplicates_count} duplicates
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-3 font-medium text-[#1b1c1a]">Community Median</td>
                      <td className="py-2 px-3">
                        {currentRun.actual_output.community_estimate != null ? `₹${currentRun.actual_output.community_estimate}` : 'Unavailable'}
                      </td>
                      <td className="py-2 px-3">₹/kg</td>
                      <td className="py-2 pl-3 text-[#594238]">Sample Median</td>
                    </tr>
                    <tr>
                      <td className="py-2 pr-3 font-medium text-[#1b1c1a]">Reconciliation Weight (α)</td>
                      <td className="py-2 px-3 font-bold text-[#9e3d00]">{currentRun.actual_output.reconciliation_weight_alpha.toFixed(2)}</td>
                      <td className="py-2 px-3">0–0.40</td>
                      <td className="py-2 pl-3 text-[#594238]">Adaptive Policy</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            {/* -----------------------------------------------------------
                SECTION 3: Step-by-Step Mathematical Calculation
                (MANDATORY: MUST APPEAR ABOVE THE OUTPUT)
               ----------------------------------------------------------- */}
            <section className="p-5 rounded-3xl bg-[#f5f3ef] border border-[#e4e2de] shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-[#e4e2de] pb-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#9e3d00]">
                  Section 3 · Step-by-Step Mathematical Calculation
                </span>
                <span className="text-[10px] font-bold uppercase tracking-wider bg-white px-2 py-0.5 rounded-full text-[#594238] border border-[#d5cfc7]">
                  Formula Trace (Computed from Actual Output)
                </span>
              </div>

              <div className="space-y-3">
                {currentRun.calculation_steps.map((st) => (
                  <div key={st.step_number} className="p-3.5 rounded-2xl bg-white border border-[#e4e2de] space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-[#1b1c1a]">
                        Step {st.step_number}: {st.title}
                      </span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        st.status === 'COMPLETE' ? 'bg-green-100 text-green-800' :
                        st.status === 'RECONCILED' ? 'bg-blue-100 text-blue-800' :
                        st.status === 'PROVISIONAL' ? 'bg-amber-100 text-amber-800' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {st.status}
                      </span>
                    </div>

                    <div className="p-2 rounded-xl bg-[#fbf9f5] font-mono text-[11px] text-[#594238] space-y-0.5">
                      <p><span className="text-[#85736b]">Formula:</span> {st.formula}</p>
                      <p><span className="text-[#85736b]">Substitution:</span> {st.substitutions}</p>
                    </div>

                    <div className="flex items-center justify-between text-xs pt-1">
                      <span className="text-[#594238]">{st.explanation}</span>
                      <span className="font-bold text-[#1b1c1a] bg-amber-50 px-2 py-0.5 rounded-lg border border-amber-200">
                        {st.result_label}: {st.result_value}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* -----------------------------------------------------------
                SECTION 4: Actual Computed Output
                (APPEARS BELOW CALCULATION SECTION)
               ----------------------------------------------------------- */}
            <section className="p-6 rounded-3xl bg-white border border-[#e4e2de] shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-[#f0eee9] pb-3">
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#594238]">
                  Section 4 · Actual Computed Output
                </span>
                <span className={`px-3 py-1 rounded-full text-xs font-extrabold tracking-wide ${
                  currentRun.actual_output.calculation_status.includes('RECONCILED') ? 'bg-blue-100 text-blue-800 border border-blue-200' :
                  currentRun.actual_output.calculation_status.includes('BASELINE') ? 'bg-green-100 text-green-800 border border-green-200' :
                  'bg-amber-100 text-amber-800 border border-amber-200'
                }`}>
                  {currentRun.actual_output.calculation_status}
                </span>
              </div>

              {/* Range Display Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-center">
                <div className="p-4 rounded-2xl bg-[#fbf9f5] border border-[#f0eee9]">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-[#594238] block mb-1">
                    Cost-Based Baseline Range
                  </span>
                  <div className="font-display text-2xl font-extrabold text-[#1b1c1a]">
                    {currentRun.actual_output.baseline_range
                      ? `₹${currentRun.actual_output.baseline_range.min}–₹${currentRun.actual_output.baseline_range.max}/kg`
                      : 'Unavailable'}
                  </div>
                  <span className="text-[11px] text-[#85736b]">
                    {currentRun.actual_output.is_provisional_wholesale_only
                      ? 'Provisional Wholesale Baseline'
                      : 'Delivered Transport-Aware Baseline'}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-[#fbf9f5] border border-[#f0eee9]">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-[#594238] block mb-1">
                    Reconciled Output Range
                  </span>
                  <div className={`font-display text-2xl font-extrabold ${
                    currentRun.actual_output.reconciliation_weight_alpha > 0 ? 'text-[#9e3d00]' : 'text-[#1b1c1a]'
                  }`}>
                    {currentRun.actual_output.reconciled_range
                      ? `₹${currentRun.actual_output.reconciled_range.min}–₹${currentRun.actual_output.reconciled_range.max}/kg`
                      : 'Unavailable'}
                  </div>
                  <span className="text-[11px] text-[#85736b]">
                    {currentRun.actual_output.reconciliation_weight_alpha > 0
                      ? `Reconciled with Crowd Reports (α=${currentRun.actual_output.reconciliation_weight_alpha})`
                      : 'Preserved Baseline Range (α=0.0)'}
                  </span>
                </div>
              </div>

              {/* Sub-Run Matrix if Scenario G Freshness */}
              {currentRun.sub_runs && currentRun.sub_runs.length > 0 && (
                <div className="p-3.5 rounded-2xl bg-[#faf8f5] border border-[#e4e2de] space-y-2">
                  <span className="text-xs font-bold text-[#1b1c1a] block">Freshness Adjustment Matrix</span>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs text-left">
                      <thead>
                        <tr className="border-b border-[#e4e2de] text-[#85736b]">
                          <th className="py-1">Condition</th>
                          <th className="py-1">Deduction</th>
                          <th className="py-1">Baseline Range</th>
                          <th className="py-1">Diff from Fresh</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#f0eee9]">
                        {currentRun.sub_runs.map((sr) => (
                          <tr key={sr.sub_id}>
                            <td className="py-1.5 font-semibold text-[#1b1c1a]">{sr.label}</td>
                            <td className="py-1.5">
                              {sr.quality_adjustment > 0 ? `+${sr.quality_adjustment}` : sr.quality_adjustment} ₹/kg
                            </td>
                            <td className="py-1.5 font-bold">₹{sr.baseline_min}–₹{sr.baseline_max}/kg</td>
                            <td className="py-1.5 text-[#9e3d00] font-semibold">
                              {sr.difference_from_fresh > 0 ? `+${sr.difference_from_fresh.toFixed(2)}` : sr.difference_from_fresh.toFixed(2)} ₹/kg
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Notes & Warnings */}
              {(currentRun.warnings.length > 0 || currentRun.notes.length > 0) && (
                <div className="space-y-1 text-xs">
                  {currentRun.warnings.map((w, i) => (
                    <p key={i} className="text-amber-800 bg-amber-50 p-2 rounded-xl border border-amber-200 flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[16px]">warning</span>
                      {w}
                    </p>
                  ))}
                  {currentRun.notes.map((n, i) => (
                    <p key={i} className="text-[#594238] bg-[#fbf9f5] p-2 rounded-xl border border-[#f0eee9] flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[16px]">info</span>
                      {n}
                    </p>
                  ))}
                </div>
              )}
            </section>

            {/* -----------------------------------------------------------
                SECTION 5: Expected versus Actual Behavior
               ----------------------------------------------------------- */}
            <section className="p-5 rounded-3xl bg-white border border-[#e4e2de] shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#594238]">
                  Section 5 · Expected vs. Actual Assertions
                </span>
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                  currentRun.expected_behavior_checks.every(c => c.passed)
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {currentRun.expected_behavior_checks.every(c => c.passed) ? 'All Assertions Passed' : 'Assertion Mismatch'}
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-[#e4e2de] text-[#85736b]">
                      <th className="py-2 pr-2 font-semibold">Check</th>
                      <th className="py-2 px-2 font-semibold">Expected</th>
                      <th className="py-2 px-2 font-semibold">Actual</th>
                      <th className="py-2 pl-2 font-semibold">Result</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#f0eee9]">
                    {currentRun.expected_behavior_checks.map((c, i) => (
                      <tr key={i}>
                        <td className="py-2 pr-2 font-medium text-[#1b1c1a]">{c.check_name}</td>
                        <td className="py-2 px-2 font-mono text-[11px] text-[#594238]">{c.expected}</td>
                        <td className="py-2 px-2 font-mono text-[11px] font-bold text-[#1b1c1a]">{c.actual}</td>
                        <td className="py-2 pl-2">
                          <span className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                            c.passed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {c.passed ? 'PASS' : 'FAIL'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            {/* -----------------------------------------------------------
                SECTION 6: Calculation Evidence & JSON Export
               ----------------------------------------------------------- */}
            <section className="p-5 rounded-3xl bg-white border border-[#e4e2de] shadow-xs space-y-3">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#594238] block">
                Section 6 · Calculation Evidence & JSON Export
              </span>

              <div className="p-3 rounded-2xl bg-[#fbf9f5] border border-[#f0eee9] text-xs font-mono space-y-1 text-[#594238]">
                <p><span className="text-[#85736b]">Saved Path:</span> experiments/scenario_results/{currentRun.persistence.relative_path}</p>
                <p><span className="text-[#85736b]">SHA-256 Digest:</span> {currentRun.persistence.sha256_hash}</p>
                <p><span className="text-[#85736b]">File Size:</span> {currentRun.persistence.file_size_bytes} bytes</p>
              </div>

              <div className="flex flex-wrap items-center gap-2 pt-1">
                <button
                  onClick={() => downloadExperimentExport(currentRun.experiment.run_id)}
                  className={`px-4 py-2 rounded-xl text-white text-xs font-bold flex items-center gap-1.5 transition-all active:scale-95 ${
                    isTerracotta ? 'bg-[#9e3d00]' : 'bg-[#012d1d]'
                  }`}
                >
                  <span className="material-symbols-outlined text-[16px]">download</span>
                  Download JSON Evidence
                </button>
                <button
                  onClick={handleCopySummary}
                  className="px-4 py-2 rounded-xl border border-[#e4e2de] bg-white hover:bg-[#f5f3ef] text-[#594238] text-xs font-bold flex items-center gap-1.5 transition-all"
                >
                  <span className="material-symbols-outlined text-[16px]">content_copy</span>
                  {copySuccess ? 'Copied!' : 'Copy Summary'}
                </button>
                <button
                  onClick={() => setShowRawJson(!showRawJson)}
                  className="px-4 py-2 rounded-xl border border-[#e4e2de] bg-white hover:bg-[#f5f3ef] text-[#594238] text-xs font-bold flex items-center gap-1.5 transition-all"
                >
                  <span className="material-symbols-outlined text-[16px]">code</span>
                  {showRawJson ? 'Hide Raw JSON' : 'Inspect Raw JSON'}
                </button>
              </div>

              {showRawJson && (
                <pre className="p-4 rounded-2xl bg-[#1b1c1a] text-[#7bf8a1] font-mono text-[11px] overflow-x-auto max-h-96 mt-2">
                  {JSON.stringify(currentRun, null, 2)}
                </pre>
              )}
            </section>

            {/* -----------------------------------------------------------
                SECTION 7: Reproducibility & Environment Settings
               ----------------------------------------------------------- */}
            <section className="p-4 rounded-3xl bg-[#f5f3ef] border border-[#e4e2de] text-xs text-[#594238] space-y-1">
              <span className="font-bold text-[#1b1c1a] block">Section 7 · Reproducibility & Deterministic Isolation</span>
              <p>• Fixture Version: {currentRun.configuration.fixture_version} | Algorithm Version: {currentRun.configuration.algorithm_version}</p>
              <p>• Controlled Clock: {currentRun.configuration.reference_clock_utc}</p>
              <p>• Isolation: Transient memory fixture execution. Normal application SQLite database (`backend/sahi_daam.db`) remained completely untouched.</p>
            </section>
          </div>
        )}
      </main>

      {/* ── HISTORY MANIFEST MODAL / DRAWER ── */}
      {showHistory && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-5 max-w-xl w-full max-h-[85vh] flex flex-col shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-[#e4e2de]">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[20px] text-[#9e3d00]">receipt_long</span>
                <h3 className="font-display text-[16px] font-bold text-[#1b1c1a]">Experiment Run History</h3>
              </div>
              <button
                onClick={() => setShowHistory(false)}
                className="w-8 h-8 rounded-full flex items-center justify-center text-[#594238] hover:bg-[#ece8e1]"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-3 space-y-2">
              {historyRuns.length === 0 ? (
                <p className="text-center text-xs text-[#85736b] py-8">No runs recorded in manifest yet.</p>
              ) : (
                historyRuns.slice().reverse().map((r) => (
                  <div
                    key={r.run_id}
                    className="p-3 rounded-2xl border border-[#e4e2de] hover:border-[#cfc9c1] bg-[#fbf9f5] flex items-center justify-between text-xs transition-all"
                  >
                    <div>
                      <p className="font-bold text-[#1b1c1a]">{r.scenario_name}</p>
                      <p className="text-[10px] text-[#85736b] font-mono">
                        {r.run_id} • {new Date(r.timestamp_utc).toLocaleTimeString('en-IN')}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        r.all_checks_passed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {r.all_checks_passed ? 'ALL PASS' : 'FAIL'}
                      </span>
                      <button
                        onClick={() => handleSelectHistoryRun(r.run_id)}
                        className="px-2.5 py-1 rounded-lg bg-white border border-[#e4e2de] hover:bg-[#f0eee9] font-bold text-[11px]"
                      >
                        Load
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="pt-3 border-t border-[#e4e2de] text-center text-[11px] text-[#85736b]">
              Indexed in experiments/scenario_results/manifest.json
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
