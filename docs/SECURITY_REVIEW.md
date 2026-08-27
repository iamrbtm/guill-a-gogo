# Security review

Scope: Guill-a-gogo Flask API + Expo client, invitation-only family deployment.

## Controls implemented (Phase 1–6)
- **Authentication:** WebAuthn passkeys (phishing-resistant) with short-lived access JWTs (15 min) and rotating, revocable refresh tokens. Recovery via single-use hashed recovery codes + email link.
- **Authorization:** Service-layer role checks (owner/editor/traveler/viewer) on every mutating operation; object-level profile sharing rules; offline-mutation permission checks.
- **Transport:** HTTPS-only production assumption; HSTS, secure headers (CSP, nosniff, frame-deny, referrer-policy, permissions-policy); restricted CORS.
- **Input/validation:** Strict request validation; pydantic-validated AI output (extra fields forbidden); provider responses normalized and provenance-tagged.
- **Secrets:** All credentials via env/Docker secrets; no secrets in Expo public config or repo; tokens/medical notes redacted from logs.
- **Audit:** Audit events for invitations, role changes, approvals, destructive actions, recovery.
- **Rate limiting:** Flask-Limiter on the API.
- **AI safety:** AI cannot mutate the itinerary, book, invent live facts, or bypass approval; all proposals are PENDING until a human approves.
- **Offline safety:** Idempotent mutation replay; optimistic-concurrency conflict detection (no last-write-wins).

## Threat model
See `docs/THREAT_MODEL.md` (account takeover, invitation abuse, IDOR, stolen refresh tokens, provider-key exposure, malicious AI output, sensitive-data leakage).

## Residual / deferred items
- Dependency + secret scanning in CI (recommend `pip-audit`, `trivy`, `gitleaks`).
- WebAuthn verified only in EAS dev/production builds (not Expo Go) — documented in `docs/KEYS_GUIDE.md`.
- Full DAST/penetration testing not performed; recommended before any public exposure (this app is invitation-only, not public SaaS).
- Push notification provider not yet wired (Phase 5 stub only).
