import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api";
import { Stop, Today, Trip } from "../lib/types";

export default function TripDetail() {
  const { id } = useParams<{ id: string }>();
  const [trip, setTrip] = useState<Trip | null>(null);
  const [stops, setStops] = useState<Stop[]>([]);
  const [today, setToday] = useState<Today | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");

  const load = () => {
    if (!id) return;
    Promise.all([
      api.get<Trip>(`/trips/${id}`),
      api.get<Stop[]>(`/trips/${id}/stops`),
      api.get<Today>(`/trips/${id}/today`),
    ])
      .then(([t, s, td]) => { setTrip(t); setStops(s); setToday(td); })
      .catch((e) => setError(e.message));
  };

  useEffect(load, [id]);

  const addStop = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post(`/trips/${id}/stops`, { name, stop_type: "required_place", required: true, order_index: stops.length + 1 });
      setName("");
      load();
    } catch (err) { setError((err as Error).message); }
  };

  const complete = async (s: Stop) => {
    try {
      await api.patch(`/trips/${id}/stops/${s.id}`, { completed: true });
      load();
    } catch (err) { setError((err as Error).message); }
  };

  const delay = async () => {
    try {
      await api.post(`/trips/${id}/delays`, { delay_minutes: 60 });
      load();
    } catch (err) { setError((err as Error).message); }
  };

  const exportFmt = (fmt: string) => {
    window.open(`/api/v1/trips/${id}/export?format=${fmt}`, "_blank");
  };

  if (error) return <div className="container"><div className="alert" role="alert">{error}</div></div>;
  if (!trip) return <div className="container">Loading…</div>;

  return (
    <div className="container">
      <h1>{trip.title}</h1>
      <p className="muted">{trip.origin} → {trip.destination} · {trip.status}</p>

      {today?.next_stop && (
        <div className="card">
          <h2>Today — Day {today.day_number}</h2>
          <p><strong>Next:</strong> {today.next_stop.name} {today.next_stop.required ? "(required)" : ""}</p>
          <p className="muted">{today.eta_note}</p>
          <div className="row">
            <button className="btn" onClick={() => window.open(`/api/v1/trips/${id}/nav?provider=google`, "_blank")}>Open Navigation</button>
            <button className="btn btn-secondary" onClick={delay}>Report delay</button>
          </div>
        </div>
      )}

      <div className="card">
        <h2>Stops</h2>
        {stops.map((s) => (
          <div key={s.id} className="row" style={{ justifyContent: "space-between", marginBottom: ".5rem" }}>
            <span>{s.name} {s.required ? "• required" : ""} {s.completed ? "✓" : ""}</span>
            {!s.completed && <button className="btn btn-secondary" onClick={() => complete(s)}>Complete</button>}
          </div>
        ))}
        <form onSubmit={addStop} className="row">
          <input placeholder="Stop name" value={name} onChange={(e) => setName(e.target.value)} aria-label="Stop name" />
          <button className="btn" type="submit">Add stop</button>
        </form>
      </div>

      <div className="card">
        <h2>Export</h2>
        <div className="row">
          <button className="btn btn-secondary" onClick={() => exportFmt("csv")}>CSV</button>
          <button className="btn btn-secondary" onClick={() => exportFmt("xlsx")}>XLSX</button>
          <button className="btn btn-secondary" onClick={() => exportFmt("pdf")}>PDF</button>
          <button className="btn btn-secondary" onClick={() => exportFmt("docx")}>DOCX</button>
        </div>
      </div>
    </div>
  );
}
