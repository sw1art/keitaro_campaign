# Architecture

AdRobot is a **modular monolith** (not microservices) with a separate **Worker** process.

```text
                 FRONTEND (Nuxt 3, SPA)
                        |
                        v
                FastAPI (REST /api/v1)
                        |
        +---------------+---------------+
        |               |               |
   campaigns        offers         streams
                        |
                Application layer
                        |
                   Domain layer
                        |
                Infrastructure
                 /           \
                v             v
          PostgreSQL       Keitaro API
                ^
                |
            RabbitMQ
                ^
                |
              Worker
```

## Layers (Clean Architecture)

- **`app/domain`** — entities (dataclasses), value objects (distribution, GEO/share
  validation), exceptions, repository ports. No FastAPI/SQLAlchemy/Keitaro deps.
- **`app/application`** — use cases (`CampaignCreationService`, `StreamService`),
  DTOs, service ports (`KeitaroClientProtocol`, `MessagePublisherProtocol`), payload
  builders (`campaign_builder.py` — the adapter logic that isolates Keitaro payloads).
- **`app/infrastructure`** — SQLAlchemy models/repositories, `KeitaroClient` (httpx),
  RabbitMQ publisher/consumer/topology, transactional outbox, GEO dictionary.
- **`app/presentation`** — FastAPI routers, Pydantic schemas, dependencies, error handlers.
- **`app/worker`** — the `campaign.create` message handler.

## Data model (PostgreSQL)

Keitaro is the source of truth for campaigns/streams/offers. AdRobot stores only what it
needs to manage operations and history:

- `campaigns` — local registry (`keitaro_id` unique).
- `operations` — async operation status, payload, partial result, error, attempts.
- `outbox_events` — transactional outbox for reliable event publishing.
- `audit_logs` — history of significant actions.

## Async campaign creation

1. `POST /api/v1/campaigns` validates input (against live Keitaro references) synchronously.
2. It writes an `Operation` (`pending`) and an `OutboxEvent` in **one transaction** and returns `202`.
3. A best-effort background task publishes the event to RabbitMQ; the Worker's outbox
   poller is the reliable fallback if the broker was down.
4. The Worker consumes `campaign.create`, runs `CampaignCreationService`, and updates the
   operation status (`processing` → `completed`/`failed`).

## RabbitMQ topology

- `adrobot.events` (direct) + `adrobot.dlx` (direct).
- `campaign.create` → main queue (dead-letters to `campaign.create.dlq`).
- `campaign.create.retry` → TTL queue that re-routes back to `campaign.create`.
- `campaign.create.dlq` → terminal queue for exhausted/failed tasks.

## Idempotency

Each event has a unique `event_id`; each operation has a unique `operation_id`. The
service commits progress (`keitaro_campaign_id`, `google_stream_id`, `offer_stream_id`)
to `operation.result` after each step, so a redelivered message reuses already-created
entities instead of creating duplicates. The handler returns `ack` for an operation that
is already `completed`.

## Security & hardening

- Optional shared-token auth (`ADROBOT_API_TOKEN`) enforced on every `/api/v1` request
  via `X-Api-Key` / `Authorization: Bearer`; disabled when the token is empty.
- Per-IP rate limiting (in-memory sliding window, `RATE_LIMIT_PER_MINUTE`).
- Security headers on every response (nosniff, frame deny, referrer policy, permissions).
- Secrets live only in `.env`; `check_secrets()` fails fast if `KEITARO_API_TOKEN` is missing.
- Backend validation of all inputs (GEO, offers, share `1..100`, domain active), independent
  of the frontend.

## Observability

- Every request gets a `X-Request-ID` correlation id (echoed or generated) and an access
  log line (method, path, status, duration, correlation id).
- Errors carry the correlation id in the response body and map to stable machine codes.
- `GET /healthz` (liveness) and `GET /readyz` (DB/RabbitMQ/Keitaro readiness).

## Optimistic concurrency (stream editing)

`GET /streams/{id}` returns a `fingerprint` of the current offers. The client sends it back
as `base_fingerprint` on `PUT /streams/{id}/offers`; a mismatch means the stream changed
since it was loaded and the backend returns `409` instead of overwriting someone else's
edit. The update itself re-reads the full stream right before the PUT, so other settings
are never lost.

