# Master Prompt: Accessible, Pet-Friendly Road Trip Planner

You are the lead software engineer responsible for designing and implementing a production-quality, private, multi-trip road-trip planning application. Build the application from scratch in the current project directory. Do not assume any existing application code is correct or reusable unless it is already present and passes inspection.

The app is intended for a family that travels with mobility limitations, sensory considerations, pets, and a trailer. It must plan future trips as well as the initial Dallas, Oregon to Clarksville, Tennessee move described below.

Do not reduce this project to a collection of attractive mock screens. Every completed feature must have a working backend, database persistence, validation, authorization, error handling, tests, and user documentation.

## 1. Working method

Before writing implementation code:

1. Inspect the repository, development environment, installed tools, and any project-level instructions.
2. Verify current stable versions and compatibility using official documentation. Prefer stable releases, not prereleases.
3. Write an implementation plan divided into the phases specified in this prompt.
4. Create an architecture decision record for consequential choices.
5. Identify required credentials and services. Never block the core app when an optional provider credential is absent.
6. Present the plan and any genuine blockers before implementation.

During implementation:

- Work test-first for business rules, permissions, calculations, synchronization, and bug fixes.
- Complete and verify one phase before starting the next.
- Use small, reviewable commits when Git is available.
- Keep modules focused. Do not create enormous route, model, service, or screen files.
- Do not silently change the approved architecture.
- Do not use fake provider data outside explicit development fixtures and tests.
- Do not report a phase complete while it contains placeholder buttons, unimplemented endpoints, skipped required tests, or hardcoded production results.
- If an external API cannot provide a requested fact, say so in the UI and support manual confirmation. Never ask an AI model to invent live availability, prices, accessibility, or pet rules.

## 2. Approved architecture

Use a modular monolith with these top-level areas:

```text
apps/
  mobile/              Expo / React Native / TypeScript client
services/
  api/                 Python / Flask REST API
  worker/              Celery tasks and scheduled jobs
packages/
  contracts/           Generated TypeScript API contracts
infra/                 Docker, deployment, backup, and operations files
docs/                  Architecture, API, setup, runbooks, and user guides
```

Use:

- Python 3.14 if all required production dependencies support it. If they do not, document the exact incompatibility and obtain approval before selecting a lower supported version.
- Flask with an application factory and blueprint/module boundaries.
- SQLAlchemy 2.x, Alembic, psycopg 3, PostgreSQL 17 or a newer explicitly verified stable major version.
- A schema/validation and OpenAPI solution that generates a correct OpenAPI document and typed TypeScript client contracts.
- Redis and Celery for background work and scheduled refreshes.
- Gunicorn for the production Flask process.
- Expo with React Native, TypeScript, Expo Router, TanStack Query, and secure native credential storage.
- A persistent offline store, preferably Expo SQLite, plus an explicit synchronization outbox.
- Docker Compose for local and production server services.

The Expo client communicates with Flask over versioned HTTPS JSON APIs. The client never connects directly to PostgreSQL, Redis, AI providers, Maps APIs requiring secrets, or hotel providers.

The reverse proxy already exists outside this project. Do not add or replace it. The Compose stack must accept a configurable external Docker network name. Only the API joins that external network. PostgreSQL and Redis must not publish host ports in production.

## 3. Product scope and users

This is an invitation-only family application, not a public SaaS product.

Users have separate accounts. Implement these trip roles:

- **Owner:** manages the trip, invitations, roles, archival, and deletion.
- **Editor:** edits the plan and may approve AI-generated proposals.
- **Traveler:** views the trip, checks in, completes stops, and reports delays.
- **Viewer:** read-only access.

Account registration occurs only through an owner-generated invitation. Use passkeys as the primary authentication method, with email recovery, hashed single-use recovery codes, revocable sessions, short-lived access tokens, and rotating refresh tokens. Use WebAuthn with the production hostname as the relying-party identity. Support native passkey flows in production Expo builds and a standards-compliant browser flow for Expo web.

