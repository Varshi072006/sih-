import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../services/api";
import { DemoTag } from "../../components/ui";

export default function ProjectsPage() {
  const [items, setItems] = useState([]);
  useEffect(() => { api("/api/projects").then(setItems); }, []);
  return (
    <div className="max-w-7xl mx-auto px-4 py-10">
      <h1 className="font-serif text-4xl mb-6">Projects</h1>
      <div className="grid md:grid-cols-2 gap-4">
        {items.map((p) => (
          <Link key={p.id} to={`/project/${p.public_id}`} className="block bg-white border p-5 rounded">
            <div className="text-sm">{p.public_id}<DemoTag show={p.is_demo} /></div>
            <h2 className="font-serif text-xl">{p.title}</h2>
            <div className="mt-2 h-2 bg-stone-200 rounded"><div className="h-2 bg-forest-700 rounded" style={{ width: `${p.progress}%` }} /></div>
            <p className="text-sm mt-1">{p.status} · {p.progress}%</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
