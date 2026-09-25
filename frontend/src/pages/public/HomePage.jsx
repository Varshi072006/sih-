import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../services/api";
import ImpactNetwork from "../../components/ImpactNetwork";

const steps = [
  "Submit Problem",
  "Verify Problem",
  "Government Resolution",
  "AI University Recommendation",
  "University Review",
  "Government Decision",
  "Industry Collaboration",
  "Prototype/Pilot",
  "Deployment",
  "Impact Measurement",
];

const fallbackStats = {
  problems_submitted: 184,
  problems_verified: 96,
  universities_participating: 28,
  industry_partners: 17,
  active_projects: 12,
  solutions_deployed: 34,
  people_impacted: 86000,
};

export default function HomePage() {
  const [stats, setStats] = useState(fallbackStats);
  const [err, setErr] = useState("");

  useEffect(() => {
    api("/api/stats")
      .then((data) => setStats(data))
      .catch((e) => {
        setErr(e?.message || "Live stats unavailable right now.");
        setStats(fallbackStats);
      });
  }, []);

  const cards = [
    ["Problems Submitted", stats.problems_submitted],
    ["Problems Verified", stats.problems_verified],
    ["Universities Participating", stats.universities_participating],
    ["Industry Partners", stats.industry_partners],
    ["Active Projects", stats.active_projects],
    ["Solutions Deployed", stats.solutions_deployed],
    ["People Impacted", stats.people_impacted],
  ];

  return (
    <div className="pb-16">
      <section className="hero-grid text-cream">
        <div className="section-shell grid gap-8 py-20 md:py-24 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
          <div>
            <p className="mb-4 inline-flex rounded-full border border-gold/40 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.25em] text-gold">Jharkhand · Civic innovation</p>
            <h1 className="max-w-2xl font-serif text-4xl leading-tight md:text-6xl">Turning community challenges into measurable public impact.</h1>
            <p className="mt-5 max-w-xl text-lg text-cream/85 md:text-xl">Challenge to Impact connects citizens, government, universities and industry to resolve grassroots problems with data-informed, accountable action.</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link className="cta-primary" to="/citizen/problems/new">Submit a Problem</Link>
              <Link className="cta-secondary" to="/problems">Explore Problems</Link>
            </div>
            <div className="mt-8 flex flex-wrap gap-3 text-sm text-cream/75">
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5">Verified workflows</span>
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5">Evidence-first process</span>
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5">Public transparency</span>
            </div>
          </div>

          <div className="glass-card rounded-[28px] p-3 shadow-soft">
            <div className="story-image h-[420px] overflow-hidden rounded-[22px] border border-white/20 shadow-2xl shadow-slate-950/20" />
            <div className="mt-4 grid grid-cols-2 gap-3 text-sm text-cream/80">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-gold">Priority</p>
                <p className="mt-2 text-xl font-semibold text-white">Water, roads & health</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-gold">Approach</p>
                <p className="mt-2 text-xl font-semibold text-white">AI + human review</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="section-shell -mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-7">
        {err && <p className="col-span-full rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">{err} Showing demo numbers.</p>}
        {cards.map(([k, v]) => (
          <div key={k} className="kpi-card">
            <div className="text-3xl font-serif text-forest-700">{v}</div>
            <div className="mt-1 text-[11px] uppercase tracking-[0.2em] text-slate-500">{k}</div>
          </div>
        ))}
      </section>

      <section className="section-shell py-20">
        <div className="mb-10 max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-forest-600">What we do</p>
          <h2 className="mt-2 font-serif text-3xl md:text-5xl text-forest-900">From civic problems to actionable solutions.</h2>
        </div>
        <div className="grid gap-5 md:grid-cols-3">
          {[
            ["Citizen reporting", "Residents submit verified problems with local evidence and urgency markers to create a reliable public record."],
            ["Government coordination", "Departments review, assign responsibility, and track the decision path from triage to implementation."],
            ["Research + delivery", "Universities and industry contribute expertise, pilots and deployment support to turn cases into impact."],
          ].map(([title, body]) => (
            <div key={title} className="feature-card">
              <div className="mb-4 h-11 w-11 rounded-xl bg-gradient-to-br from-emerald-100 to-amber-100 flex items-center justify-center text-lg font-bold text-forest-700">{title.slice(0, 1)}</div>
              <h3 className="font-serif text-2xl text-forest-900">{title}</h3>
              <p className="mt-3 text-slate-600">{body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="section-shell py-4">
        <div className="mb-10 max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-forest-600">Collaboration network</p>
          <h2 className="mt-2 font-serif text-3xl md:text-5xl text-forest-900">See who is solving what, together.</h2>
          <p className="mt-3 text-slate-600">Every problem, university suggestion and industry collaboration — visualised as a living network. Hover any node to explore connections.</p>
        </div>
        <ImpactNetwork />
      </section>

      <section className="section-shell py-4">
          <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
            <div className="story-image min-h-[320px] rounded-[26px] border border-white/10 shadow-inner" />
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-forest-600">Why it matters</p>
              <h3 className="mt-3 font-serif text-3xl md:text-4xl text-forest-900">Public-interest technology should be visible, accountable and outcome-driven.</h3>
              <p className="mt-4 text-slate-600">Challenge to Impact aligns problem selection, verification and implementation around a single governance model: citizens report, government leads, universities advise, and industry contributes where relevant.</p>
              <div className="mt-6 space-y-3">
                {[
                  "Transparent, traceable problem workflow",
                  "Evidence-backed prioritisation and triage",
                  "Improved collaboration between public institutions and technology partners",
                ].map((item) => (
                  <div key={item} className="flex items-start gap-3">
                    <span className="mt-1 inline-flex h-5 w-5 items-center justify-center rounded-full bg-emerald-100 text-xs text-emerald-700">✓</span>
                    <span className="text-slate-700">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
      </section>

      <section className="section-shell py-20">
        <div className="mb-10 max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-forest-600">Process</p>
          <h2 className="mt-2 font-serif text-3xl md:text-5xl text-forest-900">A structured path from challenge to impact.</h2>
        </div>
        <ol className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {steps.map((s, i) => (
            <li key={s} className="feature-card rounded-[22px] border border-[#e3ece7] bg-[#fbfdfb] p-5">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-emerald-100 to-amber-100 font-serif text-xl text-forest-700">{i + 1}</div>
              <div className="text-lg font-semibold text-slate-800">{s}</div>
            </li>
          ))}
        </ol>
        <div className="mt-8 text-center">
          <Link to="/how-it-works" className="inline-flex items-center justify-center rounded-full border border-forest-700 px-5 py-3 text-sm font-semibold text-forest-700 transition hover:bg-forest-700 hover:text-white">View full workflow</Link>
        </div>
      </section>
    </div>
  );
}
