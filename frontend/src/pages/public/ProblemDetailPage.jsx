import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { MapContainer, Marker, TileLayer } from "react-leaflet";
import { api } from "../../services/api";
import { useAuth } from "../../context/AuthContext";
import { DemoTag, ErrorBox, Loading, StatusBadge } from "../../components/ui";
import L from "leaflet";

const icon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

export default function ProblemDetailPage() {
  const { id } = useParams();
  const { token } = useAuth();
  const [p, setP] = useState(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    api(`/api/problems/${id}`, { token }).then(setP).catch((e) => setErr(e.message));
  }, [id, token]);
  if (err) return <div className="max-w-5xl mx-auto p-6"><ErrorBox error={err} /></div>;
  if (!p) return <div className="p-8"><Loading /></div>;
  const latestSolution = (p.solutions || []).at(-1);
  const governmentSteps = ["Report received", "Government verification", "Department action", "Solution / implementation"];
  const governmentProgress = p.status === "rejected" ? 1 : p.status === "pending_government_verification" ? 2 : p.solutions?.length ? 4 : 3;
  return (
    <div className="problem-dossier">
      <div className="section-shell py-8 md:py-12">
      <div className="dossier-hero">
        <div>
          <p className="eyebrow text-gold">Public problem record <DemoTag show={p.is_demo} /></p>
          <p className="mt-4 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-100/60">{p.public_id}</p>
          <h1 className="mt-2 max-w-4xl font-serif text-4xl leading-tight text-white md:text-6xl">{p.title}</h1>
          <div className="mt-5"><StatusBadge status={p.status} label={p.status_label} /></div>
        </div>
        <div className="dossier-hero-meta"><span>Reported in</span><strong>{p.district}</strong><small>Citizen-submitted case</small></div>
      </div>
      <div className="dossier-grid">
      <main className="space-y-6">
      <section className="dossier-card">
        <div className="dossier-section-title"><div><p className="eyebrow text-forest-700">Case overview</p><h2 className="mt-1 font-serif text-2xl text-ink">Problem information</h2></div><span className="dossier-icon">01</span></div>
        <p className="leading-7 text-slate-600">{p.description}</p>
        <dl className="grid md:grid-cols-2 gap-2 mt-4 text-sm">
          <div className="dossier-fact"><dt>Category</dt><dd>{p.category} / {p.subcategory || "General"}</dd></div>
          <div className="dossier-fact"><dt>Location</dt><dd>{p.village}, {p.block}, {p.district}</dd></div>
          <div className="dossier-fact"><dt>Affected population</dt><dd>{p.estimated_affected_population || 0} people</dd></div>
          <div className="dossier-fact"><dt>Submitted</dt><dd>{new Date(p.submitted_at).toLocaleDateString()}</dd></div>
        </dl>
        {p.latitude && p.longitude && (
          <div className="h-56 mt-4 rounded overflow-hidden border">
            <MapContainer center={[p.latitude, p.longitude]} zoom={10} style={{ height: "100%", width: "100%" }}>
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              <Marker position={[p.latitude, p.longitude]} icon={icon} />
            </MapContainer>
          </div>
        )}
      </section>
      <section className="dossier-card government-card">
        <div className="dossier-section-title"><div><p className="eyebrow text-forest-700">Official response</p><h2 className="mt-1 font-serif text-2xl text-ink">Government information</h2></div><span className="dossier-icon dossier-icon-gold">02</span></div>
        <div className="government-summary"><div><span className="fact-label">Assigned department</span><strong>{p.assigned_department || "Awaiting assignment"}</strong></div><div><span className="fact-label">Current stage</span><strong>{p.status_label}</strong></div></div>
        <div className="government-progress">{governmentSteps.map((label, index) => <div key={label} className={index < governmentProgress ? "progress-step is-done" : "progress-step"}><span>{index < governmentProgress ? "✓" : index + 1}</span><small>{label}</small></div>)}</div>
        {latestSolution ? <article className="solution-panel"><div><span className="eyebrow text-forest-700">Latest government update</span><h3 className="mt-1 font-serif text-xl text-ink">Solution version {latestSolution.version}</h3></div><p className="mt-3 text-sm leading-6 text-slate-600">{latestSolution.description}</p>{latestSolution.action_taken && <p className="mt-3 text-sm"><strong>Action taken:</strong> {latestSolution.action_taken}</p>}{latestSolution.implementation_details && <p className="mt-2 text-sm"><strong>Implementation:</strong> {latestSolution.implementation_details}</p>}</article> : <div className="government-pending"><span className="help-icon">i</span><div><strong>Government review is in progress</strong><p>No public solution update has been posted yet. This record will update as the responsible department takes action.</p></div></div>}
      </section>
      {p.ai && (
        <section>
          <h2 className="font-serif text-2xl mb-2">AI Information</h2>
          <p className="text-sm mb-2">Recommendation only — not an official decision.</p>
          <p>Domain {p.ai.domain} ({p.ai.confidence}) · Suggested department {p.ai.suggested_department}</p>
          <p>Priority {p.ai.priority_label} ({p.ai.priority_score})</p>
          {(p.duplicates || []).length > 0 && (
            <div className="mt-3">
              <h3 className="font-medium">Potential Related Problems Found</h3>
              <ul>{p.duplicates.map((d) => <li key={d.id}>{d.problem_id} · {d.similarity} · {d.reason}</li>)}</ul>
            </div>
          )}
          {(p.university_recommendations || []).map((r) => (
            <p key={r.id}>{r.university} · {r.matching_score}% · {r.reason}</p>
          ))}
        </section>
      )}
      {p.opinions && (
        <section>
          <h2 className="font-serif text-2xl mb-2">University Information</h2>
          {p.opinions.map((o) => (
            <article key={o.id} className="bg-white border p-4 rounded mb-2">
              <strong>{o.university}</strong>
              <p>{o.suggestion}</p>
            </article>
          ))}
        </section>
      )}
      {p.participations && (
        <section>
          <h2 className="font-serif text-2xl mb-2">Industry Information</h2>
          {p.participations.map((x) => <p key={x.id}>Participation {x.types} ({x.status})</p>)}
        </section>
      )}
      <section className="dossier-card">
        <div className="dossier-section-title"><div><p className="eyebrow text-forest-700">Traceable progress</p><h2 className="mt-1 font-serif text-2xl text-ink">Timeline</h2></div><span className="dossier-icon">03</span></div>
        <ol className="dossier-timeline">
          {(p.timeline || []).map((t) => (
            <li key={t.id}><span className="timeline-dot" /><div><div className="font-medium text-ink">{t.new_status}</div><div className="mt-1 text-sm leading-6 text-slate-500">{t.note || "Status recorded"} · {new Date(t.created_at).toLocaleDateString()}</div></div></li>
          ))}
        </ol>
      </section>
      </main>
      <aside className="dossier-sidebar"><div className="sidebar-card"><p className="eyebrow text-forest-700">At a glance</p><div className="sidebar-metric"><strong>{p.severity}</strong><span>Severity</span></div><div className="sidebar-metric"><strong>{p.urgency}</strong><span>Urgency</span></div><div className="sidebar-metric"><strong>{p.geographic_impact || "Local"}</strong><span>Impact area</span></div></div><div className="sidebar-card"><p className="eyebrow text-forest-700">Need help?</p><p className="mt-3 text-sm leading-6 text-slate-600">Keep this public ID handy when referring to your report.</p><p className="mt-4 rounded-xl bg-emerald-50 px-3 py-2 text-center text-sm font-semibold text-forest-800">{p.public_id}</p></div></aside>
      </div>
      <Link className="underline" to="/problems">Back to Problem List</Link>
      </div>
    </div>
  );
}
