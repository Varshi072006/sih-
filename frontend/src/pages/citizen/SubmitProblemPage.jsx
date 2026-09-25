import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import DashboardLayout from "../../layouts/DashboardLayout";
import MapPicker from "../../components/MapPicker";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../services/api";
import { ErrorBox, Field, inputClass } from "../../components/ui";

const nav = [["/citizen/dashboard", "Back to dashboard"], ["/citizen/problems/new", "Submit Problem"]];

const empty = {
  title: "", description: "", category: "Water Management", subcategory: "", expected_solution: "", affected_people_description: "",
  district: "Ranchi", block: "", village: "", address: "", latitude: null, longitude: null, location_source: "map_selection",
  estimated_affected_population: 0, severity: "medium", urgency: "medium", frequency: "", geographic_impact: "village",
  existing_solution: "", current_government_action: "",
};

export default function SubmitProblemPage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [form, setForm] = useState(empty);
  const [lookups, setLookups] = useState({ categories: {}, districts: [] });
  const [gpsFile, setGpsFile] = useState(null);
  const [extraFiles, setExtraFiles] = useState([]);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(null);
  useEffect(() => { api("/api/lookups").then(setLookups); }, []);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  async function submit() {
    setErr("");
    if (!gpsFile) { setErr("GPS/Location Image is required to help verify the reported problem."); return; }
    if (form.latitude == null || form.longitude == null) { setErr("Select a map location or use browser location."); return; }
    setBusy(true);
    try {
      const created = await api("/api/problems", { method: "POST", token, body: form });
      const fd = new FormData();
      fd.append("file", gpsFile);
      fd.append("evidence_type", "gps_location");
      fd.append("latitude", form.latitude);
      fd.append("longitude", form.longitude);
      fd.append("gps_from_image", "false");
      await api(`/api/problems/${created.public_id}/evidence`, { method: "POST", token, form: fd });
      for (const file of extraFiles) {
        const extra = new FormData();
        extra.append("file", file);
        extra.append("evidence_type", file.type.includes("pdf") ? "pdf" : file.type.includes("video") ? "video" : "additional_image");
        await api(`/api/problems/${created.public_id}/evidence`, { method: "POST", token, form: extra });
      }
      setDone(created);
    } catch (ex) { setErr(ex.message); }
    finally { setBusy(false); }
  }

  if (done) {
    return (
      <DashboardLayout title="Citizen Portal" items={nav}>
        <div className="bg-white border p-8 rounded max-w-xl">
          <h1 className="font-serif text-3xl mb-3">Problem Successfully Submitted</h1>
          <p>Problem ID: <strong>{done.public_id}</strong></p>
          <p>Current status: {done.status_label}</p>
          <p>Submission date: {done.submitted_at}</p>
          <Link className="inline-block mt-4 bg-forest-800 text-cream px-4 py-2 rounded" to={`/problem/${done.public_id}`}>Track problem</Link>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Submit Problem" items={nav}>
      <div className="citizen-intake-heading">
        <div>
          <p className="eyebrow text-forest-700">Citizen reporting desk</p>
          <h2 className="mt-1 font-serif text-3xl text-ink md:text-4xl">Turn a local concern into a tracked case.</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">Tell us what is happening, where it is happening and who is affected. Your report will be reviewed by the appropriate government department.</p>
        </div>
        <div className="intake-status"><span className="h-2 w-2 rounded-full bg-teal-500" />Autosaved locally</div>
      </div>
      <ol className="problem-stepper">
        {["Details", "Location", "Impact", "Evidence", "Review"].map((s, i) => (
          <li key={s} className={step === i + 1 ? "is-active" : step > i + 1 ? "is-complete" : ""}><span>{step > i + 1 ? "✓" : i + 1}</span>{s}</li>
        ))}
      </ol>
      <ErrorBox error={err} />
      {step === 1 && (
        <div className="citizen-step-grid">
        <div className="citizen-step-card">
          <div className="step-card-heading"><div><p className="eyebrow text-forest-700">Step 01 / Details</p><h3 className="mt-1 font-serif text-2xl text-ink">Describe the problem</h3></div><span className="step-card-number">01</span></div>
          <Field label="Problem Title"><input className={inputClass()} value={form.title} onChange={(e) => set("title", e.target.value)} required /></Field>
          <Field label="Problem Description"><textarea className={inputClass()} rows={5} value={form.description} onChange={(e) => set("description", e.target.value)} /></Field>
          <Field label="Category">
            <select className={inputClass()} value={form.category} onChange={(e) => set("category", e.target.value)}>
              {Object.keys(lookups.categories || {}).map((c) => <option key={c}>{c}</option>)}
            </select>
          </Field>
          <Field label="Subcategory">
            <select className={inputClass()} value={form.subcategory} onChange={(e) => set("subcategory", e.target.value)}>
              {(lookups.categories?.[form.category] || []).map((s) => <option key={s}>{s}</option>)}
            </select>
          </Field>
          <Field label="Expected Solution"><textarea className={inputClass()} value={form.expected_solution} onChange={(e) => set("expected_solution", e.target.value)} /></Field>
          <Field label="Description of affected people"><textarea className={inputClass()} value={form.affected_people_description} onChange={(e) => set("affected_people_description", e.target.value)} /></Field>
          <div className="step-card-footer"><span>Next: confirm the exact location</span><button className="cta-primary" type="button" onClick={() => { if (form.title.length < 8 || form.description.length < 20) setErr("Provide a complete title and description."); else { setErr(""); setStep(2); } }}>Continue <span aria-hidden="true">→</span></button></div>
        </div>
        <aside className="intake-help-card"><div className="help-icon">i</div><h3 className="mt-4 font-serif text-2xl text-ink">What makes a useful report?</h3><p className="mt-3 text-sm leading-6 text-slate-600">A specific title and a clear description help the department understand the situation quickly.</p><ul className="mt-5 space-y-3 text-sm text-slate-600"><li><strong>Be specific:</strong> mention the service, place or condition.</li><li><strong>Share impact:</strong> explain who is affected and how often.</li><li><strong>Stay factual:</strong> your location evidence comes in the next step.</li></ul></aside>
        </div>
      )}
      {step === 2 && (
        <div className="bg-white border p-6 rounded max-w-3xl space-y-3">
          <Field label="District">
            <select className={inputClass()} value={form.district} onChange={(e) => set("district", e.target.value)}>
              {(lookups.districts || []).map((d) => <option key={d}>{d}</option>)}
            </select>
          </Field>
          <Field label="Block/Mandal"><input className={inputClass()} value={form.block} onChange={(e) => set("block", e.target.value)} /></Field>
          <Field label="Village/Town/City"><input className={inputClass()} value={form.village} onChange={(e) => set("village", e.target.value)} /></Field>
          <Field label="Address"><input className={inputClass()} value={form.address} onChange={(e) => set("address", e.target.value)} /></Field>
          <MapPicker lat={form.latitude} lng={form.longitude} onChange={(lat, lng, source) => setForm((f) => ({ ...f, latitude: lat, longitude: lng, location_source: source }))} />
          <div className="flex gap-2">
            <button type="button" className="px-4 py-2 border rounded" onClick={() => setStep(1)}>Back</button>
            <button type="button" className="bg-forest-800 text-cream px-4 py-2 rounded" onClick={() => setStep(3)}>Continue</button>
          </div>
        </div>
      )}
      {step === 3 && (
        <div className="bg-white border p-6 rounded max-w-3xl">
          <Field label="Estimated affected population"><input type="number" className={inputClass()} value={form.estimated_affected_population} onChange={(e) => set("estimated_affected_population", Number(e.target.value))} /></Field>
          {["severity", "urgency"].map((k) => (
            <Field key={k} label={k}>
              <select className={inputClass()} value={form[k]} onChange={(e) => set(k, e.target.value)}>
                <option>low</option><option>medium</option><option>high</option><option>{k === "urgency" ? "immediate" : "critical"}</option>
              </select>
            </Field>
          ))}
          <Field label="Frequency"><input className={inputClass()} value={form.frequency} onChange={(e) => set("frequency", e.target.value)} /></Field>
          <Field label="Geographic impact">
            <select className={inputClass()} value={form.geographic_impact} onChange={(e) => set("geographic_impact", e.target.value)}>
              <option>household</option><option>village</option><option>block</option><option>district</option>
            </select>
          </Field>
          <Field label="Existing solution"><textarea className={inputClass()} value={form.existing_solution} onChange={(e) => set("existing_solution", e.target.value)} /></Field>
          <Field label="Current government action, if known"><textarea className={inputClass()} value={form.current_government_action} onChange={(e) => set("current_government_action", e.target.value)} /></Field>
          <div className="flex gap-2">
            <button type="button" className="px-4 py-2 border rounded" onClick={() => setStep(2)}>Back</button>
            <button type="button" className="bg-forest-800 text-cream px-4 py-2 rounded" onClick={() => setStep(4)}>Continue</button>
          </div>
        </div>
      )}
      {step === 4 && (
        <div className="bg-white border p-6 rounded max-w-3xl">
          <p className="mb-3 font-medium">GPS/Location Image is required to help verify the reported problem.</p>
          <Field label="GPS / Location Evidence Image — REQUIRED">
            <input type="file" accept="image/jpeg,image/png" onChange={(e) => setGpsFile(e.target.files[0])} />
          </Field>
          <Field label="Additional images, video, PDF or other documents">
            <input type="file" multiple accept=".jpg,.jpeg,.png,.mp4,.pdf,.doc,.docx" onChange={(e) => setExtraFiles([...e.target.files])} />
          </Field>
          <p className="text-sm">Map location is the authoritative location. This form does not claim EXIF GPS exists unless the image actually contains it.</p>
          <div className="flex gap-2 mt-4">
            <button type="button" className="px-4 py-2 border rounded" onClick={() => setStep(3)}>Back</button>
            <button type="button" className="bg-forest-800 text-cream px-4 py-2 rounded" onClick={() => { if (!gpsFile) setErr("GPS/Location Image is required to help verify the reported problem."); else { setErr(""); setStep(5); } }}>Continue</button>
          </div>
        </div>
      )}
      {step === 5 && (
        <div className="bg-white border p-6 rounded max-w-3xl space-y-2 text-sm">
          <h2 className="font-serif text-2xl">Review</h2>
          <p><strong>Title:</strong> {form.title}</p>
          <p>{form.description}</p>
          <p>{form.category} / {form.subcategory} · {form.district}</p>
          <p>Location {form.latitude}, {form.longitude} ({form.location_source})</p>
          <p>Population {form.estimated_affected_population} · {form.severity} / {form.urgency}</p>
          <p>GPS evidence: {gpsFile?.name}</p>
          <div className="flex flex-wrap gap-2 pt-3">
            <button type="button" className="border px-3 py-1 rounded" onClick={() => setStep(1)}>Edit Step 1</button>
            <button type="button" className="border px-3 py-1 rounded" onClick={() => setStep(2)}>Edit Step 2</button>
            <button type="button" className="border px-3 py-1 rounded" onClick={() => setStep(3)}>Edit Step 3</button>
            <button type="button" className="border px-3 py-1 rounded" onClick={() => setStep(4)}>Edit Step 4</button>
            <button type="button" disabled={busy} className="bg-clay text-white px-4 py-2 rounded" onClick={submit}>{busy ? "Submitting…" : "Submit Problem"}</button>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