Do not pretend passkeys can be fully validated in Expo Go if native capabilities require a development build. Document and provide the required EAS/development-build workflow.

## 4. Core domain model

Model reusable data rather than attaching everything directly to one trip.

### Accounts and access

- User
- Passkey credential
- Invitation
- Recovery token and recovery code
- Refresh session/device
- Trip membership and role
- Audit event

### Traveler profiles

Support optional fields for:

- Name and contact information
- Emergency contact
- Maximum comfortable walking distance
- Mobility devices
- Transfer needs
- Accessible restroom needs
- Preferred break frequency and duration
- Sensory considerations and routine preferences
- Food allergies and dietary restrictions
- Medication notes and emergency notes
- Privacy level for sensitive information

Medical information is optional. Restrict it to authorized trip members and exclude it from ordinary logs, analytics, notifications, and exports unless explicitly requested.

### Pets

Support:

- Name, species, breed, size, and weight
- Hotel restrictions and preferences
- Break frequency
- Feeding and medication schedule
- Vaccination-document metadata
- Emergency veterinary notes

### Vehicles and trailers

Support:

- Year, make, model, trim, engine, fuel type
- Tank capacity
- Normal MPG and towing MPG
- Rated towing capacity and payload limits
- Trailer weight and loaded estimated weight
- Range safety reserve
- Fuel-cost safety margin

Never infer towing safety from a model name alone. Surface incomplete or conflicting vehicle information as a blocking planning warning.

### Trips and itinerary

Include:

- Trip, dates or generic day numbers, origin, destination, status, timezone policy, budget, and owner
- Selected travelers, pets, vehicle, and trailer
- Required locations and optional places
- Daily driving limits, break rules, arrival targets, and preference overrides
- Trip day
- Ordered stop
- Route leg and route alternative
- Activity and timing window
- Meal plan
- Lodging candidate and confirmed reservation
- Fuel estimate and actual fuel purchase
- Expense and budget category
- Document/attachment metadata
- Planning warning and required confirmation
- AI proposal with before/after changes and approval history
- Offline mutation and synchronization conflict

Use UUIDs. Use UTC for stored instants while retaining the relevant IANA timezone for local display. Add version columns or equivalent optimistic-concurrency controls to collaboratively edited records.

Use soft deletion for trips and other meaningful user data, with a documented retention period and owner-controlled restore path.

## 5. Planning engine

Separate deterministic planning rules from AI suggestions.

### Hard constraints

Hard constraints include:

- Required destinations and minimum visit durations
- Fixed appointments and confirmed reservations
- Maximum walking distances and mobility requirements
- Required mobility equipment access
- Pet restrictions
- Food allergies
- Vehicle and trailer safety limits
- Maximum daily driving when marked mandatory

The system may explain a conflict, but it must never silently drop or weaken a hard constraint.

### Preferences

Preferences include:

- Target daily driving range
- Break frequency
- Hotel budget and amenities
- Meal style
- Sightseeing interests
- Preferred arrival time
- Scenic-route tolerance
- Maximum detour time
- Preferred navigation app

### Route generation

The planner must:

- Divide journeys into manageable travel days.
- Calculate wheel-turning time separately from breaks, meals, sightseeing, fueling, transfers, and check-in.
- Create dog and restroom breaks near the configured interval.
- Prefer accessible restrooms, dog-relief areas, safe trailer access, and short walking distances.
- Keep required destinations and minimum durations.
- Calculate route miles and time using a routing provider.
- Calculate fuel from route miles, towing MPG, estimated local fuel price, and a configurable reserve.
- Clearly distinguish estimated, live, cached, manually entered, and confirmed data.
- Generate warnings when daily limits, vehicle range, towing limits, arrival deadlines, or accessibility constraints conflict.
- Return alternative plans when no single plan satisfies every constraint.

