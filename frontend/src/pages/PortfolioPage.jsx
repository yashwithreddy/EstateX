import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { dashboardApi } from '../api/endpoints';
import RiskBadge from '../components/RiskBadge';

const INR = (val) => '₹' + Number(val).toLocaleString('en-IN');

function PortfolioPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    dashboardApi.investor()
      .then((res) => setData(res.data))
      .catch((err) => setError(err.message));
  }, []);

  if (error) return (
    <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-rose-700">
      <p className="font-semibold">Failed to load portfolio.</p><p className="text-sm">{error}</p>
    </div>
  );
  if (!data) return <div className="flex items-center justify-center p-12 text-slate-400">Loading portfolio…</div>;

  const sortedPortfolio = [...data.portfolio].sort((a, b) => b.estimated_value - a.estimated_value);
  const totalAnnualROI = data.portfolio.reduce((sum, p) => sum + (p.estimated_value * p.roi_percent) / 100, 0);
  const totalAnnualRental = data.portfolio.reduce((sum, p) => sum + (p.shares * p.share_price * 0.07), 0);

  return (
    <section className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-900">My Portfolio</h2>
        <Link to="/marketplace" className="rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-500">
          + Invest More
        </Link>
      </div>

      {/* Summary cards */}
      <div className="grid gap-3 md:grid-cols-4">
        {[
          { label: 'Total Portfolio Value', value: INR(data.total_investment_value), color: 'bg-sky-50 border-sky-200' },
          { label: 'Properties Held', value: data.portfolio.length, color: 'bg-indigo-50 border-indigo-200' },
          { label: 'Est. Annual ROI', value: INR(totalAnnualROI), color: 'bg-emerald-50 border-emerald-200' },
          { label: 'Est. Annual Rental', value: INR(totalAnnualRental), color: 'bg-amber-50 border-amber-200' },
        ].map((s) => (
          <div key={s.label} className={`rounded-2xl border p-4 ${s.color}`}>
            <p className="text-xs text-slate-500">{s.label}</p>
            <p className="mt-1 text-xl font-bold text-slate-900">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Portfolio table */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="mb-4 font-semibold text-slate-900">Invested Properties</h3>
        {data.portfolio.length === 0 ? (
          <div className="flex flex-col items-center gap-3 py-10 text-slate-400">
            <span className="text-4xl">📂</span>
            <p className="text-sm">No investments yet.</p>
            <Link to="/marketplace" className="text-sky-600 font-medium hover:underline text-sm">Browse properties →</Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-xs text-slate-400 border-b border-slate-100">
                  <th className="pb-3 pr-4">Property</th>
                  <th className="pb-3 pr-4">City</th>
                  <th className="pb-3 pr-4">Shares</th>
                  <th className="pb-3 pr-4">Value</th>
                  <th className="pb-3 pr-4">AI ROI</th>
                  <th className="pb-3 pr-4">Risk</th>
                  <th className="pb-3">Est. Annual Gain</th>
                </tr>
              </thead>
              <tbody>
                {sortedPortfolio.map((p) => {
                  const annualGain = (p.estimated_value * p.roi_percent) / 100;
                  return (
                    <tr key={p.property_id} className="border-b border-slate-50 hover:bg-slate-50">
                      <td className="py-3 pr-4">
                        <Link to={`/properties/${p.property_id}`} className="font-medium text-slate-900 hover:text-sky-600">
                          {p.title}
                        </Link>
                      </td>
                      <td className="py-3 pr-4 text-slate-500">{p.city}</td>
                      <td className="py-3 pr-4 font-semibold text-slate-800">{p.shares.toLocaleString('en-IN')}</td>
                      <td className="py-3 pr-4 font-semibold text-slate-800">{INR(p.estimated_value)}</td>
                      <td className="py-3 pr-4 font-semibold text-emerald-600">{p.roi_percent}%</td>
                      <td className="py-3 pr-4"><RiskBadge risk={p.risk_level} /></td>
                      <td className="py-3 font-semibold text-sky-700">{INR(annualGain)}</td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr className="bg-slate-50 text-sm font-semibold text-slate-700">
                  <td colSpan={3} className="py-3 pl-2">Total</td>
                  <td className="py-3">{INR(data.total_investment_value)}</td>
                  <td className="py-3 text-emerald-600">—</td>
                  <td className="py-3">—</td>
                  <td className="py-3 text-sky-700">{INR(totalAnnualROI)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>

      {/* Quick links */}
      <div className="flex gap-3">
        <Link to="/liquidity" className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50">
          ⚡ Partial Exit / Liquidity
        </Link>
        <Link to="/investor" className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50">
          📊 Full Dashboard
        </Link>
      </div>
    </section>
  );
}

export default PortfolioPage;
