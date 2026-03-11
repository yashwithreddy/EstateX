import { useEffect, useState } from 'react';
import { adminApi, dashboardApi } from '../api/endpoints';

const INR = (val) => '₹' + Number(val).toLocaleString('en-IN');
const ROLE_COLOR = { admin: 'bg-purple-100 text-purple-700', property_owner: 'bg-sky-100 text-sky-700', investor: 'bg-emerald-100 text-emerald-700' };

function AdminDashboardPage() {
  const [activeTab, setActiveTab] = useState('stats');
  const [stats, setStats] = useState(null);
  const [docs, setDocs] = useState([]);
  const [props, setProps] = useState([]);
  const [users, setUsers] = useState([]);
  const [error, setError] = useState('');
  const [reason, setReason] = useState('');
  const [actionMsg, setActionMsg] = useState('');

  const load = async () => {
    try {
      setError('');
      const [statsRes, docsRes, propsRes, usersRes] = await Promise.all([
        dashboardApi.admin(),
        adminApi.pendingDocuments(),
        adminApi.pendingProperties(),
        adminApi.listUsers(),
      ]);
      setStats(statsRes.data);
      setDocs(docsRes.data);
      setProps(propsRes.data);
      setUsers(usersRes.data);
    } catch (err) {
      setError(err.message || 'Failed to load admin data');
    }
  };

  useEffect(() => { load(); }, []);

  const verifyDoc = async (id, approve) => {
    setActionMsg('');
    try {
      await adminApi.verifyDocument(id, approve, reason);
      setActionMsg(`✓ Document ${approve ? 'approved' : 'rejected'}.`);
      load();
    } catch (e) { setActionMsg(`✗ ${e.message}`); }
  };

  const approveProp = async (id, approve) => {
    setActionMsg('');
    try {
      await adminApi.approveProperty(id, approve, reason);
      setActionMsg(`✓ Property ${approve ? 'approved and listed' : 'rejected'}.`);
      load();
    } catch (e) { setActionMsg(`✗ ${e.message}`); }
  };

  const toggleUser = async (id) => {
    setActionMsg('');
    try {
      const res = await adminApi.toggleUserActive(id);
      setActionMsg(`✓ User ${res.data.is_active ? 'activated' : 'deactivated'}.`);
      load();
    } catch (e) { setActionMsg(`✗ ${e.message}`); }
  };

  if (error) return <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-rose-700">{error}</div>;
  if (!stats) return <div className="flex items-center justify-center p-12 text-slate-400">Loading admin dashboard…</div>;

  const TAB = 'rounded-xl px-4 py-2 text-sm font-semibold transition';
  const ACTIVE = `${TAB} bg-sky-600 text-white shadow`;
  const INACTIVE = `${TAB} bg-white text-slate-600 border border-slate-200 hover:bg-slate-50`;

  return (
    <section className="space-y-5">
      <h2 className="text-xl font-bold text-slate-900">Admin Control Panel</h2>

      {/* Stats */}
      <div className="grid gap-3 md:grid-cols-5">
        {[
          { label: 'Pending Verifications', value: stats.pending_verifications, color: 'bg-amber-50 border-amber-200' },
          { label: 'Pending Properties', value: stats.pending_properties, color: 'bg-rose-50 border-rose-200' },
          { label: 'Approved Properties', value: stats.approved_properties, color: 'bg-emerald-50 border-emerald-200' },
          { label: 'Total Investments', value: stats.total_investments, color: 'bg-sky-50 border-sky-200' },
          { label: 'Liquidity Listings', value: stats.active_liquidity_listings, color: 'bg-purple-50 border-purple-200' },
        ].map((s) => (
          <div key={s.label} className={`rounded-2xl border p-4 ${s.color}`}>
            <p className="text-xs text-slate-500">{s.label}</p>
            <p className="mt-1 text-2xl font-bold text-slate-900">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2">
        <button className={activeTab === 'stats' ? ACTIVE : INACTIVE} onClick={() => setActiveTab('stats')}>📊 Overview</button>
        <button className={activeTab === 'properties' ? ACTIVE : INACTIVE} onClick={() => setActiveTab('properties')}>
          🏢 Pending Properties {props.length > 0 && <span className="ml-1 rounded-full bg-rose-500 px-1.5 text-xs text-white">{props.length}</span>}
        </button>
        <button className={activeTab === 'documents' ? ACTIVE : INACTIVE} onClick={() => setActiveTab('documents')}>
          📄 Pending Docs {docs.length > 0 && <span className="ml-1 rounded-full bg-amber-500 px-1.5 text-xs text-white">{docs.length}</span>}
        </button>
        <button className={activeTab === 'users' ? ACTIVE : INACTIVE} onClick={() => setActiveTab('users')}>👥 Users ({users.length})</button>
      </div>

      {/* Action feedback */}
      {actionMsg && (
        <div className={`rounded-xl p-3 text-sm font-medium ${actionMsg.startsWith('✓') ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'}`}>
          {actionMsg}
        </div>
      )}

      {/* Rejection reason input - shared */}
      {(activeTab === 'properties' || activeTab === 'documents') && (
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <label className="mb-1 block text-xs font-medium text-slate-600">Rejection Reason (optional – used when rejecting)</label>
          <input
            className="w-full rounded-xl border border-slate-200 p-2.5 text-sm focus:border-sky-400 focus:outline-none"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Provide a reason for rejection…"
          />
        </div>
      )}

      {/* Overview tab */}
      {activeTab === 'stats' && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-3 font-semibold text-slate-900">Platform Summary</h3>
          <div className="grid gap-3 md:grid-cols-2 text-sm text-slate-700">
            <p>✅ Approved properties visible on marketplace: <strong>{stats.approved_properties}</strong></p>
            <p>⏳ Properties awaiting approval: <strong>{stats.pending_properties}</strong></p>
            <p>📄 Documents awaiting verification: <strong>{stats.pending_verifications}</strong></p>
            <p>💰 Total investment transactions: <strong>{stats.total_investments}</strong></p>
            <p>⚡ Active secondary market listings: <strong>{stats.active_liquidity_listings}</strong></p>
            <p>👥 Total registered users: <strong>{users.length}</strong></p>
          </div>
        </div>
      )}

      {/* Pending Properties tab */}
      {activeTab === 'properties' && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-4 font-semibold text-slate-900">Properties Awaiting Approval</h3>
          {props.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-10 text-slate-400">
              <span className="text-4xl">🎉</span>
              <p className="text-sm">All properties are reviewed. Nothing pending!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {props.map((p) => (
                <div key={p.property_id} className="rounded-xl border border-slate-100 p-4 hover:bg-slate-50">
                  <div className="mb-2 flex items-start justify-between">
                    <div>
                      <p className="font-semibold text-slate-900">{p.title}</p>
                      <p className="text-xs text-slate-500">{p.city}, {p.state} · Owner #{p.owner_id}</p>
                    </div>
                    <div className="text-right text-xs text-slate-500">
                      <p>Docs: {p.verified_doc_count}/{p.document_count} verified</p>
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${p.is_verified ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                        {p.is_verified ? 'Docs verified' : 'Docs pending'}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => approveProp(p.property_id, true)} className="rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500">
                      ✓ Approve & List
                    </button>
                    <button onClick={() => approveProp(p.property_id, false)} className="rounded-xl bg-rose-600 px-4 py-2 text-xs font-semibold text-white hover:bg-rose-500">
                      ✗ Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Pending Documents tab */}
      {activeTab === 'documents' && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-4 font-semibold text-slate-900">Documents Awaiting Verification</h3>
          {docs.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-10 text-slate-400">
              <span className="text-4xl">📋</span>
              <p className="text-sm">No pending documents. All verified!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {docs.map((doc) => (
                <div key={doc.document_id} className="rounded-xl border border-slate-100 p-4 hover:bg-slate-50">
                  <div className="mb-2 flex items-start justify-between">
                    <div>
                      <p className="font-semibold text-slate-900">{doc.property_title}</p>
                      <p className="text-xs text-slate-500">
                        {doc.document_type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())} · 
                        SHA256: <span className="font-mono">{doc.sha256_hash?.slice(0, 12)}…</span>
                      </p>
                    </div>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${doc.verification_status === 'verified' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
                      {doc.verification_status}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => verifyDoc(doc.document_id, true)} className="rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500">
                      ✓ Verify
                    </button>
                    <button onClick={() => verifyDoc(doc.document_id, false)} className="rounded-xl bg-rose-600 px-4 py-2 text-xs font-semibold text-white hover:bg-rose-500">
                      ✗ Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Users tab */}
      {activeTab === 'users' && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-4 font-semibold text-slate-900">User Management</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-xs text-slate-400 border-b border-slate-100">
                  <th className="pb-3 pr-4">ID</th>
                  <th className="pb-3 pr-4">Name</th>
                  <th className="pb-3 pr-4">Email</th>
                  <th className="pb-3 pr-4">Role</th>
                  <th className="pb-3 pr-4">Wallet</th>
                  <th className="pb-3 pr-4">Status</th>
                  <th className="pb-3">Action</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b border-slate-50 hover:bg-slate-50">
                    <td className="py-3 pr-4 text-slate-400">#{u.id}</td>
                    <td className="py-3 pr-4 font-medium text-slate-900">{u.full_name}</td>
                    <td className="py-3 pr-4 text-slate-600">{u.email}</td>
                    <td className="py-3 pr-4">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${ROLE_COLOR[u.role] || 'bg-slate-100 text-slate-600'}`}>
                        {u.role}
                      </span>
                    </td>
                    <td className="py-3 pr-4 text-xs font-mono text-slate-400 max-w-28 truncate">
                      {u.wallet_address || '—'}
                    </td>
                    <td className="py-3 pr-4">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${u.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                        {u.is_active ? 'Active' : 'Disabled'}
                      </span>
                    </td>
                    <td className="py-3">
                      {u.role !== 'admin' ? (
                        <button
                          onClick={() => toggleUser(u.id)}
                          className={`rounded-lg px-3 py-1 text-xs font-semibold ${u.is_active ? 'bg-rose-50 text-rose-700 hover:bg-rose-100' : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'}`}
                        >
                          {u.is_active ? 'Disable' : 'Enable'}
                        </button>
                      ) : (
                        <span className="text-xs text-slate-400">Protected</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}

export default AdminDashboardPage;

