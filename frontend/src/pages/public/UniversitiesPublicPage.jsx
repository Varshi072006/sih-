import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../services/api";
import { DemoTag, inputClass } from "../../components/ui";

export default function UniversitiesPublicPage() {
  const [items, setItems] = useState([]);
  const [query, setQuery] = useState("");
  const [district, setDistrict] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(false);
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    if (district) params.set("district", district);
    api(`/api/universities?${params}`)
      .then(setItems)
      .catch(() => { setItems([]); setError(true); })
      .finally(() => setLoading(false));
  }, [query, district]);

  const districts = [...new Set(items.map((item) => item.district).filter(Boolean))];
  return (
    <div>
      <section className="catalog-hero">
        <div className="section-shell py-12 md:py-16">
          <div className="max-w-3xl">
            <p className="eyebrow">Research network · Jharkhand</p>
            <h1 className="mt-3 font-serif text-4xl leading-tight text-white md:text-6xl">Knowledge that moves public work forward.</h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-emerald-50/75 md:text-lg">Explore verified universities contributing research, faculty and student expertise to government-led problem solving.</p>
          </div>
          <div className="mt-10 grid max-w-2xl grid-cols-2 gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/10 sm:grid-cols-3">
            <div className="catalog-stat"><strong>{items.length}</strong><span>listed institutions</span></div>
            <div className="catalog-stat"><strong>{new Set(items.flatMap((item) => item.departments || [])).size}</strong><span>active disciplines</span></div>
            <div className="catalog-stat hidden sm:block"><strong>{new Set(items.map((item) => item.district)).size}</strong><span>districts represented</span></div>
          </div>
        </div>
      </section>
      <section className="section-shell py-8 md:py-12">
        <div className="partner-callout">
          <div>
            <p className="eyebrow text-gold">Grow the research network</p>
            <h2 className="mt-1 font-serif text-2xl text-white md:text-3xl">Register as a university partner</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-emerald-50/75">Bring your faculty, laboratories and student expertise to government-led problem solving across Jharkhand.</p>
          </div>
          <Link to="/register/university" className="cta-primary shrink-0">Register your university <span aria-hidden="true">→</span></Link>
        </div>
        <div className="catalog-toolbar">
          <div>
            <p className="eyebrow text-forest-700">Verified directory</p>
            <h2 className="mt-1 font-serif text-2xl text-ink md:text-3xl">Find the right research partner</h2>
          </div>
          <div className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row">
            <input className={`${inputClass()} sm:w-64`} placeholder="Search expertise or name" value={query} onChange={(event) => setQuery(event.target.value)} />
            <select className={`${inputClass()} sm:w-44`} value={district} onChange={(event) => setDistrict(event.target.value)}>
              <option value="">All districts</option>
              {districts.map((item) => <option key={item}>{item}</option>)}
            </select>
          </div>
        </div>
        {loading && <div className="catalog-empty">Loading verified institutions...</div>}
        {!loading && error && <div className="catalog-empty">The directory is temporarily unavailable. Please refresh and try again.</div>}
        {!loading && !error && !items.length && <div className="catalog-empty">No universities match those filters.</div>}
        <div className="mt-7 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {!loading && items.map((u) => (
            <article key={u.id} className="catalog-card group">
              <div className="flex items-start justify-between gap-4">
                <div className="catalog-mark">{u.name.slice(0, 2).toUpperCase()}</div>
                <DemoTag show={u.is_demo} />
              </div>
              <h2 className="mt-5 font-serif text-2xl leading-tight text-ink">{u.name}</h2>
              <p className="mt-2 text-sm font-medium text-forest-700">{u.institution_type} <span className="mx-1 text-slate-300">/</span> {u.district}</p>
              <p className="mt-4 min-h-12 text-sm leading-6 text-slate-600">{u.research_areas || "Research and innovation partner"}</p>
              <div className="mt-5 flex flex-wrap gap-2 border-t border-slate-100 pt-4">
                {(u.departments || []).map((department) => <span className="catalog-chip" key={department}>{department}</span>)}
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