Do not implement custom turn-by-turn navigation. Provide one-tap deep links that open Apple Maps or Google Maps for the selected route leg. The user may choose the preferred navigation app per profile.

## 6. Today mode

Create a low-clutter travel-day dashboard showing:

- Current day and next destination
- Departure deadline
- Expected arrival
- Distance and driving time
- Next break and remaining time/distance
- Fuel range and recommended fuel stop
- Weather and meaningful alerts
- Reservation and confirmation details
- Large **Open Navigation** action
- Large actions for arrived, departed, completed, delayed, skipped, and emergency pause

When a delay or skipped stop affects the plan, calculate the impact and create a proposed revision. Show the old and new schedule, affected reservations, cost difference, warnings, and assumptions. Require an Owner or Editor to approve the proposal before it changes the stored itinerary.

## 7. Offline behavior and synchronization

The active trip must remain useful without cellular service. Cache:

- Current itinerary and route summaries
- Addresses and phone numbers
- Reservation confirmation details
- Previously calculated stops
- Relevant emergency and mobility notes
- Previously retrieved warnings and source timestamps

Queue offline actions in an outbox. Synchronize when service returns. Use idempotency keys for mutations. Detect version conflicts and present a human-readable resolution screen. Never use last-write-wins for conflicting itinerary edits without notifying the user.

Do not promise offline recalculation that requires an unavailable provider. Show the cached plan and explain which refreshes require connectivity.

## 8. External provider architecture

Create narrow provider interfaces for:

- Routing and route matrix
- Geocoding and autocomplete
- Places, restaurants, attractions, and rest areas
- Lodging search and room rates
- Fuel prices
- Weather
- Road conditions
- AI text/structured planning
- Email
- Push notifications
- Document export and Google Drive/Docs delivery

Implement Google Maps Platform as the initial provider where appropriate, including Routes, Geocoding/Places, and Weather if available and suitable. Keep provider selection configurable. Google APIs may require a billing-enabled project even when usage is within free monthly caps. Document setup, restrict API keys, add server-side quotas where possible, and recommend Cloud billing alerts.

Do not use legacy APIs when a supported replacement exists. Verify current requirements against official Google documentation during implementation.

Every provider result must record:

- Provider and provider-specific identifier
- Request parameters or normalized request fingerprint
- Retrieval timestamp
- Expiration/staleness timestamp
- Normalized response
- Verification status
- Source link when permitted

Provider failures must degrade cleanly to cached data or manual entry. One unavailable integration must not bring down trip viewing or editing.

### Lodging truth rules

Model these separately:

- Advertised pet-friendly
- Two dogs explicitly permitted
- Weight and breed restrictions known
- Pet fees included in displayed total
- Accessible room listed
- Required accessibility features explicitly confirmed
- Breakfast included
- Trailer parking confirmed
- Rate and taxes retrieved for the actual dates and occupancy
- User-confirmed reservation

Google Places is useful for business discovery but is not proof of room inventory, exact rates, ADA configuration, or acceptance of two specific dogs. Add a lodging-rate provider adapter for a future approved provider. Until such a provider is configured, offer direct booking/search links and manual confirmation fields. Do not scrape booking sites in violation of their terms.

Provide a hotel call checklist and store who confirmed each requirement, the date, notes, and confirmation number.

### Fuel, weather, and road conditions

Show a visible **checked at** timestamp. Mark stale data. Fuel estimates must state whether the price is a live station result, regional average, manually entered value, or fallback assumption. Road-condition links and warnings must identify their source and timestamp.

## 9. AI assistant

The AI layer is optional and provider-neutral. Support configuration such as `none`, `gemini`, and `openai` without coupling business rules to one provider.

The AI may:

- Explain itinerary conflicts
- Recommend day divisions and stops
- Compare retrieved hotels or restaurants
- Draft schedule changes after delays
- Summarize the next travel day
- Produce a proposed itinerary from structured trip inputs

The AI may not:

