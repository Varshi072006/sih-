import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from "recharts";
import DashboardLayout from "../../layouts/DashboardLayout";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../services/api";
import { ErrorBox, Loading, inputClass } from "../../components/ui";

const nav = [
  ["/admin/dashboard", "Overview"],
  ["/admin/users", "Users"],
  ["/admin/problems", "Problems"],
  ["/admin/universities", "Universities"],
  ["/admin/industries", "Industries"],
  ["/admin/projects", "Projects"],
  ["/admin/ai", "AI monitoring"],
  ["/admin/analytics", "Analytics"],
  ["/admin/audit-logs", "Audit logs"],
];

export function AdminDashboard() {
  const { token } = useAuth();
  const [d, setD] = useState(null);
  useEffect(() => { api("/api/admin/dashboard", { token }).then(setD); }, [token]);
  if (!d) return <DashboardLayout title="Admin" items={nav}><Loading /></DashboardLayout>;
  return (
    <DashboardLayout title="Admin Portal" items={nav}>
      <div className="admin-dashboard"><section className="admin-hero"><div><p className="eyebrow text-gold">Platform operations</p><h2 className="mt-2 font-serif text-3xl text-white md:text-5xl">Keep public work moving.</h2><p className="mt-3 max-w-2xl text-sm leading-6 text-emerald-50/75">Review registrations, monitor problem workflows, and protect the platform’s record of accountable action.</p></div><div className="admin-hero-badge"><span>System status</span><strong>Operational</strong><small>All services responding</small></div></section><div className="admin-kpis">{Object.entries(d).map(([k, v]) => <div key={k}><span>{k.replaceAll("_", " ")}</span><strong>{v}</strong><small>Live platform metric</small></div>)}</div><div className="admin-quick-grid"><Link to="/admin/users" className="admin-quick-card"><span className="admin-quick-icon">01</span><div><strong>Review users</strong><p>Approve registrations and manage access.</p></div><span>→</span></Link><Link to="/admin/problems" className="admin-quick-card"><span className="admin-quick-icon admin-quick-icon-gold">02</span><div><strong>Inspect problems</strong><p>Track cases across the public workflow.</p></div><span>→</span></Link><Link to="/admin/audit-logs" className="admin-quick-card"><span className="admin-quick-icon admin-quick-icon-teal">03</span><div><strong>Audit activity</strong><p>Keep platform actions traceable.</p></div><span>→</span></Link></div></div>
    </DashboardLayout>
  );
}

