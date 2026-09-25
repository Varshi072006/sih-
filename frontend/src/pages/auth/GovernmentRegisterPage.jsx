import { useState } from "react";
import { api } from "../../services/api";
import { ErrorBox, Field, inputClass } from "../../components/ui";

export default function GovernmentRegisterPage() {
  const [form, setForm] = useState({ full_name: "", email: "", password: "", official_id: "", designation: "", department_code: "WRD", district: "Ranchi", jurisdiction: "", mobile: "" });
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  return (
    <div className="registration-page">
      <div className="registration-layout registration-layout-government">
        <aside className="registration-intro registration-intro-government"><div className="auth-intro-mark">GOV</div><p className="eyebrow">Official access request</p><h1 className="mt-4 font-serif text-4xl leading-tight text-white md:text-5xl">Coordinate action where it matters.</h1><p className="mt-5 text-sm leading-7 text-emerald-50/75">Request an official account to review citizen problems, coordinate departments and publish accountable progress.</p><div className="registration-note"><strong>Secure by design</strong><span>Unverified officers cannot access the government portal. An administrator must approve this request.</span></div></aside>
        <main className="registration-form-wrap">
      <p className="eyebrow text-forest-700">Official onboarding</p><h1 className="mt-2 font-serif text-4xl text-ink">Request government access</h1><p className="mt-3 mb-7 text-sm leading-6 text-slate-500">Use your official identity and jurisdiction details. Your account remains pending until verified.</p>
      <ErrorBox error={err} />
      {msg && <p className="bg-emerald-50 p-3">{msg}</p>}
      <form className="registration-form" onSubmit={async (e) => {
        e.preventDefault();
        try { setMsg((await api("/api/auth/register/government", { method: "POST", body: form })).message); }
        catch (ex) { setErr(ex.message); }
      }}>
        {Object.keys(form).map((k) => (
          <Field key={k} label={k.replaceAll("_"," ")}>
            <input className={inputClass()} type={k==="password"?"password":"text"} required={["full_name","email","password","official_id"].includes(k)} value={form[k]} onChange={(e)=>setForm({...form,[k]:e.target.value})} />
          </Field>
        ))}
        <div className="registration-submit"><span>Verification is required before portal access.</span><button className="cta-primary">Request official verification <span aria-hidden="true">→</span></button></div>
      </form>
        </main>
      </div>
    </div>
  );
}