- Directly modify an approved itinerary
- Book, cancel, or change a reservation
- Invent current rates, availability, accessibility, business hours, or pet rules
- Override a hard constraint
- Perform mileage, fuel, time, or budget arithmetic when deterministic code can do it
- expose private medical information unnecessarily

Require structured, schema-validated AI output. Store the prompt template version, model/provider, structured output, cited provider records, assumptions, warnings, and approval status. Reject invalid output safely. Every proposed change must be approved or rejected by an authorized user.

## 10. Expo application

Use bottom navigation:

- **Trips:** upcoming, active, past, and archived trips
- **Today:** active travel-day dashboard
- **Plan:** itinerary, map, lodging, meals, stops, budget, and proposals
- **Profiles:** travelers, pets, vehicles, trailers, and preferences
- **More:** invitations, exports, provider status, settings, and account security

Create a guided trip flow:

1. Select travelers and pets.
2. Select vehicle and trailer.
3. Enter dates or generic day numbers, origin, and destination.
4. Add required and optional stops.
5. Set daily limits and break preferences.
6. Set hotel, meal, accessibility, and budget needs.
7. Generate a draft.
8. Review warnings, alternatives, costs, and assumptions.
9. Approve the itinerary.

Support iOS, Android, tablet layouts, and Expo web where practical. Provide clear loading, empty, offline, stale-data, permission-denied, provider-disabled, and recoverable-error states.

## 11. Accessibility requirements

Meet WCAG 2.2 AA where applicable and follow native platform accessibility guidance.

Required behavior:

- Screen-reader labels, roles, order, and announcements
- Dynamic/large text without clipping
- High contrast and dark mode
- Reduced-motion support
- At least 44 by 44 point touch targets
- No status communicated by color alone
- No drag-only interactions; provide buttons for reordering
- Orientation flexibility on tablets
- Plain language and short actions in Today mode
- Confirmation for destructive or schedule-changing actions
- Optional simplified Today-only experience for Travelers
- Easy copy/open actions for addresses, phone numbers, reservation numbers, and navigation
- Keyboard accessibility for Expo web

Accessibility is an acceptance criterion, not a cleanup task at the end.

## 12. Exports

Generate useful, readable exports from approved itinerary data:

- PDF
- DOCX suitable for import into Google Docs
- XLSX with itinerary, locations, expenses, lodging, and calculation sheets
- CSV for core tables
- Printable day-by-day summary

Support an optional Google Drive/Docs delivery provider using user-authorized OAuth. When not configured, local download must still work. Include timestamps and distinguish estimates from confirmed data in every export.

The spreadsheet export should include formulas where helpful, but it is an export, not the system of record.

## 13. Initial Tennessee trip seed

Create a repeatable seed/import fixture for the first real trip. Do not put trip-specific data in schema migrations or planner code.

### Travelers

- Mother: can walk approximately 100 feet with a walker; otherwise uses a motorized wheelchair. The collapsible wheelchair and walker travel in the trailer.
- Jeremy: can walk approximately the length of a football field; has no toes on the right foot and is recovering from a left tibia break.
- Nephew: able-bodied, age 22, has Asperger's and may benefit from predictable timing and low-surprise schedule changes.
- Only Jeremy and the nephew drive.
- Two dogs are traveling. Their weights, breeds, and restrictions are not yet known and must remain required profile fields before hotel eligibility is considered confirmed.

### Vehicle and trailer

The earlier vehicle entry, **2001 Volkswagen Atlas Cross Sport**, is impossible because that model did not exist in that year. Do not guess the correct vehicle, fuel economy, towing capacity, or trailer weight. Seed an incomplete vehicle record with a blocking warning requiring year, make, model, trim/engine, towing MPG, towing capacity, and loaded trailer weight.

The trailer is small and carries luggage, the collapsible wheelchair, and the walker.

### Required route locations and visits

Origin: Dallas, Oregon.

Destination: Clarksville, Tennessee.

Required locations:

