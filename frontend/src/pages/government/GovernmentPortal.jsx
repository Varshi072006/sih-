import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import DashboardLayout from "../../layouts/DashboardLayout";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../services/api";
import { DemoTag, ErrorBox, Field, Loading, StatusBadge, inputClass } from "../../components/ui";

const nav = [
  ["/government/dashboard", "Overview"],
  ["/government/problems", "Problem queue"],
  ["/government/tracking", "Case tracking"],
  ["/government/departments", "Departments"],
  ["/government/opinions", "Opinions"],
  ["/government/solutions", "Solutions"],
];

export function GovernmentDashboard() {
  const { token } = useAuth();
  const [d, setD] = useState(null);
  useEffect(() => { api("/api/government/dashboard", { token }).then(setD).catch(() => setD(null)); }, [token]);
  if (!d) return <DashboardLayout title="Government Portal" items={nav}><Loading /></DashboardLayout>;
  const cards = [
    ["Total Problems", d.total],
    ["Pending Verification", d.pending_verification],
    ["Verified Problems", d.verified],
    ["Assigned to Departments", d.assigned],
    ["Under Resolution", d.under_resolution],
    ["Awaiting University Opinion", d.awaiting_university],
    ["Ready for Industry", d.ready_for_industry],
    ["Completed Problems", d.completed],
  ];
  return (
    <DashboardLayout title="Government Portal" items={nav}>
      <div className="government-dashboard"><section className="government-hero"><div><p className="eyebrow text-gold">Government operations</p><h2 className="mt-2 font-serif text-3xl text-white md:text-5xl">Move every case forward.</h2><p className="mt-3 max-w-2xl text-sm leading-6 text-emerald-50/75">Track verification, departmental action, university review, industry participation, and completion from one accountable workspace.</p></div><Link to="/government/tracking" className="cta-primary shrink-0">Open case tracker <span aria-hidden="true">→</span></Link></section><div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-5">
        {cards.map(([k, v]) => <div key={k} className="bg-white border p-4 rounded"><div className="text-2xl font-serif">{v}</div><div className="text-xs uppercase">{k}</div></div>)}
      </div></div>
      <div className="grid md:grid-cols-2 gap-4 mt-6">
        <div className="bg-white border p-4 rounded"><h2 className="font-medium mb-2">District-wise</h2>{Object.entries(d.districts || {}).map(([k, v]) => <p key={k}>{k}: {v}</p>)}</div>
        <div className="bg-white border p-4 rounded"><h2 className="font-medium mb-2">Department-wise</h2>{Object.entries(d.departments || {}).map(([k, v]) => <p key={k}>{k}: {v}</p>)}</div>
      </div>
    </DashboardLayout>
  );
}

export function GovernmentTracking() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  const [query, setQuery] = useState("");
  const [stage, setStage] = useState("");
  useEffect(() => { api("/api/government/problems", { token }).then(setItems); }, [token]);
  const stages = [
    ["pending_government_verification", "Needs verification", "bg-amber-100 text-amber-800"],
    ["assigned_to_department", "Department action", "bg-sky-100 text-sky-800"],
    ["under_department_review", "Under review", "bg-indigo-100 text-indigo-800"],
    ["university_review", "University review", "bg-violet-100 text-violet-800"],
    ["industry_participation", "Industry ready", "bg-orange-100 text-orange-800"],
    ["completed", "Completed", "bg-emerald-100 text-emerald-800"],
  ];
  const filtered = items.filter((item) => (!stage || item.status === stage) && (!query || `${item.public_id} ${item.title} ${item.district}`.toLowerCase().includes(query.toLowerCase())));
  return <DashboardLayout title="Government Case Tracking" items={nav}><div className="tracking-page"><div className="tracking-heading"><div><p className="eyebrow text-forest-700">Workflow visibility</p><h1 className="mt-1 font-serif text-3xl text-ink md:text-4xl">Case tracking</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">See where each public problem is in the government workflow and open a case to take the next action.</p></div><span className="admin-count-badge">{filtered.length} visible cases</span></div><div className="tracking-stage-grid">{stages.map(([value, label, color]) => <button type="button" key={value} className={`tracking-stage ${stage === value ? "is-selected" : ""}`} onClick={() => setStage(stage === value ? "" : value)}><span className={color}>{items.filter((item) => item.status === value).length}</span><strong>{label}</strong><small>{stage === value ? "Showing this stage" : "Filter cases"}</small></button>)}</div><div className="tracking-toolbar"><input className={inputClass()} placeholder="Search ID, title, or district" value={query} onChange={(event) => setQuery(event.target.value)} /><select className={inputClass()} value={stage} onChange={(event) => setStage(event.target.value)}><option value="">All workflow stages</option>{stages.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div><div className="tracking-list">{filtered.map((item) => <Link key={item.id} to={`/government/problem/${item.public_id}`} className="tracking-card"><div className="tracking-card-top"><div><span className="tracking-id">{item.public_id}</span><h2>{item.title}</h2></div><StatusBadge status={item.status} label={item.status_label} /></div><div className="tracking-card-meta"><span>{item.district}</span><span>{item.category}</span><span>{item.assigned_department || "Department not assigned"}</span></div><div className="tracking-progress"><span className="tracking-progress-fill" style={{ width: `${item.status === "completed" ? 100 : item.status === "pending_government_verification" ? 18 : item.status.includes("review") ? 52 : 72}%` }} /></div><small>Open case details and continue workflow <b>→</b></small></Link>)}{!filtered.length && <div className="partner-empty">No cases match the selected tracking filters.</div>}</div></div></DashboardLayout>;
}

