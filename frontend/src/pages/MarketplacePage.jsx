import { useEffect, useState, useCallback } from 'react';
import PropertyCard from '../components/PropertyCard';
import { propertyApi } from '../api/endpoints';
import { useAuth } from '../context/AuthContext';

const CITIES = ['Hyderabad', 'Mumbai', 'Bangalore', 'Pune', 'Chennai', 'Delhi', 'Ahmedabad', 'Noida', 'Gurugram', 'Kolkata', 'Jaipur'];

function MarketplacePage() {
  const { user } = useAuth();
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    city: '', property_type: '', risk_level: '', min_roi: '', max_roi: '', search: '',
  });

  const fetchProperties = useCallback(() => {
    setLoading(true);
    propertyApi
      .list(filters)
      .then((res) => setProperties(res.data))
      .catch(() => setProperties([]))
      .finally(() => setLoading(false));
  }, [filters]);

  useEffect(() => {
    fetchProperties();
  }, [fetchProperties]);

  const setFilter = (key, value) => setFilters((prev) => ({ ...prev, [key]: value }));

  const clearFilters = () =>
    setFilters({ city: '', property_type: '', risk_level: '', min_roi: '', max_roi: '', search: '' });

  const hasActiveFilters = Object.values(filters).some(Boolean);

  return (
    <section className="py-2">
      {/* Header */}
      <div className="mb-6 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-900">Property Marketplace</h2>
          <p className="text-sm text-slate-500">Fractional investment in verified Indian real estate</p>
        </div>
        {!loading && (
          <span className="rounded-full bg-sky-50 px-3 py-1 text-sm font-semibold text-sky-700">
            {properties.length} {properties.length === 1 ? 'listing' : 'listings'} found
          </span>
        )}
      </div>

      {/* Filters */}
      <div className="mb-6 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="mb-3 flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Filters</p>
          {hasActiveFilters && (
            <button onClick={clearFilters} className="text-xs font-medium text-sky-600 hover:underline">
              Clear all
            </button>
          )}
        </div>
        <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
          <input
            className="col-span-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-sky-400 focus:outline-none sm:col-span-2"
            placeholder="🔍  Search by title, city, description…"
            value={filters.search}
            onChange={(e) => setFilter('search', e.target.value)}
          />
          <select
            className="rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-sky-400 focus:outline-none"
            value={filters.city}
            onChange={(e) => setFilter('city', e.target.value)}
          >
            <option value="">All Cities</option>
            {CITIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <select
            className="rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-sky-400 focus:outline-none"
            value={filters.property_type}
            onChange={(e) => setFilter('property_type', e.target.value)}
          >
            <option value="">All Types</option>
            <option value="commercial">Commercial</option>
            <option value="residential">Residential</option>
            <option value="retail">Retail</option>
            <option value="office">Office</option>
            <option value="industrial">Industrial</option>
            <option value="warehouse">Warehouse</option>
          </select>
          <select
            className="rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-sky-400 focus:outline-none"
            value={filters.risk_level}
            onChange={(e) => setFilter('risk_level', e.target.value)}
          >
            <option value="">All Risk Levels</option>
            <option value="Low">Low Risk</option>
            <option value="Medium">Medium Risk</option>
            <option value="High">High Risk</option>
          </select>
          <input
            type="number"
            min="0"
            className="rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-sky-400 focus:outline-none"
            placeholder="Min ROI %"
            value={filters.min_roi}
            onChange={(e) => setFilter('min_roi', e.target.value)}
          />
          <input
            type="number"
            min="0"
            className="rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-sky-400 focus:outline-none"
            placeholder="Max ROI %"
            value={filters.max_roi}
            onChange={(e) => setFilter('max_roi', e.target.value)}
          />
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-64 animate-pulse rounded-2xl bg-slate-100" />
          ))}
        </div>
      ) : properties.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 py-16 text-center">
          <p className="text-4xl mb-3">🏘️</p>
          <h3 className="text-lg font-semibold text-slate-700">No properties found</h3>
          <p className="mt-1 text-sm text-slate-500">Try adjusting your filters or clearing them.</p>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="mt-4 rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-500"
            >
              Clear Filters
            </button>
          )}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {properties.map((property) => (
            <PropertyCard key={property.id} property={property} canInvest={user?.role === 'investor'} />
          ))}
        </div>
      )}
    </section>
  );
}

export default MarketplacePage;
