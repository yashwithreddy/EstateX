import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const roleRoutes = {
  investor: [
    { to: '/marketplace', label: '🏪 Marketplace', desc: 'Browse properties' },
    { to: '/investor', label: '📊 Dashboard', desc: 'Portfolio overview' },
    { to: '/portfolio', label: '💼 Portfolio', desc: 'My investments' },
    { to: '/liquidity', label: '⚡ Liquidity & Exit', desc: 'Simulate exit' },
  ],
  property_owner: [
    { to: '/marketplace', label: '🏪 Marketplace', desc: 'Browse listings' },
    { to: '/owner', label: '🏢 Owner Dashboard', desc: 'Manage properties' },
  ],
  admin: [
    { to: '/marketplace', label: '🏪 Marketplace', desc: 'Browse listings' },
    { to: '/admin', label: '⚙️ Admin Panel', desc: 'Manage platform' },
  ],
};

const ROLE_STYLES = {
  admin: { badge: 'bg-purple-100 text-purple-700', label: 'Admin' },
  property_owner: { badge: 'bg-sky-100 text-sky-700', label: 'Owner' },
  investor: { badge: 'bg-emerald-100 text-emerald-700', label: 'Investor' },
};

function Sidebar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const routes = user?.role ? roleRoutes[user.role] : [{ to: '/marketplace', label: '🏪 Marketplace', desc: 'Browse properties' }];
  const roleStyle = ROLE_STYLES[user?.role] || { badge: 'bg-slate-100 text-slate-600', label: 'Guest' };

  return (
    <aside className="flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm md:w-64 md:sticky md:top-4 md:max-h-screen">
      {/* Brand */}
      <div className="mb-6">
        <Link to="/marketplace" className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-600 text-white font-bold text-lg">₹</div>
          <div>
            <h1 className="text-xl font-extrabold tracking-tight text-sky-900">EstateX</h1>
            <p className="text-xs text-slate-400">Hyderabad Real Estate</p>
          </div>
        </Link>
      </div>

      {/* User info */}
      {user && (
        <div className="mb-5 rounded-xl bg-slate-50 p-3">
          <div className="flex items-center gap-2 mb-1">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-sky-600 text-white text-sm font-bold">
              {user.full_name?.charAt(0)?.toUpperCase() || '?'}
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800 leading-tight">{user.full_name}</p>
              <p className="text-xs text-slate-500 truncate max-w-36">{user.email}</p>
            </div>
          </div>
          <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${roleStyle.badge}`}>
            {roleStyle.label}
          </span>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 space-y-1">
        {routes.map((route) => {
          const isActive = location.pathname === route.to;
          return (
            <Link
              key={route.to}
              to={route.to}
              className={`flex items-center rounded-xl px-3 py-2.5 text-sm font-medium transition-all ${
                isActive
                  ? 'bg-sky-600 text-white shadow-sm'
                  : 'text-slate-700 hover:bg-slate-100'
              }`}
            >
              <span className="flex-1">{route.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer actions */}
      <div className="mt-4 space-y-2 pt-4 border-t border-slate-100">
        {user ? (
          <button
            onClick={logout}
            className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            Sign Out
          </button>
        ) : (
          <Link to="/login" className="block w-full rounded-xl bg-sky-600 px-3 py-2 text-center text-sm font-semibold text-white hover:bg-sky-500">
            Sign In
          </Link>
        )}
      </div>
    </aside>
  );
}

export default Sidebar;
