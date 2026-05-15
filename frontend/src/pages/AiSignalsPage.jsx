import { Link } from 'react-router-dom';

const readSignals = () => {
  try {
    const stored = sessionStorage.getItem('estatex.aiSignals');
    return stored ? JSON.parse(stored) : null;
  } catch (e) {
    console.warn('Failed to read AI signals from storage', e);
    return null;
  }
};

function AiSignalsPage() {
  const stored = readSignals();
  const roi = stored?.roi?.predicted_roi_percent ?? 0;
  const rentalYield = stored?.rentalYield?.predicted_rental_yield_percent ?? 0;
  const riskScore = stored?.risk?.probability_score != null
    ? Math.round(stored.risk.probability_score * 100)
    : 0;
  return (
    <section className="relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="pointer-events-none absolute -right-20 -top-20 h-56 w-56 rounded-full bg-sky-100 blur-3xl" />
      <div className="pointer-events-none absolute -left-16 bottom-0 h-64 w-64 rounded-full bg-emerald-100 blur-3xl" />

      <div className="relative">
        <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">AI Signals</p>
            <h2 className="text-2xl font-extrabold text-slate-900">Signals Snapshot</h2>
            <p className="mt-1 text-sm text-slate-600">Numeric summary for this listing.</p>
          </div>
          <Link
            to="/marketplace"
            className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            Back to Marketplace
          </Link>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <h3 className="text-sm font-bold text-slate-800">Predicted ROI</h3>
            <div className="mt-3 text-3xl font-extrabold text-slate-900">{roi}%</div>
            <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full bg-emerald-500"
                style={{ width: `${Math.min(100, Math.max(0, roi))}%` }}
              />
            </div>
            <div className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Annual</div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <h3 className="text-sm font-bold text-slate-800">Predicted Rental Yield</h3>
            <div className="mt-3 text-3xl font-extrabold text-slate-900">{rentalYield}%</div>
            <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full bg-sky-500"
                style={{ width: `${Math.min(100, Math.max(0, rentalYield))}%` }}
              />
            </div>
            <div className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Annual</div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <h3 className="text-sm font-bold text-slate-800">Risk Score</h3>
            <div className="mt-3 text-3xl font-extrabold text-rose-600">{riskScore}</div>
            <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full bg-rose-500"
                style={{ width: `${Math.min(100, Math.max(0, riskScore))}%` }}
              />
            </div>
            <div className="mt-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Out of 100</div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default AiSignalsPage;