- Redding, California: Bethel Church and its prayer room; allow at least two hours.
- Exeter, California: family visit; stay two nights. Lodging may be in a nearby city such as Tulare when Exeter options do not meet pet and accessibility requirements.
- Goodsprings, Nevada: short stop at the bar associated with the nephew's game interest.
- Las Vegas, Nevada: one overnight for the nephew's delayed 21st-birthday trip.
- Grand Canyon: plan enough time for an appropriate accessible visit; use a two-night starting assumption that remains editable.
- Shawnee, Oklahoma: meal with friends.
- Beggs, Oklahoma: meal with friends.
- Include a Little Rock-area overnight when needed to keep the Oklahoma-to-Clarksville portion within daily driving limits.

Use the earlier approximately 11-day, 3,140-mile concept only as a starting draft. Recalculate all distances and times from current route data once the missing vehicle and travel dates are supplied.

### Travel constraints and preferences

- Target six to eight hours of driving per day, excluding breaks.
- Stop approximately every two hours for dogs, restrooms, movement, and mobility transfers.
- Prefer stops with accessible restrooms, dog parks or safe dog-relief areas, trailer access, and minimal walking.
- Hotels must support three people, an ADA room matching the required features, two dogs, breakfast, and parking suitable for the vehicle and trailer.
- The family will bring an air mattress for Jeremy or the nephew.
- Breakfast is eaten at the hotel.
- Sandwich supplies are purchased while leaving the starting city and sandwich lunches are eaten at planned breaks.
- Dinner should be affordable and locally distinctive. Avoid restaurants available near Dallas, Oregon.
- Waffle House is explicitly acceptable. Cheddar's Scratch Kitchen is a strong preference where practical.
- There is a fish allergy. A restaurant may serve fish only if safe non-fish meals can be ordered and cross-contact concerns are clearly surfaced for confirmation.
- Include interesting roadside sights when they do not create unsafe stops or unreasonable detours.
- No departure date is known. Support generic Day 1, Day 2, and so forth until dates are assigned.

## 14. Security and privacy

Implement:

- HTTPS-only production assumptions
- Restricted CORS
- Secure headers
- API rate limiting
- Strict request and response validation
- Authorization in the service layer, not only in UI or route decorators
- Redaction of tokens, secrets, medical notes, and provider payload secrets from logs
- Audit logging for account recovery, invitations, role changes, itinerary approvals, and destructive actions
- Environment variables or Docker secrets for credentials
- No secrets in Expo public configuration or the Git repository
- Dependency scanning and secret scanning in CI
- A documented threat model covering account takeover, invitation abuse, insecure direct object references, stolen refresh tokens, provider-key exposure, malicious AI output, and sensitive-data leakage

Do not expose PostgreSQL or Redis publicly.

## 15. Docker and operations

The production Compose stack must include:

- API
- Celery worker
- Celery scheduler/beat
- PostgreSQL
- Redis
- Automated backup job

Include:

- Health checks and dependency readiness
- Restart policies
- Resource limits
- Named persistent volumes
- Log rotation
- One-shot migration command and safe startup behavior
- `.env.example` containing names and explanations but no secrets
- Development override configuration
- Configurable external reverse-proxy network
- Backup retention and encrypted off-host backup guidance
- Tested restore script and restore runbook
- Provider-health status endpoint that does not reveal secrets
- Application liveness and readiness endpoints

Do not automatically run unsafe or irreversible migrations without a documented backup and rollback procedure.

## 16. Testing and quality gates

Backend:

- Unit tests for rules and calculations
- API integration tests against PostgreSQL
- Migration upgrade/downgrade tests where safe
- Role and object-level permission tests
- Invitation, passkey, session rotation, recovery, and revocation tests
- Provider contract tests with mocks or legally recorded fixtures
- AI schema-rejection and approval tests
- Timezone and daylight-saving tests
- Idempotency and optimistic-concurrency tests

Mobile:

