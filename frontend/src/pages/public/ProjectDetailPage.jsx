import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../../services/api";
import { DemoTag, Loading } from "../../components/ui";

export default function ProjectDetailPage() {
  const { id } = useParams();
  const [p, setP] = useState(null);
  useEffect(() => { api(`/api/projects/${id}`).then(setP); }, [id]);
  if (!p) return <div className="p-8"><Loading /></div>;
  return (
    <div className="max-w-5xl mx-auto px-4 py-10 space-y-6">
      <h1 className="font-serif text-4xl">{p.title}<DemoTag show={p.is_demo} /></h1>
      <p>{p.public_id} · Problem {p.problem_id}</p>
      <p>{p.objectives}</p>
      <p>University: {p.university || "—"} · Industry: {p.industry || "—"}</p>
      <h2 className="font-serif text-2xl">Team</h2>
      <ul>{(p.members || []).map((m) => <li key={m.id}>{m.name} · {m.type} · {m.department} · {m.role}</li>)}</ul>
      <h2 className="font-serif text-2xl">Milestones</h2>
      <ol className="space-y-2">
        {(p.milestones || []).map((m) => (
          <li key={m.id} className="bg-white border p-3 rounded flex justify-between">
            <span>{m.sequence}. {m.name} — {m.description}</span>
            <span>{m.status}{m.approved ? " · approved" : ""}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
