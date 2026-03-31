import { useEffect, useState } from 'react';
import { investmentApi, dashboardApi } from '../api/endpoints';
import { useAuth } from '../context/AuthContext';

const INR = (val) => '₹' + Number(val).toLocaleString('en-IN');

function LiquidityPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('simulate');
  const [listings, setListings] = useState([]);
  const [portfolio, setPortfolio] = useState([]);
  const [createForm, setCreateForm] = useState({ property_id: '', shares_for_sale: '', price_per_share: '' });

  // Exit simulator state
  const [simForm, setSimForm] = useState({ property_id: '', shares_to_exit: '' });
  const [simResult, setSimResult] = useState(null);
  const [simLoading, setSimLoading] = useState(false);
  const [simError, setSimError] = useState('');

  const [listingMsg, setListingMsg] = useState('');
  const [tradeMsg, setTradeMsg] = useState('');

  const adjustPortfolioShares = (propertyId, delta) => {
    if (!propertyId || !Number.isFinite(delta)) return;
    setPortfolio((prev) =>
      prev.map((item) =>
        Number(item.property_id) === Number(propertyId)
          ? { ...item, shares: Math.max(0, Number(item.shares || 0) + delta) }
          : item
      )
    );
  };

  const loadData = () => Promise.all([
    investmentApi.getListings().then((res) => setListings(res.data)).catch(console.error),
    dashboardApi.investor().then((res) => setPortfolio(res.data.portfolio || [])).catch(console.error),
  ]);

  useEffect(() => { loadData(); }, []);

  useEffect(() => {
    if (activeTab === 'market') {
      investmentApi.getListings().then((res) => setListings(res.data)).catch(console.error);
    }
  }, [activeTab]);

  const runSimulation = async (e) => {
    e.preventDefault();
    if (!simForm.property_id || !simForm.shares_to_exit) return;
    setSimLoading(true);
    setSimError('');
    setSimResult(null);
    try {
      const res = await investmentApi.exitSimulate({
        property_id: Number(simForm.property_id),
        shares_to_exit: Number(simForm.shares_to_exit),
      });
      setSimResult(res.data);
      const propertyId = Number(simForm.property_id);
      const sharesToExit = Number(simForm.shares_to_exit);
      const portfolioItem = portfolio.find((item) => Number(item.property_id) === propertyId);
      const fallbackPrice = res?.data?.current_market_value
        ? Number(res.data.current_market_value) / sharesToExit
        : null;
      const pricePerShare = Number(portfolioItem?.share_price ?? fallbackPrice);

      if (Number.isFinite(pricePerShare) && pricePerShare > 0) {
        const listingRes = await investmentApi.createListing({
          property_id: propertyId,
          shares_for_sale: sharesToExit,
          price_per_share: pricePerShare,
        });
        if (listingRes?.data) {
          setListings((prev) => [listingRes.data, ...prev.filter((item) => item.id !== listingRes.data.id)]);
        } else {
          investmentApi.getListings().then((listingsRes) => setListings(listingsRes.data)).catch(console.error);
        }
        adjustPortfolioShares(propertyId, -sharesToExit);
        window.dispatchEvent(new Event('estatex:portfolio-updated'));
        setActiveTab('market');
      }
    } catch (e) {
      setSimError(e.message || 'Simulation failed');
    } finally {
      setSimLoading(false);
    }
  };

  const createListing = async (e) => {
    e.preventDefault();
    setListingMsg('');
    try {
      const res = await investmentApi.createListing({
        property_id: Number(createForm.property_id),
        shares_for_sale: Number(createForm.shares_for_sale),
        price_per_share: Number(createForm.price_per_share),
      });
      setListingMsg('✓ Sell order created successfully!');
      setCreateForm({ property_id: '', shares_for_sale: '', price_per_share: '' });
      if (res?.data) {
        setListings((prev) => [res.data, ...prev.filter((item) => item.id !== res.data.id)]);
      } else {
        loadData();
      }
      adjustPortfolioShares(Number(createForm.property_id), -Number(createForm.shares_for_sale));
      window.dispatchEvent(new Event('estatex:portfolio-updated'));
      setActiveTab('market');
    } catch (e) {
      setListingMsg(`✗ ${e.message}`);
    }
  };

  const buyFromListing = async (listing, isOwnListing) => {
    setTradeMsg('');
    try {
      const wallet = user?.wallet_address || '0x2222222222222222222222222222222222222222';
      await investmentApi.tradeShares({ listing_id: listing.id, shares_to_buy: 1, buyer_wallet_address: wallet });
      setTradeMsg(isOwnListing ? '✓ Listing updated (1 share removed).' : '✓ Share purchased from secondary market!');
      await loadData();
      window.dispatchEvent(new Event('estatex:portfolio-updated'));
    } catch (e) {
      setTradeMsg(`✗ ${e.message}`);
    }
  };

  const TAB = 'rounded-xl px-4 py-2 text-sm font-semibold transition';
  const ACTIVE = `${TAB} bg-sky-600 text-white shadow`;
  const INACTIVE = `${TAB} bg-white text-slate-600 border border-slate-200 hover:bg-slate-50`;

  return (
    <section className="space-y-5">
      <div>
        <h2 className="text-xl font-bold text-slate-900">Liquidity & Exit Simulation</h2>
        <p className="text-sm text-slate-500 mt-0.5">Simulate partial exit returns or trade on the secondary market</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        <button className={activeTab === 'simulate' ? ACTIVE : INACTIVE} onClick={() => setActiveTab('simulate')}>
          📊 Exit Simulator
        </button>
        <button className={activeTab === 'sell' ? ACTIVE : INACTIVE} onClick={() => setActiveTab('sell')}>
          📤 Create Sell Order
        </button>
        <button className={activeTab === 'market' ? ACTIVE : INACTIVE} onClick={() => setActiveTab('market')}>
          🔄 Secondary Market ({listings.length})
        </button>
      </div>

      {/* Exit Simulator Tab */}
      {activeTab === 'simulate' && (
        <div className="space-y-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="mb-1 font-semibold text-slate-900">Partial Exit Simulator</h3>
            <p className="mb-4 text-xs text-slate-500">
              Estimate your net proceeds including capital appreciation, rental income, and Indian LTCG tax (20%)
            </p>
            <form onSubmit={runSimulation} className="flex flex-wrap items-end gap-3">
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Property</label>
                <select
                  className="rounded-xl border border-slate-200 p-2.5 text-sm focus:border-sky-400 focus:outline-none min-w-52"
                  value={simForm.property_id}
                  onChange={(e) => setSimForm({ ...simForm, property_id: e.target.value })}
                  required
                >
                  <option value="">Select your property…</option>
                  {portfolio.map((p) => (
                    <option key={p.property_id} value={p.property_id}>
                      {p.title} ({p.shares} shares)
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Shares to Exit</label>
                <input
                  className="w-32 rounded-xl border border-slate-200 p-2.5 text-sm focus:border-sky-400 focus:outline-none"
                  type="number"
                  min="1"
                  placeholder="e.g. 100"
                  value={simForm.shares_to_exit}
                  onChange={(e) => setSimForm({ ...simForm, shares_to_exit: e.target.value })}
                  required
                />
              </div>
              <button
                type="submit"
                disabled={simLoading}
                className="rounded-xl bg-sky-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-sky-500 disabled:opacity-60"
              >
                {simLoading ? 'Calculating…' : 'Simulate Exit'}
              </button>
            </form>
            {simError && <p className="mt-3 rounded-xl bg-rose-50 p-3 text-sm text-rose-600">{simError}</p>}
          </div>

          {simResult && (
            <div className="rounded-2xl border border-sky-200 bg-sky-50 p-5 shadow-sm space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-bold text-slate-900 text-lg">{simResult.property_title}</h3>
                  <p className="text-sm text-slate-500">{simResult.city}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500">Exiting</p>
                  <p className="text-2xl font-bold text-sky-700">{simResult.shares_to_exit.toLocaleString('en-IN')} shares</p>
                  <p className="text-xs text-slate-500">{simResult.shares_retained.toLocaleString('en-IN')} retained</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
                {[
                  { label: 'Cost Basis', value: INR(simResult.cost_basis), color: 'bg-white' },
                  { label: 'Current Market Value', value: INR(simResult.current_market_value), color: 'bg-white' },
                  { label: 'Capital Gain', value: INR(simResult.capital_gain), color: 'bg-emerald-50' },
                  { label: 'LTCG Tax (20%)', value: INR(simResult.ltcg_tax_estimate), color: 'bg-rose-50' },
                  { label: 'Est. Annual Rental Income', value: INR(simResult.estimated_annual_rental_income), color: 'bg-white' },
                  { label: 'Net Proceeds (After Tax)', value: INR(simResult.net_proceeds_after_tax), color: 'bg-sky-100' },
                ].map((item) => (
                  <div key={item.label} className={`rounded-xl border border-white p-3 ${item.color}`}>
                    <p className="text-xs text-slate-500">{item.label}</p>
                    <p className="text-lg font-bold text-slate-900">{item.value}</p>
                  </div>
                ))}
              </div>

              <div className="rounded-xl border border-sky-200 bg-white p-3 text-xs text-slate-600">
                <span className="font-semibold text-slate-800">Absolute Gain: </span>
                <span className={`font-bold text-lg ${simResult.absolute_gain >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                  {simResult.absolute_gain >= 0 ? '+' : ''}{INR(simResult.absolute_gain)}
                </span>
                <span className="ml-4">ROI {simResult.roi_percent}% · Rental Yield {simResult.rental_yield_percent}%</span>
              </div>

              <p className="text-xs text-slate-400">
                ⚠ Disclaimer: LTCG tax estimate uses 20% flat rate. Actual tax liability depends on holding period, indexation, and applicable slabs. Consult a CA for precise figures.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Create Sell Order Tab */}
      {activeTab === 'sell' && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-1 font-semibold text-slate-900">Create Secondary Market Listing</h3>
          <p className="mb-4 text-xs text-slate-500">List your shares on the secondary market for other investors to buy.</p>
          <form onSubmit={createListing} className="flex flex-wrap items-end gap-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Property</label>
              <select
                className="rounded-xl border border-slate-200 p-2.5 text-sm focus:border-sky-400 focus:outline-none min-w-52"
                value={createForm.property_id}
                onChange={(e) => setCreateForm({ ...createForm, property_id: e.target.value })}
                required
              >
                <option value="">Select property…</option>
                {portfolio.map((p) => (
                  <option key={p.property_id} value={p.property_id}>
                    {p.title} ({p.shares} shares @ {INR(p.share_price)} each)
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Shares to Sell</label>
              <input className="w-28 rounded-xl border border-slate-200 p-2.5 text-sm focus:border-sky-400 focus:outline-none" type="number" min="1" placeholder="qty" value={createForm.shares_for_sale} onChange={(e) => setCreateForm({ ...createForm, shares_for_sale: e.target.value })} required />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Price per Share (₹)</label>
              <input className="w-32 rounded-xl border border-slate-200 p-2.5 text-sm focus:border-sky-400 focus:outline-none" type="number" min="1" step="0.01" placeholder="₹1000" value={createForm.price_per_share} onChange={(e) => setCreateForm({ ...createForm, price_per_share: e.target.value })} required />
            </div>
            <button type="submit" className="rounded-xl bg-slate-800 px-5 py-2.5 text-sm font-semibold text-white hover:bg-slate-700">
              Create Listing
            </button>
          </form>
          {listingMsg && (
            <p className={`mt-3 rounded-xl p-3 text-sm font-medium ${listingMsg.startsWith('✓') ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}`}>
              {listingMsg}
            </p>
          )}
        </div>
      )}

      {/* Secondary Market Tab */}
      {activeTab === 'market' && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-4 font-semibold text-slate-900">Active Secondary Market Listings</h3>
          {tradeMsg && (
            <p className={`mb-3 rounded-xl p-3 text-sm font-medium ${tradeMsg.startsWith('✓') ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}`}>
              {tradeMsg}
            </p>
          )}
          {listings.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-10 text-slate-400">
              <span className="text-4xl">📭</span>
              <p className="text-sm">No active listings. Be the first to list!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {listings.map((listing) => {
                const isOwnListing = Number(listing.seller_id) === Number(user?.id);
                return (
                <div key={listing.id} className="flex items-center justify-between rounded-xl border border-slate-100 p-4 hover:bg-slate-50">
                  <div>
                    <p className="font-semibold text-slate-800">Property #{listing.property_id}</p>
                    <p className="text-sm text-slate-500">
                      {listing.shares_for_sale} shares available · {INR(listing.price_per_share)} per share
                    </p>
                    <p className="text-xs text-slate-400">
                      Total: {INR(listing.shares_for_sale * listing.price_per_share)}
                    </p>
                  </div>
                  <button
                    onClick={() => buyFromListing(listing, isOwnListing)}
                    className="rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-500"
                  >
                    {isOwnListing ? 'Remove 1 Share' : 'Buy 1 Share'}
                  </button>
                </div>
              );
              })}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export default LiquidityPage;
