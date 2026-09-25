import { Link, NavLink, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import AssistantWidget from "../components/AssistantWidget";

export default function DashboardLayout({ title, items, children }) {
  const { user, logout, token } = useAuth();
  const navigate = useNavigate();
  const [notes, setNotes] = useState([]);
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (!token) return;
    api("/api/notifications", { token }).then(setNotes).catch(() => setNotes([]));
  }, [token]);
  const unread = notes.filter((n) => !n.read).length;
  const workspaceLabel = title.toLowerCase().includes("admin") || title.toLowerCase().includes("user management") || title.toLowerCase().includes("analytics") || title.toLowerCase().includes("audit") ? "Admin workspace" : title.toLowerCase().includes("industry") ? "Industry workspace" : title.toLowerCase().includes("university") ? "Research workspace" : title.toLowerCase().includes("government") ? "Government workspace" : "Citizen workspace";
  const rootPaths = ["/citizen/dashboard", "/industry/dashboard", "/university/dashboard", "/government/dashboard", "/admin/dashboard"];

  return (
    <div className="min-h-screen bg-[#eef3ee] flex">
      <aside className="dashboard-sidebar hidden md:flex">
        <Link to="/" className="dashboard-brand"><span className="dashboard-brand-mark">CI</span><span><strong>Challenge to Impact</strong><small>{workspaceLabel}</small></span></Link>
        <div className="dashboard-sidebar-intro"><span className="dashboard-live-dot" />Workspace online</div>
        <nav className="dashboard-nav">
          <p className="dashboard-nav-label">Workspace</p>
          {items.map(([to, label]) => (
            <NavLink key={to} to={to} end={rootPaths.includes(to)} className={({ isActive }) => `dashboard-nav-item ${isActive ? "is-active" : ""}`}>
              <span className="dashboard-nav-icon">{label.slice(0, 2).toUpperCase()}</span><span>{label}</span><i aria-hidden="true">→</i>
            </NavLink>
          ))}
        </nav>
        <div className="dashboard-sidebar-footer"><span className="dashboard-footer-avatar">{user?.full_name?.slice(0, 2).toUpperCase() || "U"}</span><span><strong>{user?.full_name || "Workspace user"}</strong><small>Secure session</small></span><span className="dashboard-footer-dot" /></div>
      </aside>
      <div className="flex-1 min-w-0">
        <header className="bg-white border-b px-4 py-3 flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-forest-700">{title}</p>
            <h1 className="font-serif text-xl">{user?.full_name}</h1>
          </div>
          <div className="flex items-center gap-3">
            <button type="button" className="relative text-sm" onClick={() => setOpen((v) => !v)} aria-expanded={open}>
              Notifications{unread ? ` (${unread})` : ""}
            </button>
            <Link to="/" className="text-sm">Public site</Link>
            <button type="button" className="text-sm" onClick={() => { logout(); navigate("/"); }}>Logout</button>
          </div>
        </header>
        {open && (
          <div className="bg-white border-b max-h-64 overflow-auto">
            {notes.length === 0 && <p className="p-4 text-sm">No notifications.</p>}
            {notes.map((n) => (
              <button
                key={n.id}
                type="button"
                className="block w-full text-left px-4 py-2 border-b text-sm"
                onClick={async () => {
                  await api(`/api/notifications/${n.id}/read`, { method: "POST", token });
                  setNotes((prev) => prev.map((x) => (x.id === n.id ? { ...x, read: true } : x)));
                }}
              >
                <strong>{n.title}</strong>
                <div className="text-forest-700">{n.message}</div>
              </button>
            ))}
          </div>
        )}
        <nav className="dashboard-mobile-nav md:hidden">
          {items.map(([to, label]) => (
            <NavLink key={to} to={to} end={rootPaths.includes(to)} className={({ isActive }) => `dashboard-mobile-item ${isActive ? "is-active" : ""}`}><span>{label.slice(0, 1)}</span>{label}</NavLink>
          ))}
        </nav>
        <div className="p-4 md:p-6">{children}</div>
        <AssistantWidget />
      </div>
    </div>
  );
}
