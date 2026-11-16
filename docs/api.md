# AdRobot Backend API contract

Base URL: `http://localhost:8000/api/v1`

All JSON. Errors use a unified shape:

```json
{ "error": { "code": "NOT_FOUND", "message": "...", "correlation_id": "..." } }
```

## Authentication (optional)

When the backend `ADROBOT_API_TOKEN` is set, every `/api/v1` request must send it as
`X-Api-Key: <token>` (or `Authorization: Bearer <token>`); otherwise the API returns
`401`. When the token is empty, auth is disabled. The frontend sends `NUXT_PUBLIC_API_TOKEN`
as `X-Api-Key` when configured.

Rate limiting (per client IP) is applied by default; exceeding it returns `429`.

Common list response shape:

```json
{ "items": [ ... ], "total": 123, "page": 1, "page_size": 20 }
```

---

## Campaigns

### `POST /campaigns` — start campaign creation (async)

Request:

```json
{
  "name": "Campaign Test",
  "geo": ["AU", "MX"],
  "offer_ids": [25327, 25328],
  "domain_id": 1813
}
```

- `name` required, trimmed, max 255.
- `geo` required, non-empty, ISO 3166-1 alpha-2 codes.
- `offer_ids` required, non-empty, unique.
- `domain_id` required positive int.

Response `202 Accepted`:

```json
{
  "operation_id": "6f4c...",
  "status": "pending",
  "message": "Campaign creation started",
  "warnings": []
}
```

