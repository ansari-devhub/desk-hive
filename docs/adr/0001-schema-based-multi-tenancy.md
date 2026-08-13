# ADR-0001: Schema-Based Multi-Tenancy over Shared-Schema Row-Level Isolation

## Status
Accepted

## Context
DeskHive is a multi-tenant helpdesk SaaS. Each organization ("tenant") using
the platform must have its data fully isolated from every other tenant —
tickets, agents, and customers belonging to one organization must never be
readable, queryable, or leakable to another.

Two broad approaches were available:

1. **Shared schema, row-level isolation** — all tenants share the same
   tables; every row carries a `tenant_id`/`organization` foreign key, and
   isolation is enforced entirely in application code (custom managers,
   mandatory `.filter(organization=...)` on every query).
2. **Schema-based isolation** — each tenant gets its own PostgreSQL schema,
   with physically separate tables. Isolation is enforced by the database
   itself via the connection's `search_path`, not by application code
   discipline.

Approach 1 was already implemented and understood from prior projects
(FarmLedger and earlier coursework) before this project began.

## Decision
DeskHive uses **schema-based multi-tenancy**, implemented via the
`django-tenants` library. Each tenant (`Client` model) maps to one
PostgreSQL schema. `TENANT_APPS` (currently `apps.tickets`) are migrated
into every tenant schema separately; `SHARED_APPS` (auth, admin, the
tenant/domain registry itself) live only in the `public` schema and are
made visible to every tenant via PostgreSQL's `search_path` fallback.

Tenant resolution happens via subdomain (`acme.localhost`,
`globex.localhost`), handled by `TenantMainMiddleware`, which sets the
correct `search_path` before any view code executes.

## Alternatives Considered
- **Row-level filtering (shared schema)** — rejected as the primary
  approach for this project specifically because the isolation guarantee
  depends entirely on every developer remembering to filter every query
  correctly, forever. A single missed `.filter()` is a real cross-tenant
  data leak. This approach remains valid and was deliberately explored
  first (Phase 1) to understand the trade-off firsthand, but was not
  chosen for DeskHive's actual implementation.
- **Database-per-tenant** — considered and deferred. Provides the
  strongest possible isolation but at significantly higher operational
  cost (connection pool exhaustion risk, per-tenant backup/migration
  orchestration). Documented as a possible Phase 5 evolution, not needed
  at current scale.

## Consequences
- **Positive**: isolation is enforced by PostgreSQL itself, not by
  application-code discipline. A missing filter cannot leak data across
  tenants for `TENANT_APPS` models.
- **Positive**: a single, physical proof of isolation was demonstrated in
  `apps/tickets/test_isolation.py` — creating data in one tenant schema
  and confirming zero visibility from another.
- **Negative**: migrations must be run per-schema (`migrate_schemas`, not
  plain `migrate`), which does not parallelize trivially and will need
  revisiting at scale (see future ADR on migration strategy).
- **Negative**: any code running outside the request/response cycle
  (background workers, management commands) has no automatic tenant
  context and must explicitly manage it — see ADR-0002.