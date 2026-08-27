import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { setTokens } from "../lib/api";
import { registerWithInvitation } from "../lib/webauthn";

export default function AcceptInvite() {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [codes, setCodes] = useState<string[]>([]);

  useEffect(() => {
    if (!token) setError("Missing invitation token in URL.");
  }, [token]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = await registerWithInvitation(token, name);
      setTokens(res.tokens.access_token, res.tokens.refresh_token);
      setCodes(res.recovery_codes ?? []);
      setDone(true);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  if (done) {
    return (
      <div className="container" style={{ maxWidth: 520 }}>
        <div className="card">
          <h1>Welcome!</h1>
          <p>Save these single-use recovery codes somewhere safe. They're your backup if you lose your passkey.</p>
          <ul>
            {codes.map((c) => (
              <li key={c}><code>{c}</code></li>
            ))}
          </ul>
          <button className="btn" onClick={() => (window.location.href = "/trips")}>
            Continue to trips
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container" style={{ maxWidth: 420 }}>
      <div className="card">
        <h1>Accept invitation</h1>
        {error && <div className="alert" role="alert">{error}</div>}
        <form onSubmit={submit}>
          <label htmlFor="name">Your name</label>
          <input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
          <div style={{ marginTop: "1rem" }}>
            <button className="btn" type="submit" disabled={busy || !token}>
              {busy ? "Registering…" : "Register passkey"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
