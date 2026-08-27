# API contracts

This package holds the source-of-truth OpenAPI document for the Flask API
(`openapi.yaml`) and the generated TypeScript client used by the Expo app.

## Generate TypeScript contracts (after editing openapi.yaml)
```bash
npm install -g openapi-typescript
openapi-typescript openapi.yaml -o src/api-contracts.ts
# Or use the typed fetch client:
npm install openapi-fetch
```
Import the generated types in `apps/mobile` and use `openapi-fetch` against the
versioned API base URL. Re-run generation whenever `openapi.yaml` changes.

> Longer term this can be automated (e.g. dump from the API via an OpenAPI lib
> and regenerate in CI). For Phase 1 the document is maintained by hand and kept
> in sync with `services/api/app/routes/*`.
