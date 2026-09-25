import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { ErrorBox, Field, inputClass } from "../../components/ui";

export default function IndustryRegisterPage() {
  const [lookups, setLookups] = useState({ districts: [] });
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [form, setForm] = useState({
    company_name: "", organization_type: "industry", sector: "", registration_details: "", website: "", address: "",
    district: "Ranchi", contact_person: "", email: "", phone: "", password: "", technical_expertise: "", products_services: "",
    technologies: "", csr_areas: "", funding_capability: false, mentorship_capability: false, prototype_capability: false,
    testing_capability: false, deployment_capability: false,
  });
  useEffect(() => { api("/api/lookups").then(setLookups); }, []);
  return (
    <div className="registration-page">
      <div className="registration-layout">
        <aside className="registration-intro registration-intro-industry"><div className="auth-intro-mark">IND</div><p className="eyebrow">Delivery partner network</p><h1 className="mt-4 font-serif text-4xl leading-tight text-white md:text-5xl">Turn capability into community impact.</h1><p className="mt-5 text-sm leading-7 text-emerald-50/75">Tell us how your company can contribute technology, mentoring, funding, prototyping or deployment.</p><div className="registration-note"><strong>Built for collaboration</strong><span>Verified partners can respond to government-led opportunities after a solution is ready for participation.</span></div></aside>
        <main className="registration-form-wrap">
      <p className="eyebrow text-forest-700">Partner onboarding</p><h1 className="mt-2 font-serif text-4xl text-ink">Register your organization</h1><p className="mt-3 mb-7 text-sm leading-6 text-slate-500">Share your organization profile and delivery capabilities for administrator verification.</p>
      <ErrorBox error={err} />
      {msg && <p className="bg-emerald-50 p-3 mb-4">{msg}</p>}
      <form className="registration-form grid md:grid-cols-2 gap-3" onSubmit={async (e) => {
        e.preventDefault();
        try { setMsg((await api("/api/auth/register/industry", { method: "POST", body: form })).message); }
        catch (ex) { setErr(ex.message); }
      }}>
        {["company_name","sector","registration_details","website","address","contact_person","email","phone","password","technical_expertise","products_services","technologies","csr_areas"].map((k) => (
          <Field key={k} label={k.replaceAll("_"," ")}>
            <input className={inputClass()} type={k==="password"?"password":"text"} required={["company_name","contact_person","email","phone","password"].includes(k)} value={form[k]} onChange={(e)=>setForm({...form,[k]:e.target.value})} />
          </Field>
        ))}
        <Field label="Organization type">
          <select className={inputClass()} value={form.organization_type} onChange={(e)=>setForm({...form, organization_type:e.target.value})}>
            <option value="industry">Industry</option>
            <option value="startup">Startup</option>
            <option value="msme">MSME</option>
            <option value="csr">CSR Organization</option>
          </select>
        </Field>
        <Field label="District">
          <select className={inputClass()} value={form.district} onChange={(e)=>setForm({...form, district:e.target.value})}>
            {(lookups.districts||[]).map((d)=><option key={d}>{d}</option>)}
          </select>
        </Field>
        {["funding_capability","mentorship_capability","prototype_capability","testing_capability","deployment_capability"].map((k)=>(
          <label key={k} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form[k]} onChange={(e)=>setForm({...form,[k]:e.target.checked})} />{k.replaceAll("_"," ")}</label>
        ))}
        <div className="registration-submit md:col-span-2"><span>Admin review keeps the partner directory trusted.</span><button className="cta-primary">Submit for verification <span aria-hidden="true">→</span></button></div>
      </form>
        </main>
      </div>
    </div>
  );
}
