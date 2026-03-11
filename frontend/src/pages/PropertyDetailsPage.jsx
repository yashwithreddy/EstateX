import { useEffect, useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Bar } from 'react-chartjs-2';
import { Chart, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js';
import { aiApi, investmentApi, propertyApi } from '../api/endpoints';
import { useAuth } from '../context/AuthContext';
import RiskBadge from '../components/RiskBadge';

Chart.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend);

const INR = (val) => '₹' + Number(val).toLocaleString('en-IN');

const FEATURE_ICONS = {
  'Location Score': '📍',
  'Rental Demand Index': '🏘️',
  'Infrastructure Growth': '🏗️',
  'Vacancy Rate': '📉',
  'Market Appreciation Trend': '📈',
};

function PropertyDetailsPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const [property, setProperty] = useState(null);
  const [explain, setExplain] = useState(null);
  const [shares, setShares] = useState(1);
  const [investing, setInvesting] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    propertyApi.detail(id).then((res) => {
      const p = res.data;
      setProperty(p);
      return aiApi.explain({
        property_price: Number(p.property_price),
        rental_yield: p.rental_yield,
        demand_index: p.demand_index,
        market_trend: p.market_trend,
      });
    }).then((res) => setExplain(res.data)).catch(console.error);
  }, [id]);

  const { chartData, totalContrib, featureList } = useMemo(() => {
    if (!explain) return { chartData: null, totalContrib: 0, featureList: [] };
    const entries = Object.entries(explain.feature_contributions);
    const absVals = entries.map(([, v]) => Math.abs(v));
    const total = absVals.reduce((a, b) => a + b, 0) || 1;
    const featureList = entries.map(([k, v]) => ({
      name: k,
      value: v,
      pct: Math.round((Math.abs(v) / total) * 100),
      positive: v >= 0,
    }));
    const colors = featureList.map((f) => (f.positive ? '#0ea5e9' : '#f43f5e'));
    const chartData = {
      labels: featureList.map((f) => f.name),
      datasets: [{
        label: 'SHAP Contribution',
        data: featureList.map((f) => f.value),
        backgroundColor: colors,
        borderRadius: 6,
      }],
    };
    return { chartData, totalContrib: total, featureList };
  }, [explain]);

  const invest = async () => {
    if (!shares || shares < 1) return;
    setInvesting(true);
    setMessage('');
    try {
      const wallet = localStorage.getItem('wallet_address') || '0x2222222222222222222222222222222222222222';
      await investmentApi.buyShares({ property_id: Number(id), shares: Number(shares), wallet_address: wallet });
      setMessage(`✓ Successfully purchased ${shares} share(s) for ${INR(Number(shares) * Number(property.price_per_share))}`);
    } catch (e) {
      setMessage(`✗ ${e.message}`);
    } finally {
      setInvesting(false);
    }
  };

  if (!property) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-center text-slate-400">
          <div className="mb-2 text-4xl">⏳</div>
          <p>Loading property details…</p>
        </div>
      </div>
    );
  }

  const soldPercent = property.total_shares > 0
    ? Math.round(((property.total_shares - property.available_shares) / property.total_shares) * 100)
    : 0;

  return (
    <section className="space-y-5">
      <Link to="/marketplace" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800">
        ← Back to Marketplace
      </Link>

      {/* Hero */}
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        {property.image_url && (
          <img src={property.image_url} alt={property.title} className="h-72 w-full object-cover" />
        )}
        <div className="p-5">
          <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">{property.title}</h1>
              <p className="text-sm text-slate-500">{property.city}, {property.state} · {property.property_type}</p>
            </div>
            <div className="flex items-center gap-2">
              <RiskBadge risk={property.risk_level} />
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${property.is_verified ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                {property.is_verified ? '✓ Verified' : 'Pending Verification'}
              </span>
            </div>
          </div>
          <p className="text-sm text-slate-600 leading-relaxed">{property.description}</p>
        </div>
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {[
          { label: 'Total Valuation', value: INR(property.property_price), icon: '🏢', color: 'border-sky-200 bg-sky-50' },
          { label: 'Share Price', value: INR(property.price_per_share), icon: '💰', color: 'border-indigo-200 bg-indigo-50' },
          { label: 'AI Predicted ROI', value: `${property.ai_predicted_roi}%`, icon: '📈', color: 'border-emerald-200 bg-emerald-50' },
          { label: 'Annual Rental Yield', value: `${property.rental_yield}%`, icon: '🏘️', color: 'border-amber-200 bg-amber-50' },
        ].map((m) => (
          <div key={m.label} className={`rounded-2xl border p-4 ${m.color}`}>
            <p className="text-lg">{m.icon}</p>
            <p className="text-xs text-slate-500">{m.label}</p>
            <p className="text-lg font-bold text-slate-900">{m.value}</p>
          </div>
        ))}
      </div>

      {/* Funding progress */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-2 flex justify-between text-sm font-medium text-slate-700">
          <span>{property.available_shares.toLocaleString('en-IN')} shares available</span>
          <span>{soldPercent}% funded</span>
        </div>
        <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
          <div className="h-full rounded-full bg-sky-500 transition-all" style={{ width: `${soldPercent}%` }} />
        </div>
        <p className="mt-2 text-xs text-slate-400">Total shares: {property.total_shares.toLocaleString('en-IN')}</p>
      </div>

      {/* SHAP Explainability */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4">
          <h2 className="text-lg font-bold text-slate-900">AI Explainability (SHAP)</h2>
          <p className="text-xs text-slate-500">Top 5 factors driving the ROI prediction for this property</p>
        </div>

        {explain ? (
          <div className="grid gap-5 md:grid-cols-2">
            {/* Bar chart */}
            <div>
              <Bar
                data={chartData}
                options={{
                  indexAxis: 'y',
                  plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => ` ${c.raw.toFixed(3)} contribution` } } },
                  scales: { x: { grid: { color: '#f1f5f9' } }, y: { grid: { display: false } } },
                  responsive: true,
                  maintainAspectRatio: false,
                }}
                style={{ height: '200px' }}
              />
            </div>

            {/* Feature list with percentage bars */}
            <div className="space-y-3">
              {featureList.map((f) => (
                <div key={f.name}>
                  <div className="mb-1 flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-700">
                      {FEATURE_ICONS[f.name] || '•'} {f.name}
                    </span>
                    <span className={`font-semibold ${f.positive ? 'text-sky-600' : 'text-rose-600'}`}>
                      {f.positive ? '+' : ''}{f.pct}%
                    </span>
                  </div>
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                    <div
                      className={`h-full rounded-full transition-all ${f.positive ? 'bg-sky-400' : 'bg-rose-400'}`}
                      style={{ width: `${f.pct}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex h-32 items-center justify-center text-slate-400 text-sm">Loading AI explanation…</div>
        )}
      </div>

      {/* Investment Calculator */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="mb-4 text-lg font-bold text-slate-900">Investment Calculator</h2>

        <div className="mb-4 grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
          <div className="rounded-xl bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Shares to buy</p>
            <p className="text-xl font-bold text-slate-900">{shares}</p>
          </div>
          <div className="rounded-xl bg-sky-50 p-3">
            <p className="text-xs text-slate-500">Total Investment</p>
            <p className="text-xl font-bold text-sky-700">{INR(Number(shares) * Number(property.price_per_share))}</p>
          </div>
          <div className="rounded-xl bg-emerald-50 p-3">
            <p className="text-xs text-slate-500">Est. Annual Return</p>
            <p className="text-xl font-bold text-emerald-700">
              {INR(Number(shares) * Number(property.price_per_share) * property.ai_predicted_roi / 100)}
            </p>
          </div>
          <div className="rounded-xl bg-amber-50 p-3">
            <p className="text-xs text-slate-500">Est. Annual Rental</p>
            <p className="text-xl font-bold text-amber-700">
              {INR(Number(shares) * Number(property.price_per_share) * property.rental_yield / 100)}
            </p>
          </div>
        </div>

        {user?.role === 'investor' ? (
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-slate-700">Number of Shares:</label>
            <input
              className="w-28 rounded-xl border border-slate-200 p-2 text-center text-lg font-bold focus:border-sky-400 focus:outline-none"
              type="number"
              min="1"
              max={property.available_shares}
              value={shares}
              onChange={(e) => setShares(Math.max(1, Number(e.target.value)))}
            />
            <button
              onClick={invest}
              disabled={investing}
              className="rounded-xl bg-sky-600 px-6 py-2.5 font-semibold text-white shadow-sm hover:bg-sky-500 disabled:opacity-60"
            >
              {investing ? 'Processing…' : 'Invest Now'}
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2 rounded-xl bg-slate-50 p-3 text-sm text-slate-600">
            <span>🔒</span>
            <span>
              <Link to="/login" className="font-medium text-sky-700 hover:underline">Sign in as Investor</Link>
              {' '}to invest in this property.
            </span>
          </div>
        )}

        {message && (
          <div className={`mt-3 rounded-xl p-3 text-sm font-medium ${message.startsWith('✓') ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'}`}>
            {message}
          </div>
        )}
      </div>

      {/* Documents (list only - not download) */}
      {property.documents && property.documents.length > 0 && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="mb-3 text-lg font-bold text-slate-900">Verified Documents</h2>
          <div className="grid gap-2 md:grid-cols-2">
            {property.documents.map((doc) => (
              <div key={doc.id} className="flex items-center gap-3 rounded-xl border border-slate-100 p-3 text-sm">
                <span className={`h-2 w-2 rounded-full ${doc.is_verified ? 'bg-emerald-500' : 'bg-amber-400'}`} />
                <div>
                  <p className="font-medium text-slate-700">{doc.document_type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}</p>
                  <p className="text-xs text-slate-400">{doc.is_verified ? 'Verified' : 'Pending verification'}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

export default PropertyDetailsPage;

Chart.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend);
