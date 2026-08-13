# ADR-0003: `Customer` as a Standalone Model, Not Tied to Django's `User`

## Status
Accepted (revisit when customer self-service login is introduced)

## Context
DeskHive needs to record who a support ticket belongs to — a name, an
email, and (later) a phone number for SMS notification. Django provides a
built-in `User` model, and an early draft of the `Customer` model linked to
it via a foreign key.

Two distinct kinds of accounts exist in this system's domain, with
different needs:
- **Agents** — internal staff who log into DeskHive to manage tickets.
  They need real authentication.
- **Customers** — external end users who submit tickets. At the current
  stage of the project, they do not log in anywhere; a ticket is
  effectively a contact form submission.

## Decision
`Customer` is a standalone model (`name`, `email`, `phone_number`) with no
foreign key to `User` and no authentication capability. `Agent` retains its
`OneToOneField` to `User` (via `settings.AUTH_USER_MODEL`), since agents
are genuine authenticated users of the system.

## Alternatives Considered
- **`Customer.user` as a `ForeignKey`/`OneToOneField` to `User`** —
  rejected for the current phase: it would force every customer to have
  Django auth credentials before submitting a ticket, which is not part of
  the current workflow and adds unnecessary complexity (password
  management, login flow, session/JWT handling) for a feature that does
  not yet need it.
- **Custom `User` model with a `role` field distinguishing agents from
  customers** — considered as a more "correct" long-term architecture
  (see project discussion on `AbstractUser` vs. profile models), but
  explicitly deferred: `AUTH_USER_MODEL` must be set before the first
  migration ever runs, and DeskHive had already migrated with the stock
  `User` model by the time this was discussed. Switching now would require
  a full database reset. Recorded here as a known future option, not a
  rejected one.

## Consequences
- **Positive**: no unnecessary auth coupling; customers can submit tickets
  without an account, matching the actual current workflow.
- **Negative**: if customer self-service (e.g., a portal where customers
  log in to view their own ticket history) is added later, this decision
  will need to be revisited deliberately — likely via a proper profile
  model pattern (`CustomerProfile` with a `OneToOneField` to `User`) rather
  than retrofitting a `User` FK directly onto `Customer`, to avoid
  disrupting existing `Customer` records that have no associated account.