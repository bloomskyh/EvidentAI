import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  CreditCard, 
  AlertTriangle, 
  FileCheck2, 
  CheckCircle2, 
  HelpCircle, 
  ArrowRight,
  TrendingUp,
  RefreshCw,
  PlusCircle,
  Clock,
  ShieldCheck
} from 'lucide-react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, BarChart, Bar, XAxis, YAxis } from 'recharts';
import { DashboardStats } from '../types';

const STATUS_COLORS: Record<string, string> = {
  READY_FOR_DRAFT: '#06B6D4', // Cyan
  ALREADY_REFUNDED: '#10B981', // Emerald
  NEEDS_MORE_EVIDENCE: '#F59E0B', // Amber
  UNDER_REVIEW: '#8B5CF6', // Purple
  OUTSIDE_DISPUTE_WINDOW: '#EF4444', // Red
  BLOCKED: '#64748B', // Slate
  SUBMITTED: '#3B82F6', // Blue
  APPROVED: '#14B8A6' // Teal
};

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/dashboard/stats');
      if (!res.ok) throw new Error('Failed to load dashboard metrics');
      const data = await res.json();
      setStats(data);
    } catch (err: any) {
      setError(err.message || 'Error connecting to backend');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
        <p className="text-slate-400 text-sm">Aggregating real-time financial ledger metrics...</p>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="max-w-4xl mx-auto my-12 p-6 bg-red-950/40 border border-red-800/60 rounded-xl text-center">
        <AlertTriangle className="w-10 h-10 text-red-400 mx-auto mb-3" />
        <h3 className="text-lg font-semibold text-white">Metrics Unavailable</h3>
        <p className="text-slate-300 text-sm mt-1">{error || 'Could not query backend database.'}</p>
        <button
          onClick={fetchStats}
          className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm font-medium transition"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const pieData = Object.entries(stats.status_distribution).map(([status, count]) => ({
    name: status.replace(/_/g, ' '),
    value: count,
    color: STATUS_COLORS[status] || '#94A3B8'
  }));

  return (
    <div className="space-y-8 pb-12">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/80 p-6 rounded-2xl border border-slate-800 shadow-xl backdrop-blur-sm">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Chargeback Evidence Assistant Overview
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Agentic multi-source evidence cross-referencing, deterministic eligibility & bank-grade audit trail.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchStats}
            title="Refresh database counters"
            className="p-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl border border-slate-700 transition"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <Link
            to="/new-dispute"
            className="flex items-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-cyan-600/20 transition transform active:scale-95"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Start New Dispute</span>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-slate-900/60 border border-slate-800 p-5 rounded-2xl shadow-sm hover:border-slate-700 transition">
          <div className="flex justify-between items-center text-slate-400 mb-2">
            <span className="text-xs uppercase font-medium tracking-wider">Total Transactions</span>
            <CreditCard className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-3xl font-bold text-white">{stats.total_transactions}</div>
          <span className="text-[11px] text-slate-500 mt-1 block">Live Bank Core Ledger</span>
        </div>

        <div className="bg-slate-900/60 border border-cyan-900/40 p-5 rounded-2xl shadow-sm hover:border-cyan-800/60 transition">
          <div className="flex justify-between items-center text-cyan-400 mb-2">
            <span className="text-xs uppercase font-medium tracking-wider">Open Disputes</span>
            <Clock className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-bold text-cyan-400">{stats.open_disputes}</div>
          <span className="text-[11px] text-slate-500 mt-1 block">Actively orchestrated</span>
        </div>

        <div className="bg-slate-900/60 border border-blue-900/40 p-5 rounded-2xl shadow-sm hover:border-blue-800/60 transition">
          <div className="flex justify-between items-center text-blue-400 mb-2">
            <span className="text-xs uppercase font-medium tracking-wider">Draft Packets</span>
            <FileCheck2 className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-3xl font-bold text-blue-400">{stats.draft_packets}</div>
          <span className="text-[11px] text-slate-500 mt-1 block">Awaiting / Verified</span>
        </div>

        <div className="bg-slate-900/60 border border-emerald-900/40 p-5 rounded-2xl shadow-sm hover:border-emerald-800/60 transition">
          <div className="flex justify-between items-center text-emerald-400 mb-2">
            <span className="text-xs uppercase font-medium tracking-wider">Resolved / Refunded</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-bold text-emerald-400">{stats.resolved_or_refunded}</div>
          <span className="text-[11px] text-slate-500 mt-1 block">No duplicate chargeback</span>
        </div>

        <div className="bg-slate-900/60 border border-amber-900/40 p-5 rounded-2xl shadow-sm hover:border-amber-800/60 transition">
          <div className="flex justify-between items-center text-amber-400 mb-2">
            <span className="text-xs uppercase font-medium tracking-wider">Requires Evidence</span>
            <HelpCircle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-bold text-amber-400">{stats.requiring_evidence}</div>
          <span className="text-[11px] text-slate-500 mt-1 block">Needs proof or affidavit</span>
        </div>
      </div>

      {/* Analytics & Activity Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Status Distribution Visualizer */}
        <div className="lg:col-span-1 bg-slate-900/60 border border-slate-800 p-6 rounded-2xl shadow-sm">
          <h2 className="text-base font-semibold text-white mb-1 flex items-center justify-between">
            <span>Dispute Status Distribution</span>
            <TrendingUp className="w-4 h-4 text-cyan-400" />
          </h2>
          <p className="text-xs text-slate-400 mb-4">Real database distribution breakdown</p>

          <div className="h-56 w-full">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                No active disputes recorded yet
              </div>
            )}
          </div>

          <div className="mt-4 space-y-2">
            {pieData.map((item) => (
              <div key={item.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-slate-300 font-medium">{item.name}</span>
                </div>
                <span className="text-slate-400 font-bold">{item.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Orchestrator Activity Log */}
        <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800 p-6 rounded-2xl shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-base font-semibold text-white">Recent Agent Investigation Activity</h2>
              <p className="text-xs text-slate-400">Chronological decisions evaluated by orchestrator & financial rules</p>
            </div>
            <Link to="/transactions" className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-medium">
              View all transactions <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="space-y-3">
            {stats.recent_activity.length > 0 ? (
              stats.recent_activity.map((act) => {
                const color = STATUS_COLORS[act.status] || '#94A3B8';
                return (
                  <div
                    key={act.id}
                    className="p-4 rounded-xl bg-slate-800/40 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:border-slate-700 transition"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span 
                          className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wide"
                          style={{ backgroundColor: `${color}20`, color: color, border: `1px solid ${color}40` }}
                        >
                          {act.status}
                        </span>
                        <span className="text-xs font-mono text-slate-400">{act.dispute_id}</span>
                      </div>
                      <p className="text-xs text-slate-300 line-clamp-1">{act.summary}</p>
                      <p className="text-[11px] text-cyan-400 font-medium">{act.action}</p>
                    </div>

                    <Link
                      to={`/disputes/${act.dispute_id}`}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-700 self-start sm:self-center transition"
                    >
                      <span>Investigate</span>
                      <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                );
              })
            ) : (
              <div className="text-center py-12 text-slate-500 text-sm">
                No recent agent investigation runs. Start a dispute or run the test scenarios.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
