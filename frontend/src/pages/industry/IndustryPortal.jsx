import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import DashboardLayout from "../../layouts/DashboardLayout";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../services/api";
import { ErrorBox, Field, Loading, StatusBadge, inputClass } from "../../components/ui";
import ImpactNetwork from "../../components/ImpactNetwork";

const nav = [
  ["/industry/dashboard", "Overview"],
  ["/industry/problems", "Available Problems"],
  ["/industry/dashboard?tab=collab", "My Collaborations"],
];

export function IndustryDashboard() {
  const { token } = useAuth();
  const [me, setMe] = useState(null);
  const [collab, setCollab] = useState([]);
  useEffect(() => {
    api("/api/industry/me", { token }).then(setMe);
    api("/api/industry/collaborations", { token }).then(setCollab);
  }, [token]);
  if (!me) return <DashboardLayout title="Industry Portal" items={nav}><Loading /></DashboardLayout>;
  return (
    <DashboardLayout title="Industry Portal" items={nav}>
      <div className="partner-dashboard">
        <section className="partner-hero"><div><p className="eyebrow text-gold">Industry partner cockpit</p><h1 className="mt-2 font-serif text-3xl text-white md:text-5xl">{me.company_name}</h1><p className="mt-3 text-sm text-emerald-50/75">{me.organization_type} <span className="mx-1 text-white/30">/</span> {me.sector}</p><p className="mt-4 max-w-xl text-sm leading-6 text-emerald-50/70">Participation is optional. Your expertise can accelerate solutions without ever blocking a government-led problem workflow.</p></div><Link to="/industry/problems" className="cta-primary shrink-0">Explore opportunities <span aria-hidden="true">→</span></Link></section>
        <div className="partner-kpis"><div><span>Open opportunities</span><strong>—</strong><small>Browse available problems</small></div><div><span>My collaborations</span><strong>{collab.length}</strong><small>Active participation records</small></div><div><span>Capabilities</span><strong>{me.capabilities?.length || 0}</strong><small>Declared delivery strengths</small></div></div>
        <div className="partner-grid"><section className="partner-panel"><div className="partner-section-heading"><div><p className="eyebrow text-forest-700">Active relationships</p><h2 className="font-serif text-2xl text-ink">My collaborations</h2></div><Link to="/industry/problems" className="text-sm font-semibold text-forest-700">Find more →</Link></div>{collab.length ? <div className="space-y-3">{collab.map((c) => <article key={c.id} className="collaboration-card"><div className="partner-mark">{c.title?.slice(0, 1) || "C"}</div><div className="min-w-0 flex-1"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">{c.problem_id}</p><h3 className="mt-1 truncate font-semibold text-forest-900">{c.title}</h3><div className="mt-2 flex flex-wrap gap-2">{c.types.split(",").map((type) => <span className="capability-chip" key={type}>{type}</span>)}<span className="capability-chip capability-chip-status">{c.status}</span></div></div></article>)}</div> : <div className="partner-empty">No collaborations yet. Browse available problems to find a good fit.</div>}</section><aside className="partner-panel"><p className="eyebrow text-forest-700">Your capabilities</p><h2 className="mt-1 font-serif text-2xl text-ink">What you bring</h2><div className="mt-5 flex flex-wrap gap-2">{(me.capabilities || []).map((capability) => <span className="capability-chip" key={capability}>{capability}</span>)}</div><p className="mt-5 text-sm leading-6 text-slate-500">Keep your capabilities visible so government teams can understand how you may contribute.</p></aside></div>
        <div className="mt-8">
          <div className="mb-4"><p className="eyebrow text-forest-700">Platform network</p><h2 className="font-serif text-2xl text-ink">Live collaboration graph</h2><p className="mt-1 text-sm text-slate-500">See how problems connect to universities and industries across Jharkhand.</p></div>
          <ImpactNetwork compact />
        </div>
      </div>
    </DashboardLayout>
  );
}

export function IndustryProblems() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  useEffect(() => { api("/api/industry/problems", { token }).then(setItems); }, [token]);
  return (
    <DashboardLayout title="Industry problems" items={nav}>
      {items.map((p) => (
        <Link key={p.id} to={`/industry/problem/${p.public_id}`} className="block bg-white border p-3 rounded mb-2">
          {p.public_id} · {p.title} · <StatusBadge status={p.status} label={p.status_label} />
        </Link>
      ))}
    </DashboardLayout>
  );
}

export function IndustryProblemPage() {
  const { id } = useParams();
  const { token } = useAuth();
  const [p, setP] = useState(null);
  const [err, setErr] = useState("");
  const [types, setTypes] = useState([]);
  const [lookups, setLookups] = useState({ participation_types: [] });
  useEffect(() => {
    api(`/api/industry/problems/${id}`, { token }).then(setP).catch((e) => setErr(e.message));
    api("/api/lookups").then(setLookups);
  }, [id, token]);
  if (!p && !err) return <DashboardLayout title="Industry" items={nav}><Loading /></DashboardLayout>;
  return (
    <DashboardLayout title="Industry participation" items={nav}>
      <ErrorBox error={err} />
      {p && (
        <>
          <h1 className="font-serif text-3xl">{p.title}</h1>
          <p>{p.description}</p>
          <div className="my-4">
            {(lookups.participation_types || []).map((t) => (
              <label key={t} className="block text-sm"><input type="checkbox" checked={types.includes(t)} onChange={(e) => setTypes(e.target.checked ? [...types, t] : types.filter((x) => x !== t))} /> {t}</label>
            ))}
            <button className="mt-2 bg-forest-800 text-cream px-3 py-2 rounded" type="button" onClick={async () => {
              try { await api(`/api/industry/problems/${id}/participate`, { method: "POST", token, body: { participation_types: types } }); alert("Participation recorded"); }
              catch (e) { setErr(e.message); }
            }}>Participate</button>
          </div>
          <form className="bg-white border p-4 rounded space-y-2" onSubmit={async (e) => {
            e.preventDefault();
            const fd = new FormData(e.target);
            try {
              await api(`/api/industry/problems/${id}/proposal`, { method: "POST", token, body: Object.fromEntries(fd.entries()) });
              alert("Proposal submitted for government review");
            } catch (ex) { setErr(ex.message); }
          }}>
            <h2 className="font-medium">Industry proposal</h2>
            {["proposal","technology_offered","resources","estimated_budget","timeline","team","expected_contribution"].map((k) => (
              <Field key={k} label={k.replaceAll("_"," ")}><textarea name={k} className={inputClass()} required={k==="proposal"} /></Field>
            ))}
            <button className="bg-clay text-white px-3 py-2 rounded">Submit proposal</button>
          </form>
        </>
      )}
    </DashboardLayout>
  );
}