- Component and navigation tests
- Authentication and invitation flows
- Offline cache and outbox behavior
- Conflict-resolution flow
- Dynamic text and screen-reader semantics
- Today-mode actions
- Provider-disabled and stale-data states

End to end:

- Create an account and invite a family member.
- Create traveler, pet, vehicle, and trailer profiles.
- Import the initial Tennessee trip.
- Generate and approve a route draft.
- View it offline.
- Record a delay.
- Generate, review, and approve a revised schedule.
- Export the approved itinerary.

Use linting, formatting, type checks, tests, and production builds in CI. Set reasonable coverage thresholds for critical domain, permission, and authentication code. Do not chase a vanity percentage by testing framework internals.

## 17. Delivery phases

### Phase 1: Foundation and authentication

Monorepo, Compose stack, API skeleton, database migrations, Expo shell, OpenAPI contracts, invitation-only accounts, passkeys, recovery, sessions, audit foundation, CI, and setup documentation.

### Phase 2: Profiles and manual trips

Traveler, pet, vehicle, trailer, preference, trip, membership, day, stop, lodging, meal, reservation, and expense CRUD with permissions and accessible Expo screens.

### Phase 3: Deterministic planning and Tennessee seed

Google routing/geocoding adapters, route legs, daily division, timing, breaks, fuel calculations, warnings, alternatives, and repeatable Tennessee-trip import.

### Phase 4: Today mode and offline operation

Today dashboard, navigation deep links, progress updates, delay handling, persistent offline cache, mutation outbox, synchronization, conflict resolution, and notifications.

### Phase 5: Research providers and AI proposals

Places, meals, lodging adapter, fuel, weather, road-condition links, provider provenance, staleness, structured AI proposals, approval workflow, and graceful provider-disabled behavior.

### Phase 6: Exports and production hardening

PDF, DOCX, XLSX, CSV, optional Google Drive/Docs delivery, security review, accessibility audit, backup restore test, performance review, operations documentation, and release checklist.

At the end of each phase:

1. Run all relevant tests, linters, type checks, and builds.
2. Report the exact commands and results.
3. Demonstrate working acceptance criteria.
4. Update documentation and the phase checklist.
5. Stop for review before proceeding if the user requested checkpoints.

## 18. Definition of done

The project is complete only when:

- A new developer can start the development stack from documented commands.
- Production deployment works behind an existing reverse proxy.
- Invitations, passkeys, recovery, permissions, and session revocation work.
- Users can maintain reusable traveler, pet, vehicle, trailer, and preference profiles.
- Users can create and collaboratively manage multiple trips.
- The Tennessee trip can be imported without hardcoding it into the planner.
- The app calculates route days, breaks, mileage, timing, and fuel using deterministic rules.
- Today mode works online and remains useful offline.
- Schedule changes are proposed and require approval.
- Provider data carries provenance and timestamps and degrades safely.
- Hotel accessibility and two-dog eligibility are never falsely marked confirmed.
- AI cannot bypass approval or fabricate live facts.
- Exports are readable and identify estimates versus confirmations.
- Automated tests cover the critical workflows.
- Accessibility review finds no known high-severity issues.
- PostgreSQL backup and restore are demonstrated.
- No critical or high-severity security findings remain unresolved.
- There are no placeholder implementations presented as finished functionality.

## 19. Final handoff requirements

Provide:

- Architecture overview and diagrams
- Complete setup instructions for macOS development and Ubuntu/Docker production
- Environment-variable reference
- Google Cloud API setup with quota and billing-alert guidance
- Passkey domain and mobile-build setup
- Database schema documentation
- OpenAPI documentation
- Provider-extension guide
- Backup and restore runbook
- Admin and family-user guides
- Test strategy and exact verification commands
- Known limitations and deferred enhancements
- A release checklist

When a decision is missing, use the safest reversible default, record it, and continue unless it materially changes security, cost, data ownership, or the user experience. Ask before incurring paid services, weakening a hard constraint, changing the approved stack, or deploying publicly.
