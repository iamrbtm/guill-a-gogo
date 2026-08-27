# Step-by-step: obtaining every external key/credential

This guide lists every external dependency in the master prompt, whether it is
**required**, and the exact steps to obtain it. Nothing here blocks local
development: every provider is optional and degrades to manual entry / console
logging until configured.

Legend: ✅ required for production • ⚪ optional • 🚫 not used

---

## 1. Google Cloud + Maps Platform ⚪ (recommended for routing/geocoding)

Used by Phase 3/5 for routing, geocoding, places, and (optionally) weather.

1. Create/sign in to a Google Cloud project: https://console.cloud.google.com/
2. Billing: enable a billing account. Google's "free tier" still requires a
   billing-enabled project; you will not be charged below the monthly free
   quota, but set a **budget + billing alert** (step 6).
3. Enable the APIs you need (APIs & Services → Library):
   - **Routes API** (preferred; the old Directions/ Distance Matrix are legacy)
   - **Places API** (and/or Places *New*)
   - **Geocoding API**
   - (Optional) **Weather API** if you later want Google weather
4. Create an API key: APIs & Services → Credentials → Create Credentials → API key.
5. **Restrict the key** (critical):
   - Application restrictions → HTTP referrers (for web) or IP addresses.
   - API restrictions → restrict to the specific APIs above.
   - Do NOT ship this key in the Expo app. The app calls **our Flask API**,
     which holds the key server-side only.
6. Set a budget alert: Billing → Budgets & alerts → create budget (e.g. $20/mo)
   with 50%/100% alerts.
7. Put the key in `infra/.env` as `GOOGLE_MAPS_API_KEY=...`.

> Until this key exists, the planner falls back to manual entry and clearly
> marks route/fuel/geocode data as "manual / unconfirmed".

---

## 2. Production domain + passkeys / WebAuthn ✅ (production only)

Passkeys (WebAuthn) need a real relying-party hostname. There is **no key to
buy**, but you must own a domain.

1. Register a domain (any registrar). Example: `guill.example`.
2. Deploy behind your **existing reverse proxy** (outside this repo). The API
   container joins the external Docker network (`EXTERNAL_NETWORK`) and the
   proxy terminates TLS, so the app assumes HTTPS.
3. Set these env vars to match the public hostname:
   - `RP_ID=guill.example` (hostname only, no scheme/port)
   - `RP_ORIGIN=https://guill.example`
   - `CORS_ALLOWED_ORIGINS=https://guill.example`
   - `INVITATION_BASE_URL=https://guill.example/accept`
4. **Expo passkeys**: native WebAuthn requires a **development build / EAS
   build**, not Expo Go. Steps:
   - `npm i -g eas-cli && eas login`
   - `eas build --platform ios` (and android) to produce a dev/prod build.
   - The Expo web target uses the browser WebAuthn flow (works on HTTPS).
   - Documented in `docs/SETUP.md`; do not pretend Expo Go supports native
     passkeys.

---

## 3. AI provider ⚪ (optional, provider-neutral)

The AI layer defaults to `none`. It is **not** required for any core feature.

- The spec supports `none | gemini | openai`. It is provider-neutral and never
  performs arithmetic or books anything.
- **Kilocode** is an AI *coding assistant*, not a callable REST API. To use an
  OpenAI-compatible model endpoint, point the config at it:
  - `AI_PROVIDER=openai`
  - `AI_BASE_URL=https://<your-openai-compatible-endpoint>/v1`
  - `AI_API_KEY=<key>`
  - `AI_MODEL=<model-name>`
- If you only have Kilocode for *your own* coding, leave `AI_PROVIDER=none`;
  the app runs fully without AI. When enabled, AI output is schema-validated
  and every change requires human approval (see spec §9).

---

## 4. Email (invitations + recovery) ⚪ (console by default)

The app is invitation-only; invitations/recovery emails are optional.

- Default `EMAIL_PROVIDER=console` → logs the message (great for dev).
- For real delivery without a paid SaaS, self-host or use an open relay:
  - **Mailpit** (dev only, no auth): `docker run -p 1025:1025 -p 8025:8025 axllent/mailpit`
    then `SMTP_HOST=mailpit SMTP_PORT=1025`.
  - **Self-hosted Postal** (production-grade, open source): https://postal.atech.media/
  - Or any SMTP you already control (provider, or your reverse-proxy host).
- Set `EMAIL_FROM`, and `SMTP_*` accordingly. No SMS provider is used.

---

## 5. SMS 🚫 — not used

The spec lists "push notifications" as an optional provider. We intentionally
use **email** for invitations/recovery and (later) push via a configurable
provider. There is **no SMS dependency**. If you later want push, it is an
optional adapter and will degrade gracefully when unconfigured.

---

## 6. Database / Redis / Docker ✅ (local infra, no external account)

PostgreSQL 17, Redis 7, and Docker are run via Compose — no external signup.
Secrets for these are generated locally (see `docs/SETUP.md`) and never
committed.

---

## Summary of what to actually go get

| Item | Action | Blocks dev? |
|------|--------|-------------|
| Google Maps key | Google Cloud console | No (manual fallback) |
| Domain + TLS | Your registrar + existing proxy | No (works on localhost) |
| AI endpoint | Optional; leave `none` | No |
| Email SMTP | Mailpit for dev / Postal for prod | No (console) |
| Postgres/Redis | Docker Compose | No |

You can build, test, and demo the entire Phase 1 foundation **without any of
these keys**. Add them incrementally as you reach the phases that need them.
