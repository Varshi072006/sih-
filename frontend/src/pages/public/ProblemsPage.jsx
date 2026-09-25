import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../services/api";
import { DemoTag, StatusBadge, Loading, Field, inputClass } from "../../components/ui";

export default function ProblemsPage() {
  const [items, setItems] = useState(null);
  const [lookups, setLookups] = useState({ categories: {}, districts: [] });
  const [f, setF] = useState({ q: "", category: "", district: "", status: "" });
  useEffect(() => {
    api("/api/lookups").then(setLookups).catch(() => {});
  }, []);
  useEffect(() => {
    const p = new URLSearchParams();
    Object.entries(f).forEach(([k, v]) => v && p.set(k === "q" ? "q" : k, v));
    api(`/api/problems?${p}`).then(setItems).catch(() => setItems([]));
  }, [f]);
  return (
    <div className="max-w-7xl mx-auto px-4 py-10">
      <h1 className="font-serif text-4xl mb-6">Problem List</h1>
      <div className="grid md:grid-cols-4 gap-3 mb-6">
        <input className={inputClass()} placeholder="Search title or Problem ID" value={f.q} onChange={(e) => setF({ ...f, q: e.target.value })} />
        <select className={inputClass()} value={f.category} onChange={(e) => setF({ ...f, category: e.target.value })}>
          <option value="">All categories</option>
          {Object.keys(lookups.categories || {}).map((c) => <option key={c}>{c}</option>)}
        </select>
        <select className={inputClass()} value={f.district} onChange={(e) => setF({ ...f, district: e.target.value })}>
          <option value="">All districts</option>
          {(lookups.districts || []).map((d) => <option key={d}>{d}</option>)}
        </select>
        <select className={inputClass()} value={f.status} onChange={(e) => setF({ ...f, status: e.target.value })}>
          <option value="">All statuses</option>
          {Object.entries(lookups.statuses || {}).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </div>
      {!items && <Loading />}
      <div className="overflow-x-auto bg-white border rounded">
        <table className="min-w-full text-sm">
          <thead className="bg-forest-800 text-cream text-left">
            <tr><th className="p-3">Problem ID</th><th>Title</th><th>District</th><th>Category</th><th>Status</th></tr>
          </thead>
          <tbody>
            {(items || []).map((p) => (
              <tr key={p.id} className="border-t">
                <td className="p-3"><Link className="underline" to={`/problem/${p.public_id}`}>{p.public_id}</Link><DemoTag show={p.is_demo} /></td>
                <td>{p.title}</td>
                <td>{p.district}</td>
                <td>{p.category}</td>
                <td className="p-3"><StatusBadge status={p.status} label={p.status_label} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
