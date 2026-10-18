import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { 
  CheckCircle2, 
  AlertCircle, 
  CreditCard, 
  ArrowRight, 
  ArrowLeft, 
  Bot, 
  ShieldAlert, 
  FileText, 
  UploadCloud,
  Loader2
} from 'lucide-react';
import { BankTransaction } from '../types';

export const NewDisputeWizard: React.FC = () => {
  const [searchParams] = useSearchParams();
  const preselectedTxn = searchParams.get('txn') || '';
  const navigate = useNavigate();

  const [step, setStep] = useState(1);
  const [transactions, setTransactions] = useState<BankTransaction[]>([]);
  const [loadingTxns, setLoadingTxns] = useState(true);

  // Form State
  const [selectedTxnId, setSelectedTxnId] = useState(preselectedTxn);
  const [disputeReason, setDisputeReason] = useState('PRODUCT_NOT_RECEIVED');
  const [explanation, setExplanation] = useState('');
  const [merchantContacted, setMerchantContacted] = useState(true);
  const [supportingNotes, setSupportingNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const loadTxns = async () => {
      try {
        setLoadingTxns(true);
        const res = await fetch('/api/mock-bank/transactions');
        const data = await res.json();
        setTransactions(data);
        if (preselectedTxn && !selectedTxnId) {
          setSelectedTxnId(preselectedTxn);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoadingTxns(false);
      }
    };
    loadTxns();
  }, [preselectedTxn]);

  const activeTransaction = transactions.find((t) => t.id === selectedTxnId);

  const handleNextStep = () => {
    setErrorMsg(null);
    if (step === 1 && !selectedTxnId) {
      setErrorMsg('Please select a valid transaction to investigate.');
      return;
    }
    if (step === 2 && !explanation.trim()) {
      setErrorMsg('Please provide an explanation of what happened.');
      return;
    }
    setStep((prev) => prev + 1);
  };

  const handleBackStep = () => {
    setErrorMsg(null);
    setStep((prev) => prev - 1);
  };

  const handleSubmitDispute = async () => {
    try {
      setSubmitting(true);
      setErrorMsg(null);

      const res = await fetch('/api/disputes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transaction_id: selectedTxnId,
          user_stated_reason: disputeReason,
          user_explanation: explanation,
          merchant_contacted: merchantContacted,
          supporting_notes: supportingNotes
        })
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Failed to initialize dispute investigation');
      }

      const data = await res.json();
      // Navigate directly to Investigation Workspace
      navigate(`/disputes/${data.dispute_id}`);
    } catch (err: any) {
      setErrorMsg(err.message || 'Error occurred while creating dispute');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      {/* Wizard Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center justify-center gap-2">
          New Dispute Evidence Wizard
        </h1>
        <p className="text-slate-400 text-sm max-w-xl mx-auto">
          Collect dispute claims, link with Bank core transactions, and deploy the EvidentAI orchestrator to gather evidence.
        </p>
      </div>

      {/* Step Indicator */}
      <div className="grid grid-cols-4 gap-2 sm:gap-4">
        {[
          { num: 1, label: 'Select Transaction' },
          { num: 2, label: 'Dispute Reason & Claim' },
          { num: 3, label: 'Merchant Communications' },
          { num: 4, label: 'Review & Launch Agent' }
        ].map((s) => {
          const isDone = step > s.num;
          const isCurrent = step === s.num;
          return (
            <div
              key={s.num}
              className={`p-3 rounded-xl border transition text-center ${
                isCurrent
                  ? 'bg-slate-800 border-cyan-500/80 text-cyan-400 shadow-sm'
                  : isDone
                  ? 'bg-slate-900/40 border-emerald-500/40 text-emerald-400'
                  : 'bg-slate-900/20 border-slate-800 text-slate-500'
              }`}
            >
              <div className="flex items-center justify-center space-x-1.5 text-xs font-semibold">
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <span className="w-4 h-4 rounded-full border border-current flex items-center justify-center text-[10px]">
                    {s.num}
                  </span>
                )}
                <span className="hidden sm:inline">{s.label}</span>
              </div>
            </div>
          );
        })}
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-950/60 border border-red-800 text-red-200 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Step 1: Select Transaction */}
      {step === 1 && (
        <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl space-y-4">
          <h2 className="text-lg font-semibold text-white">Step 1: Choose Disputed Bank Transaction</h2>
          <p className="text-xs text-slate-400">
            Select an authorized settled card transaction from the verified Mock Bank ledger.
          </p>

          {loadingTxns ? (
            <div className="py-8 text-center text-slate-400 text-sm flex items-center justify-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-cyan-400" /> Loading bank records...
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
              {transactions.map((txn) => {
                const isSelected = selectedTxnId === txn.id;
                return (
                  <div
                    key={txn.id}
                    onClick={() => setSelectedTxnId(txn.id)}
                    className={`p-4 rounded-xl border cursor-pointer transition flex items-center justify-between ${
                      isSelected
                        ? 'bg-slate-800 border-cyan-500 ring-1 ring-cyan-500'
                        : 'bg-slate-800/40 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-cyan-400 font-semibold text-sm">{txn.id}</span>
                        <span className="text-xs text-slate-400">
                          {new Date(txn.transaction_date).toLocaleDateString()}
                        </span>
                        {txn.has_provisional_credit && (
                          <span className="text-[10px] bg-purple-900/60 text-purple-300 px-1.5 py-0.5 rounded border border-purple-700/60 font-semibold">
                            Provisional Credit
                          </span>
                        )}
                        {txn.refund_status === 'FULL' && (
                          <span className="text-[10px] bg-emerald-900/60 text-emerald-300 px-1.5 py-0.5 rounded border border-emerald-700/60 font-semibold">
                            Full Refund
                          </span>
                        )}
                      </div>
                      <div className="text-white text-sm font-medium">{txn.merchant_name}</div>
                      <div className="text-xs text-slate-400">{txn.description}</div>
                    </div>

                    <div className="text-right">
                      <div className="text-base font-bold text-white">
                        {txn.currency} {txn.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </div>
                      <div className="text-xs text-slate-400 font-mono">Card: **** {txn.card_last4}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Step 2: Dispute Reason & Claim */}
      {step === 2 && (
        <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl space-y-4">
          <h2 className="text-lg font-semibold text-white">Step 2: Dispute Reason & Incident Explanation</h2>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Select Primary Chargeback Reason
            </label>
            <select
              value={disputeReason}
              onChange={(e) => setDisputeReason(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-cyan-500"
            >
              <option value="PRODUCT_NOT_RECEIVED">Product Not Received (13.1)</option>
              <option value="DUPLICATE_CHARGE">Duplicate Charge / Multiple Processing (12.6)</option>
              <option value="INCORRECT_AMOUNT">Incorrect Transaction Amount (12.5)</option>
              <option value="SUSPECTED_FRAUD">Suspected Fraud / Unauthorized Charge (10.4)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Detailed Cardholder Explanation
            </label>
            <textarea
              rows={4}
              value={explanation}
              onChange={(e) => setExplanation(e.target.value)}
              placeholder="Describe in detail what happened (e.g. Expected delivery date, tracking status, discrepancies observed)..."
              className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-cyan-500 placeholder-slate-500"
            />
            <p className="text-[11px] text-slate-400 mt-1">
              Note: Statements entered here will be labeled as Cardholder Allegations until verified against bank/store ledger records.
            </p>
          </div>
        </div>
      )}

      {/* Step 3: Merchant Communications */}
      {step === 3 && (
        <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl space-y-4">
          <h2 className="text-lg font-semibold text-white">Step 3: Direct Merchant Resolution & Supporting Proof</h2>

          <div className="flex items-center space-x-3 bg-slate-800/40 p-4 rounded-xl border border-slate-800">
            <input
              type="checkbox"
              id="merchantContact"
              checked={merchantContacted}
              onChange={(e) => setMerchantContacted(e.target.checked)}
              className="w-4 h-4 text-cyan-500 rounded bg-slate-800 border-slate-700 focus:ring-cyan-500"
            />
            <label htmlFor="merchantContact" className="text-sm text-slate-200 cursor-pointer">
              I have attempted to resolve this issue directly with the merchant prior to requesting a chargeback.
            </label>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Additional Supporting Notes or Ticket Numbers (Optional)
            </label>
            <textarea
              rows={3}
              value={supportingNotes}
              onChange={(e) => setSupportingNotes(e.target.value)}
              placeholder="e.g. Support ticket #88712, merchant promised replacement that never shipped..."
              className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-cyan-500 placeholder-slate-500"
            />
          </div>

          <div className="p-4 rounded-xl border border-dashed border-slate-700 text-center space-y-2 bg-slate-800/20">
            <UploadCloud className="w-8 h-8 text-cyan-400 mx-auto" />
            <p className="text-xs text-slate-300 font-medium">Synthetic Document Intake Sandbox</p>
            <p className="text-[11px] text-slate-500">
              The Evidence Retrieval Agent will automatically ingest simulated order invoices, courier delivery logs, and support chat transcripts from the Mock Store API.
            </p>
          </div>
        </div>
      )}

      {/* Step 4: Confirmation & Launch */}
      {step === 4 && (
        <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl space-y-5">
          <h2 className="text-lg font-semibold text-white">Step 4: Confirm Details & Launch Investigation Agent</h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-slate-800/40 p-4 rounded-xl border border-slate-800">
            <div>
              <span className="text-xs text-slate-400 block">Transaction Reference</span>
              <span className="font-mono text-cyan-400 font-semibold">{activeTransaction?.id}</span>
            </div>
            <div>
              <span className="text-xs text-slate-400 block">Disputed Amount</span>
              <span className="text-white font-bold">
                {activeTransaction?.currency} {activeTransaction?.amount.toFixed(2)}
              </span>
            </div>
            <div>
              <span className="text-xs text-slate-400 block">Merchant Name</span>
              <span className="text-white font-medium">{activeTransaction?.merchant_name}</span>
            </div>
            <div>
              <span className="text-xs text-slate-400 block">Dispute Reason</span>
              <span className="text-white font-medium">{disputeReason}</span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-800/60 border border-cyan-900/40 flex items-start gap-3">
            <Bot className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-slate-300 space-y-1">
              <span className="font-semibold text-white block">Agentic Investigation Plan to be executed:</span>
              <p>1. Query Bank core for transaction authorization and dispute rule deadline.</p>
              <p>2. Query Mock Store for order fulfillment status and refund records.</p>
              <p>3. Apply deterministic financial eligibility checks (window validity, duplicate prevention).</p>
              <p>4. Assemble structured evidence packet for your mandatory human approval.</p>
            </div>
          </div>
        </div>
      )}

      {/* Nav Controls */}
      <div className="flex justify-between items-center pt-2">
        {step > 1 ? (
          <button
            onClick={handleBackStep}
            disabled={submitting}
            className="flex items-center gap-1.5 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold rounded-xl border border-slate-700 transition"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Previous</span>
          </button>
        ) : <div />}

        {step < 4 ? (
          <button
            onClick={handleNextStep}
            className="flex items-center gap-1.5 px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-cyan-600/20 transition"
          >
            <span>Continue</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={handleSubmitDispute}
            disabled={submitting}
            className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-cyan-600/30 transition disabled:opacity-50"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Orchestrating Agent...</span>
              </>
            ) : (
              <>
                <Bot className="w-4 h-4" />
                <span>Launch Agent Investigation</span>
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
};
