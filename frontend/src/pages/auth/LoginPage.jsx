import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { ErrorBox, Field, inputClass } from "../../components/ui";

const PORTALS = [
  { path: "/login/citizen", roleHint: "citizen", label: "Citizen" },
  { path: "/university/login", roleHint: "university", label: "University" },
  { path: "/industry/login", roleHint: "industry", label: "Industry" },
  { path: "/government/login", roleHint: "government", label: "Government" },
  { path: "/admin/login", roleHint: "admin", label: "Admin" },
];

const DEMO_ACCOUNTS = {
  university: [
    ["Demo University 1", "university@demo.in"],
    ["Demo Research University", "research@demo.in"],
  ],
  industry: [
    ["Demo IoT Solutions", "iot@demo.in"],
    ["Demo Mobility Systems", "mobility@demo.in"],
  ],
  government: [
    ["Demo Government Officer", "gov@demo.in"],
  ],
  admin: [
    ["Demo Admin", "admin@c2i.jharkhand.gov.in"],
    ["Demo Super Admin", "superadmin@c2i.jharkhand.gov.in"],
  ],
};

export default function LoginPage({ title = "Login", expected }) {
  const { login, dashboardPath } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const activePortal = expected || "citizen";

  return (
    <div className="relative overflow-hidden bg-[#edf6f1] py-10 md:py-16">
      <div className="pointer-events-none absolute -right-24 top-8 h-72 w-72 rounded-full bg-gold/20 blur-3xl" />
      <div className="pointer-events-none absolute -left-24 bottom-0 h-80 w-80 rounded-full bg-teal-500/10 blur-3xl" />

      <div className="section-shell relative">
        <div className="mb-8 flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-forest-600">Secure access</p>
            <p className="mt-2 text-sm text-slate-500">One network. Different roles. Shared public impact.</p>
          </div>
          <Link to="/" className="hidden rounded-full border border-forest-700/20 bg-white/70 px-4 py-2 text-sm font-medium text-forest-800 transition hover:bg-white md:inline-flex">
            Back to platform
          </Link>
        </div>

        <div className="grid overflow-hidden rounded-[30px] border border-white/80 bg-white/75 shadow-soft backdrop-blur-sm lg:grid-cols-[0.9fr_1.1fr]">
          <aside className="relative overflow-hidden bg-forest-950 px-6 py-8 text-white md:px-10 md:py-10 lg:min-h-[650px]">
            <div className="absolute -right-24 -top-20 h-64 w-64 rounded-full border-[36px] border-gold/20" />
            <div className="absolute -bottom-28 -left-20 h-72 w-72 rounded-full border-[46px] border-teal-500/10" />
            <div className="relative flex h-full flex-col">
              <div className="flex items-center gap-3">
                <div className="grid h-11 w-11 place-items-center rounded-2xl bg-gold font-serif text-xl font-bold text-forest-950">CI</div>
                <div>
                  <p className="font-serif text-xl">Challenge to Impact</p>
                  <p className="text-[10px] uppercase tracking-[0.2em] text-emerald-100/60">Civic innovation network</p>
                </div>
              </div>
              <div className="mt-16 max-w-md">
                <p className="text-xs font-semibold uppercase tracking-[0.25em] text-gold">Welcome back</p>
                <h1 className="mt-4 font-serif text-4xl leading-tight md:text-5xl">Good work starts with the right people in the room.</h1>
                <p className="mt-5 text-base leading-7 text-emerald-50/75">Access your workspace to review challenges, coordinate solutions, and help move public ideas from evidence to action.</p>
              </div>
              <div className="mt-auto hidden gap-3 pt-12 sm:flex">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-2xl font-serif text-gold">24/7</p>
                  <p className="mt-1 text-xs text-emerald-50/60">Transparent workflow</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-2xl font-serif text-gold">4</p>
                  <p className="mt-1 text-xs text-emerald-50/60">Connected communities</p>
                </div>
              </div>
            </div>
          </aside>

          <section className="px-6 py-8 md:px-10 md:py-10">
            <div className="max-w-xl">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.25em] text-forest-600">Workspace login</p>
                  <h2 className="mt-2 font-serif text-4xl text-forest-950">{title}</h2>
                  <p className="mt-3 max-w-md text-sm leading-6 text-slate-500">Use your registered email. Access is enforced by the server according to role and verification status.</p>
                </div>
                <span className="hidden rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 sm:inline-flex">Encrypted access</span>
              </div>

              <div className="mt-8">
                <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Choose your workspace</p>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
                  {PORTALS.map((p) => (
                    <Link
                      key={p.path}
                      to={p.path}
                      className={`rounded-xl border px-3 py-3 text-center text-xs font-semibold transition ${activePortal === p.roleHint ? "border-forest-700 bg-forest-800 text-white shadow-md" : "border-slate-200 bg-slate-50 text-slate-600 hover:border-forest-300 hover:bg-emerald-50 hover:text-forest-800"}`}
                    >
                      <span className="mx-auto mb-2 grid h-7 w-7 place-items-center rounded-lg bg-white/80 text-[11px] font-bold text-forest-700">{p.label.slice(0, 1)}</span>
                      {p.label}
                    </Link>
                  ))}
                </div>
              </div>

              <div className="mt-8">
                <ErrorBox error={err} />
                {DEMO_ACCOUNTS[activePortal] && (
                  <div className="demo-login-panel mb-6">
                    <div><p className="eyebrow text-forest-700">Demo access</p><p className="mt-1 text-sm font-semibold text-forest-900">Try a verified {activePortal} workspace</p><p className="mt-1 text-xs leading-5 text-slate-500">Development credentials only. Password: <strong>Demo@1234</strong></p></div>
                    <div className="mt-3 grid gap-2 sm:grid-cols-2">
                      {DEMO_ACCOUNTS[activePortal].map(([name, accountEmail]) => <button key={accountEmail} type="button" className="demo-login-option" onClick={() => { setEmail(accountEmail); setPassword("Demo@1234"); setErr(""); }}><span>{name}</span><small>{accountEmail}</small></button>)}
                    </div>
                  </div>
                )}
                <form
                  onSubmit={async (e) => {
                    e.preventDefault();
                    setBusy(true);
                    setErr("");
                    try {
                      const data = await login(email, password);
                      if (expected && !String(data.role).includes(expected) && !["admin", "super_admin"].includes(data.role) && expected !== "government") {
                        if (expected === "government" && !["government_officer", "government_department", "admin", "super_admin"].includes(data.role)) {
                          setErr("This portal is for verified government officers.");
                          return;
                        }
                      }
                      const role = data.role;
                      const dest =
                        ["admin", "super_admin"].includes(role) ? "/admin/dashboard" :
                        ["government_officer", "government_department"].includes(role) ? "/government/dashboard" :
                        ["university", "faculty", "student"].includes(role) ? "/university/dashboard" :
                        ["industry", "startup", "msme", "csr"].includes(role) ? "/industry/dashboard" :
                        "/citizen/dashboard";
                      navigate(dest);
                    } catch (ex) {
                      setErr(ex.message);
                    } finally {
                      setBusy(false);
                    }
                  }}
                  className="space-y-5"
                >
                  <Field label="Email / official ID">
                    <input className={`${inputClass()} mt-1 h-12 rounded-xl border-slate-200 bg-slate-50 px-4 transition focus:border-forest-500 focus:bg-white`} type="email" required value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" placeholder="you@example.gov.in" />
                  </Field>
                  <Field label="Password">
                    <div className="relative mt-1">
                      <input className={`${inputClass()} h-12 rounded-xl border-slate-200 bg-slate-50 px-4 pr-20 transition focus:border-forest-500 focus:bg-white`} type={showPassword ? "text" : "password"} required value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" placeholder="Enter your password" />
                      <button type="button" onClick={() => setShowPassword((value) => !value)} className="absolute inset-y-0 right-3 text-xs font-semibold text-forest-700 hover:text-clay" aria-label={showPassword ? "Hide password" : "Show password"}>
                        {showPassword ? "Hide" : "Show"}
                      </button>
                    </div>
                  </Field>
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span className="inline-flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-emerald-500" /> Server-verified access</span>
                    <span>Protected session</span>
                  </div>
                  <button disabled={busy} className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-forest-800 font-semibold text-white shadow-lg shadow-forest-900/15 transition hover:-translate-y-0.5 hover:bg-forest-700 disabled:cursor-wait disabled:opacity-70">
                    {busy ? "Signing in…" : "Sign in to workspace"}
                    {!busy && <span aria-hidden="true">→</span>}
                  </button>
                </form>
              </div>

              <p className="mt-7 text-center text-sm text-slate-500">New to the network? <Link className="font-semibold text-forest-700 hover:text-clay" to="/register">Create an account</Link></p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