export function GovernmentProblems() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  const [lookups, setLookups] = useState({ statuses: {}, districts: [], categories: {} });
  const [f, setF] = useState({ status: "", district: "", category: "", q: "" });
  useEffect(() => { api("/api/lookups").then(setLookups); }, []);
  useEffect(() => {
        const p = new URLSearchParams();
        p.set("q", f.q);
    Object.entries(f).forEach(([k, v]) => v && p.set(k, v));
    api(`/api/government/problems?${p}`, { token }).then(setItems);
  }, [token, f]);
  return (
    <DashboardLayout title="Government Problem Queue" items={nav}>
      <GovernmentPageHeader eyebrow="Workflow intake" title="Problem queue" description="Review citizen reports, filter by responsibility, and open a case to continue government action." count={`${items.length} visible cases`} />
      <div className="grid md:grid-cols-4 gap-2 mb-4">
        <input className={inputClass()} placeholder="Search" value={f.q} onChange={(e) => setF({ ...f, q: e.target.value })} />
        <select className={inputClass()} value={f.status} onChange={(e) => setF({ ...f, status: e.target.value })}>
          <option value="">Status</option>
          {Object.entries(lookups.statuses || {}).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select className={inputClass()} value={f.district} onChange={(e) => setF({ ...f, district: e.target.value })}>
          <option value="">District</option>
          {(lookups.districts || []).map((d) => <option key={d}>{d}</option>)}
        </select>
        <select className={inputClass()} value={f.category} onChange={(e) => setF({ ...f, category: e.target.value })}>
          <option value="">Category</option>
          {Object.keys(lookups.categories || {}).map((c) => <option key={c}>{c}</option>)}
        </select>
      </div>
      <div className="overflow-x-auto bg-white border rounded">
        <table className="min-w-full text-sm">
          <thead className="bg-forest-800 text-cream text-left"><tr><th className="p-2">ID</th><th>Title</th><th>District</th><th>Status</th></tr></thead>
          <tbody>
            {items.map((p) => (
              <tr key={p.id} className="border-t">
                <td className="p-2"><Link className="underline" to={`/government/problem/${p.public_id}`}>{p.public_id}</Link><DemoTag show={p.is_demo} /></td>
                <td>{p.title}</td>
                <td>{p.district}</td>
                <td><StatusBadge status={p.status} label={p.status_label} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </DashboardLayout>
  );
}

export function GovernmentProblemDetail() {
  const { id } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [p, setP] = useState(null);
  const [depts, setDepts] = useState([]);
  const [err, setErr] = useState("");
  const [remarks, setRemarks] = useState("");
  const [dept, setDept] = useState("");
  const [doneOpen, setDoneOpen] = useState(false);
  const [matching, setMatching] = useState(false);
  const [notifying, setNotifying] = useState(false);
  const reload = () => api(`/api/government/problems/${id}`, { token }).then(setP);
  useEffect(() => {
    reload();
    api("/api/government/departments", { token }).then(setDepts);
  }, [id, token]);

  async function act(path, body) {
    setErr("");
    try {
      await api(`/api/government/problems/${id}/${path}`, { method: "POST", token, body });
      await reload();
    } catch (e) { setErr(e.message); }
  }

  async function askAiForUniversities() {
    setMatching(true);
    setErr("");
    try {
      await api(`/api/ai/recommendations/${id}`, { method: "GET", token });
      await reload();
    } catch (e) { setErr(e.message); }
    finally { setMatching(false); }
  }

  async function notifyRecommendedUniversities() {
    const ids = (p.university_recommendations || []).map((recommendation) => recommendation.university_id);
    if (!ids.length) return;
    setNotifying(true);
    setErr("");
    try {
      await api(`/api/government/problems/${id}/select-universities`, { method: "POST", token, body: { university_ids: ids } });
      await reload();
    } catch (e) { setErr(e.message); }
    finally { setNotifying(false); }
  }

  if (!p) return <DashboardLayout title="Government Portal" items={nav}><Loading /></DashboardLayout>;
  return (
    <DashboardLayout title="Government Verification" items={nav}>
      <ErrorBox error={err} />
         <div className="government-detail"><div className="government-detail-hero"><p className="eyebrow text-gold">Case workspace · {p.public_id}</p><h1 className="mt-2 font-serif text-3xl text-white md:text-5xl">{p.title}</h1><div className="mt-4"><StatusBadge status={p.status} label={p.status_label} /><DemoTag show={p.is_demo} /></div><p className="mt-4 max-w-3xl text-sm leading-6 text-emerald-50/75">{p.description}</p></div>
         <div className="government-detail-grid"><main className="space-y-4">
      {p.ai && (
        <section className="bg-white border p-4 rounded mt-4">
          <h2 className="font-medium">AI recommendation (reviewable)</h2>
          <p>Category {p.ai.domain} / {p.ai.subdomain} · confidence {p.ai.confidence}</p>
          <p>Suggested department: {p.ai.suggested_department}</p>
          <p>Priority {p.ai.priority_label} ({p.ai.priority_score}) · {p.ai.explanation}</p>
        </section>
      )}
      {(p.duplicates || []).length > 0 && (
        <section className="bg-white border p-4 rounded mt-4">
          <h2 className="font-medium">Potential Related Problems Found</h2>
          {p.duplicates.map((d) => (
            <form key={d.id} className="flex flex-wrap gap-2 items-center text-sm py-1" onSubmit={async (e) => {
              e.preventDefault();
              await api(`/api/government/problems/${id}/duplicate`, { method: "POST", token, body: { related_problem_id: d.internal_id, decision: e.target.decision.value, reason: "Officer decision" } });
              reload();
            }}>
              <span>{d.problem_id} · {d.similarity} · {d.reason}</span>
              <select name="decision" className="border rounded"><option value="related">Mark Related</option><option value="merged">Merge</option><option value="separate">Keep Separate</option></select>
              <button className="border px-2 py-1 rounded">Save decision</button>
            </form>
          ))}
        </section>
      )}
         <div className="government-detail-card"><div className="government-card-title"><div><p className="eyebrow text-forest-700">Official action</p><h2 className="font-serif text-2xl text-ink">Verify and assign</h2></div><span className="government-card-index">03</span></div><Field label="Official remarks"><textarea className={inputClass()} value={remarks} onChange={(e) => setRemarks(e.target.value)} /></Field>
         <div className="flex flex-wrap gap-2">
        <button className="bg-forest-800 text-cream px-3 py-2 rounded" type="button" onClick={() => act("verify", { remarks })}>Verify</button>
        <button className="bg-red-800 text-white px-3 py-2 rounded" type="button" onClick={() => act("reject", { remarks })}>Reject</button>
        <button className="border px-3 py-2 rounded" type="button" onClick={() => act("request-info", { remarks })}>Request More Information</button>
      </div>
      <div className="flex flex-wrap gap-2 mt-4 items-end">
        <Field label="Assign department">
          <select className={inputClass()} value={dept} onChange={(e) => setDept(e.target.value)}>
            <option value="">Select</option>
            {depts.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </Field>
        <button className="bg-forest-700 text-white px-3 py-2 rounded mb-3" type="button" onClick={() => act("assign", { department_id: Number(dept), remarks })}>Assign Department</button>
      </div>
      <form className="bg-white border p-4 rounded mt-4 space-y-2" onSubmit={async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        try {
          await api(`/api/government/problems/${id}/solution`, { method: "POST", token, form: fd });
          e.target.reset();
          reload();
        } catch (ex) { setErr(ex.message); }
      }}>
        <h2 className="font-medium">Upload Solution / Action Taken</h2>
        <input name="description" className={inputClass()} placeholder="Solution description" required />
        <input name="action_taken" className={inputClass()} placeholder="Action taken" required />
        <textarea name="implementation_details" className={inputClass()} placeholder="Implementation details" />
        <input type="file" name="files" multiple />
        <button className="bg-clay text-white px-3 py-2 rounded">Save versioned solution</button>
      </form>
      <section className="government-detail-card">
        <div className="government-card-title"><div><p className="eyebrow text-forest-700">AI-assisted matching</p><h2 className="font-serif text-2xl text-ink">Find suitable university partners</h2><p className="mt-2 text-sm leading-6 text-slate-500">Recommendations use the problem, government solution, departments, expertise, laboratories, previous projects, and technologies of verified institutions.</p></div><span className="government-card-index">05</span></div>
        <div className="flex flex-wrap gap-3"><button type="button" className="cta-primary" disabled={matching} onClick={askAiForUniversities}>{matching ? "Matching universities…" : "Ask AI for suggestions"} <span aria-hidden="true">→</span></button>{(p.university_recommendations || []).length > 0 && <button type="button" className="border border-forest-700 px-4 py-2 rounded-xl text-sm font-semibold text-forest-800" disabled={notifying} onClick={notifyRecommendedUniversities}>{notifying ? "Sending notifications…" : "Notify all recommended colleges"}</button>}</div>
        {(p.university_recommendations || []).length > 0 && <div className="mt-5 space-y-2">{p.university_recommendations.map((r) => <div key={r.id} className="ai-university-row"><div><strong>{r.university}</strong><p>{r.relevant_department || "Relevant institutional expertise"} · {r.matching_score}% match</p></div><span>{r.selected ? "Notification sent" : "Recommended"}</span></div>)}</div>}
      </section>
      {(p.university_recommendations || []).length > 0 && (
        <form className="bg-white border p-4 rounded mt-4" onSubmit={async (e) => {
          e.preventDefault();
          const ids = [...e.target.querySelectorAll("input[name=uni]:checked")].map((i) => Number(i.value));
          try {
            await api(`/api/government/problems/${id}/select-universities`, { method: "POST", token, body: { university_ids: ids } });
            reload();
          } catch (ex) { setErr(ex.message); }
        }}>
          <h2 className="font-medium mb-2">Choose specific universities to notify</h2>
          {(p.university_recommendations || []).map((r) => (
            <label key={r.id} className="block text-sm mb-1">
              <input type="checkbox" name="uni" value={r.university_id} defaultChecked={r.selected} /> {r.university} · {r.matching_score}% · {r.reason}
            </label>
          ))}
          <button className="mt-2 bg-forest-800 text-cream px-3 py-2 rounded">Notify selected universities</button>
        </form>
      )}
      {(p.opinions || []).map((o) => (
        <form key={o.id} className="bg-white border p-4 rounded mt-3" onSubmit={async (e) => {
          e.preventDefault();
          const fd = new FormData(e.target);
          try {
            await api(`/api/government/opinions/${o.id}/review`, { method: "POST", token, body: { decision: fd.get("decision"), remarks: fd.get("remarks"), update_solution: fd.get("update") === "on", solution: { description: fd.get("sdesc") || o.suggestion, action_taken: fd.get("sact") || "Updated after university opinion", implementation_details: "" } } });
            reload();
          } catch (ex) { setErr(ex.message); }
        }}>
          <h3>View University Opinion — {o.university}</h3>
          <p>{o.suggestion}</p>
          <select name="decision" className="border rounded p-1">
            <option value="accept">Accept Suggestion</option>
            <option value="partial">Partially Accept</option>
            <option value="reject">Reject</option>
            <option value="clarification">Request Clarification</option>
          </select>
          <textarea name="remarks" className={inputClass()} placeholder="Official remarks" />
          <label className="text-sm flex gap-2"><input type="checkbox" name="update" /> Update Solution (creates next version)</label>
          <input name="sdesc" className={inputClass()} placeholder="Updated solution description" />
          <input name="sact" className={inputClass()} placeholder="Updated action taken" />
          <button className="bg-forest-800 text-cream px-3 py-1 rounded mt-2">Save review</button>
        </form>
      ))}
      <button type="button" className="mt-4 bg-gold text-forest-900 px-4 py-2 rounded" onClick={() => setDoneOpen(true)}>Done Solution</button>
      {doneOpen && (
        <div className="fixed inset-0 bg-black/40 grid place-items-center p-4" role="dialog" aria-modal="true">
          <div className="bg-white p-6 rounded max-w-md">
            <p>Are you sure you want to mark this solution as completed and make it available for industry participation?</p>
            <div className="flex gap-2 mt-4">
              <button className="bg-forest-800 text-cream px-3 py-2 rounded" type="button" onClick={async () => { await act("done-solution", { remarks }); setDoneOpen(false); }}>Confirm</button>
              <button className="border px-3 py-2 rounded" type="button" onClick={() => setDoneOpen(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
      <button type="button" className="ml-2 mt-4 border px-4 py-2 rounded" onClick={() => act("complete", { remarks: "Marked completed" })}>Mark problem completed</button>
      <p className="mt-4"><Link className="underline" to="/government/problems">Back to queue</Link></p>
      </div></main></div></div>
    </DashboardLayout>
  );
}

export function GovernmentDepartments() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  useEffect(() => { api("/api/government/departments", { token }).then(setItems); }, [token]);
  return (
    <DashboardLayout title="Departments" items={nav}>
      <GovernmentPageHeader eyebrow="Operating structure" title="Departments" description="Browse the government units responsible for reviewing and resolving public problems." count={`${items.length} departments`} />
      <ul className="government-list">{items.map((d) => <li key={d.id} className="government-list-card"><span className="department-code">{d.code}</span><div><strong>{d.name}</strong><div className="mt-1 text-sm leading-6 text-slate-500">{d.description}</div></div></li>)}</ul>
    </DashboardLayout>
  );
}

export function GovernmentOpinions() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  useEffect(() => {
    api("/api/government/problems?status=university_opinion_submitted", { token }).then(setItems);
  }, [token]);
  return (
    <DashboardLayout title="University opinions" items={nav}>
      <GovernmentPageHeader eyebrow="Research input" title="University opinions" description="Review academic suggestions waiting for an official government decision." count={`${items.length} awaiting review`} />
      <div className="government-list">{items.map((p) => <Link key={p.id} className="government-list-card" to={`/government/problem/${p.public_id}`}><span className="department-code opinion-code">UNI</span><div><strong>{p.public_id}</strong><div className="mt-1 text-sm text-slate-600">{p.title}</div></div><span className="text-forest-700">Open →</span></Link>)}</div>
    </DashboardLayout>
  );
}

export function GovernmentSolutions() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  useEffect(() => { api("/api/government/problems?status=action_solution_uploaded", { token }).then(setItems); }, [token]);
  return (
    <DashboardLayout title="Solutions" items={nav}>
      <GovernmentPageHeader eyebrow="Resolution pipeline" title="Solutions" description="Track cases with uploaded government action and prepare the next implementation step." count={`${items.length} solution records`} />
      <div className="government-list">{items.map((p) => <Link key={p.id} className="government-list-card" to={`/government/problem/${p.public_id}`}><span className="department-code solution-code">SOL</span><div><strong>{p.public_id}</strong><div className="mt-1 text-sm text-slate-600">{p.title}</div></div><span className="text-forest-700">Open →</span></Link>)}</div>
    </DashboardLayout>
  );
}

function GovernmentPageHeader({ eyebrow, title, description, count }) {
  return <div className="government-page-header"><div><p className="eyebrow text-forest-700">{eyebrow}</p><h1 className="mt-1 font-serif text-3xl text-ink md:text-4xl">{title}</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">{description}</p></div><span className="admin-count-badge">{count}</span></div>;
}
