const colorMap = {
  Low: 'bg-emerald-100 text-emerald-700',
  Medium: 'bg-amber-100 text-amber-700',
  High: 'bg-rose-100 text-rose-700',
};

function RiskBadge({ risk }) {
  return <span className={`rounded-full px-2 py-1 text-xs font-semibold ${colorMap[risk] || 'bg-slate-100 text-slate-700'}`}>{risk}</span>;
}

export default RiskBadge;
