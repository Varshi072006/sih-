import { useEffect, useRef, useState } from "react";
import { api } from "../../services/api";
import { ErrorBox, Field, inputClass } from "../../components/ui";

// ── Searchable dropdown ──────────────────────────────────────────────────────
function SearchableSelect({ options, value, onChange, placeholder, disabled }) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  const selected = options.find((o) => o.id === value);
  const filtered = query
    ? options.filter((o) => o.name.toLowerCase().includes(query.toLowerCase()))
    : options;

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        disabled={disabled}
        onClick={() => { setOpen((o) => !o); setQuery(""); }}
        className={`${inputClass()} flex items-center justify-between text-left w-full ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
      >
        <span className={selected ? "" : "text-slate-400"}>{selected ? selected.name : placeholder}</span>
        <span className="ml-2 text-slate-400">▾</span>
      </button>
      {open && (
        <div className="absolute z-50 mt-1 w-full rounded-xl border border-slate-200 bg-white shadow-lg">
          <div className="p-2 border-b border-slate-100">
            <input
              autoFocus
              className="w-full rounded-lg border border-slate-200 px-3 py-1.5 text-sm outline-none focus:border-forest-600"
              placeholder="Search..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <ul className="max-h-56 overflow-y-auto py-1">
            {filtered.length === 0 && <li className="px-4 py-2 text-sm text-slate-400">No results</li>}
            {filtered.map((o) => (
              <li
                key={o.id}
                className={`cursor-pointer px-4 py-2 text-sm hover:bg-emerald-50 ${o.id === value ? "bg-emerald-50 font-medium text-forest-700" : ""}`}
                onMouseDown={() => { onChange(o.id); setOpen(false); setQuery(""); }}
              >
                {o.name}
                {o.district && <span className="ml-2 text-xs text-slate-400">{o.district}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// ── Main page ────────────────────────────────────────────────────────────────
export default function UniversityRegisterPage() {
  const [lookups, setLookups] = useState({ districts: [] });
  const [states, setStates] = useState([]);
  const [institutions, setInstitutions] = useState([]);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  // step: "state" | "institution" | "form"
  const [step, setStep] = useState("state");
  const [selectedStateId, setSelectedStateId] = useState(null);
  const [selectedInstitutionId, setSelectedInstitutionId] = useState(null);
  const [isOther, setIsOther] = useState(false);

  const [form, setForm] = useState({
    name: "", institution_type: "University", official_id: "", address: "", district: "Ranchi", website: "",
    contact_person: "", email: "", phone: "", password: "", departments: "", faculty_expertise: "",
    research_areas: "", laboratories: "", innovation_centre: "", incubation_centre: "",
    previous_projects: "", technologies: "",
  });

  useEffect(() => {
    api("/api/lookups").then(setLookups);
    api("/api/states").then(setStates);
  }, []);

  // Load institutions when state is selected
  useEffect(() => {
    if (!selectedStateId) return;
    setLoading(true);
    api(`/api/states/${selectedStateId}/universities`)
      .then(setInstitutions)
      .finally(() => setLoading(false));
  }, [selectedStateId]);

  // Pre-fill form when a catalog institution is selected
  useEffect(() => {
    if (!selectedInstitutionId || !institutions.length) return;
    const inst = institutions.find((i) => i.id === selectedInstitutionId);
    if (!inst) return;
    const other = inst.short_name === "OTHER";
    setIsOther(other);
    if (!other) {
      setForm((f) => ({
        ...f,
        name: inst.name,
        institution_type: inst.institution_type || "University",
        district: inst.district || f.district,
        website: inst.official_website || f.website,
      }));
    } else {
      setForm((f) => ({ ...f, name: "", institution_type: "University", district: "Ranchi", website: "" }));
    }
  }, [selectedInstitutionId, institutions]);

  const requiredFields = ["name", "contact_person", "email", "phone", "password", "district", "departments", "faculty_expertise", "research_areas", "laboratories", "innovation_centre", "incubation_centre", "previous_projects", "technologies"];
  const labels = { name: "University / institution name", institution_type: "Institution type", official_id: "Official ID / recognition number", address: "Address", district: "District", website: "Official website", contact_person: "Contact person", email: "Official email", phone: "Phone", password: "Password", departments: "Departments (comma-separated)", faculty_expertise: "Faculty expertise", research_areas: "Research areas", laboratories: "Laboratories", innovation_centre: "Innovation centre", incubation_centre: "Incubation centre", previous_projects: "Previous projects", technologies: "Technologies" };

  const selectedState = states.find((s) => s.id === selectedStateId);
  const selectedInstitution = institutions.find((i) => i.id === selectedInstitutionId);

  return (
    <div className="registration-page">
      <div className="registration-layout">
        <aside className="registration-intro registration-intro-university">
          <div className="auth-intro-mark">UNI</div>
          <p className="eyebrow">Research partner network</p>
          <h1 className="mt-4 font-serif text-4xl leading-tight text-white md:text-5xl">Bring knowledge into public action.</h1>
          <p className="mt-5 text-sm leading-7 text-emerald-50/75">Connect your faculty, laboratories and student expertise with government-led problem solving across Jharkhand.</p>
          <div className="registration-note"><strong>What happens next?</strong><span>Our administrators review your institutional details before enabling dashboard access.</span></div>
        </aside>

        <main className="registration-form-wrap">
          <p className="eyebrow text-forest-700">Institutional onboarding</p>
          <h2 className="mt-2 font-serif text-4xl text-ink">Register your university</h2>
          <p className="mt-3 mb-7 text-sm leading-6 text-slate-500">Status after submission: pending verification. Please provide accurate institutional information.</p>

          <ErrorBox error={err} />
          {msg && <p className="bg-emerald-50 p-3 mb-4">{msg}</p>}

          {/* ── STEP 1: State selection ── */}
          {!msg && step === "state" && (
            <div className="registration-form">
              <div className="form-section-title"><span>01</span><div><strong>Select your state</strong><small>Choose the state where your institution is located</small></div></div>
              <Field label="State *">
                <SearchableSelect
                  options={states}
                  value={selectedStateId}
                  onChange={setSelectedStateId}
                  placeholder="Select State..."
                />
              </Field>
              <button
                type="button"
                className="cta-primary mt-5 w-full"
                disabled={!selectedStateId}
                onClick={() => { setErr(""); setStep("institution"); }}
              >
                Continue <span aria-hidden="true">→</span>
              </button>
            </div>
          )}

          {/* ── STEP 2: Institution selection ── */}
          {!msg && step === "institution" && (
            <div className="registration-form">
              <div className="form-section-title"><span>02</span><div><strong>Select your institution</strong><small>{selectedState?.name} — choose from the list or select Other</small></div></div>
              {loading ? (
                <p className="text-sm text-slate-500 py-4">Loading institutions…</p>
              ) : (
                <Field label="University / Institution *">
                  <SearchableSelect
                    options={institutions}
                    value={selectedInstitutionId}
                    onChange={setSelectedInstitutionId}
                    placeholder="Search and select institution..."
                  />
                </Field>
              )}
              {selectedInstitution && !isOther && (
                <div className="mt-3 rounded-xl bg-emerald-50 px-4 py-3 text-sm text-forest-800">
                  <strong>{selectedInstitution.name}</strong>
                  {selectedInstitution.district && <span className="ml-2 text-slate-500">· {selectedInstitution.district}</span>}
                  <span className="ml-2 text-slate-500">· {selectedInstitution.institution_type}</span>
                  <p className="mt-1 text-xs text-amber-700">Note: selecting a listed institution does not automatically verify your account. Admin review is required.</p>
                </div>
              )}
              {isOther && (
                <div className="mt-3 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800">
                  Your institution will be marked <strong>Pending Institutional Verification</strong>. Please provide full details in the next step.
                </div>
              )}
              <div className="mt-5 flex gap-3">
                <button type="button" className="cta-secondary flex-1" onClick={() => { setStep("state"); setSelectedInstitutionId(null); setIsOther(false); }}>
                  ← Back
                </button>
                <button
                  type="button"
                  className="cta-primary flex-1"
                  disabled={!selectedInstitutionId}
                  onClick={() => { setErr(""); setStep("form"); }}
                >
                  Continue <span aria-hidden="true">→</span>
                </button>
              </div>
            </div>
          )}

          {/* ── STEP 3: Existing registration form ── */}
          {!msg && step === "form" && (
            <form
              className="registration-form grid md:grid-cols-2 gap-3"
              onSubmit={async (e) => {
                e.preventDefault();
                setErr("");
                try {
                  const res = await api("/api/auth/register/university", {
                    method: "POST",
                    body: {
                      ...form,
                      state_id: selectedStateId,
                      institution_catalog_id: isOther ? null : selectedInstitutionId,
                    },
                  });
                  setMsg(res.message);
                } catch (ex) { setErr(ex.message); }
              }}
            >
              <div className="md:col-span-2 mb-1 flex items-center gap-3 text-sm text-slate-500">
                <span className="rounded-full bg-emerald-100 px-3 py-0.5 text-xs font-medium text-forest-700">{selectedState?.name}</span>
                <span className="rounded-full bg-slate-100 px-3 py-0.5 text-xs">{selectedInstitution?.name}</span>
                <button type="button" className="ml-auto text-xs underline text-slate-400 hover:text-slate-600" onClick={() => setStep("institution")}>Change</button>
              </div>

              {Object.keys(form).map((k) => (
                k === "district" ? (
                  <Field key={k} label="District">
                    <select className={inputClass()} required value={form.district} onChange={(e) => setForm({ ...form, district: e.target.value })}>
                      {(lookups.districts || []).map((d) => <option key={d}>{d}</option>)}
                    </select>
                  </Field>
                ) : (
                  <Field key={k} label={labels[k] || k.replaceAll("_", " ")}>
                    <input
                      className={inputClass()}
                      type={k === "password" ? "password" : k === "email" ? "email" : "text"}
                      required={requiredFields.includes(k)}
                      placeholder={requiredFields.includes(k) ? "Required" : "Optional"}
                      value={form[k]}
                      onChange={(e) => setForm({ ...form, [k]: e.target.value })}
                    />
                  </Field>
                )
              ))}

              <div className="registration-submit md:col-span-2">
                <span>Admin review required before dashboard access.</span>
                <div className="flex gap-3">
                  <button type="button" className="cta-secondary" onClick={() => setStep("institution")}>← Back</button>
                  <button className="cta-primary">Submit for verification <span aria-hidden="true">→</span></button>
                </div>
              </div>
            </form>
          )}

          {msg && (
            <div className="registration-success">
              <div className="success-mark">✓</div>
              <p className="eyebrow text-forest-700">Request received</p>
              <h3 className="mt-2 font-serif text-3xl text-ink">Your university is pending verification.</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">{msg}</p>
              <div className="success-next">
                <strong>What happens next</strong>
                <span>1. An administrator reviews your institutional profile.</span>
                <span>2. You receive approval before dashboard access is enabled.</span>
                <span>3. Sign in using the email and password you registered.</span>
              </div>
              <a className="cta-primary mt-6" href="/login">Continue to login <span aria-hidden="true">→</span></a>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
