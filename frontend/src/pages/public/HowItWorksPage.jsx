import { Link } from "react-router-dom";

const flow = [
  "Citizen Registration",
  "Submit Problem with GPS/location evidence",
  "AI classification, related-problem detection and priority recommendation",
  "Government verification (human decision)",
  "Department assignment and review",
  "Government action / versioned solution",
  "AI university recommendation (human selection)",
  "University review: no opinion or suggestion",
  "Government review of opinion and optional solution update",
  "Done Solution — industry queue is optional",
  "Implementation / pilot / citizen feedback",
  "Problem completed and impact report",
];

export default function HowItWorksPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      <h1 className="font-serif text-4xl mb-6">How It Works</h1>
      <ol className="space-y-3">
        {flow.map((s, i) => <li key={s} className="bg-white border rounded p-4"><span className="text-gold font-serif mr-2">{i + 1}.</span>{s}</li>)}
      </ol>
      <div className="mt-8 flex gap-4">
        <Link className="underline" to="/register/citizen">Register as citizen</Link>
        <Link className="underline" to="/problems">View problems</Link>
      </div>
    </div>
  );
}
