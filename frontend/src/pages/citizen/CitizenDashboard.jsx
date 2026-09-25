import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import DashboardLayout from "../../layouts/DashboardLayout";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../services/api";
import { DemoTag, StatusBadge, Loading, Empty, ErrorBox, Field, inputClass } from "../../components/ui";
import ImpactNetwork from "../../components/ImpactNetwork";

const nav = [
  ["/citizen/dashboard", "Overview"],
  ["/citizen/dashboard?tab=profile", "My Profile"],
  ["/citizen/problems/new", "Submit Problem"],
  ["/citizen/dashboard?tab=problems", "My Problems"],
  ["/citizen/dashboard?tab=status", "Problem Status"],
  ["/citizen/dashboard?tab=notifications", "Notifications"],
  ["/citizen/dashboard?tab=messages", "Messages"],
  ["/citizen/dashboard?tab=feedback", "Feedback"],
];

export default function CitizenDashboard() {
  const { token, user } = useAuth();
  const [params] = useSearchParams();
  const tab = params.get("tab") || "overview";
  const [problems, setProblems] = useState(null);
  const [notes, setNotes] = useState([]);
  const [messages, setMessages] = useState([]);
  const [err, setErr] = useState("");
  useEffect(() => {
    api("/api/problems/mine", { token }).then(setProblems).catch((e) => setErr(e.message));
    api("/api/notifications", { token }).then(setNotes);
    api("/api/messages", { token }).then(setMessages);
  }, [token]);
  return (
    <DashboardLayout title="Citizen Portal" items={nav}>
      <ErrorBox error={err} />
      {tab === "overview" && (
        <div className="citizen-overview">
          <div className="citizen-welcome"><div><p className="eyebrow text-gold">Citizen workspace</p><h2 className="mt-2 font-serif text-3xl text-white md:text-4xl">Your voice, tracked to impact.</h2><p className="mt-3 max-w-xl text-sm leading-6 text-emerald-50/75">Follow every problem you report, stay informed about government action and share feedback when conditions change.</p></div><Link to="/citizen/problems/new" className="cta-primary shrink-0">Submit a problem <span aria-hidden="true">→</span></Link></div>
          <div className="citizen-kpis"><div><span>My problems</span><strong>{problems ? problems.length : "—"}</strong><small>Reports submitted by you</small></div><div><span>Unread notifications</span><strong>{notes.filter((n) => !n.read).length}</strong><small>Updates waiting for you</small></div><div><span>Account status</span><strong className="text-base capitalize">{user?.verification_status?.replaceAll("_", " ") || "—"}</strong><small>Identity and access</small></div></div>
          <div className="citizen-section-heading"><div><p className="eyebrow text-forest-700">Recent activity</p><h2 className="font-serif text-2xl text-ink">My problems</h2></div><Link className="text-sm font-semibold text-forest-700 hover:text-clay" to="/citizen/dashboard?tab=problems">View all →</Link></div>
          <ProblemList problems={problems} />
          <div className="mt-10">
            <div className="mb-4"><p className="eyebrow text-forest-700">Platform network</p><h2 className="font-serif text-2xl text-ink">Live collaboration graph</h2><p className="mt-1 text-sm text-slate-500">See how problems connect to universities and industries across Jharkhand.</p></div>
            <ImpactNetwork compact />
          </div>
        </div>
      )}
      {tab === "profile" && user && (
        <div className="citizen-profile-card"><div className="profile-avatar">{user.full_name?.slice(0, 2).toUpperCase()}</div><div><p className="eyebrow text-forest-700">Account profile</p><h2 className="mt-1 font-serif text-3xl text-ink">{user.full_name}</h2><div className="mt-5 grid gap-3 text-sm sm:grid-cols-2"><p><span className="profile-label">Email</span>{user.email}</p><p><span className="profile-label">Mobile</span>{user.mobile}</p><p><span className="profile-label">Access status</span><span className="capitalize">{user.verification_status?.replaceAll("_", " ")}</span></p></div></div>
        </div>
      )}
      {(tab === "problems" || tab === "status" || tab === "overview") && tab !== "profile" && (
        <div className="citizen-problems-page mt-2">
          <div className="citizen-section-heading"><div><p className="eyebrow text-forest-700">Your case history</p><h2 className="font-serif text-3xl text-ink">My Problems</h2></div><Link to="/citizen/problems/new" className="cta-primary">New report <span aria-hidden="true">+</span></Link></div>
          {!problems && <Loading />}
          {problems && problems.length === 0 && <Empty>You have not submitted a problem yet.</Empty>}
          <ProblemList problems={problems} />
        </div>
      )}
      {tab === "notifications" && <div className="citizen-problems-page"><div className="citizen-section-heading"><div><p className="eyebrow text-forest-700">Stay informed</p><h2 className="font-serif text-3xl text-ink">Notifications</h2></div></div><ul className="space-y-3">{notes.map((n) => <li key={n.id} className="activity-card"><span className="activity-dot" /><div><strong>{n.title}</strong><div className="mt-1 text-sm leading-6 text-slate-600">{n.message}</div></div></li>)}</ul></div>}
      {tab === "messages" && <Messages token={token} items={messages} />}
      {tab === "feedback" && <FeedbackForm token={token} problems={problems || []} />}
    </DashboardLayout>
  );
}

