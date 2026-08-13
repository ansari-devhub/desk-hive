# ADR-0002: Asynchronous SMS Delivery via Celery, Not Inline API Calls

## Status
Accepted

## Context
When a customer submits a support ticket, DeskHive should notify them via
SMS (using Africa's Talking) that their ticket was received. This requires
calling a third-party HTTP API from within the ticket-creation flow.

Calling a third-party API synchronously, inline with the request that
creates the ticket, would tie the availability and latency of DeskHive's
core function (accepting a support ticket) to the availability and latency
of an unrelated external service. If Africa's Talking is slow, rate-limited,
or down, a synchronous integration would make ticket creation itself slow
or fail — even though ticket creation has no functional dependency on SMS
delivery succeeding.

## Decision
SMS delivery is handled by a Celery task (`apps/tickets/tasks.py:
send_ticket_sms`), dispatched via `.delay()` from the DRF view's
`perform_create`, backed by Redis as the broker. The HTTP request that
creates the ticket returns as soon as the ticket is saved and the task is
queued — it does not wait for the SMS to actually send.

Because Celery workers run outside the Django request/response cycle, they
are never touched by `TenantMainMiddleware` and have no implicit tenant
context. The task therefore receives `schema_name` as an explicit string
argument (not a `Client` model instance — task arguments are serialized to
JSON and must be safely serializable) and re-establishes the correct
tenant context itself via `django_tenants.utils.schema_context(schema_name)`
before touching any tenant-scoped data.

## Alternatives Considered
- **Synchronous inline call** — rejected: couples ticket-creation
  reliability to a third-party service's reliability.
- **Django signal (`post_save` on `Ticket`)** — considered, and would work
  for the async-dispatch concern equally well, but rejected for a
  different reason: signals fire unconditionally for any code path that
  saves a `Ticket` (admin, shell, future bulk-import scripts), which is
  broader than intended. DeskHive's workflow calls for SMS notification to
  be tied specifically to ticket creation through the customer-facing API,
  not every possible write path. An explicit call in `perform_create`
  keeps the trigger point visible and intentional.

## Consequences
- **Positive**: ticket creation is fast and resilient to SMS provider
  downtime or latency.
- **Positive**: the tenant-context bug class (a worker silently operating
  against the wrong or default schema) was hit and fixed deliberately
  during development, rather than discovered later as a production
  incident.
- **Negative**: added operational dependency — Redis and at least one
  running Celery worker process are now required for the notification
  feature to function, in addition to the web server.
- **Negative**: failure handling is not yet automatic. If the SMS task
  fails (bad credentials, provider outage), it currently does not retry.
  Revisit with `autoretry_for` / `retry_backoff` once notification
  reliability matters beyond development.