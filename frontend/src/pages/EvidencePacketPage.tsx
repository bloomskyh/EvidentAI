import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { 
  FileCheck2, 
  Download, 
  CheckCircle, 
  XCircle, 
  RotateCcw, 
  Send, 
  ShieldCheck, 
  Lock, 
  Clock, 
  AlertTriangle,
  FileCode,
  FileText,
  Loader2
} from 'lucide-react';
import { DisputeDetails } from '../types';

export const EvidencePacketPage: React.FC = () => {
  const { disputeId } = useParams<{ disputeId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<DisputeDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [approving, setApproving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [comments, setComments] = useState('');
  const [approverName, setApproverName] = useState('Rahul Sharma (Cardholder)');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchDispute = async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/disputes/${disputeId}`);
      if (!res.ok) throw new Error('Failed to load dispute');
      const json = await res.json();
      setData(json);
    } catch (e: any) {
      setErrorMsg(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (disputeId) fetchDispute();
  }, [disputeId]);

  const handleApprovalAction = async (action: 'APPROVED' | 'REJECTED' | 'RETURNED_FOR_CORRECTION') => {
    if (!data?.draft_packet) return;
    try {
      setApproving(true);
      setErrorMsg(null);
      const res = await fetch(`/api/disputes/${disputeId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          packet_id: data.draft_packet.id,
          packet_version: data.draft_packet.packet_version,
          action: action,
          approver_name: approverName,
          comments: comments
        })
      });

      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || 'Approval recording failed');
      }

      await fetchDispute();
    } catch (e: any) {
      setErrorMsg(e.message);
    } finally {
      setApproving(false);
    }
  };

  const handleSubmitToBank = async () => {
    if (!data?.draft_packet) return;
    try {
      setSubmitting(true);
      setErrorMsg(null);
      // Generate a stable idempotency key for this submission attempt
      const idempotencyKey = `IDEMP-${data.draft_packet.id}-v${data.draft_packet.packet_version}`;

      const res = await fetch(`/api/disputes/${disputeId}/submit-to-bank`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          packet_id: data.draft_packet.id,
          idempotency_key: idempotencyKey
        })
      });

      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || 'Submission to bank network failed');
      }

      const resData = await res.json();
      await fetchDispute();
      // Navigate to Approval and Verification view
      navigate(`/disputes/${disputeId}/verification?bank_sub_id=${resData.bank_submission_id}`);
    } catch (e: any) {
      setErrorMsg(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
        <p className="text-slate-400 text-sm">Compiling verified evidence packet...</p>
      </div>
    );
  }

  if (!data || !data.draft_packet) {
    return (
      <div className="max-w-2xl mx-auto my-12 p-6 bg-slate-900 border border-slate-800 rounded-xl text-center">
        <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-2" />
        <h3 className="text-lg font-semibold text-white">No Draft Packet Generated</h3>
        <p className="text-slate-400 text-sm mt-1">
          This case either requires more evidence or has already been resolved via merchant refund.
        </p>
        <Link to={`/disputes/${disputeId}`} className="mt-4 inline-block px-4 py-2 bg-slate-800 text-white rounded-lg text-sm">
          Return to Workspace
        </Link>
      </div>
    );
  }

  const { draft_packet, dispute } = data;
  const pData = draft_packet.packet_data;

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-16">
      {/* Top Packet Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-cyan-400 font-bold text-lg">{draft_packet.id}</span>
            <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">
              Version {draft_packet.packet_version}
            </span>
            {draft_packet.is_approved ? (
              <span className="text-xs bg-teal-950 text-teal-400 border border-teal-800 px-2.5 py-0.5 rounded-full font-bold">
                HUMAN APPROVED
              </span>
            ) : (
              <span className="text-xs bg-amber-950 text-amber-400 border border-amber-800 px-2.5 py-0.5 rounded-full font-bold">
                AWAITING HUMAN APPROVAL
              </span>
            )}
          </div>
          <p className="text-xs font-mono text-slate-500 mt-1">
            SHA-256 Hash: {draft_packet.content_hash}
          </p>
        </div>

        {/* Download Buttons */}
        <div className="flex items-center gap-2">
          <a
            href={`/api/disputes/${disputeId}/export/json`}
            download
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition"
          >
            <FileCode className="w-3.5 h-3.5" />
            <span>Export JSON</span>
          </a>

          <a
            href={`/api/disputes/${disputeId}/export/pdf`}
            download
            className="flex items-center gap-1.5 px-3 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-cyan-600/20 transition"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Download Official PDF</span>
          </a>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-950/60 border border-red-800 text-red-200 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Draft Dispute Form Viewer */}
      <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl space-y-6">
        <div className="border-b border-slate-800 pb-4">
          <h2 className="text-lg font-bold text-white">Draft Bank Dispute Submission Form</h2>
          <p className="text-xs text-slate-400 mt-1">
            Standard cardholder dispute declaration compiled by EvidentAI for network transmission.
          </p>
        </div>

        {/* Form Details Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-slate-800/40 p-4 rounded-xl border border-slate-800">
          <div>
            <span className="text-xs text-slate-400 block">Dispute Category</span>
            <span className="text-white font-medium text-sm">{pData.reason}</span>
          </div>
          <div>
            <span className="text-xs text-slate-400 block">Disputed Amount</span>
            <span className="text-white font-bold text-sm">{pData.currency} {pData.amount.toFixed(2)}</span>
          </div>
          <div>
            <span className="text-xs text-slate-400 block">Bank Transaction Ref</span>
            <span className="font-mono text-cyan-400 text-sm">{pData.transaction_id}</span>
          </div>
        </div>

        {/* Cardholder Allegation vs Verified Facts */}
        <div className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block">
            Cardholder Stated Claim (Unverified Allegation)
          </span>
          <p className="p-4 rounded-xl bg-slate-950/50 border border-slate-800 text-slate-300 text-sm">
            "{pData.customer_allegation}"
          </p>
        </div>

        {/* Chronological Timeline */}
        <div className="space-y-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block">
            Chronological Evidence Timeline
          </span>
          <div className="space-y-2 border-l-2 border-cyan-500/40 pl-4 ml-2">
            {pData.timeline && pData.timeline.map((evt: any, idx: number) => (
              <div key={idx} className="relative pb-2">
                <div className="absolute -left-[21px] top-1.5 w-2 h-2 rounded-full bg-cyan-400" />
                <div className="text-xs font-semibold text-white">{evt.event}</div>
                <div className="text-xs text-slate-400">{evt.details}</div>
                <div className="text-[10px] text-slate-500 font-mono">{evt.timestamp}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Included Evidence Items */}
        <div className="space-y-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block">
            Included Verified Evidence Items ({pData.evidence_items?.length || 0})
          </span>
          <div className="space-y-2">
            {pData.evidence_items && pData.evidence_items.map((evi: any) => (
              <div key={evi.evidence_id} className="p-3 bg-slate-800/40 border border-slate-800 rounded-xl text-xs space-y-1">
                <div className="flex justify-between items-center">
                  <span className="font-mono text-cyan-400 font-semibold">{evi.evidence_id}</span>
                  <span className="text-slate-400">{evi.source_system} ({evi.source_record_id})</span>
                </div>
                <p className="text-slate-300">{evi.relevance}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Human Approval Section */}
      <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl space-y-4">
        <div className="flex items-center gap-2">
          <Lock className="w-5 h-5 text-cyan-400" />
          <h2 className="text-base font-semibold text-white">Mandatory Human Review & Approval</h2>
        </div>
        <p className="text-xs text-slate-400">
          Backend security policy requires explicit human cardholder consent and signature prior to network transmission.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Approver Full Name / Role</label>
            <input
              type="text"
              value={approverName}
              onChange={(e) => setApproverName(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-xs text-white"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Compliance Notes (Optional)</label>
            <input
              type="text"
              placeholder="e.g. Verified tracking failure with courier..."
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-xs text-white"
            />
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-slate-800">
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleApprovalAction('APPROVED')}
              disabled={approving || draft_packet.is_approved}
              className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-emerald-600/20 disabled:opacity-40 transition"
            >
              <CheckCircle className="w-4 h-4" />
              <span>{draft_packet.is_approved ? 'Approved' : 'Approve Draft Packet'}</span>
            </button>

            <button
              onClick={() => handleApprovalAction('RETURNED_FOR_CORRECTION')}
              disabled={approving}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 text-xs font-semibold rounded-xl border border-amber-500/40 transition"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Return for Correction</span>
            </button>

            <button
              onClick={() => handleApprovalAction('REJECTED')}
              disabled={approving}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-300 text-xs font-semibold rounded-xl border border-red-500/40 transition"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>Reject Draft</span>
            </button>
          </div>

          <div>
            <button
              onClick={handleSubmitToBank}
              disabled={!draft_packet.is_approved || submitting || dispute.status === 'SUBMITTED'}
              className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-blue-600/30 disabled:opacity-40 transition"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Submitting to Bank Network...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Submit to Mock Bank Network</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