export function AdminUsers() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  const [err, setErr] = useState("");
  const load = () => api("/api/admin/users", { token }).then(setItems);
  useEffect(() => { load(); }, [token]);
  async function act(id, action) {
    try { await api(`/api/admin/users/${id}/${action}`, { method: "POST", token, body: { remarks: action } }); load(); }
    catch (e) { setErr(e.message); }
  }
  return (
    <DashboardLayout title="User management" items={nav}>
      <AdminPageHeader eyebrow="Access control" title="User management" description="Review identity, organization access, and verification status across the network." count={`${items.length} accounts`} />
      <ErrorBox error={err} />
      <div className="admin-table-wrap">
        <table className="min-w-full text-sm">
          <thead className="bg-forest-800 text-cream"><tr><th className="p-3 text-left">Name</th><th>Email</th><th>Role</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            {items.map((u) => (
              <tr key={u.id} className="admin-table-row">
                <td className="p-3"><strong>{u.full_name}</strong>{u.is_demo && <span className="admin-demo-tag">Demo</span>}</td>
                <td>{u.email}</td>
                <td>{u.primary_role}</td>
                <td><span className={`admin-status admin-status-${u.verification_status}`}>{u.verification_status?.replaceAll("_", " ")}</span>{!u.is_active && <span className="ml-1 text-xs text-red-600">suspended</span>}</td>
                <td className="space-x-1 p-2">
                  {["approve","reject","more-info","suspend","reactivate"].map((a) => (
                    <button key={a} className="admin-action" type="button" onClick={() => act(u.id, a)}>{a}</button>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </DashboardLayout>
  );
}

export function AdminProblems() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  useEffect(() => { api("/api/admin/problems", { token }).then(setItems); }, [token]);
  return (
    <DashboardLayout title="Problem management" items={nav}>
      <AdminPageHeader eyebrow="Workflow oversight" title="Problem management" description="Monitor every public-interest case and open the government workspace for action." count={`${items.length} cases`} />
      <div className="admin-record-list">{items.map((p) => <Link key={p.id} to={`/government/problem/${p.public_id}`} className="admin-record"><span className="admin-record-mark">P</span><div><strong>{p.public_id}</strong><p>{p.title}</p></div><span className="admin-status">{p.status_label}</span><span className="text-slate-400">→</span></Link>)}</div>
    </DashboardLayout>
  );
}

export function AdminUniversities() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  useEffect(() => { api("/api/admin/universities", { token }).then(setItems); }, [token]);
  return (
    <DashboardLayout title="Universities" items={nav}>
      <AdminPageHeader eyebrow="Research network" title="University review" description="Verify institutions before they join the research and expertise network." count={`${items.length} institutions`} />
      {items.map((u) => (
        <article key={u.id} className="admin-org-card">
          <div className="admin-org-mark">UNI</div><div className="min-w-0 flex-1"><h2 className="font-semibold text-forest-900">{u.name} {u.is_demo && <span className="admin-demo-tag">Demo</span>}</h2><p className="mt-1 text-sm text-slate-500">{u.district} · <span className="capitalize">{u.verification_status?.replaceAll("_", " ")}</span></p><p className="mt-2 text-sm text-slate-600">{u.research_areas}</p>
          <AdminOrgActions userId={u.user_id} token={token} />
          </div>
        </article>
      ))}
    </DashboardLayout>
  );
}

export function AdminIndustries() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  useEffect(() => { api("/api/admin/industries", { token }).then(setItems); }, [token]);
  return (
    <DashboardLayout title="Industries" items={nav}>
      <AdminPageHeader eyebrow="Delivery network" title="Industry review" description="Manage verified companies, startups, and organizations contributing to implementation." count={`${items.length} partners`} />
      {items.map((i) => (
        <article key={i.id} className="admin-org-card">
          <div className="admin-org-mark admin-org-mark-clay">IND</div><div className="min-w-0 flex-1"><h2 className="font-semibold text-forest-900">{i.company_name} {i.is_demo && <span className="admin-demo-tag">Demo</span>}</h2><p className="mt-1 text-sm text-slate-500">{i.organization_type} · {i.sector} · <span className="capitalize">{i.verification_status?.replaceAll("_", " ")}</span></p>
          <AdminOrgActions userId={i.user_id} token={token} />
          </div>
        </article>
      ))}
    </DashboardLayout>
  );
}

function AdminOrgActions({ userId, token }) {
  return (
    <div className="flex gap-2 mt-2 text-sm">
      {["approve","reject","more-info","suspend"].map((a) => (
        <button key={a} className="border px-2 rounded" type="button" onClick={() => api(`/api/admin/users/${userId}/${a}`, { method: "POST", token, body: { remarks: a } }).then(() => window.location.reload())}>{a}</button>
      ))}
    </div>
  );
}

export function AdminProjects() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  useEffect(() => { api("/api/admin/projects", { token }).then(setItems); }, [token]);
  return (
    <DashboardLayout title="Projects" items={nav}>
      <AdminPageHeader eyebrow="Impact delivery" title="Projects" description="Track structured pilots connecting public problems with university and industry partners." count={`${items.length} projects`} />
      <div className="admin-record-list">{items.map((p) => <Link key={p.id} to={`/project/${p.public_id}`} className="admin-record"><span className="admin-record-mark admin-record-mark-gold">PJ</span><div><strong>{p.public_id}</strong><p>{p.title}</p></div><span className="text-slate-400">→</span></Link>)}</div>
    </DashboardLayout>
  );
}

export function AdminAI() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  useEffect(() => { api("/api/admin/ai", { token }).then(setItems); }, [token]);
  return (
    <DashboardLayout title="AI monitoring" items={nav}>
      <AdminPageHeader eyebrow="Decision support" title="AI monitoring" description="Review explainable recommendations without allowing automation to replace public accountability." count={`${items.length} analyses`} />
      <div className="admin-info-banner">Stored recommendations remain explainable. AI never auto-verifies, assigns or completes problems.</div>
      <div className="admin-record-list">{items.map((a, i) => (
        <article key={i} className="admin-record text-sm">
          <strong>{a.problem_id}</strong> · {a.domain} ({a.confidence}) · priority {a.priority_label} · {a.suggested_department} · {a.model_used}
        </article>
      ))}</div>
    </DashboardLayout>
  );
}

