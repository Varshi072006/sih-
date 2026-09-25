export function StatusBadge({ status, label }) {
  const color = {
    pending_government_verification: "bg-amber-100 text-amber-900",
    verified: "bg-emerald-100 text-emerald-900",
    rejected: "bg-red-100 text-red-800",
    completed: "bg-forest-700 text-white",
    done_solution: "bg-sky-100 text-sky-900",
  }[status] || "bg-stone-200 text-stone-800";
  return <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${color}`}>{label || status}</span>;
}

export function DemoTag({ show }) {
  if (!show) return null;
  return <span className="ml-2 text-[10px] uppercase tracking-wider bg-gold/20 text-forest-900 px-1.5 py-0.5 rounded">Demo</span>;
}

export function ErrorBox({ error }) {
  if (!error) return null;
  return <div role="alert" className="bg-red-50 text-red-800 border border-red-200 p-3 rounded mb-4">{error}</div>;
}

export function Loading() {
  return <div className="animate-pulse space-y-3"><div className="h-6 bg-stone-200 rounded w-1/3" /><div className="h-24 bg-stone-200 rounded" /></div>;
}

export function Empty({ children }) {
  return <p className="text-sm text-forest-700 bg-white border rounded p-6">{children}</p>;
}

export function Field({ label, children }) {
  return (
    <label className="block mb-3">
      <span className="block text-sm font-medium mb-1">{label}</span>
      {children}
    </label>
  );
}

export function inputClass() {
  return "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm text-ink shadow-sm transition placeholder:text-slate-400 focus:border-forest-600 focus:ring-2 focus:ring-emerald-100";
}
