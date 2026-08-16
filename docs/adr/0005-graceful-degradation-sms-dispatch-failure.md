# ADR-0005: Graceful Degradation When SMS Task Dispatch Fails

## Status
Accepted

## Context
`send_ticket_sms.delay(...)` requires a live connection to the Celery
broker (Redis) to enqueue the task. If the broker is unavailable, `.delay()`
raises a connection error immediately, synchronously, inside the view — at
the exact point where the `Ticket` itself has already been successfully
created and committed to the database.

Left unhandled, this exception propagates out of `TicketViewSet.create()`
and DRF returns a `500 Internal Server Error` to the client. This is
misleading: the primary resource (the ticket) was created successfully:
only the secondary, best-effort notification failed to queue. A client
seeing a `500` has no way to know the operation actually partially
succeeded, and a naive retry risks creating a duplicate ticket for a
request that, in fact, already worked.

## Decision
`TicketViewSet.create()` wraps the `.delay()` call in its own `try/except`,
separate from the ticket-creation logic. A broker failure:

1. Is logged via `logger.error(...)`, so the failure is discoverable
   through server-side logs/monitoring even though the client is not shown
   the technical error.
2. Does **not** fail the request. The response remains `201 Created` — the
   ticket genuinely was created.
3. Is surfaced to the client as a non-fatal `warning` field added to the
   otherwise-normal serialized ticket response, e.g.
   `"warning": "Ticket created, but SMS notification could not be queued."`
   — allowing a client application to distinguish "fully succeeded" from
   "succeeded with a non-critical caveat" without treating the request as
   failed.

This required overriding `create()` directly rather than using
`perform_create()`, since `perform_create()`'s return value is discarded by
DRF's default `create()` implementation and offers no hook to modify the
response body.

## Alternatives Considered
- **Let the exception propagate (`500`)** — rejected: actively misleading,
  since the primary resource did succeed; also encourages unsafe client
  retries that could produce duplicate tickets.
- **Silently swallow the failure with no client-facing signal** — rejected:
  solves the "don't fail the request" problem but leaves the client with no
  way to know a customer might not receive their expected SMS
  confirmation, which could itself cause confused support follow-up.
- **Synchronous fallback (attempt the SMS send directly if queuing fails)**
  — rejected: reintroduces the exact coupling to a third-party API's
  availability that ADR-0002 was written to avoid; a broker outage is not
  a good moment to also block the request on a live network call to
  Africa's Talking.

## Consequences
- **Positive**: ticket creation is resilient to broker downtime; the
  client always receives an accurate status for the resource it actually
  requested.
- **Positive**: the failure is both logged (for operators) and surfaced
  (for clients), rather than being visible to only one audience.
- **Negative**: no automatic retry or recovery path exists yet for a
  ticket whose SMS failed to queue at creation time — the notification for
  that specific ticket is simply never sent unless a future mechanism
  (e.g. a periodic reconciliation task scanning for unnotified tickets) is
  added.
- **Negative**: any future endpoint that also dispatches a Celery task
  inline with a request must apply this same pattern deliberately — it is
  not automatically enforced framework-wide, and a new view could
  reintroduce the original `500` failure mode by omission.