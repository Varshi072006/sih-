import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import logo from "../assets/c2i-logo.svg";
import AssistantWidget from "../components/AssistantWidget";

const links = [
  ["/", "Home"],
  ["/problems", "Problems"],
  ["/universities", "Universities"],
  ["/industry", "Industry"],
  ["/projects", "Projects"],
  ["/impact", "Impact"],
  ["/how-it-works", "How It Works"],
];

export default function PublicLayout({ children }) {
  const { user, dashboardPath, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col">
      <a className="skip-link" href="#main">Skip to content</a>
      <header className="bg-forest-950 text-cream">
        <div className="section-shell flex justify-between items-center py-2 text-[11px] uppercase tracking-[0.22em] text-cream/70">
          <span>Government of Jharkhand</span>
          <span>AI decision-support platform</span>
        </div>
        <div className="border-t border-white/10 bg-forest-900/90 backdrop-blur-sm">
          <div className="section-shell flex flex-wrap items-center justify-between gap-4 py-4">
            <Link to="/" className="flex items-center gap-3">
              <img src={logo} alt="Challenge to Impact logo" className="h-12 w-12 rounded-xl shadow-lg shadow-emerald-900/30" />
              <div>
                <div className="font-serif text-xl md:text-2xl leading-tight text-white">Challenge to Impact</div>
                <div className="text-[11px] uppercase tracking-[0.2em] text-emerald-100/70">Civic innovation network</div>
              </div>
            </Link>
            <nav className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm font-medium" aria-label="Primary navigation">
              {links.map(([to, label]) => (
                <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => `transition ${isActive ? "text-gold" : "text-cream/80 hover:text-gold"}`}>
                  {label}
                </NavLink>
              ))}
              {user ? (
                <>
                  <NavLink to={dashboardPath()} className="text-cream/80 hover:text-gold">Dashboard</NavLink>
                  <button type="button" onClick={() => { logout(); navigate("/"); }} className="rounded-full border border-white/15 px-3 py-1.5 text-sm hover:border-gold hover:text-gold">
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <NavLink to="/login" className="text-cream/80 hover:text-gold">Login</NavLink>
                  <NavLink to="/register" className="rounded-full bg-gradient-to-r from-clay to-[#f29d5a] px-4 py-2 text-white shadow-lg shadow-orange-900/20">Register</NavLink>
                </>
              )}
            </nav>
          </div>
        </div>
      </header>
      <main id="main" className="flex-1">{children}</main>
      <footer className="mt-16 border-t border-slate-200 bg-forest-950 text-cream/80">
        <div className="section-shell grid gap-6 py-10 md:grid-cols-3">
          <p>Challenge to Impact connects citizens, government, universities and industry around verified public-interest problems in Jharkhand.</p>
          <p>Government remains the official problem owner, while universities and industry contribute expertise, technology and implementation support.</p>
          <p>Demo records are labelled <strong className="text-gold">DEMO DATA</strong> and are not official government actions.</p>
        </div>
      </footer>
      <AssistantWidget />
    </div>
  );
}
