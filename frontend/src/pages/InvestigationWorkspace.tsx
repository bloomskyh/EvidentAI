import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  Bot, 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  FileCheck, 
  Terminal, 
  ArrowRight, 
  Download, 
  RefreshCw,
  ExternalLink,
  Info,
  Building,
  Store
} from 'lucide-react';
import { DisputeDetails } from '../types';

export const InvestigationWorkspace: React.FC = () => {
  const { disputeId } = useParams<{ disputeId: string }>();
  const [data, setData] = useState<DisputeDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [reinvestigating, setReinvestigating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDisputeData = async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/disputes/${disputeId}`);
      if (!res.ok) throw new Error('Dispute case not found');
      const json = await res.json();
      setData(json);
    } catch (err: any) {
      setError(err.message || 'Error fetching investigation details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (disputeId) {
      fetchDisputeData();
    }
  }, [disputeId]);

  const handleReinvestigate = async () => {
    try {
      setReinvestigating(true);
      const res = await fetch(`/api/disputes/${disputeId}/re-investigate`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed to run investigation');
      await fetchDisputeData();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setReinvestigating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
        <p className="text-slate-400 text-sm">Loading multi-system investigation workspace...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-2xl mx-auto my-12 p-6 bg-red-950/40 border border-red-800 rounded-xl text-center">
        <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
        <h3 className="text-lg font-semibold text-white">Dispute Case Not Found</h3>
        <p className="text-slate-300 text-sm mt-1">{error || 'Unknown error'}</p>
        <Link to="/" className="mt-4 inline-block px-4 py-2 bg-slate-800 text-white rounded-lg text-sm">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const { dispute, evidence_items, latest_investigation, draft_packet } = data;

  return (
    <div className="space-y-8 pb-16">
      {/* Top Case Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-cyan-400 font-bold text-lg">{dispute.id}</span>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide border ${
              dispute.status === 'READY_FOR_DRAFT' ? 'bg-cyan-950 text-cyan-400 border-cyan-800' :
              dispute.status === 'ALREADY_REFUNDED' ? 'bg-emerald-950 text-emerald-400 border-emerald-800' :
              dispute.status === 'UNDER_REVIEW' ? 'bg-purple-950 text-purple-400 border-purple-800' :
              dispute.status === 'NEEDS_MORE_EVIDENCE' ? 'bg-amber-950 text-amber-400 border-amber-800' :
              dispute.status === 'APPROVED' ? 'bg-teal-950 text-teal-400 border-teal-800' :
              dispute.status === 'SUBMITTED' ? 'bg-blue-950 text-blue-400 border-blue-800' :
              'bg-slate-800 text-slate-300 border-slate-700'
            }`}>
              {dispute.status.replace(/_/g, ' ')}
            </span>
          </div>
          <p className="text-slate-400 text-sm">
            Disputed Transaction: <span className="text-white font-mono">{dispute.transaction_id}</span> ({dispute.currency} {dispute.amount.toFixed(2)})
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleReinvestigate}
            disabled={reinvestigating}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${reinvestigating ? 'animate-spin' : ''}`} />
            <span>Re-evaluate Evidence</span>
          </button>

          {draft_packet && (
            <Link
              to={`/disputes/${dispute.id}/packet`}
              className="flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-cyan-600/20 transition"
            >
              <FileCheck className="w-4 h-4" />
              <span>Review Evidence Packet</span>
            </Link>
          )}
        </div>
      </div>

      {/* Decision Summary Card */}
      {latest_investigation && (
        <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Bot className="w-5 h-5 text-cyan-400" />
              <span>Orchestrator Decision & Recommendation</span>
            </h2>
            <span className="text-xs font-semibold text-cyan-400 bg-cyan-950/80 px-2.5 py-1 rounded-full border border-cyan-800/80">
              Confidence: {Math.round(latest_investigation.confidence_score * 100)}%
            </span>
          </div>

          <p className="text-sm text-slate-200 bg-slate-800/40 p-4 rounded-xl border border-slate-800">
            {latest_investigation.decision_summary}
          </p>

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between text-xs pt-1 gap-2">
            <div className="text-slate-400">
              <span className="font-semibold text-slate-300">Recommended Action:</span> {latest_investigation.recommended_action}
            </div>

            {latest_investigation.missing_requirements.length > 0 && (
              <div className="text-amber-400 font-medium">
                Missing: {latest_investigation.missing_requirements.join(', ')}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Two Columns: Evidence Ledger & Agent Tool Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Retrieved Multi-source Evidence Items */}
        <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl space-y-4">
          <h2 className="text-base font-semibold text-white flex items-center justify-between">
            <span>Retrieved Evidence Records ({evidence_items.length})</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </h2>
          <p className="text-xs text-slate-400">
            Immutable records harvested from Mock Bank Core, Order Management, and Communication Logs.
          </p>

          <div className="space-y-3">
            {evidence_items.map((item) => (
              <div
                key={item.id}
                className="p-4 rounded-xl bg-slate-800/40 border border-slate-800 hover:border-slate-700 transition space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {item.source_system === 'BANK_CORE' ? (
                      <span className="p-1 rounded bg-blue-950 text-blue-400 border border-blue-800">
                        <Building className="w-3.5 h-3.5" />
                      </span>
                    ) : (
                      <span className="p-1 rounded bg-purple-950 text-purple-400 border border-purple-800">
                        <Store className="w-3.5 h-3.5" />
                      </span>
                    )}
                    <span className="font-mono text-xs font-semibold text-white">{item.id}</span>
                  </div>

                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                    {item.verification_status}
                  </span>
                </div>

                <div className="text-xs text-slate-300">
                  <span className="text-slate-400 font-medium">Provenance:</span> {item.source_system} (Endpoint: <code className="text-cyan-400">{item.source_endpoint}</code>)
                </div>

                <p className="text-xs text-slate-400 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/80">
                  {item.relevance_explanation}
                </p>

                <div className="text-[11px] font-mono text-slate-500 flex justify-between">
                  <span>Record: {item.source_record_id}</span>
                  <span>{new Date(item.retrieval_timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Orchestration Agent Tool Executions & Plan */}
        <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl space-y-4">
          <h2 className="text-base font-semibold text-white flex items-center justify-between">
            <span>Agent Tool Execution History</span>
            <Terminal className="w-4 h-4 text-cyan-400" />
          </h2>
          <p className="text-xs text-slate-400">
            Live trace of orchestrator tool calls, network queries, and deterministic evaluations.
          </p>

          {latest_investigation && (
            <div className="space-y-2">
              {latest_investigation.tool_executions.map((exec, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 font-mono text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-cyan-400 font-semibold">{exec.tool_name}</span>
                    <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold ${
                      exec.status === 'SUCCESS' ? 'text-emerald-400 bg-emerald-950/60' : 'text-slate-400 bg-slate-800'
                    }`}>
                      {exec.status}
                    </span>
                  </div>

                  <div className="text-[11px] text-slate-400 truncate">
                    {exec.endpoint}
                  </div>

                  <div className="text-[10px] text-slate-500 flex justify-between pt-1">
                    <span>Target: {exec.system}</span>
                    <span>{new Date(exec.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Planned Steps */}
          {latest_investigation && (
            <div className="mt-4 pt-4 border-t border-slate-800">
              <span className="text-xs font-semibold text-slate-300 block mb-2">Investigation Plan:</span>
              <ul className="space-y-1 text-xs text-slate-400 list-inside list-disc">
                {latest_investigation.plan_steps.map((st, i) => (
                  <li key={i}>{st}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
