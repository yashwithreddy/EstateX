import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ROLE_REDIRECT = {
  admin: '/admin',
  property_owner: '/owner',
  investor: '/investor',
};

function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [payload, setPayload] = useState({ email: '', full_name: '', password: '', role: 'investor', wallet_address: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const walletPattern = /^0x[a-fA-F0-9]{40}$/;

  const submit = async (e) => {
    e.preventDefault();
    if (payload.password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    const trimmedWallet = payload.wallet_address.trim();
    if (trimmedWallet && !walletPattern.test(trimmedWallet)) {
      setError('Wallet address must be a valid 0x address (40 hex characters).');
      return;
    }
    try {
      setError('');
      setLoading(true);
      const cleanPayload = {
        ...payload,
        email: payload.email.trim(),
        full_name: payload.full_name.trim(),
        wallet_address: trimmedWallet === '' ? undefined : trimmedWallet,
      };
      const data = await register(cleanPayload);
      const role = data.user?.role;
      navigate(ROLE_REDIRECT[role] || '/marketplace', { replace: true });
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 via-sky-950 to-slate-900 p-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <h1 className="text-4xl font-extrabold tracking-tight text-white">EstateX</h1>
          <p className="mt-1 text-sky-300 text-sm">Create your investor or owner account</p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md shadow-2xl">
          <h2 className="mb-5 text-xl font-bold text-white">Create Account</h2>
          <form className="grid gap-4" onSubmit={submit}>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-300">Full Name</label>
              <input
                className="w-full rounded-xl border border-white/20 bg-white/10 p-3 text-white placeholder-slate-500 focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
                placeholder="Arjun Kumar"
                required
                value={payload.full_name}
                onChange={(e) => setPayload({ ...payload, full_name: e.target.value })}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-300">Email Address</label>
              <input
                className="w-full rounded-xl border border-white/20 bg-white/10 p-3 text-white placeholder-slate-500 focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
                placeholder="arjun@example.com"
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
                placeholder="Min. 8 characters"
                type="password"
                required
                value={payload.password}
                onChange={(e) => setPayload({ ...payload, password: e.target.value })}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-300">Account Type</label>
              <select
                className="w-full rounded-xl border border-white/20 bg-slate-800 p-3 text-white focus:border-sky-400 focus:outline-none"
                value={payload.role}
                onChange={(e) => setPayload({ ...payload, role: e.target.value })}
              >
                <option value="investor">Investor</option>
                <option value="property_owner">Property Owner</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-300">
                Wallet Address <span className="text-slate-500">(optional)</span>
              </label>
              <input
                className="w-full rounded-xl border border-white/20 bg-white/10 p-3 text-white placeholder-slate-500 focus:border-sky-400 focus:outline-none focus:ring-1 focus:ring-sky-400"
                placeholder="0x..."
                value={payload.wallet_address}
                onChange={(e) => setPayload({ ...payload, wallet_address: e.target.value })}
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
              {loading ? 'Creating Account…' : 'Create Account'}
            </button>
          </form>
          <p className="mt-4 text-center text-sm text-slate-400">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-sky-400 hover:underline">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default RegisterPage;
