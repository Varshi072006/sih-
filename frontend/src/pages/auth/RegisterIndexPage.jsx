import { Link } from "react-router-dom";

const options = [
  ["/register/citizen", "Citizen", "Report a societal problem in your locality.", "CIT", "Share what your community needs"],
  ["/register/university", "University", "Contribute research, labs and student-faculty expertise.", "UNI", "Bring knowledge into public action"],
  ["/register/industry", "Industry", "Offer technology, mentoring, funding or deployment support.", "IND", "Turn capability into impact"],
  ["/register/government", "Government", "Official officers request access; admin verification is required.", "GOV", "Coordinate accountable action"],
];

export default function RegisterIndexPage() {
  return (
    <div className="register-chooser">
      <section className="register-chooser-hero">
        <div className="section-shell py-12 md:py-16">
          <p className="eyebrow">Challenge to Impact · Join the network</p>
          <h1 className="mt-3 max-w-3xl font-serif text-4xl leading-tight text-white md:text-6xl">Choose your way to create public impact.</h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-emerald-50/75 md:text-lg">Every role contributes differently. Select the account that matches how you want to participate in Jharkhand's civic innovation network.</p>
        </div>
      </section>
      <section className="section-shell register-chooser-content">
        <div className="mb-7 flex flex-col justify-between gap-3 md:flex-row md:items-end"><div><p className="eyebrow text-forest-700">Select a role</p><h2 className="mt-1 font-serif text-2xl text-ink md:text-3xl">Where do you belong?</h2></div><p className="text-sm text-slate-500">Registration takes a few minutes.</p></div>
        <div className="grid gap-5 md:grid-cols-2">
        {options.map(([to, title, text, code, prompt], index) => (
          <Link key={to} to={to} className={`role-card role-card-${index + 1}`}>
            <div className="flex items-start justify-between gap-4"><span className="role-mark">{code}</span><span className="role-arrow" aria-hidden="true">↗</span></div>
            <p className="mt-7 text-xs font-semibold uppercase tracking-[0.16em] text-forest-700">{prompt}</p>
            <h2 className="mt-2 font-serif text-3xl text-ink">{title}</h2>
            <p className="mt-3 max-w-sm text-sm leading-6 text-slate-600">{text}</p>
          </Link>
        ))}
        </div>
        <div className="registration-trust"><span className="help-icon">✓</span><div><strong>All organization accounts are verified before access.</strong><p>Citizens can begin after email verification. University, industry and government accounts require administrator review.</p></div></div>
      </section>
    </div>
  );
}
