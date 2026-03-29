import { useEffect, useState } from 'react';
import { dashboardApi, propertyApi } from '../api/endpoints';

const INR = (val) => '₹' + Number(val).toLocaleString('en-IN');
const STATUS_COLOR = {
  approved: 'bg-emerald-100 text-emerald-700',
  pending: 'bg-amber-100 text-amber-700',
  rejected: 'bg-rose-100 text-rose-700',
  draft: 'bg-slate-100 text-slate-600',
};

function PropertyOwnerPage() {
  const [activeTab, setActiveTab] = useState('add');
  const [form, setForm] = useState({
    title: '', description: '', city: '', state: '', location: '', property_type: 'commercial', image_url: '',
    property_price: '', total_shares: '10000', rental_yield: '7.5', demand_index: '0.7', market_trend: '0.6', ai_predicted_roi: '13', risk_level: 'Medium',
  });
  const [docs, setDocs] = useState({ sale_deed: null, encumbrance_certificate: null, property_tax_receipt: null, identity_proof: null });
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const load = () => dashboardApi.owner().then((res) => setDashboard(res.data)).catch(console.error);
  useEffect(() => { load(); }, []);

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    if (!docs.sale_deed || !docs.encumbrance_certificate || !docs.property_tax_receipt || !docs.identity_proof) {
      setError('All 4 verification documents are required (Sale Deed, Encumbrance Certificate, Tax Receipt, Identity Proof).');
      return;
    }
    setSubmitting(true);
    try {
      const data = new FormData();
      Object.entries(form).forEach(([k, v]) => data.append(k, v));
      Object.entries(docs).forEach(([k, v]) => { if (v) data.append(k, v); });
      await propertyApi.create(data);
      setSuccess('✓ Property submitted for admin verification. You will be notified once approved.');
      setForm({ title: '', description: '', city: '', state: '', location: '', property_type: 'commercial', image_url: '', property_price: '', total_shares: '10000', rental_yield: '7.5', demand_index: '0.7', market_trend: '0.6', ai_predicted_roi: '13', risk_level: 'Medium' });
      setDocs({ sale_deed: null, encumbrance_certificate: null, property_tax_receipt: null, identity_proof: null });
      load();
      setActiveTab('listings');
    } catch (err) {
      setError(err.message || 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  const TAB = 'rounded-xl px-4 py-2 text-sm font-semibold transition';
  const ACTIVE = `${TAB} bg-sky-600 text-white shadow`;
  const INACTIVE = `${TAB} bg-white text-slate-600 border border-slate-200 hover:bg-slate-50`;

  return (
    <section className="space-y-5">
      <div>
        <h2 className="text-xl font-bold text-slate-900">Property Owner Dashboard</h2>
        <p className="text-sm text-slate-500 mt-0.5">List properties, upload verification documents, and track investor activity.</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        <button className={activeTab === 'add' ? ACTIVE : INACTIVE} onClick={() => setActiveTab('add')}>➕ Add Property</button>
        <button className={activeTab === 'listings' ? ACTIVE : INACTIVE} onClick={() => setActiveTab('listings')}>📋 My Listings</button>
        <button className={activeTab === 'activity' ? ACTIVE : INACTIVE} onClick={() => setActiveTab('activity')}>💰 Activity</button>
      </div>

      {/* Add Property tab */}
      {activeTab === 'add' && (
        <form onSubmit={submit} className="space-y-5">
          {/* Property info */}
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="mb-4 font-semibold text-slate-900">Property Details</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="md:col-span-2">
                <label className="mb-1 block text-xs font-medium text-slate-600">Property Title</label>
                <input className="w-full rounded-xl border border-slate-200 p-2.5 text-sm focus:border-sky-400 focus:outline-none" placeholder="e.g. Hyderabad IT Park, Cyberabad" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
              </div>
              <div className="md:col-span-2">
                <label className="mb-1 block text-xs font-medium text-slate-600">Description</label>
                <textarea className="w-full rounded-xl border border-slate-200 p-2.5 text-sm focus:border-sky-400 focus:outline-none" rows={3} placeholder="Premium commercial asset with strong rental demand…" required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              </div>
              {[['Full Address', 'location', 'e.g. Gachibowli, Hyderabad']].map(([label, key, ph]) => (
                <div key={key} className="md:col-span-2">
                  <label className="mb-1 block text-xs font-medium text-slate-600">{label}</label>
                  <input className="w-full rounded-xl border border-slate-200 p-2.5 text-sm focus:border-sky-400 focus:outline-none" placeholder={ph} required value={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })} />
                </div>
              ))}
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Locality</label>
                <select className="w-full rounded-xl border border-slate-200 p-2.5 text-sm focus:border-sky-400 focus:outline-none" required value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value, state: 'Telangana' })}>
                  <option value="">Select Locality</option>
                  {['Gachibowli','Hitech City','Kondapur','Madhapur','Manikonda','Narsingi','Tellapur','Kukatpally','Miyapur','Banjara Hills','Jubilee Hills','Financial District','Begumpet','Secunderabad','Uppal','LB Nagar','Attapur','Kompally','Shamshabad','Bachupally'].map((l) => (
                    <option key={l} value={l}>{l}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Property Type</label>
                <select className="w-full rounded-xl border border-slate-200 p-2.5 text-sm focus:border-sky-400 focus:outline-none" value={form.property_type} onChange={(e) => setForm({ ...form, property_type: e.target.value })}>
                  <option value="commercial">Commercial</option>
                  <option value="residential">Residential</option>
                  <option value="retail">Retail</option>
                  <option value="office">Office</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Risk Level</label>
                <select className="w-full rounded-xl border border-slate-200 p-2.5 text-sm focus:border-sky-400 focus:outline-none" value={form.risk_level} onChange={(e) => setForm({ ...form, risk_level: e.target.value })}>
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="mb-1 block text-xs font-medium text-slate-600">Image URL (optional)</label>
                <input className="w-full rounded-xl border border-slate-200 p-2.5 text-sm focus:border-sky-400 focus:outline-none" placeholder="https://images.unsplash.com/…" value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })} />
              </div>
            </div>
          </div>

          {/* Financial details */}
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="mb-4 font-semibold text-slate-900">Financial Details</h3>
            <div className="grid gap-4 md:grid-cols-3">
              {[
                ['Total Valuation (₹)', 'property_price', '185000000'],
                ['Total Shares', 'total_shares', '10000'],
              ].map(([label, key, ph]) => (
                <div key={key}>
                  <label className="mb-1 block text-xs font-medium text-slate-600">{label}</label>
                  <input
                    className="w-full rounded-xl border border-slate-200 p-2.5 text-sm focus:border-sky-400 focus:outline-none"
                    type="number" step="any" placeholder={ph} required
                    value={form[key]}
                    onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                  />
                </div>
              ))}
            </div>
            {form.property_price && form.total_shares && (
              <p className="mt-3 text-xs text-slate-500">
                Share price will be: <strong className="text-sky-700">{INR(Number(form.property_price) / Number(form.total_shares))}</strong> per share
              </p>
            )}
          </div>

          {/* Document upload */}
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="mb-1 font-semibold text-slate-900">Verification Documents</h3>
            <p className="mb-4 text-xs text-slate-500">All 4 documents required for compliance. PDFs only.</p>
            <div className="grid gap-4 md:grid-cols-2">
              {[
                ['Sale Deed', 'sale_deed'],
                ['Encumbrance Certificate', 'encumbrance_certificate'],
                ['Property Tax Receipt', 'property_tax_receipt'],
                ['Identity Proof (Aadhaar/PAN)', 'identity_proof'],
              ].map(([label, key]) => (
                <div key={key} className={`rounded-xl border-2 p-3 transition ${docs[key] ? 'border-emerald-300 bg-emerald-50' : 'border-dashed border-slate-200 bg-slate-50'}`}>
                  <label className="block cursor-pointer">
                    <p className="mb-1 text-xs font-semibold text-slate-700">
                      {docs[key] ? '✓ ' : ''}{label}
                    </p>
                    {docs[key] ? (
                      <p className="text-xs text-emerald-600">{docs[key].name}</p>
                    ) : (
                      <p className="text-xs text-slate-400">Click to upload PDF</p>
                    )}
                    <input type="file" accept="application/pdf" className="hidden" onChange={(e) => setDocs({ ...docs, [key]: e.target.files[0] })} required />
                  </label>
                </div>
              ))}
            </div>
          </div>

          {error && <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}
          {success && <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{success}</div>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-xl bg-sky-600 p-3 font-semibold text-white shadow hover:bg-sky-500 disabled:opacity-60"
          >
            {submitting ? 'Submitting…' : 'Submit Property for Verification'}
          </button>
        </form>
      )}

      {/* My Listings tab */}
      {activeTab === 'listings' && dashboard && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-4 font-semibold text-slate-900">My Properties</h3>
          {dashboard.properties.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-10 text-slate-400">
              <span className="text-4xl">🏢</span>
              <p className="text-sm">No properties listed yet. Add your first one!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {dashboard.properties.map((p) => (
                <div key={p.id} className="rounded-xl border border-slate-100 p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-semibold text-slate-900">{p.title}</p>
                      <p className="text-xs text-slate-500">{p.city}, {p.state}</p>
                    </div>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${STATUS_COLOR[p.verification_status] || 'bg-slate-100 text-slate-600'}`}>
                      {p.verification_status.charAt(0).toUpperCase() + p.verification_status.slice(1)}
                    </span>
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-slate-500">
                    <p>Available: <strong className="text-slate-700">{p.available_shares?.toLocaleString('en-IN')} / {p.total_shares?.toLocaleString('en-IN')} shares</strong></p>
                    {p.rejection_reason && (
                      <p className="col-span-2 text-rose-600">Reason: {p.rejection_reason}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Activity tab */}
      {activeTab === 'activity' && dashboard && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-4 font-semibold text-slate-900">Investment Activity on My Properties</h3>
          {dashboard.investment_activity.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-10 text-slate-400">
              <span className="text-4xl">📊</span>
              <p className="text-sm">No activity yet. Once investors buy shares, transactions appear here.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="text-xs text-slate-400 border-b border-slate-100">
                    <th className="pb-3 pr-4">Tx ID</th>
                    <th className="pb-3 pr-4">Property</th>
                    <th className="pb-3 pr-4">Type</th>
                    <th className="pb-3 pr-4">Shares</th>
                    <th className="pb-3">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboard.investment_activity.map((tx) => (
                    <tr key={tx.id} className="border-b border-slate-50">
                      <td className="py-2 pr-4 text-slate-400">#{tx.id}</td>
                      <td className="py-2 pr-4 text-slate-700">#{tx.property_id}</td>
                      <td className="py-2 pr-4">
                        <span className="rounded-full bg-sky-100 px-2 py-0.5 text-xs font-medium text-sky-700">
                          {tx.tx_type.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="py-2 pr-4 font-medium text-slate-800">{tx.shares}</td>
                      <td className="py-2 font-semibold text-emerald-700">{INR(tx.amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export default PropertyOwnerPage;