`warnings` carries non-blocking advisories (e.g. selected GEO does not overlap the offers' GEO).

### `GET /campaigns` — list campaigns (live from Keitaro)

Query: `search`, `state`, `sort_by` (`id`|`name`|`state`|`created_at`|`updated_at`, default `created_at`), `sort_order` (`asc`|`desc`, default `desc`), `page` (default 1), `page_size` (default 20).

```json
{
  "items": [
    {
      "id": 212138,
      "name": "test_petrov_qa_create_1",
      "state": "active",
      "alias": "qa-create-1-6cf56e",
      "domain": "https://kylovoa.com/",
      "domain_id": 1813,
      "traffic_source_id": 836,
      "traffic_source": "FORTESTS",
      "group_id": 10332,
      "group": "FORTESTS",
      "cost_type": "CPC",
      "cost_value": 0,
      "cost_currency": "USD",
      "created_at": "2026-11-16 19:46:32",
      "updated_at": "2026-11-16 19:46:32"
    }
  ],
  "total": 194,
  "page": 1,
  "page_size": 20
}
```

### `GET /campaigns/{id}` — campaign details (live from Keitaro)

Same item shape as the list element, without the wrapper.

### `GET /campaigns/{id}/streams` — streams of a campaign

`{id}` is the Keitaro campaign id.

```json
{
  "items": [
    {
      "id": 1311444,
      "type": "regular",
      "name": "Flow 1",
      "campaign_id": 212138,
      "position": 1,
      "state": "active",
      "schema": "redirect",
      "action_type": "http",
      "action_payload": "https://www.google.com",
      "collect_clicks": true,
      "filter_or": false,
      "weight": 0,
      "offer_selection": "before_click",
      "filters": [ { "name": "country", "mode": "accept", "payload": ["RO"] } ],
      "offers": [
        { "offer_id": 10050, "state": "active", "share": 100 }
      ],
      "landings": [],
      "fingerprint": "sha256-of-sorted-offers"
    }
  ]
}
```

`fingerprint` is a stable hash of the current `(offer_id, share)` pairs, used for
optimistic concurrency on edits.

### `GET /campaigns/{id}/status` — creation operation status

`{id}` is the Keitaro campaign id (also accepts a local operation id). Returns an operation object (see below).

---

## Streams (editor)

### `GET /streams/{id}` — single stream

Same shape as an element of `GET /campaigns/{id}/streams`.

### `PUT /streams/{id}/offers` — replace offers and shares of a stream

Request:

```json
{
  "offers": [ { "offer_id": 25327, "share": 100 }, { "offer_id": 25328, "share": 50 } ],
  "base_fingerprint": "sha256-of-the-state-the-client-loaded"
}
```

- `share` must be an integer in `1..100` (verified against the live Keitaro; values `>100` and fractional values are rejected).
- `offer_id` must be positive, unique, and reference an active offer.
- `base_fingerprint` (optional) enables optimistic concurrency: if the stream's current
  offers fingerprint differs from it, the backend returns `409 CONFLICT` and the client
  should reload.

Response `200`: the updated stream (same shape as `GET /streams/{id}`).

The backend fetches the full current stream from Keitaro, replaces only `offers`, and sends the complete payload back via `PUT /streams/{id}` (no settings lost).

---

## Operations

### `GET /operations` — operation history

Query: `page`, `page_size`. Sorted newest first.

```json
{
  "items": [
    {
      "operation_id": "6f4c...",
      "type": "campaign.create",
      "status": "completed",
      "campaign_id": 212138,
      "error": null,
      "created_at": "2026-11-16T19:46:32Z",
      "completed_at": "2026-11-16T19:46:36Z"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20
}
```

### `GET /operations/{id}` — one operation

```json
{
  "operation_id": "6f4c...",
  "type": "campaign.create",
  "status": "completed",
  "campaign_id": 212138,
  "current_stage": "completed",
  "progress": 100,
  "error": null,
  "started_at": "2026-11-16T19:46:32Z",
  "finished_at": "2026-11-16T19:46:36Z",
  "created_at": "2026-11-16T19:46:32Z",
  "completed_at": "2026-11-16T19:46:36Z"
}
```

Statuses: `pending` | `processing` | `completed` | `failed` | `partially_failed` | `needs_attention`.

Saga stages (`current_stage` / `progress`): `creating_campaign` (20) → `creating_google_stream` (40) → `creating_offer_stream` (60) → `verifying` (80) → `completed` (100).

On failure `error` is `{ "code": "KEITARO_STREAM_CREATION_FAILED", "message": "..." }`.

### `POST /operations/{id}/retry` — re-enqueue a failed operation

Resets a `failed` operation to `pending` (keeping its partial result so already-created
entities are reused) and re-publishes its event. Returns `409` if the operation is not
`failed`.

### `GET /operations/{id}/audit` — audit trail for an operation

Returns `{ items: [AuditLogItem], total, page, page_size }` (actions ordered oldest first).

### `GET /audit-logs` — global audit trail

Query: `page`, `page_size`. Returns `{ items: [AuditLogItem], total, page, page_size }`.

`AuditLogItem`:

```json
{ "id": "...", "operation_id": "...", "action": "stream.create", "entity_type": "stream", "entity_id": "1311598", "details": {}, "created_at": "..." }
```

---

## Dashboard

### `GET /dashboard`

```json
{
  "campaigns_count": 203,
  "recent_campaigns": [ "CampaignItem..." ],
  "operations_total": 4,
  "operations_completed": 4,
  "operations_failed": 0,
  "recent_operations": [ "OperationItem..." ]
}
```

---

## Dictionaries

### `GET /dictionaries/geo` — countries

```json
{ "items": [ { "code": "AU", "name": "Australia" }, { "code": "MX", "name": "Mexico" } ] }
```

### `GET /offers` — offers (server-side search/filter/pagination)

Query: `search` (matches name or id), `state` (default `active`), `page`, `page_size`.

```json
{
  "items": [
    {
      "id": 25327,
      "name": "25327 Flexacil ...",
      "state": "active",
      "country": ["Peru"],
      "group": "JO Flexacil PE",
      "affiliate_network": "59"
    }
  ],
  "total": 173,
  "page": 1,
  "page_size": 20
}
```

### `GET /domains` — domains

```json
{ "items": [ { "id": 1813, "name": "kylovoa.com", "state": "active", "is_ssl": true, "ssl_status": "issued" } ] }
```

### `GET /traffic-sources` — traffic sources

```json
{ "items": [ { "id": 836, "name": "FORTESTS", "state": "active" } ] }
```

---

## Analytics (Keitaro Custom Reports)

All analytics endpoints accept: `range` (`today`|`yesterday`|`last_7_days`|`last_30_days`|`custom`, default `last_7_days`), optional `from`/`to` (for `custom`), `timezone` (default `Europe/Moscow`).

Metrics: `clicks`, `campaign_unique_clicks`, `conversions`, `leads`, `sales`, `rejected`, `cr`, `cost`, `revenue`, `profit`, `roi`, `epc`, `cpa`.

### `GET /analytics/overview`

```json
{
  "range": { "from": "...", "to": "...", "prev_from": "...", "prev_to": "...", "timezone": "Europe/Moscow" },
  "metrics": { "clicks": 29, "campaign_unique_clicks": 11, "conversions": 0, "...": 0 },
  "deltas": { "clicks": 100.0, "conversions": null, "...": null }
}
```

### `GET /analytics/trends`

`{ "range": {...}, "items": [ { "day": "2026-11-16", "clicks": 19, "conversions": 0, "revenue": 0, "cost": 0, "profit": 0, "roi": 0, "cr": 0 } ] }`

### `GET /analytics/campaigns/{id}`

`{ "range": {...}, "campaign_id": 211913, "metrics": {...}, "streams": [...], "offers": [...], "geo": [...] }`

### `GET /analytics/offers?campaign_id=&range=...`

`{ "range": {...}, "campaign_id": null, "items": [ { "offer_id": 10184, "offer_name": "...", "offer_state": "active", "clicks": 13, "...": 0, "planned_share": 50.0, "actual_share": 100.0 } ] }`

`planned_share` / `actual_share` are present only when `campaign_id` is provided (planned = offer `share` in the Offer Flow, actual = share of clicks).

### `GET /analytics/geo?campaign_id=&range=...`

`{ "range": {...}, "items": [ { "country": "Netherlands", "clicks": 13, "conversions": 0, "cr": 0, "revenue": 0, "cost": 0, "profit": 0, "roi": 0, "epc": 0, "cpa": 0 } ] }`

### `GET /analytics/export?type=&campaign_id=&range=&from=&to=`

Downloads a CSV (`type`: `campaigns`|`offers`|`geo`|`streams`).

## System

- `GET /healthz` (and `GET /health/live`) — liveness (no dependency checks).
- `GET /readyz` (and `GET /health/ready`) — readiness; checks database, RabbitMQ and Keitaro, returns `200` when all are ok or `503` with per-dependency status.
- `GET /health/keitaro` — checks Keitaro reachability only.

### `POST /dictionaries/refresh` — clear reference cache

Clears the in-memory cache for offers/domains/traffic sources (TTL is 5 minutes by default).

