# ADR-0006: Tenant-Scoped JWT Tokens (Superseding Part of ADR-0004)

## Status
Accepted — amends ADR-0004

## Context
ADR-0004 established a shared `User` model with a custom authentication
class (`TenantAwareJWTAuthentication`) that checks, on every request,
whether the authenticated user has an `Agent` profile in the currently
active tenant schema. This correctly blocked users with no relationship to
a tenant from accessing its data.

However, testing surfaced a real gap: a token was checked only against
*membership* ("does this user have an Agent profile here"), never against
*where the token was issued*. A user who is legitimately an agent at both
`acme` and `globex` — a deliberately supported scenario per ADR-0004 —
could obtain a single token by logging in through either tenant's
subdomain, and that same token would then be accepted at *both* tenants
interchangeably. A token obtained via `acme.localhost` was never expected
to work at `globex.localhost`, but nothing prevented it. Separately, the
login endpoint itself (`TokenObtainPairView`) performed no tenant-
membership check at all — any user with valid Django credentials could
obtain a token while talking to any tenant's subdomain, regardless of
whether they had any `Agent` profile there, with the mismatch only ever
caught later, on the next request that tried to use the token.

## Decision
JWT tokens are now scoped to the specific tenant schema they were issued
from, enforced at two points:

1. **At login** (`TenantScopedTokenObtainPairSerializer`): token issuance
   itself now fails with a validation error if the authenticating user has
   no `Agent` profile in the tenant schema currently active on the
   connection (`connection.schema_name`, set by `TenantMainMiddleware`
   before this code runs). A user with no relationship to a tenant can no
   longer obtain a token there at all, not just be blocked on later use.
2. **At authentication** (`TenantAwareJWTAuthentication`, updated): the
   token now carries a `schema_name` custom claim, embedded at issuance.
   On every subsequent request, the authentication class checks that this
   claim matches `connection.schema_name` for the request currently being
   processed, in addition to the pre-existing `Agent`-membership check. A
   token issued at `acme.localhost` is rejected outright at
   `globex.localhost`, even for an agent who legitimately belongs to both.

A dual-org agent must now log in separately per tenant to obtain a
separately-scoped token for each — this is a deliberate trade-off, not an
oversight.

## Alternatives Considered
- **Leave tokens person-scoped, not tenant-scoped (original ADR-0004
  behavior)** — rejected on further review: a leaked or stolen token would
  be valid at every organization that person works for, not just one,
  unnecessarily widening the blast radius of a credential compromise for
  no corresponding benefit — the convenience of one login working
  everywhere was not worth that trade-off once identified.
- **Check membership only at authentication time, not at login** —
  rejected: this was the original state, and it allowed the login endpoint
  itself to succeed for users who would immediately fail every subsequent
  request, which is both a confusing API experience and unnecessary
  server-side token issuance for a credential that can never be used
  successfully.

## Consequences
- **Positive**: closes the cross-tenant token reuse gap. A compromised
  token's blast radius is now limited to the single tenant it was issued
  for.
- **Positive**: login failures for non-members now happen at the login
  step itself, with a clear error, rather than surfacing confusingly on a
  later, unrelated request.
- **Negative**: a genuinely dual-org agent must authenticate separately per
  tenant and manage two distinct tokens/sessions if working across both
  simultaneously — a deliberate increase in friction, accepted in exchange
  for the tighter security boundary.
- **Open question, not yet resolved**: the `public` schema is itself a
  real, registered tenant (`Domain: localhost`), not specially exempted.
  If any `Agent` row ever exists in the `public` schema, `/api/token/` at
  the bare domain becomes a fully legitimate, working login path, since
  none of the above checks distinguish `public` from any other tenant.
  Whether the `public` schema should be allowed to issue API tokens at
  all, or should be explicitly reserved for platform-admin (Django
  `/admin/`) use only, is a decision this ADR deliberately leaves open for
  a future revision once that question is deliberately settled.