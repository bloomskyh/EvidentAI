import React, { useEffect, useState } from 'react';
import { 
  FlaskConical, 
  Play, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  RefreshCw, 
  ShieldCheck, 
  FileText,
  Terminal,
  Info
} from 'lucide-react';
import { ScenarioResult } from '../types';

export const TestScenariosPage: React.FC = () => {
  const [results, setResults] = useState<ScenarioResult[]>([]);
  const [running, setRunning] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchExistingResults = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/scenarios/results');
      if (res.ok) {
        const data = await res.json();
        setResults(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExistingResults();
  }, []);

  const handleRunAllScenarios = async () => {
    try {
      setRunning(true);
      const res = await fetch('/api/scenarios/run-all', { method: 'POST' });
      if (!res.ok) throw new Error('Scenario execution failed');
      const data = await res.json();
      setResults(data);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setRunning(false);
    }
  };

  const scenarioMeta: Record<string, { desc: string; expectedTag: string }> = {
    TC1: {
      desc: 'Genuine disputed charge with matching transaction & order, unfulfilled delivery, verified within 60-day window.',
      expectedTag: 'draft packet'
    },
    TC2: {
      desc: 'Disputed transaction where store order already records an issued and completed full refund.',
      expectedTag: 'flagged resolved'
    },
    TC3: {
      desc: 'Fraud claim alleging account takeover without independent police report or unauthorized IP affidavit.',
      expectedTag: 'not added'
    },
    TC4: {
      desc: 'Disputed charge with active interim provisional credit provided by the card issuer.',
      expectedTag: 'not called final'
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <FlaskConical className="w-6 h-6 text-cyan-400" />
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Official Hackathon Test Scenarios
            </h1>
          </div>
          <p className="text-slate-400 text-sm mt-1">
            Mandatory test suite validating TC1 through TC4 with deterministic financial rules & proof verification.
          </p>
        </div>

        <button
          onClick={handleRunAllScenarios}
          disabled={running}
          className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-cyan-600/30 transition disabled:opacity-50"
        >
          {running ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Executing Test Scenarios...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              <span>Run All 4 Official Test Cases</span>
            </>
          )}
        </button>
      </div>

      {/* Test Scenarios Grid */}
      <div className="space-y-4">
        {['TC1', 'TC2', 'TC3', 'TC4'].map((tcKey) => {
          const runResult = results.find((r) => r.id === tcKey);
          const meta = scenarioMeta[tcKey];

          return (
            <div
              key={tcKey}
              className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl space-y-4 hover:border-slate-700 transition"
            >
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-cyan-400 font-bold text-base px-2 py-1 rounded bg-slate-800 border border-slate-700">
                    {tcKey}
                  </span>
                  <div>
                    <h2 className="text-base font-semibold text-white">
                      {tcKey === 'TC1' && 'TC1 — Disputed charge'}
                      {tcKey === 'TC2' && 'TC2 — Already refunded'}
                      {tcKey === 'TC3' && 'TC3 — Fraud claim without evidence'}
                      {tcKey === 'TC4' && 'TC4 — Provisional credit'}
                    </h2>
                    <p className="text-xs text-slate-400">{meta?.desc}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <span className="text-[10px] uppercase font-mono text-slate-500 block">Expected Outcome</span>
                    <span className="text-xs font-mono font-bold text-cyan-300 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                      {meta?.expectedTag}
                    </span>
                  </div>

                  {runResult ? (
                    <div className={`px-3 py-1.5 rounded-xl text-xs font-bold font-mono flex items-center gap-1.5 border ${
                      runResult.status === 'PASS' 
                        ? 'bg-emerald-950/80 text-emerald-400 border-emerald-800' 
                        : 'bg-red-950/80 text-red-400 border-red-800'
                    }`}>
                      {runResult.status === 'PASS' ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-400" />
                      )}
                      <span>{runResult.status}</span>
                    </div>
                  ) : (
                    <span className="text-xs font-mono text-slate-500 px-2 py-1 bg-slate-800/40 rounded">
                      Not Run Yet
                    </span>
                  )}
                </div>
              </div>

              {/* Execution Details if Available */}
              {runResult && (
                <div className="pt-3 border-t border-slate-800/80 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="space-y-1.5">
                    <span className="font-semibold text-slate-300 block">Decision Explanation:</span>
                    <p className="text-slate-400 bg-slate-800/40 p-3 rounded-xl border border-slate-800">
                      {runResult.decision_explanation}
                    </p>
                  </div>

                  <div className="space-y-1.5">
                    <span className="font-semibold text-slate-300 block">Observed Result & Trace:</span>
                    <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 font-mono text-[11px] text-slate-300 space-y-1">
                      <div><span className="text-slate-500">Actual Result:</span> {runResult.actual_result}</div>
                      <div>
                        <span className="text-slate-500">Tools Called:</span> {runResult.evidence_references?.join(', ')}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
