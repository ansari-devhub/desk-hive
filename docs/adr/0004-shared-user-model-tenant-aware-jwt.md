# ADR-0004: Shared `User` Model with a Tenant-Aware JWT Authentication Class

## Status
Accepted

## Context
DeskHive needs JWT-based authentication for agents. Two structurally
different identity models were available:

1. **Shared `User`** (current state, per ADR-0001/ADR-0003) — `auth.User`
   lives in `SHARED_APPS`, one physical table, visible from every tenant
   schema via PostgreSQL's `search_path` fallback. `Agent` (the tenant-scoped
   profile linking a `User` to a specific organization) lives in
   `TENANT_APPS`, with separate rows per schema.
2. **Tenant-scoped `User`** — moving `auth.User` itself into `TENANT_APPS`,
   giving each tenant a fully separate, unrelated `auth_user` table.

This decision determines what "the same person" means across tenants, and
directly affects how JWT authentication must be implemented, since a JWT
authenticates against whichever `User` table is reachable at the time.

## Decision
`User` remains shared (unchanged from the existing architecture). This
means the same human can hold an `Agent` profile in more than one tenant
schema — e.g., a person contracting as support staff for both Acme and
Globex — represented as one shared identity with two independent,
tenant-scoped `Agent` rows.

Because a shared `User` is authenticable from *any* tenant schema
regardless of whether that user has any relationship to it (PostgreSQL's
`search_path` makes the lookup succeed everywhere by design — this is
correct behavior for a shared table, not a bug), default JWT authentication
alone cannot answer "does this authenticated user actually belong to the
tenant this request is for." A custom authentication class
(`TenantAwareJWTAuthentication`) wraps `simplejwt`'s default behavior and
adds an explicit check: after the token is verified and the shared `User`
is resolved, the request is only accepted if an `Agent` row exists for that
`User` in the *currently active* tenant schema (i.e., in `TENANT_APPS`,
correctly isolated per schema). A valid token for a real user with no
`Agent` profile in the requested tenant is rejected.

## Alternatives Considered
- **Tenant-scoped `User`** — each tenant gets a fully independent
  `auth_user` table. Rejected for DeskHive's current identity model: it
  would treat the same person working at two organizations as two
  unrelated accounts with no shared identity, coincidentally matching
  usernames. This is a legitimate design for products where per-workspace
  identity is the intended model (e.g., Slack-style accounts), but does not
  match DeskHive's intended "one person, multiple tenant relationships"
  model. Would also require duplicating password-reset and any future
  single-identity flows per tenant.
- **No additional check, rely on `search_path` alone** — rejected: proven
  insufficient. `search_path` determines *where* a query looks, not
  *whether the result implies tenant membership*. A shared-table lookup
  succeeding from any schema is expected, correct behavior for shared data,
  and specifically cannot be used as a tenant-membership check.

## Consequences
- **Positive**: preserves a single, coherent identity per human across all
  their tenant relationships — matches the intended product model.
- **Positive**: the missing-membership gap is closed at the authentication
  layer, in one place, rather than needing to be re-checked in every view.
- **Negative**: every view relying on JWT auth now depends on this custom
  authentication class rather than `simplejwt`'s default — any future
  contributor adding a new endpoint must not silently revert to the
  default `JWTAuthentication` class, or the membership check is lost
  without any obvious error until a real cross-tenant token is tested.
- **Negative**: a valid, unexpired token can still be rejected
  (`AuthenticationFailed`) purely because the request targets the wrong
  tenant's subdomain — this must be handled clearly in any client
  application to avoid confusing "your session expired" messaging when the
  real cause is "wrong tenant."