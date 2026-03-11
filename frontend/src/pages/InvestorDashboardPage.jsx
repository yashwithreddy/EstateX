import { useEffect, useMemo, useState } from 'react';
import { Doughnut } from 'react-chartjs-2';
import { Chart, ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js';
import RiskBadge from '../components/RiskBadge';
import { dashboardApi } from '../api/endpoints';
import { Link } from 'react-router-dom';

Chart.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

const INR = (val) => '₹' + Number(val).toLocaleString('en-IN');

const PALETTE = ['#0ea5e9', '#14b8a6', '#f59e0b', '#f43f5e', '#8b5cf6', '#10b981', '#ef4444', '#3b82f6'];

function StatBox({ label, value, sub, color = 'bg-sky-50 border-sky-200' }) {
  return (
    <div className={`rounded-2xl border p-4 ${color}`}>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-slate-900">{value}</p>
      {sub && <p className="mt-0.5 text-xs text-slate-500">{sub}</p>}
    </div>
  );
}

function InvestorDashboardPage() {
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    dashboardApi.investor()
      .then((res) => setDashboard(res.data))
      .catch((err) => setError(err.message));
  }, []);

  const doughnutData = useMemo(() => {
    if (!dashboard || !dashboard.ownership_distribution.length) return null;
    return {
      labels: dashboard.ownership_distribution.map((d) => d.property),
      datasets: [{
        data: dashboard.ownership_distribution.map((d) => d.value),
        backgroundColor: PALETTE.slice(0, dashboard.ownership_distribution.length),
        borderWidth: 2,
        borderColor: '#fff',
      }],
    };
  }, [dashboard]);

  if (error) return (
    <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-rose-700">
      <p className="font-semibold">Failed to load dashboard</p>
      <p className="text-sm mt-1">{error}</p>
    </div>
  );

  if (!dashboard) return (
    <div className="flex items-center justify-center p-12 text-slate-400">Loading dashboard…</div>
  );

  const totalRentalEst = dashboard.portfolio.reduce(
    (sum, p) => sum + (p.estimated_value * p.roi_percent / 100), 0
  );

  return (
    <section className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-900">Investor Dashboard</h2>
        <Link to="/marketplace" className="rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-500">
          Browse Listings
        </Link>
      </div>

      {/* Stat cards */}
      <div className="grid gap-3 md:grid-cols-4">
        <StatBox
          label="Total Portfolio Value"
          value={INR(dashboard.total_investment_value)}
          sub="Current market valuation"
          color="bg-sky-50 border-sky-200"
        />
        <StatBox
          label="Properties Owned"
          value={dashboard.portfolio.length}
          sub="Across Indian markets"
          color="bg-indigo-50 border-indigo-200"
        />
        <StatBox
          label="Est. Annual ROI"
          value={INR(totalRentalEst)}
          sub="Based on AI predictions"
          color="bg-emerald-50 border-emerald-200"
        />
        <StatBox
          label="Transactions"
          value={dashboard.transaction_history.length}
          sub="Buy / sell records"
          color="bg-amber-50 border-amber-200"
        />
      </div>

      {/* Charts + Portfolio */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Doughnut */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-3 font-semibold text-slate-900">Portfolio Distribution</h3>
          {doughnutData ? (
            <div className="flex items-center gap-4">
              <div style={{ width: 180, height: 180 }}>
                <Doughnut data={doughnutData} options={{ plugins: { legend: { display: false } }, cutout: '65%', maintainAspectRatio: false }} />
              </div>
              <ul className="flex-1 space-y-2 text-xs">
                {dashboard.ownership_distribution.map((d, i) => (
                  <li key={d.property_id} className="flex items-center gap-2">
                    <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: PALETTE[i % PALETTE.length] }} />
                    <span className="truncate max-w-28 text-slate-700">{d.property}</span>
                    <span className="ml-auto font-medium text-slate-800">{INR(d.value)}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="flex h-40 items-center justify-center text-slate-400 text-sm">
              No investments yet. <Link to="/marketplace" className="ml-1 text-sky-600 underline">Browse properties →</Link>
            </div>
          )}
        </div>

        {/* Portfolio table */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-3 font-semibold text-slate-900">Holdings</h3>
          {dashboard.portfolio.length === 0 ? (
            <div className="flex h-40 items-center justify-center text-slate-400 text-sm">No holdings yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="text-slate-400">
                    <th className="pb-2">Property</th>
                    <th className="pb-2">Shares</th>
                    <th className="pb-2">ROI</th>
                    <th className="pb-2">Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboard.portfolio.map((p) => (
                    <tr key={p.property_id} className="border-t border-slate-100">
                      <td className="py-2 pr-2">
                        <Link to={`/properties/${p.property_id}`} className="font-medium text-slate-800 hover:text-sky-600">{p.title}</Link>
                        <p className="text-slate-400">{p.city}</p>
                      </td>
                      <td className="py-2 font-semibold text-slate-800">{p.shares}</td>
                      <td className="py-2 font-semibold text-emerald-600">{p.roi_percent}%</td>
                      <td className="py-2"><RiskBadge risk={p.risk_level} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Transaction history */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="mb-3 font-semibold text-slate-900">Transaction History</h3>
        {dashboard.transaction_history.length === 0 ? (
          <p className="text-slate-400 text-sm">No transactions yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-xs text-slate-400">
                  <th className="pb-2 pr-4">ID</th>
                  <th className="pb-2 pr-4">Type</th>
                  <th className="pb-2 pr-4">Property</th>
                  <th className="pb-2 pr-4">Shares</th>
                  <th className="pb-2 pr-4">Amount</th>
                  <th className="pb-2">Tx Hash</th>
                </tr>
              </thead>
              <tbody>
                {dashboard.transaction_history.slice(0, 15).map((tx) => (
                  <tr key={tx.id} className="border-t border-slate-100">
                    <td className="py-2 pr-4 text-slate-400">#{tx.id}</td>
                    <td className="py-2 pr-4">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${tx.tx_type === 'primary_buy' ? 'bg-sky-100 text-sky-700' : tx.tx_type === 'secondary_buy' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                        {tx.tx_type.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="py-2 pr-4 text-slate-700">#{tx.property_id}</td>
                    <td className="py-2 pr-4 font-medium text-slate-800">{tx.shares}</td>
                    <td className="py-2 pr-4 font-semibold text-slate-800">{INR(tx.amount)}</td>
                    <td className="py-2 max-w-40 truncate text-xs text-slate-400 font-mono">
                      {tx.onchain_tx_hash || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

export default InvestorDashboardPage;
