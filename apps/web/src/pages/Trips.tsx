import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Trip } from "../lib/types";
import { Link } from "react-router-dom";

export default function Trips() {
  const [trips, setTrips] = useState<Trip[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");

  const load = () => api.get<Trip[]>("/trips").then(setTrips).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post("/trips", { title, origin, destination });
      setTitle(""); setOrigin(""); setDestination("");
      load();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  if (error) return <div className="container"><div className="alert" role="alert">{error}</div></div>;
  if (!trips) return <div className="container">Loading…</div>;

  return (
    <div className="container">
      <h1>Trips</h1>
      <div className="card">
        <form onSubmit={create} className="row">
          <input placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} required aria-label="Trip title" />
          <input placeholder="Origin" value={origin} onChange={(e) => setOrigin(e.target.value)} aria-label="Origin" />
          <input placeholder="Destination" value={destination} onChange={(e) => setDestination(e.target.value)} aria-label="Destination" />
          <button className="btn" type="submit">New trip</button>
        </form>
      </div>
      {trips.length === 0 && <p>No trips yet.</p>}
      {trips.map((t) => (
        <Link key={t.id} to={`/trips/${t.id}`} className="card" style={{ display: "block", textDecoration: "none" }}>
          <strong>{t.title}</strong>
          <div className="muted">{t.origin ?? "?"} → {t.destination ?? "?"} · {t.status}</div>
        </Link>
      ))}
    </div>
  );
}
