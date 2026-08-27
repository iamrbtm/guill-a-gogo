# Guill-a-Gogo mobile (Expo)

Phase 1 shell: bottom-tab navigation (Trips / Today / Plan / Profiles / More)
with placeholder screens. Business screens arrive in later phases.

## Run
```bash
npm install
npx expo start        # press w for web
```
> Native passkeys require an EAS development build (not Expo Go). See
> `docs/KEYS_GUIDE.md` §2.

## API contract
Generated TypeScript types live in `packages/contracts` (run the generator
described there) and are consumed via `openapi-fetch` against the versioned API.
