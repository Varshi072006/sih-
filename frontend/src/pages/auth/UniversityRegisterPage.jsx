import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { ErrorBox, Field, inputClass } from "../../components/ui";

export default function UniversityRegisterPage() {
  const [lookups, setLookups] = useState({ districts: [] });
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [form, setForm] = useState({
    name: "", institution_type: "University", official_id: "", address: "", district: "Ranchi", website: "",
    contact_person: "", email: "", phone: "", password: "", departments: "", faculty_expertise: "", research_areas: "",
    laboratories: "", innovation_centre: "", incubation_centre: "", previous_projects: "", technologies: "",
  });
  useEffect(() => { api("/api/lookups").then(setLookups); }, []);
  const requiredFields = ["name", "contact_person", "email", "phone", "password", "district", "departments", "faculty_expertise", "research_areas", "laboratories", "innovation_centre", "incubation_centre", "previous_projects", "technologies"];
  const labels = { name: "University name", institution_type: "Institution type", official_id: "Official ID", address: "Address", district: "District", website: "Website", contact_person: "Contact person", email: "Email", phone: "Phone", password: "Password", departments: "Departments", faculty_expertise: "Faculty expertise", research_areas: "Research areas", laboratories: "Laboratories", innovation_centre: "Innovation centre", incubation_centre: "Incubation centre", previous_projects: "Previous projects", technologies: "Technologies" };
  return (
    <div className="registration-page">
      <div className="registration-layout">
        <aside className="registration-intro registration-intro-university"><div className="auth-intro-mark">UNI</div><p className="eyebrow">Research partner network</p><h1 className="mt-4 font-serif text-4xl leading-tight text-white md:text-5xl">Bring knowledge into public action.</h1><p className="mt-5 text-sm leading-7 text-emerald-50/75">Connect your faculty, laboratories and student expertise with government-led problem solving across Jharkhand.</p><div className="registration-note"><strong>What happens next?</strong><span>Our administrators review your institutional details before enabling dashboard access.</span></div></aside>
        <main className="registration-form-wrap">
      <p className="eyebrow text-forest-700">Institutional onboarding</p><h2 className="mt-2 font-serif text-4xl text-ink">Register your university</h2>
      <p className="mt-3 mb-7 text-sm leading-6 text-slate-500">Status after submission: pending verification. Please provide accurate institutional information.</p>
      <ErrorBox error={err} />
      {msg && <p className="bg-emerald-50 p-3 mb-4">{msg}</p>}
      {!msg ? <form
        className="registration-form grid md:grid-cols-2 gap-3"
        onSubmit={async (e) => {
          e.preventDefault();
          setErr("");
          try {
            const res = await api("/api/auth/register/university", { method: "POST", body: form });
            setMsg(res.message);
          } catch (ex) { setErr(ex.message); }
        }}
      >
        {Object.keys(form).map((k) => (
          k === "district" ? (
            <Field key={k} label="District">
              <select className={inputClass()} required value={form.district} onChange={(e) => setForm({ ...form, district: e.target.value })}>
                {(lookups.districts || []).map((d) => <option key={d}>{d}</option>)}
              </select>
            </Field>
          ) : (
            <Field key={k} label={labels[k] || k.replaceAll("_", " ")}>
              <input className={inputClass()} type={k === "password" ? "password" : k === "email" ? "email" : "text"} required={requiredFields.includes(k)} placeholder={requiredFields.includes(k) ? "Required" : "Optional"} value={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} />
            </Field>
          )
        ))}
        <div className="registration-submit md:col-span-2"><span>Admin review required before dashboard access.</span><button className="cta-primary">Submit for verification <span aria-hidden="true">→</span></button></div>
      </form> : <div className="registration-success"><div className="success-mark">✓</div><p className="eyebrow text-forest-700">Request received</p><h3 className="mt-2 font-serif text-3xl text-ink">Your university is pending verification.</h3><p className="mt-3 text-sm leading-6 text-slate-600">{msg}</p><div className="success-next"><strong>What happens next</strong><span>1. An administrator reviews your institutional profile.</span><span>2. You receive approval before dashboard access is enabled.</span><span>3. Sign in using the email and password you registered.</span></div><a className="cta-primary mt-6" href="/login">Continue to login <span aria-hidden="true">→</span></a></div>}
        </main>
      </div>
    </div>
  );
}