export function AdminAudit() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  useEffect(() => { api("/api/admin/audit-logs", { token }).then(setItems); }, [token]);
  return (
    <DashboardLayout title="Audit logs" items={nav}>
      <AdminPageHeader eyebrow="Trust and traceability" title="Audit logs" description="A chronological record of sensitive actions across the platform." count={`${items.length} events`} />
      <div className="admin-info-banner">Audit records are append-only. Normal users cannot delete or alter this history.</div>
      <div className="admin-table-wrap overflow-x-auto">
        <table className="min-w-full text-xs">
          <thead className="bg-forest-800 text-cream"><tr><th className="p-2">Time</th><th>User</th><th>Action</th><th>Entity</th><th>Status</th></tr></thead>
          <tbody>
            {items.map((l) => (
              <tr key={l.id} className="border-t">
                <td className="p-2">{l.created_at}</td>
                <td>{l.role} #{l.user_id}</td>
                <td>{l.action}</td>
                <td>{l.entity_type} {l.entity_id}</td>
                <td>{l.previous_status} → {l.new_status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </DashboardLayout>
  );
}

export function AdminAnalytics() {
  const { token } = useAuth();
  const [data, setData] = useState(null);
  useEffect(() => { api("/api/analytics", { token }).then(setData); }, [token]);
  if (!data) return <DashboardLayout title="Analytics" items={nav}><Loading /></DashboardLayout>;
  return (
    <DashboardLayout title="Analytics" items={nav}>
      <div className="admin-analytics"><AdminPageHeader eyebrow="Decision intelligence" title="Platform analytics" description="A live view of the problem-solving network, from intake and verification to partnerships and delivery." count="Live data" />
        <div className="analytics-summary"><div><span>Total problems</span><strong>{data.status.reduce((sum, item) => sum + item.value, 0)}</strong><small>Across all workflow stages</small></div><div><span>Universities</span><strong>{data.universities}</strong><small>Research institutions</small></div><div><span>Industry partners</span><strong>{data.industries}</strong><small>Verified contributors</small></div><div><span>Projects</span><strong>{data.projects}</strong><small>Structured pilots</small></div></div>
        <div className="analytics-chart-grid"><section className="admin-chart-card"><div className="chart-heading"><div><p className="eyebrow text-forest-700">Workflow distribution</p><h2 className="mt-1 font-serif text-2xl text-ink">Problems by status</h2></div><span className="chart-kicker">{data.status.length} stages</span></div><ResponsiveContainer width="100%" height="88%"><BarChart data={data.status} margin={{ top: 12, right: 8, left: -16, bottom: 8 }}><CartesianGrid vertical={false} stroke="#e5eee9" /><XAxis dataKey="name" tick={{ fontSize: 10, fill: "#64748b" }} angle={-22} textAnchor="end" height={58} interval={0} /><YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "#64748b" }} /><Tooltip cursor={{ fill: "#edf6f1" }} contentStyle={{ borderRadius: 12, border: "1px solid #dfeae4", boxShadow: "0 8px 25px rgba(15,55,46,.12)" }} /><Bar dataKey="value" radius={[7, 7, 0, 0]}>{data.status.map((entry, index) => <Cell key={entry.name} fill={index % 3 === 0 ? "#123d34" : index % 3 === 1 ? "#2e7a69" : "#ea7f48"} />)}</Bar></BarChart></ResponsiveContainer></section><section className="admin-chart-card"><div className="chart-heading"><div><p className="eyebrow text-forest-700">Problem mix</p><h2 className="mt-1 font-serif text-2xl text-ink">By category</h2></div><span className="chart-kicker">{data.category.length} categories</span></div><ResponsiveContainer width="100%" height="88%"><BarChart data={data.category} layout="vertical" margin={{ top: 8, right: 12, left: 22, bottom: 8 }}><CartesianGrid horizontal={false} stroke="#e5eee9" /><XAxis type="number" allowDecimals={false} tick={{ fontSize: 11, fill: "#64748b" }} /><YAxis type="category" dataKey="name" width={95} tick={{ fontSize: 10, fill: "#64748b" }} /><Tooltip cursor={{ fill: "#edf6f1" }} contentStyle={{ borderRadius: 12, border: "1px solid #dfeae4" }} /><Bar dataKey="value" fill="#2e7a69" radius={[0, 7, 7, 0]} /></BarChart></ResponsiveContainer></section></div>
        <section className="district-strip"><div><p className="eyebrow text-forest-700">Geographic reach</p><h2 className="mt-1 font-serif text-2xl text-ink">District activity</h2></div><div className="district-pills">{data.district.map((item) => <span key={item.name}><strong>{item.value}</strong>{item.name}</span>)}</div></section>
      </div>
    </DashboardLayout>
  );
}

function AdminPageHeader({ eyebrow, title, description, count }) {
  return <div className="admin-page-header"><div><p className="eyebrow text-forest-700">{eyebrow}</p><h1 className="mt-1 font-serif text-3xl text-ink md:text-4xl">{title}</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">{description}</p></div><span className="admin-count-badge">{count}</span></div>;
}
