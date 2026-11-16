# AdRobot Backend API contract

Base URL: `http://localhost:8000/api/v1`

All JSON. Errors use a unified shape:

```json
{ "error": { "code": "NOT_FOUND", "message": "..." } }
```

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
{ "operation_id": "6f4c...", "status": "pending", "message": "Campaign creation started" }
```

### `GET /campaigns` — list campaigns (live from Keitaro)

Query: `search`, `state`, `page` (default 1), `page_size` (default 20).

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
      "landings": []
    }
  ]
}
```

### `GET /campaigns/{id}/status` — creation operation status

`{id}` is the Keitaro campaign id (also accepts a local operation id). Returns an operation object (see below).

---

## Streams (editor)

### `GET /streams/{id}` — single stream

Same shape as an element of `GET /campaigns/{id}/streams`.

### `PUT /streams/{id}/offers` — replace offers and shares of a stream

Request:

```json
{ "offers": [ { "offer_id": 25327, "share": 100 }, { "offer_id": 25328, "share": 50 } ] }
```

- `share` must be an integer in `1..100` (verified against the live Keitaro; values `>100` and fractional values are rejected).
- `offer_id` must be positive, unique, and reference an active offer.

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
  "status": "pending",
  "campaign_id": null,
  "error": null,
  "created_at": "2026-11-16T19:46:32Z",
  "completed_at": null
}
```

Statuses: `pending` | `processing` | `completed` | `failed`.

On failure `error` is `{ "code": "KEITARO_STREAM_CREATION_FAILED", "message": "..." }`.

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

## Dashboard (composed by frontend)

Use `GET /campaigns?page_size=5` (sorted by `created_at` desc) for "latest campaigns" and `GET /operations?page_size=5` for "latest operations". Campaigns count = `total` from `GET /campaigns?page_size=1`.
