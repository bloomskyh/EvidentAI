import React, { useEffect, useState } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import { 
  ShieldCheck, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  ArrowRight, 
  Building2, 
  Copy, 
  FileCheck2,
  Lock,
  Loader2
} from 'lucide-react';
import { DisputeDetails } from '../types';

export const ApprovalVerificationPage: React.FC = () => {
  const { disputeId } = useParams<{ disputeId: string }>();
  const [searchParams] = useSearchParams();
  const bankSubId = searchParams.get('bank_sub_id');

  const [data, setData] = useState<DisputeDetails | null>(null);
  const [bankRecord, setBankRecord] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadVerificationState = async () => {
      try {
        setLoading(true);
        // 1. Load dispute details
        const resDispute = await fetch(`/api/disputes/${disputeId}`);
        const jsonDispute = await resDispute.json();
        setData(jsonDispute);

        // 2. Independently query Mock Bank API for recorded dispute entry
        const subIdToQuery = bankSubId || jsonDispute.verifications?.[0]?.bank_dispute_id;
        if (subIdToQuery) {
          const resBank = await fetch(`/api/mock-bank/disputes/${subIdToQuery}`);
          if (resBank.ok) {
            const jsonBank = await resBank.json();
            setBankRecord(jsonBank);
          }
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (disputeId) loadVerificationState();
  }, [disputeId, bankSubId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
        <p className="text-slate-400 text-sm">Executing independent verification audit against bank ledger...</p>
      </div>
    );
  }

  const latestVerification = data?.verifications?.[0];
  const isPass = latestVerification?.verification_status === 'PASS';

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      {/* Top Banner */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-xs font-semibold text-slate-300">
          <ShieldCheck className="w-4 h-4 text-cyan-400" />
          <span>Independent Post-Submission Audit</span>
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-white">
          Submission & Ledger Verification State
        </h1>
        <p className="text-slate-400 text-sm max-w-lg mx-auto">
          EvidentAI independently queries the mock banking network to prove immutable record recording without trusting frontend assumptions.
        </p>
      </div>

      {/* Verification Status Card */}
      <div className={`p-6 rounded-2xl border ${
        isPass 
          ? 'bg-emerald-950/30 border-emerald-800/80' 
          : 'bg-red-950/30 border-red-800/80'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {isPass ? (
              <CheckCircle2 className="w-8 h-8 text-emerald-400" />
            ) : (
              <XCircle className="w-8 h-8 text-red-400" />
            )}
            <div>
              <div className="text-lg font-bold text-white flex items-center gap-2">
                <span>Verification Outcome:</span>
                <span className={isPass ? 'text-emerald-400 font-mono' : 'text-red-400 font-mono'}>
                  {latestVerification?.verification_status || 'UNKNOWN'}
                </span>
              </div>
              <p className="text-xs text-slate-300 mt-0.5">{latestVerification?.explanation}</p>
            </div>
          </div>

          <span className="text-[11px] font-mono text-slate-500">
            {latestVerification?.verified_at && new Date(latestVerification.verified_at).toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* Two Column Grid: Audit Checks & Raw Bank Network Confirmation */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Verification Checks Grid */}
        <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl space-y-4">
          <h2 className="text-base font-semibold text-white">Deterministic Financial Audit Checks</h2>
          <div className="space-y-3">
            {[
              { key: 'dispute_id_exists', label: 'Dispute Record Present in Bank Ledger' },
              { key: 'transaction_id_match', label: 'Transaction Reference Matched' },
              { key: 'amount_currency_match', label: 'Amount & Currency Exact Match' },
              { key: 'evidence_references_valid', label: 'Evidence References Bound' },
              { key: 'single_execution_guaranteed', label: 'Idempotency: Exactly-Once Submission' },
              { key: 'status_matches_network_protocol', label: 'Network Lifecycle State Authorized' }
            ].map((check) => {
              const details = latestVerification?.details?.checks || {};
              const checked = details[check.key];
              return (
                <div key={check.key} className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
                  <span className="text-slate-300 font-medium">{check.label}</span>
                  {checked ? (
                    <span className="text-emerald-400 font-bold flex items-center gap-1 font-mono">
                      PASS
                    </span>
                  ) : (
                    <span className="text-red-400 font-bold flex items-center gap-1 font-mono">
                      FAIL
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Mock Bank Ledger Raw Confirmation */}
        <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl space-y-4">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Building2 className="w-4 h-4 text-cyan-400" />
            <span>Mock Bank Core Network Ledger</span>
          </h2>

          {bankRecord ? (
            <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 font-mono text-xs space-y-2">
              <div>
                <span className="text-slate-500 block text-[10px]">BANK NETWORK RECORD ID</span>
                <span className="text-cyan-400 font-semibold">{bankRecord.id}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">LINKED DISPUTE CASE</span>
                <span className="text-slate-300">{bankRecord.dispute_case_id}</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-slate-500 block text-[10px]">RECORDED AMOUNT</span>
                  <span className="text-white font-bold">{bankRecord.currency} {bankRecord.amount}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px]">NETWORK STATUS</span>
                  <span className="text-emerald-400 font-bold">{bankRecord.status}</span>
                </div>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">IDEMPOTENCY KEY</span>
                <span className="text-slate-400 text-[11px] truncate block">{bankRecord.idempotency_key}</span>
              </div>
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-slate-500">
              No direct bank record returned.
            </div>
          )}

          <div className="pt-2 flex justify-between items-center text-xs">
            <Link
              to={`/disputes/${disputeId}`}
              className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1"
            >
              <span>Return to Workspace</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>

            <Link
              to="/"
              className="text-slate-400 hover:text-slate-200"
            >
              Back to Dashboard
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