function ProblemList({ problems }) {
  if (!problems) return <Loading />;
  if (problems.length === 0) return <Empty>You have not submitted a problem yet.</Empty>;
  return <ul className="space-y-3">{problems.map((p) => <li key={p.id} className="problem-row"><div className="problem-row-marker">{p.category?.slice(0, 1) || "P"}</div><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><Link className="font-semibold text-forest-800 hover:text-clay" to={`/problem/${p.public_id}`}>{p.public_id}</Link><DemoTag show={p.is_demo} /></div><p className="mt-1 truncate text-sm text-slate-600">{p.title}</p><p className="mt-2 text-xs text-slate-400">{p.district} · {p.submitted_at ? new Date(p.submitted_at).toLocaleDateString() : "Recently submitted"}</p></div><StatusBadge status={p.status} label={p.status_label} /></li>)}</ul>;
}

function Messages({ token, items }) {
  const [err, setErr] = useState("");
  return (
    <div className="citizen-problems-page">
      <div className="citizen-section-heading"><div><p className="eyebrow text-forest-700">Direct communication</p><h2 className="font-serif text-3xl text-ink">Messages</h2></div></div>
      <ErrorBox error={err} />
      <form className="dashboard-form mb-5" onSubmit={async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        try {
          await api("/api/messages", { method: "POST", token, body: { recipient_id: Number(fd.get("recipient_id")), subject: fd.get("subject"), body: fd.get("body") } });
          window.location.reload();
        } catch (ex) { setErr(ex.message); }
      }}>
        <Field label="Recipient user ID (government officer)"><input name="recipient_id" className={inputClass()} required /></Field>
        <Field label="Subject"><input name="subject" className={inputClass()} /></Field>
        <Field label="Message"><textarea name="body" className={inputClass()} required /></Field>
        <button className="bg-forest-800 text-cream px-3 py-2 rounded">Send</button>
      </form>
      <ul className="activity-list">{items.map((m) => <li key={m.id} className="activity-card"><span className="activity-dot" /><div><strong>{m.subject}</strong><p className="mt-1 text-sm text-slate-600">{m.body}</p></div></li>)}</ul>
    </div>
  );
}

function FeedbackForm({ token, problems }) {
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  return (
    <form className="dashboard-form max-w-2xl" onSubmit={async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      try {
        await api(`/api/problems/${fd.get("pid")}/feedback`, { method: "POST", token, body: { satisfaction: Number(fd.get("satisfaction")), resolved: fd.get("resolved") === "on", comments: fd.get("comments") } });
        setMsg("Feedback recorded. Official records were not modified.");
      } catch (ex) { setErr(ex.message); }
    }}>
      <div className="mb-6"><p className="eyebrow text-forest-700">Close the loop</p><h2 className="mt-1 font-serif text-3xl text-ink">Citizen feedback</h2><p className="mt-2 text-sm leading-6 text-slate-500">Tell us what changed on the ground. Your feedback helps keep public work accountable.</p></div>
      <ErrorBox error={err} />
      {msg && <p className="text-emerald-800">{msg}</p>}
      <Field label="Problem">
        <select name="pid" className={inputClass()}>{problems.map((p) => <option key={p.id} value={p.public_id}>{p.public_id}</option>)}</select>
      </Field>
      <Field label="Satisfaction 1-5"><input name="satisfaction" type="number" min="1" max="5" defaultValue="4" className={inputClass()} /></Field>
      <label className="flex gap-2 text-sm mb-3"><input type="checkbox" name="resolved" /> Problem appears resolved on the ground</label>
      <Field label="Comments"><textarea name="comments" className={inputClass()} /></Field>
      <button className="bg-forest-800 text-cream px-3 py-2 rounded">Submit feedback</button>
    </form>
  );
}
