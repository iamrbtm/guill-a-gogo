# Threat model (summary)

Scope: invitation-only family trip planner. Trust boundary: the Expo client
talks only to the Flask API over HTTPS; the API alone holds provider secrets and
the database. Postgres/Redis are never exposed publicly.

| Threat | Vector | Mitigation |
|--------|--------|------------|
| Account takeover (passkey theft) | Stolen authenticator | WebAuthn (phishing-resistant); rotating + revocable refresh tokens; recovery codes single-use & hashed |
| Invitation abuse | Leaked invitation token | Single-use, short TTL, hashed token store; audit on create/accept |
| Insecure Direct Object References | User edits another's trip | Authorization in service layer (not just UI); membership/role checks on every mutating op |
| Stolen refresh token | DB/device leak | Only hash stored; rotation revokes prior; revocation endpoint |
| Provider-key exposure | Key in client/repo | Keys server-side only; never in Expo public config or Git; restricted API keys + quotas |
| Malicious AI output | Prompt injection / hallucinated facts | AI cannot mutate itinerary; schema-validated output; human approval required; no live-fact fabrication |
| Sensitive-data leakage | Logs/exports/analytics | Medical fields excluded from logs/exports unless explicitly requested; redaction of tokens/secrets |

Out of scope for Phase 1 (covered in later phases): full push notification
security, exhaustive DAST. CI performs dependency + secret scanning.
