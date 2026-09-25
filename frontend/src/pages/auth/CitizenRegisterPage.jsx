import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../services/api";
import { useAuth } from "../../context/AuthContext";
import { ErrorBox, Field, inputClass } from "../../components/ui";

export default function CitizenRegisterPage() {
  const [lookups, setLookups] = useState({ districts: [] });
  const [form, setForm] = useState({ full_name: "", email: "", mobile: "", password: "", confirm_password: "", district: "Ranchi", block: "", village: "", address: "", aadhaar: "" });
  const [err, setErr] = useState("");
  const [step, setStep] = useState("form");
  const { login } = useAuth();
  const navigate = useNavigate();
  useEffect(() => { api("/api/lookups").then(setLookups); }, []);
  const set = (k, v) => setForm({ ...form, [k]: v });
  const labels = { full_name: "Full name", email: "Email address", mobile: "Mobile number", password: "Password", confirm_password: "Confirm password", block: "Block", village: "Village / locality", address: "Address" };
  return (
    <div className="auth-page">
      <div className="auth-layout">
        <aside className="auth-intro">
          <div className="auth-intro-mark">C2I</div>
          <p className="eyebrow">Join the civic network</p>
          <h1 className="mt-4 font-serif text-4xl leading-tight text-white md:text-5xl">Make your local problem visible.</h1>
          <p className="mt-5 max-w-md text-sm leading-7 text-emerald-50/75">Create a citizen account to report issues, follow government action and contribute feedback as solutions move toward impact.</p>
          <div className="mt-10 space-y-5">{["Report a problem with location evidence", "Track verification and official updates", "Help measure what changed locally"].map((item, index) => <div className="flex items-start gap-3" key={item}><span className="auth-step">0{index + 1}</span><span className="pt-1 text-sm text-emerald-50/80">{item}</span></div>)}</div>
        </aside>
        <main className="auth-form-wrap">
          <div className="mb-8"><p className="eyebrow text-forest-700">Citizen account</p><h2 className="mt-2 font-serif text-4xl text-ink">Create your account</h2><p className="mt-3 text-sm leading-6 text-slate-500">A few details help us connect your reports to the right locality.</p></div>
      <ErrorBox error={err} />
      {step === "form" && (
        <form
          className="auth-form"
          onSubmit={async (e) => {
            e.preventDefault();
            setErr("");
            try {
              await api("/api/auth/register/citizen", { method: "POST", body: form });
              setStep("verify");
            } catch (ex) { setErr(ex.message); }
          }}
        >
          <div className="form-section-title"><span>01</span><div><strong>Account details</strong><small>How we can reach you</small></div></div>
          <div className="grid gap-x-4 md:grid-cols-2">
          {["full_name", "email", "mobile", "password", "confirm_password"].map((k) => (
            <Field key={k} label={labels[k]}>
              <input className={inputClass()} type={k.includes("password") ? "password" : k === "email" ? "email" : "text"} required={["full_name","email","mobile","password","confirm_password","district"].includes(k)} value={form[k]} onChange={(e) => set(k, e.target.value)} />
            </Field>
          ))}
          </div>
          <div className="form-section-title mt-5"><span>02</span><div><strong>Your locality</strong><small>Where you are reporting from</small></div></div>
          <div className="grid gap-x-4 md:grid-cols-2">
          {["block", "village"].map((k) => (
            <Field key={k} label={labels[k]}><input className={inputClass()} type="text" value={form[k]} onChange={(e) => set(k, e.target.value)} /></Field>
          ))}
          <Field label="District">
            <select className={inputClass()} value={form.district} onChange={(e) => set("district", e.target.value)}>
              {(lookups.districts || []).map((d) => <option key={d}>{d}</option>)}
            </select>
          </Field>
          </div>
          <Field label={labels.address}><input className={inputClass()} type="text" value={form.address} onChange={(e) => set("address", e.target.value)} /></Field>
          <div className="form-section-title mt-5"><span>03</span><div><strong>Identity</strong><small>Aadhaar number for verification</small></div></div>
          <Field label="Aadhaar number">
            <input
              className={inputClass()}
              type="text"
              inputMode="numeric"
              maxLength={14}
              placeholder="XXXX XXXX XXXX"
              value={form.aadhaar}
              onChange={(e) => {
                const digits = e.target.value.replace(/\D/g, "").slice(0, 12);
                set("aadhaar", digits.replace(/(\d{4})(?=\d)/g, "$1 "));
              }}
            />
          </Field>
          <button className="cta-primary mt-3 w-full">Create citizen account <span aria-hidden="true">→</span></button>
          <p className="mt-4 text-center text-xs leading-5 text-slate-500">By continuing, you agree to provide accurate information for public-interest reporting.</p>
        </form>
      )}
      {step === "verify" && (
        <form
          className="auth-form"
          onSubmit={async (e) => {
            e.preventDefault();
            const code = e.target.code.value;
            try {
              await api("/api/auth/verify", { method: "POST", body: { email: form.email, code } });
              await login(form.email, form.password);
              navigate("/citizen/dashboard");
            } catch (ex) { setErr(ex.message); }
          }}
        >
          <div className="form-section-title"><span>03</span><div><strong>Verify your email</strong><small>One last step before you begin</small></div></div>
          <p className="mb-5 rounded-xl bg-emerald-50 p-4 text-sm leading-6 text-forest-800">Enter the verification code sent to <strong>{form.email}</strong>. In this development environment use <strong>123456</strong>.</p>
          <Field label="Verification code"><input name="code" className={inputClass()} required /></Field>
          <button className="cta-primary mt-3 w-full">Activate account <span aria-hidden="true">→</span></button>
        </form>
      )}
        </main>
      </div>
    </div>
  );
}
