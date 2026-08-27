# Known limitations & deferred enhancements

## Current limitations
- **Routing is a deterministic mock** unless `GOOGLE_MAPS_API_KEY` is set. Distances for the Tennessee seed are approximate and must be recomputed from live route data once the vehicle and dates are known.
- **No live turn-by-turn navigation** — the app provides deep links to Apple/Google Maps only.
- **Passkeys require an EAS development/production build**; Expo Go cannot exercise native WebAuthn.
- **AI layer is disabled by default** (`AI_PROVIDER=none`). When enabled, the OpenAI-compatible gateway call is a stub until wired.
- **Push notifications** are not yet implemented (provider stub only).
- **Google Drive/Docs delivery** is a stub; local download works for all formats.
- **Offline recalculation** requiring an unavailable provider is not performed — the cached plan is shown with a clear note.
- **Tablet layouts** and **reduced-motion** preferences are scaffolded but not fully tuned.
- **Automated accessibility / dependency / secret scanning** not yet in CI.

## Deferred enhancements
- Real Google Routes/Places/Weather client implementations.
- Lodging-rate provider adapter for live room inventory and exact rates.
- Full push-notification provider.
- Automated a11x testing in CI.
- Multi-language support.
- Advanced scenic-route optimization.

## Notes
- The Tennessee seed intentionally leaves dog weights/breeds and vehicle facts incomplete so the app surfaces the required blocking warnings — never guess these values.
- Hotel accessibility and two-dog eligibility are never marked confirmed without explicit human verification.
