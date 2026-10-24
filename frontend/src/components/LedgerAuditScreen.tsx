import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { fetchCalculations, verifyLedger, downloadCalculationExport } from '../services/api';
import { CalculationRecordSummary, LedgerVerificationResult } from '../types';

export const LedgerAuditScreen: React.FC = () => {
  const { setCurrentScreen, theme } = useApp();
  const [calculations, setCalculations] = useState<CalculationRecordSummary[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [verification, setVerification] = useState<LedgerVerificationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [verifying, setVerifying] = useState<boolean>(false);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isTerracotta = theme === 'terracotta';

  useEffect(() => {
    loadLedgerData();
  }, []);

  const loadLedgerData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [listRes, verifyRes] = await Promise.all([
        fetchCalculations(50, 0),
        verifyLedger().catch(() => null),
      ]);
      setCalculations(listRes.calculations);
      setTotalCount(listRes.total_count);
      if (verifyRes) setVerification(verifyRes);
    } catch (err: any) {
      setError(err?.message || 'Failed to load ledger data.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyChain = async () => {
    setVerifying(true);
    try {
      const res = await verifyLedger();
      setVerification(res);
    } catch (err: any) {
      setError(err?.message || 'Verification request failed.');
    } finally {
      setVerifying(false);
    }
  };

  const handleDownloadExport = async (calcId: string) => {
    setDownloadingId(calcId);
    try {
      await downloadCalculationExport(calcId);
    } catch (err: any) {
      alert(`Download failed: ${err?.message || 'Unknown error'}`);
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-[#fbf9f5] pb-24 text-[#1b1c1a]">
      {/* Top App Bar */}
      <div className="sticky top-0 z-40 bg-[#fbf9f5]/90 backdrop-blur-md border-b border-[#e4e2de] px-4 py-3 flex items-center justify-between">
        <button
          onClick={() => setCurrentScreen('home')}
          className="w-10 h-10 rounded-full flex items-center justify-center text-[#594238] hover:bg-[#ece8e1] transition-all"
        >
          <span className="material-symbols-outlined text-[24px]">arrow_back</span>
        </button>
        <h1 className="font-display text-[18px] font-bold text-[#1b1c1a]">Calculation Ledger & Audit</h1>
        <button
          onClick={loadLedgerData}
          disabled={loading}
          className="w-10 h-10 rounded-full flex items-center justify-center text-[#594238] hover:bg-[#ece8e1] transition-all"
          title="Refresh Ledger"
        >
          <span className={`material-symbols-outlined text-[20px] ${loading ? 'animate-spin' : ''}`}>
            refresh
          </span>
        </button>
      </div>

      <div className="max-w-xl mx-auto px-4 pt-4 space-y-4">
        {error && (
          <div className="p-3 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px]">error</span>
            <span>{error}</span>
          </div>
        )}

        {/* Verification Status Card */}
        <div className="p-5 rounded-3xl bg-white border border-[#e4e2de] shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2.5">
              <div className={`w-9 h-9 rounded-full flex items-center justify-center ${
                verification?.is_valid ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              }`}>
                <span className="material-symbols-outlined text-[20px]">
                  {verification?.is_valid ? 'verified_user' : 'gpp_bad'}
                </span>
              </div>
              <div>
                <h2 className="font-display text-[15px] font-bold text-[#1b1c1a]">SHA-256 Hash Chain</h2>
                <p className="text-[11px] text-[#85736b]">Cryptographic Tamper-Evident Ledger</p>
              </div>
            </div>

            <button
              onClick={handleVerifyChain}
              disabled={verifying}
              className={`px-3.5 py-2 rounded-xl text-white text-[12px] font-bold shadow-sm transition-all active:scale-95 ${
                isTerracotta ? 'bg-[#9e3d00] hover:bg-[#7e3100]' : 'bg-[#1b4332] hover:bg-[#143326]'
              }`}
            >
              {verifying ? 'Verifying...' : 'Verify Chain'}
            </button>
          </div>

          {verification && (
            <div className="mt-3 pt-3 border-t border-[#f0eee9] grid grid-cols-2 gap-2 text-[12px]">
              <div className="p-2.5 rounded-xl bg-[#fbf9f5] border border-[#f0eee9]">
                <div className="text-[10px] text-[#85736b] uppercase font-semibold">Chain Status</div>
                <div className={`font-bold mt-0.5 ${verification.is_valid ? 'text-green-700' : 'text-red-600'}`}>
                  {verification.is_valid ? 'Unbroken & Valid' : 'Tampering Detected'}
                </div>
              </div>
              <div className="p-2.5 rounded-xl bg-[#fbf9f5] border border-[#f0eee9]">
                <div className="text-[10px] text-[#85736b] uppercase font-semibold">Total Blocks</div>
                <div className="font-bold text-[#1b1c1a] mt-0.5">
                  {verification.total_records} Records
                </div>
              </div>
              {verification.last_record_hash && (
                <div className="col-span-2 p-2.5 rounded-xl bg-[#fbf9f5] border border-[#f0eee9]">
                  <div className="text-[10px] text-[#85736b] uppercase font-semibold">Latest Tip Hash</div>
                  <div className="font-mono text-[10px] text-[#594238] truncate mt-0.5">
                    {verification.last_record_hash}
                  </div>
                </div>
              )}
            </div>
          )}

          {verification?.errors && verification.errors.length > 0 && (
            <div className="mt-3 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-[12px]">
              <span className="font-bold">Violations Detected:</span>
              <ul className="list-disc list-inside mt-1 space-y-0.5 text-[11px]">
                {verification.errors.map((e, idx) => (
                  <li key={idx}>{e}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Ledger Records List */}
        <div>
          <div className="flex items-center justify-between mb-2 px-1">
            <h3 className="font-display text-[15px] font-bold text-[#1b1c1a]">
              Historical Pricing Records ({totalCount})
            </h3>
            <span className="text-[11px] font-semibold text-[#85736b] bg-[#f0eee9] px-2 py-0.5 rounded-full">
              Global Sequence
            </span>
          </div>

          {loading ? (
            <div className="p-8 text-center text-[#85736b] text-[13px] bg-white rounded-3xl border border-[#e4e2de]">
              <span className="material-symbols-outlined text-[32px] animate-spin text-[#9e3d00] mb-2 block">
                sync
              </span>
              Loading persistent ledger records...
            </div>
          ) : calculations.length === 0 ? (
            <div className="p-8 text-center text-[#85736b] text-[13px] bg-white rounded-3xl border border-[#e4e2de]">
              <span className="material-symbols-outlined text-[36px] text-[#d5cfc7] mb-2 block">
                receipt_long
              </span>
              No calculations recorded yet. Complete a produce scan to create the genesis ledger entry.
            </div>
          ) : (
            <div className="space-y-3">
              {calculations.map((item) => (
                <div
                  key={item.id}
                  className="p-4 rounded-2xl bg-white border border-[#e4e2de] shadow-sm hover:border-[#d5cfc7] transition-all"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[11px] font-bold bg-[#f0eee9] text-[#1b1c1a] px-2 py-0.5 rounded-md">
                          #{item.sequence_number}
                        </span>
                        <h4 className="font-bold text-[15px] capitalize text-[#1b1c1a]">
                          {item.commodity_id}
                        </h4>
                        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                          item.status.includes('COMPLETED') || item.status.includes('RECONCILED')
                            ? 'bg-green-100 text-green-700'
                            : 'bg-amber-100 text-amber-700'
                        }`}>
                          {item.status}
                        </span>
                      </div>
                      <div className="text-[12px] text-[#594238] mt-1 flex items-center gap-2">
                        <span>Locality: {item.locality_id || 'Regional'}</span>
                        <span>•</span>
                        <span>{new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                    </div>

                    <button
                      onClick={() => handleDownloadExport(item.id)}
                      disabled={downloadingId === item.id}
                      className="px-3 py-1.5 rounded-xl border border-[#d5cfc7] text-[#594238] hover:bg-[#fbf9f5] text-[12px] font-semibold flex items-center gap-1 transition-all active:scale-95"
                      title="Download canonical JSON export"
                    >
                      <span className="material-symbols-outlined text-[16px]">
                        {downloadingId === item.id ? 'downloading' : 'download'}
                      </span>
                      JSON
                    </button>
                  </div>

                  <div className="mt-3 pt-2.5 border-t border-[#f5f2eb] flex items-center justify-between text-[11px] font-mono text-[#85736b]">
                    <span className="truncate max-w-[220px]" title={item.current_record_hash}>
                      SHA: {item.current_record_hash.substring(0, 16)}...
                    </span>
                    <span className="text-[10px] font-sans bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded">
                      Mock Seed Provenance
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
