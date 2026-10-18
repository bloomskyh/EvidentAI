import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  CreditCard, 
  Search, 
  Filter, 
  ArrowUpRight, 
  ShieldAlert, 
  CheckCircle, 
  Clock, 
  RotateCcw,
  Sparkles,
  ExternalLink
} from 'lucide-react';
import { BankTransaction } from '../types';

export const TransactionsPage: React.FC = () => {
  const [transactions, setTransactions] = useState<BankTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        setLoading(true);
        const res = await fetch('/api/mock-bank/transactions');
        if (!res.ok) throw new Error('Failed to fetch transactions');
        const data = await res.json();
        setTransactions(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchTransactions();
  }, []);

  const filtered = transactions.filter((t) => {
    const matchesSearch = 
      t.id.toLowerCase().includes(search.toLowerCase()) ||
      t.merchant_name.toLowerCase().includes(search.toLowerCase()) ||
      (t.order_id && t.order_id.toLowerCase().includes(search.toLowerCase())) ||
      (t.description && t.description.toLowerCase().includes(search.toLowerCase()));

    const matchesStatus = 
      statusFilter === 'ALL' ||
      (statusFilter === 'REFUNDED' && t.refund_status === 'FULL') ||
      (statusFilter === 'PROVISIONAL' && t.has_provisional_credit) ||
      (statusFilter === 'SETTLED' && t.status === 'SETTLED' && t.refund_status === 'NONE');

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Bank Core Ledger Transactions
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Searchable card settlement ledger connected to Mock Bank API with cross-system store order identifiers.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 bg-slate-900/60 p-4 rounded-xl border border-slate-800">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3.5" />
          <input
            type="text"
            placeholder="Search by Transaction ID, Merchant, or Order ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-800/80 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-400 focus:outline-none focus:border-cyan-500 transition"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-800/80 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Ledger Records</option>
            <option value="SETTLED">Settled Charges</option>
            <option value="REFUNDED">Refunded</option>
            <option value="PROVISIONAL">With Provisional Credit</option>
          </select>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-800/60 text-slate-400 text-xs uppercase font-medium border-b border-slate-800">
              <tr>
                <th className="px-5 py-4">Transaction / Order</th>
                <th className="px-5 py-4">Merchant & Description</th>
                <th className="px-5 py-4">Date</th>
                <th className="px-5 py-4">Amount</th>
                <th className="px-5 py-4">Payment Status</th>
                <th className="px-5 py-4">Credit / Refund</th>
                <th className="px-5 py-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-5 py-12 text-center text-slate-400">
                    Loading transactions from bank core...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-12 text-center text-slate-400">
                    No transactions match your search filter.
                  </td>
                </tr>
              ) : (
                filtered.map((txn) => {
                  return (
                    <tr key={txn.id} className="hover:bg-slate-800/40 transition">
                      <td className="px-5 py-4">
                        <div className="font-mono text-cyan-400 font-semibold">{txn.id}</div>
                        <div className="text-xs text-slate-400 font-mono mt-0.5">
                          {txn.order_id || 'No Store Link'}
                        </div>
                      </td>

                      <td className="px-5 py-4">
                        <div className="font-medium text-white">{txn.merchant_name}</div>
                        <div className="text-xs text-slate-400 truncate max-w-xs">{txn.description}</div>
                      </td>

                      <td className="px-5 py-4 text-xs text-slate-400">
                        {new Date(txn.transaction_date).toLocaleDateString(undefined, {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric'
                        })}
                      </td>

                      <td className="px-5 py-4 font-semibold text-white">
                        {txn.currency} {txn.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>

                      <td className="px-5 py-4">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-950/80 text-blue-400 border border-blue-800/80">
                          {txn.status}
                        </span>
                      </td>

                      <td className="px-5 py-4 text-xs">
                        {txn.refund_status === 'FULL' ? (
                          <span className="inline-flex items-center gap-1 text-emerald-400 font-medium">
                            <RotateCcw className="w-3.5 h-3.5" /> Full Refund
                          </span>
                        ) : txn.has_provisional_credit ? (
                          <span className="inline-flex items-center gap-1 text-purple-400 font-medium">
                            <Sparkles className="w-3.5 h-3.5" /> Provisional Credit ({txn.currency} {txn.provisional_credit_amount})
                          </span>
                        ) : (
                          <span className="text-slate-500">None</span>
                        )}
                      </td>

                      <td className="px-5 py-4 text-right">
                        <button
                          onClick={() => navigate(`/new-dispute?txn=${txn.id}`)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 rounded-lg border border-cyan-500/40 transition"
                        >
                          <span>Investigate Dispute</span>
                          <ArrowUpRight className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
