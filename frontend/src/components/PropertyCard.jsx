import { useState } from 'react';
import { Link } from 'react-router-dom';
import { aiApi, investmentApi } from '../api/endpoints';
import RiskBadge from './RiskBadge';
import { useAuth } from '../context/AuthContext';

const INR = (val) => '₹' + Number(val).toLocaleString('en-IN');
const TYPE_COLOR = {
  commercial: 'bg-blue-100 text-blue-700',
  residential: 'bg-green-100 text-green-700',
  retail: 'bg-orange-100 text-orange-700',
  office: 'bg-purple-100 text-purple-700',
};

function PropertyCard({ property, canInvest }) {
  const { user } = useAuth();
  const [shares, setShares] = useState(1);
  const [roi, setRoi] = useState(null);
  const [risk, setRisk] = useState(null);
  const [loading, setLoading] = useState(false);
  const [investing, setInvesting] = useState(false);
  const [message, setMessage] = useState('');

  const soldPercent = property.total_shares > 0
    ? Math.round(((property.total_shares - property.available_shares) / property.total_shares) * 100)
    : 0;

  const fetchSignals = async () => {
    setLoading(true);
    try {
      const params = {
        property_price: Number(property.property_price),
        rental_yield: property.rental_yield,
        demand_index: property.demand_index,
        market_trend: property.market_trend,
      };
      const [roiRes, riskRes] = await Promise.all([aiApi.roi(params), aiApi.risk(params)]);
      setRoi(roiRes.data);
      setRisk(riskRes.data);
    } catch (e) {
      console.error('AI signals failed', e);
    } finally {
      setLoading(false);
    }
  };

  const invest = async () => {
    if (!shares || shares < 1) return;
    setInvesting(true);
    setMessage('');
    try {
      const wallet = user?.wallet_address || '0x2222222222222222222222222222222222222222';
      await investmentApi.buyShares({ property_id: property.id, shares: Number(shares), wallet_address: wallet });
      setMessage(`✓ ${shares} share(s) purchased successfully!`);
      window.dispatchEvent(new Event('estatex:portfolio-updated'));
    } catch (e) {
      setMessage(`✗ ${e.message}`);
    } finally {
      setInvesting(false);
    }
  };

  return (
    <article className="group flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all hover:shadow-lg hover:-translate-y-0.5">
      {/* Image */}
      <div className="relative h-44 overflow-hidden bg-slate-100">
        {property.image_url ? (
          <img
            src={property.image_url}
            alt={property.title}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-slate-400">No Image</div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
        <div className="absolute bottom-2 left-3 right-3 flex items-end justify-between">
          <span className="rounded-full bg-white/90 px-2 py-0.5 text-xs font-semibold text-slate-800">
            {property.city}, Hyderabad
          </span>
          <RiskBadge risk={property.risk_level} />
        </div>
      </div>

      {/* Content */}
      <div className="flex flex-1 flex-col p-4">
        <div className="mb-1 flex items-start justify-between gap-2">
          <h3 className="font-semibold text-slate-900 leading-tight">{property.title}</h3>
          <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${TYPE_COLOR[property.property_type] || 'bg-slate-100 text-slate-600'}`}>
            {property.property_type}
          </span>
        </div>

        <p className="mb-3 text-xs text-slate-500 line-clamp-2">{property.description}</p>

        {/* Stats grid */}
        <div className="mb-3 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
          <div>
            <p className="text-slate-500">Valuation</p>
            <p className="font-bold text-slate-800">{INR(property.property_price)}</p>
          </div>
          <div>
            <p className="text-slate-500">Share Price</p>
            <p className="font-bold text-slate-800">{INR(property.price_per_share)}</p>
          </div>
          <div>
            <p className="text-slate-500">AI ROI</p>
            <p className="font-bold text-emerald-600">{property.ai_predicted_roi}%</p>
          </div>
          <div>
            <p className="text-slate-500">Rental Yield</p>
            <p className="font-bold text-sky-600">{property.rental_yield}%</p>
          </div>
        </div>

        {/* Funding progress */}
        <div className="mb-3">
          <div className="mb-1 flex justify-between text-xs text-slate-500">
            <span>{property.available_shares.toLocaleString('en-IN')} shares left</span>
            <span>{soldPercent}% filled</span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
            <div className="h-full rounded-full bg-sky-500 transition-all" style={{ width: `${soldPercent}%` }} />
          </div>
        </div>

        {/* AI signals */}
        {(roi || risk) && (
          <div className="mb-3 flex gap-2 rounded-xl bg-sky-50 border border-sky-100 p-2 text-xs">
            {roi && <span className="text-slate-600">Predicted ROI: <strong className="text-emerald-600">{roi.predicted_roi_percent}%</strong></span>}
            {risk && <span className="text-slate-600 ml-auto">Risk: <strong>{risk.risk_level}</strong> ({Math.round(risk.probability_score * 100)}%)</span>}
          </div>
        )}

        {message && (
          <p className={`mb-2 rounded-lg p-2 text-xs font-medium ${message.startsWith('✓') ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}`}>
            {message}
          </p>
        )}

        {/* Actions */}
        <div className="mt-auto flex flex-wrap items-center gap-2">
          <Link
            to={`/properties/${property.id}`}
            className="rounded-lg bg-slate-800 px-3 py-2 text-xs font-semibold text-white hover:bg-slate-700"
          >
            View Details
          </Link>
          <button
            onClick={fetchSignals}
            disabled={loading}
            className="rounded-lg border border-sky-200 bg-sky-50 px-3 py-2 text-xs font-semibold text-sky-700 hover:bg-sky-100 disabled:opacity-60"
          >
            {loading ? '…' : 'AI Signals'}
          </button>
          {canInvest && (
            <>
              <input
                type="number"
                min="1"
                value={shares}
                onChange={(e) => setShares(Number(e.target.value))}
                className="w-16 rounded-lg border border-slate-200 px-2 py-2 text-xs"
              />
              <button
                onClick={invest}
                disabled={investing}
                className="rounded-lg bg-sky-600 px-3 py-2 text-xs font-semibold text-white hover:bg-sky-500 disabled:opacity-60"
              >
                {investing ? 'Buying…' : 'Buy'}
              </button>
            </>
          )}
        </div>
      </div>
    </article>
  );
}

export default PropertyCard;
