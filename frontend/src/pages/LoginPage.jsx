import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const DEMO_CREDENTIALS = [
  { role: 'Admin', email: 'admin@estatex.in', password: 'Admin@123', color: 'border-purple-300 bg-purple-50', tag: 'bg-purple-600' },
  { role: 'Owner', email: 'owner@estatex.in', password: 'Owner@123', color: 'border-sky-300 bg-sky-50', tag: 'bg-sky-600' },
  { role: 'Investor', email: 'investor@estatex.in', password: 'Investor@123', color: 'border-emerald-300 bg-emerald-50', tag: 'bg-emerald-600' },
];

const ROLE_REDIRECT = {
  admin: '/admin',
  property_owner: '/owner',
  investor: '/investor',
};

function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [payload, setPayload] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    try {
      setError('');
      setLoading(true);
      const data = await login(payload);
      const role = data.user?.role;
      navigate(ROLE_REDIRECT[role] || '/marketplace', { replace: true });
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = (cred) => {
    setPayload({ email: cred.email, password: cred.password });
    setError('');
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 via-sky-950 to-slate-900 p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Brand */}
        <div className="text-center">
          <h1 className="text-4xl font-extrabold tracking-tight text-white">EstateX</h1>
          <p className="mt-1 text-sky-300 text-sm">Fractional Real Estate Investing · India</p>
        </div>

        {/* Demo credential cards */}
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">Quick Demo Access</p>
          <div className="grid grid-cols-3 gap-2">
            {DEMO_CREDENTIALS.map((cred) => (
              <button
                key={cred.role}
                type="button"
                onClick={() => fillDemo(cred)}
                className={`rounded-xl border p-3 text-left transition-all hover:shadow-md ${cred.color}`}
              >
                <span className={`mb-1 inline-block rounded-full px-2 py-0.5 text-xs font-semibold text-white ${cred.tag}`}>
                  {cred.role}
                </span>
                <p className="text-xs font-medium text-slate-700 truncate">{cred.email}</p>
                <p className="text-xs text-slate-500">{cred.password}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Login form */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md shadow-2xl">
          <h2 className="mb-5 text-xl font-bold text-white">Sign In</h2>
          <form className="space-y-4" onSubmit={submit}>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-300">Email Address</label>
              <input
                className="w-full rounded-xl border border-white/20 bg-white/10 p-3 text-white placeholder-slate-500 focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
                placeholder="you@example.com"
                type="email"
                required
                value={payload.email}
                onChange={(e) => setPayload({ ...payload, email: e.target.value })}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-300">Password</label>
              <input
                className="w-full rounded-xl border border-white/20 bg-white/10 p-3 text-white placeholder-slate-500 focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
                placeholder="••••••••"
                type="password"
                required
                value={payload.password}
                onChange={(e) => setPayload({ ...payload, password: e.target.value })}
              />
            </div>

            {error && (
              <div className="rounded-xl border border-rose-600/30 bg-rose-900/20 p-3">
                <p className="text-sm text-rose-400">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-sky-600 p-3 text-sm font-semibold text-white shadow-lg transition hover:bg-sky-500 disabled:opacity-60"
            >
              {loading ? 'Signing in…' : 'Sign In'}
            </button>
          </form>
          <p className="mt-4 text-center text-sm text-slate-400">
            No account?{' '}
            <Link to="/register" className="font-medium text-sky-400 hover:underline">
              Register
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
