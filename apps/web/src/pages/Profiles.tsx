import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Profile } from "../lib/types";

const KINDS: { key: string; label: string }[] = [
  { key: "traveler", label: "Travelers" },
  { key: "pet", label: "Pets" },
  { key: "vehicle", label: "Vehicles" },
  { key: "trailer", label: "Trailers" },
];

export default function Profiles() {
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all(KINDS.map((k) => api.get<Profile[]>(`/profiles/${k.key}`).then((r) => [k.key, r.length] as const)))
      .then((pairs) => setCounts(Object.fromEntries(pairs)))
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="container"><div className="alert" role="alert">{error}</div></div>;

  return (
    <div className="container">
      <h1>Profiles</h1>
      {KINDS.map((k) => (
        <div key={k.key} className="card">
          <h2>{k.label}</h2>
          <p>{counts[k.key] ?? 0} saved</p>
        </div>
      ))}
    </div>
  );
}
