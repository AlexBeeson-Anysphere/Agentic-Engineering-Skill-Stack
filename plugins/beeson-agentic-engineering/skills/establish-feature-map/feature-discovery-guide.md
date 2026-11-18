# Feature Discovery & Slicing Guide

How to slice any repository into a tight, high-signal set of feature files in `agent-map/` without bloating the repo or missing critical surfaces.

## Target Granularity

- **Small / single-purpose repo:** 4–8 feature files.
- **Medium app or multi-service repo:** 8–15 feature files.
- **Large monorepo:** 12–25 feature files.
- **Never** create one file per component, one file per database table, or one file per endpoint. Group by **user-visible or caller-visible capability** (e.g., `auth-and-sessions.md`, `billing-and-subscriptions.md`, `search-and-filtering.md`, `webhook-ingestion.md`).
- **Max 150 lines per feature file.** If a feature file exceeds 150 lines, split it into two distinct user flows (e.g., `checkout-flow.md` and `subscription-management.md`).

## How to Discover Features Across Any Stack

Run `scripts/discover.py <root> --summary` first to see stack manifests, candidate surface directories, route/command/controller clusters, and existing verification skills. Then inspect the codebase along these five axes:

### 1. User-Facing UI Surfaces (Web, Mobile, Desktop)
- **Next.js / Remix / Nuxt / SvelteKit / Astro:** Look at route groups in `app/`, `pages/`, `src/routes/`. Group related pages into a single feature (e.g., `/settings/profile`, `/settings/security`, `/settings/billing` → `account-settings.md` or `billing.md`).
- **React / Vue / Angular SPAs:** Check the router config (`App.tsx`, `routes.ts`, `router/index.ts`) and `src/features/` or `src/modules/`.
- **Mobile (iOS / Android / React Native / Flutter):** Inspect navigation graphs, screen directories, and deep-link handlers.

### 2. API & Service Surfaces (REST, GraphQL, gRPC, WebSockets)
- **HTTP routers & controllers:** Express/Fastify/NestJS routes, Go `chi`/`gin`/`http.ServeMux`, Python FastAPI/Django/Flask blueprints, Rails `config/routes.rb`, Spring `@RestController`, .NET Minimal APIs/Controllers.
- **GraphQL / gRPC / tRPC:** Schema definitions (`*.graphql`, `*.proto`, tRPC routers) grouped by domain entity or mutation/query family.
- **Public SDKs / Libraries:** If the repo is a library or SDK, the "user" is the calling developer. Slice features by primary capability (e.g., `client-initialization-and-auth.md`, `streaming-responses.md`, `retry-and-error-handling.md`).

### 3. CLI & TUI Surfaces
- Inspect subcommand definitions (`cobra` in Go, `click`/`typer`/`argparse` in Python, `commander`/`yargs`/`oclif` in Node, `clap` in Rust).
- Group closely related subcommands into a single feature file.

### 4. Async Workflows, Workers & Scheduled Jobs
- Background queues (BullMQ, Celery, Sidekiq, Temporal, Kafka/SQS consumers, cron schedules).
- If an async job is purely an internal half of a user feature (e.g., sending a welcome email after signup), include it inside that feature's file (`auth-and-onboarding.md`) and list the worker path in `Paths:`.
- If an async pipeline is a standalone capability (e.g., nightly billing reconciliation, webhook delivery engine, data sync pipeline), give it its own feature file.

### 5. Cross-Cutting Foundations
- Pure infrastructure or shared internal layers (e.g., a design-system UI kit, a database client wrapper, telemetry/logging middleware) usually belong in `agent-map/README.md` under **Stack & architecture at a glance** and **Common tasks → start here**.
- Give a foundational layer its own file in `agent-map/` **only** if agents are frequently asked to work on it directly as a product surface (e.g., `plugin-system.md`, `design-system-primitives.md`, `database-migrations-and-tenancy.md`).

## Ordering the Regression Sweep (`agent-map/README.md`)

Order the feature table in `agent-map/README.md` from top to bottom so an agent or human verifying the app can run top-to-bottom:

1. **Bootstrap / Health / Auth:** Account creation, login, session setup, API key provisioning, tenant/workspace creation.
2. **Core Domain Creation (Write paths):** Creating the primary entities the app manages.
3. **Core Domain Consumption (Read / Search / Update / Delete):** Viewing, searching, filtering, editing, exporting.
4. **Secondary & Collaboration Flows:** Sharing, notifications, webhooks, integrations, permissions.
5. **Admin, Billing & Teardown:** Usage metering, billing/subscriptions, account deletion.

## Choosing `Paths:` for Each Feature File

Every `agent-map/<feature>.md` has a `Paths:` list in its line-3 metadata comment:
```markdown
<!-- agent-map v2 | Last linted: 7f3a91c | Paths: apps/web/src/features/billing, apps/api/src/routes/billing.ts, packages/db/prisma/schema.prisma -->
```
- Include the specific directories and files that implement or test this feature across layers (frontend feature dir, backend route/service dir, relevant schema/proto file, e2e spec).
- Avoid listing `.` or broad parent directories like `src/` unless the repo is tiny—broad paths cause every commit to mark every feature `STALE`.
- Together, the union of `Paths:` across all feature files should cover every active product directory in the repo so `drift.py` can detect unmapped code churn.
