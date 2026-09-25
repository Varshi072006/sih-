import { useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import DashboardLayout from "../../layouts/DashboardLayout";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../services/api";
import { ErrorBox, Field, Loading, StatusBadge, inputClass } from "../../components/ui";

const nav = [
  ["/university/dashboard", "Overview"],
  ["/university/problems", "Problem Desk"],
  ["/university/dashboard?tab=teams", "Research Team"],
  ["/university/dashboard?tab=messages", "Messages"],
  ["/university/dashboard?tab=profile", "Profile"],
];

export function UniversityDashboard() {
  const { token } = useAuth();
  const [searchParams] = useSearchParams();
  const [me, setMe] = useState(null);
  const [problems, setProblems] = useState({ recommended: [], available: [] });
  const [messages, setMessages] = useState([]);
  const [err, setErr] = useState("");
  const tab = searchParams.get("tab") || "overview";
  useEffect(() => {
    Promise.all([
      api("/api/universities/me", { token }).then(setMe),
      api("/api/universities/problems", { token }).then(setProblems),
    ]).catch((e) => setErr(e.message));
  }, [token]);
  useEffect(() => {
    if (tab === "messages") api("/api/messages", { token }).then(setMessages).catch((e) => setErr(e.message));
  }, [tab, token]);
  return (
    <DashboardLayout title="University workspace" items={nav}>
      <ErrorBox error={err} />
      {!me && !err && <Loading />}
      {me && tab === "overview" && (
        <div className="space-y-8">
          <section className="relative overflow-hidden rounded-[28px] bg-forest-950 p-6 text-white shadow-lg md:p-8">
            <div className="absolute -right-20 -top-24 h-64 w-64 rounded-full border-[34px] border-gold/20" />
            <div className="relative max-w-3xl">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-gold">Institution command centre</p>
              <h1 className="mt-3 font-serif text-4xl md:text-5xl">{me.name}</h1>
              <p className="mt-3 text-emerald-50/70">{me.district} · {me.verification_status}</p>
              <p className="mt-5 text-base leading-7 text-emerald-50/80">Review verified public challenges, bring your research community into the process, and turn expertise into practical recommendations.</p>
              <div className="mt-7 flex flex-wrap gap-3">
                <Link className="rounded-xl bg-clay px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#d96d39]" to="/university/problems">Open problem desk →</Link>
                <Link className="rounded-xl border border-white/20 px-4 py-3 text-sm font-semibold text-white transition hover:bg-white/10" to="/university/dashboard?tab=profile">View institution profile</Link>
              </div>
            </div>
          </section>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Recommended problems" value={problems.recommended.length} detail="AI-matched to your research" tone="gold" />
            <StatCard label="Available problems" value={problems.available.length} detail="Verified challenges open for review" />
            <StatCard label="Faculty network" value={me.faculty?.length || 0} detail="Researchers on your profile" tone="clay" />
            <StatCard label="Student contributors" value={me.students?.length || 0} detail="Applied research capacity" />
          </div>
          <section>
            <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
              <div><p className="text-xs font-semibold uppercase tracking-[0.22em] text-forest-600">Priority queue</p><h2 className="mt-1 font-serif text-3xl text-forest-950">Recommended for your institution</h2></div>
              <Link className="text-sm font-semibold text-forest-700 hover:text-clay" to="/university/problems">View all →</Link>
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              {problems.recommended.slice(0, 4).map((problem) => <ProblemCard key={problem.id} problem={problem} />)}
              {problems.recommended.length === 0 && <EmptyState title="No recommendations yet" text="New challenges matched to your research areas will appear here." />}
            </div>
          </section>
        </div>
      )}
      {me && tab === "profile" && <ProfileView me={me} />}
      {me && tab === "teams" && <TeamView me={me} token={token} onSaved={() => api("/api/universities/me", { token }).then(setMe)} />}
      {tab === "messages" && <MessageView messages={messages} />}
    </DashboardLayout>
  );
}

function ProfileView({ me }) {
  const rows = [
    ["Institution", me.name],
    ["District", me.district],
    ["Verification", me.verification_status],
    ["Departments", me.departments?.join(", ")],
    ["Research areas", me.research_areas],
    ["Faculty expertise", me.faculty_expertise],
    ["Laboratories", me.laboratories],
  ];
  return <div className="space-y-6"><div><p className="text-xs font-semibold uppercase tracking-[0.22em] text-forest-600">Institution record</p><h1 className="mt-1 font-serif text-4xl text-forest-950">Profile & capabilities</h1></div><div className="grid gap-5 lg:grid-cols-2"><div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="font-serif text-2xl text-forest-950">Verified information</h2><dl className="mt-5 divide-y divide-slate-100">{rows.map(([label, value]) => <div key={label} className="grid gap-1 py-3 sm:grid-cols-[0.8fr_1.2fr]"><dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">{label}</dt><dd className="text-sm leading-6 text-slate-700">{value || "Not provided"}</dd></div>)}</dl></div><div className="rounded-2xl bg-forest-950 p-6 text-white shadow-lg"><p className="text-xs font-semibold uppercase tracking-[0.22em] text-gold">Your contribution</p><h2 className="mt-3 font-serif text-3xl">Make expertise visible.</h2><p className="mt-4 text-sm leading-7 text-emerald-50/75">Keep your research areas, laboratories and contributors current so the matching system can surface challenges where your institution can help.</p><Link className="mt-6 inline-flex rounded-xl bg-clay px-4 py-3 text-sm font-semibold" to="/university/dashboard?tab=teams">Manage contributors →</Link></div></div></div>;
}

function TeamView({ me, token, onSaved }) {
  const [kind, setKind] = useState("faculty");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [err, setErr] = useState("");
  async function submit(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true); setErr(""); setMessage("");
    try {
      await api(`/api/universities/${kind}`, { method: "POST", token, body: { name: form.get("name"), member_type: kind, department: form.get("department"), responsibilities: form.get("responsibilities") || "" } });
      event.currentTarget.reset(); setMessage(`${kind === "faculty" ? "Faculty member" : "Student contributor"} added.`); onSaved();
    } catch (e) { setErr(e.message); } finally { setBusy(false); }
  }
  return <div className="space-y-6"><div><p className="text-xs font-semibold uppercase tracking-[0.22em] text-forest-600">People and expertise</p><h1 className="mt-1 font-serif text-4xl text-forest-950">Research team</h1></div><div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]"><div className="grid gap-5 sm:grid-cols-2"><MemberList title="Faculty & researchers" items={me.faculty || []} detail={(item) => `${item.department || "Research"} · ${item.expertise || "Expertise not added"}`} /><MemberList title="Student contributors" items={me.students || []} detail={(item) => item.department || "Department not added"} /></div><div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-xs font-semibold uppercase tracking-[0.2em] text-forest-600">Add contributor</p><div className="mt-4 flex rounded-xl bg-slate-100 p-1 text-sm"><button type="button" onClick={() => setKind("faculty")} className={`flex-1 rounded-lg px-3 py-2 font-semibold ${kind === "faculty" ? "bg-white text-forest-800 shadow-sm" : "text-slate-500"}`}>Faculty</button><button type="button" onClick={() => setKind("students")} className={`flex-1 rounded-lg px-3 py-2 font-semibold ${kind === "students" ? "bg-white text-forest-800 shadow-sm" : "text-slate-500"}`}>Student</button></div><ErrorBox error={err} />{message && <p className="mt-3 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800">{message}</p>}<form onSubmit={submit} className="mt-5 space-y-3"><Field label="Full name"><input name="name" className={inputClass()} required placeholder="Contributor name" /></Field><Field label="Department"><input name="department" className={inputClass()} placeholder="Department or centre" /></Field><Field label={kind === "faculty" ? "Expertise" : "Role or interests"}><input name="responsibilities" className={inputClass()} placeholder="What can they contribute?" /></Field><button disabled={busy} className="w-full rounded-xl bg-forest-800 px-4 py-3 font-semibold text-white disabled:opacity-60">{busy ? "Adding…" : "Add contributor"}</button></form></div></div></div>;
}

function MemberList({ title, items, detail }) {
  return <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="font-serif text-2xl text-forest-950">{title}</h2><div className="mt-4 space-y-3">{items.map((item) => <div key={item.id} className="flex items-center gap-3 rounded-xl bg-slate-50 p-3"><div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-emerald-100 font-semibold text-forest-700">{item.name?.slice(0, 1)}</div><div className="min-w-0"><p className="truncate font-semibold text-slate-800">{item.name}</p><p className="truncate text-xs text-slate-500">{detail(item)}</p></div></div>)}{items.length === 0 && <p className="text-sm text-slate-500">No contributors added yet.</p>}</div></div>;
}

function MessageView({ messages }) {
  return <div className="space-y-6"><div><p className="text-xs font-semibold uppercase tracking-[0.22em] text-forest-600">Coordination</p><h1 className="mt-1 font-serif text-4xl text-forest-950">Messages</h1></div><div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">{messages.map((message) => <div key={message.id} className="border-b border-slate-100 p-5 last:border-0"><div className="flex flex-wrap justify-between gap-2"><p className="font-semibold text-forest-900">{message.subject || "Untitled conversation"}</p><span className="text-xs text-slate-400">{message.created_at ? new Date(message.created_at).toLocaleDateString() : "Recent"}</span></div><p className="mt-2 text-sm leading-6 text-slate-600">{message.body}</p></div>)}{messages.length === 0 && <EmptyState title="Your inbox is clear" text="Government and project partners will contact you here when coordination is needed." />}</div></div>;
}

function StatCard({ label, value, detail, tone = "green" }) {
  const bar = tone === "gold" ? "bg-gold" : tone === "clay" ? "bg-clay" : "bg-teal-500";
  return <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className={`mb-4 h-2 w-12 rounded-full ${bar}`} /><p className="text-3xl font-serif text-forest-900">{value}</p><p className="mt-1 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</p><p className="mt-3 text-sm text-slate-500">{detail}</p></div>;
}

function ProblemCard({ problem }) {
  return <Link to={`/university/problem/${problem.public_id}`} className="group block rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:border-forest-300 hover:shadow-md"><div className="flex items-start justify-between gap-3"><span className="text-xs font-bold tracking-[0.16em] text-forest-600">{problem.public_id}</span><StatusBadge status={problem.status} label={problem.status_label} /></div><h3 className="mt-4 font-serif text-2xl text-forest-950 group-hover:text-forest-700">{problem.title}</h3><p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-600">{problem.description}</p><div className="mt-5 flex flex-wrap gap-2 text-xs text-slate-500"><span className="rounded-full bg-emerald-50 px-3 py-1 text-emerald-800">{problem.category || "Public challenge"}</span>{problem.district && <span className="rounded-full bg-slate-100 px-3 py-1">{problem.district}</span>}</div></Link>;
}

function EmptyState({ title, text }) {
  return <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center"><p className="font-serif text-xl text-forest-900">{title}</p><p className="mt-2 text-sm text-slate-500">{text}</p></div>;
}

export function UniversityProblems() {
  const { token } = useAuth();
  const [data, setData] = useState({ recommended: [], available: [] });
  const [query, setQuery] = useState("");
  const [view, setView] = useState("recommended");
  const [err, setErr] = useState("");
  useEffect(() => { api("/api/universities/problems", { token }).then(setData).catch((e) => setErr(e.message)); }, [token]);
  const items = useMemo(() => {
    const source = view === "recommended" ? data.recommended : data.available;
    return source.filter((p) => `${p.title} ${p.description} ${p.district} ${p.category}`.toLowerCase().includes(query.toLowerCase()));
  }, [data, query, view]);
  return (
    <DashboardLayout title="University problem desk" items={nav}>
      <ErrorBox error={err} />
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-[0.22em] text-forest-600">Evidence to action</p><h1 className="mt-1 font-serif text-4xl text-forest-950">Problem desk</h1></div><Link className="rounded-xl bg-forest-800 px-4 py-2.5 text-sm font-semibold text-white" to="/university/dashboard">Back to overview</Link></div>
      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:p-5"><div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between"><div className="flex rounded-xl bg-slate-100 p-1 text-sm"><button type="button" onClick={() => setView("recommended")} className={`rounded-lg px-4 py-2 font-semibold ${view === "recommended" ? "bg-white text-forest-800 shadow-sm" : "text-slate-500"}`}>Recommended ({data.recommended.length})</button><button type="button" onClick={() => setView("available")} className={`rounded-lg px-4 py-2 font-semibold ${view === "available" ? "bg-white text-forest-800 shadow-sm" : "text-slate-500"}`}>All available ({data.available.length})</button></div><input value={query} onChange={(e) => setQuery(e.target.value)} className="h-11 rounded-xl border border-slate-200 bg-slate-50 px-4 text-sm md:w-72" placeholder="Search title, district or topic" aria-label="Search problems" /></div></div>
      <div className="mt-5 grid gap-4 lg:grid-cols-2">{items.map((problem) => <ProblemCard key={problem.id} problem={problem} />)}{items.length === 0 && <EmptyState title="No matching problems" text="Try another search or check the available challenge queue." />}</div>
    </DashboardLayout>
  );
}

function Row({ p }) {
  return (
    <Link to={`/university/problem/${p.public_id}`} className="block bg-white border p-3 rounded mb-2">
      {p.public_id} · {p.title} · <StatusBadge status={p.status} label={p.status_label} />
    </Link>
  );
}

export function UniversityProblemReview() {
  const { id } = useParams();
  const { token } = useAuth();
  const [p, setP] = useState(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const reload = () => api(`/api/universities/problems/${id}`, { token }).then(setP);
  useEffect(() => { reload(); }, [id, token]);
  async function post(path, body) {
    try {
      const res = await api(`/api/universities/problems/${id}/${path}`, { method: "POST", token, body });
      setMsg(res.message || "Saved");
      reload();
    } catch (e) { setErr(e.message); }
  }
  if (!p && !err) return <DashboardLayout title="Problem review" items={nav}><Loading /></DashboardLayout>;
  return (
    <DashboardLayout title="University problem review" items={nav}>
      <ErrorBox error={err} />
      {p && <div className="space-y-6">
        <Link to="/university/problems" className="text-sm font-semibold text-forest-700">← Back to problem desk</Link>
        <section className="rounded-[28px] bg-forest-950 p-6 text-white shadow-lg md:p-8">
          <div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-bold tracking-[0.18em] text-gold">{p.public_id}</p><h1 className="mt-3 max-w-3xl font-serif text-4xl">{p.title}</h1></div><StatusBadge status={p.status} label={p.status_label} /></div>
          <p className="mt-5 max-w-4xl text-base leading-7 text-emerald-50/80">{p.description}</p>
          <div className="mt-6 flex flex-wrap gap-2 text-xs text-emerald-50/70"><span className="rounded-full bg-white/10 px-3 py-1.5">{p.category || "Public challenge"}</span><span className="rounded-full bg-white/10 px-3 py-1.5">{p.district || "District pending"}</span><span className="rounded-full bg-white/10 px-3 py-1.5">Department: {p.assigned_department || "Unassigned"}</span></div>
        </section>
        {msg && <p className="rounded-xl bg-emerald-50 p-4 text-sm font-medium text-emerald-800">{msg}</p>}
        <div className="grid gap-6 lg:grid-cols-[0.7fr_1.3fr]">
          <div className="space-y-4"><ActionCard title="Review decision" text="Record that your institution has assessed the challenge." action="Mark as reviewed" onClick={() => post("review", { remarks: "Reviewed by university" })} /><ActionCard title="Need more context?" text="Ask the owning department for clarification before advising." action="Request clarification" onClick={() => { const remarks = window.prompt("What clarification is needed?"); if (remarks) post("clarification", { remarks }); }} /><ActionCard title="Outside our scope" text="Close the loop when your institution cannot provide an opinion." action="Record no opinion" onClick={() => post("no-opinion")} /></div>
          <form className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm" onSubmit={async (e) => { e.preventDefault(); const fd = new FormData(e.currentTarget); await post("opinion", Object.fromEntries(fd.entries())); }}><p className="text-xs font-semibold uppercase tracking-[0.2em] text-forest-600">Expert contribution</p><h2 className="mt-1 font-serif text-2xl text-forest-950">Submit an expert opinion</h2><p className="mt-2 text-sm leading-6 text-slate-500">Give government a practical recommendation that can be evaluated and acted on.</p><div className="mt-5 space-y-3"><Field label="Core suggestion"><textarea name="suggestion" className={`${inputClass()} min-h-28`} required placeholder="What should change?" /></Field><Field label="Recommended improvement"><textarea name="recommended_improvement" className={`${inputClass()} min-h-20`} placeholder="How can the current approach improve?" /></Field><Field label="Technical recommendation"><textarea name="technical_recommendation" className={`${inputClass()} min-h-20`} placeholder="Methods, technology or research required" /></Field><div className="grid gap-3 md:grid-cols-2"><Field label="Alternative solution"><textarea name="alternative_solution" className={`${inputClass()} min-h-20`} /></Field><Field label="Expected benefit"><textarea name="expected_benefit" className={`${inputClass()} min-h-20`} required /></Field></div><button className="w-full rounded-xl bg-clay px-4 py-3 font-semibold text-white">Submit opinion to government →</button></div></form>
        </div>
      </div>}
    </DashboardLayout>
  );
}

function ActionCard({ title, text, action, onClick }) {
  return <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="font-serif text-xl text-forest-950">{title}</h2><p className="mt-2 text-sm leading-6 text-slate-500">{text}</p><button type="button" onClick={onClick} className="mt-4 rounded-xl border border-forest-700 px-3 py-2 text-sm font-semibold text-forest-700 transition hover:bg-forest-700 hover:text-white">{action}</button></div>;
}
