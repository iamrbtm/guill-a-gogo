import { useState } from "react";
import { setTokens } from "../lib/api";
import { loginWithPasskey } from "../lib/webauthn";

export default function Login() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = await loginWithPasskey(email);
      setTokens(res.access_token, res.refresh_token);
      window.location.href = "/trips";
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: 420 }}>
      <div className="card">
        <h1>Sign in</h1>
        <p className="muted">Use your passkey. Your email identifies which credential to use.</p>
        {error && <div className="alert" role="alert">{error}</div>}
        <form onSubmit={submit}>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="username"
          />
          <div style={{ marginTop: "1rem" }}>
            <button className="btn" type="submit" disabled={busy}>
              {busy ? "Signing in…" : "Sign in with passkey"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
