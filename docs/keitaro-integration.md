# Keitaro integration notes & verified findings

The live test instance is `https://tlgk.host/admin_api/v1`, authenticated with the
`Api-Key` header. All payload shapes below were verified by actually creating a
campaign and two flows (campaign id `212170`), and by exercising the offer editor
(`PUT /streams/{id}`).

## Verified endpoint behavior

| Endpoint | Verified behavior |
|---|---|
| `GET /campaigns` | Supports `query` (name substring) and `limit`/`offset`. Returns an array. |
| `POST /campaigns` | Requires unique `name` **and** unique `alias`. Returns `422` with the invalid field(s) otherwise. |
| `GET /campaigns/{id}` | Returns the same object as a list element. |
| `GET /campaigns/{id}/streams` | Returns the campaign's streams with `filters` and `offers`. |
| `GET /streams/{id}` | Returns one stream (same shape as the list element). |
| `POST /streams` | Accepts the payload produced by `campaign_builder.py` (verified). |
| `PUT /streams/{id}` | Full update. Replacing the `offers` array adds/removes offers. |
| `GET /offers` | Returns **all** offers (173 on the test instance). Query params (`limit`, `query`, `search`, `state`) are ignored — filtering/pagination is done in AdRobot. |
| `GET /domains` | Returns an array (one element in the test account: `1813` kylovoa.com). |
| `GET /traffic_sources` | Returns an array (one element: `836` FORTESTS). |
| `GET /groups?type=campaigns` | Returns campaign groups (includes `10332` FORTESTS). |
| `GET /stream_filters` | Contains the `country` filter (`modes.accept = "IS"`). |
| `GET /stream_schemas` | `landings`, `redirect`, `action`. |
| `GET /stream_types` | `regular`, `default`, `forced`. |
| `GET /streams_actions` | Includes `http` (field `url`, type `redirect`). |

## Task.md §14.3 checks — results

| # | Check | Result |
|---|---|---|
| 1 | Does the `country` filter accept ISO codes in `payload`? | **Yes** — `payload: ["AU","MX"]` accepted. |
| 2 | Actual `payload` format for POST/PUT | Arrays of ISO-2 strings for `filters`; `offers` is `[{offer_id, share, state}]`. |
| 3 | Is `action_options: {"url": ...}` used for `http`? | **No** — the URL goes in `action_payload` (string). `action_options` stays `null`. |
| 4 | Are `schema=redirect` + `action_type=http` enough? | **Yes** — plus `action_payload` (the URL). |
| 5 | Is `type=forced` correct? | Not used. Verified flows use `type=regular` with `position` ordering. |
| 6 | How are `position`/`weight` interpreted? | `position` orders the flows; `weight` is `0` for these ordered flows. |
| 7 | Does the second flow catch the rest of the traffic? | Ordering by `position` (Google `1`, Offer Flow `2`) is the routing model; the Offer Flow has no filters. |
| 8 | Required fields in a full PUT | `campaign_id, type, name, position, state, schema, action_type, action_payload, collect_clicks, filter_or, weight, offer_selection, filters[], triggers[], offers[], landings[]`. |
| 9 | How is offer removal handled? | Sending a smaller `offers` array removes the omitted offers. |
| 10 | Is `share=100` accepted and how are weights interpreted? | `share` must be an **integer in `1..100`**. `>100` → `422 "Share must be no more than 100"`; fractional → `422 "Share must be an integer"`. Distribution = `share / sum(shares) * 100`. |

## Consequences for the implementation

1. Campaign creation must generate a **unique `alias`** (AdRobot uses `adrobot-<operation-id-hex>`).
   The user-provided `name` must also be unique (Keitaro constraint); a conflict is surfaced
   as an operation error.
2. The redirect URL is written to **`action_payload`**, not `action_options`.
3. Flows are created with **`type="regular"`**, `position` 1 and 2, `weight=0`.
4. Offer `share` is validated as an **integer in `1..100`** in the domain layer.
5. `/offers` provides no server-side search/pagination, so AdRobot fetches the list and
   filters/paginates in its own backend (cached for 5 minutes, refreshable).

## Contract verification — point by point

The specific ambiguities called out in the task are resolved as follows (all against the
live instance):

| Concern | Verdict | Evidence |
|---|---|---|
| `POST /campaigns` `group_id` type | **Integer** | `group_id: 10332` (int) accepted; response echoes `"group_id":10332`. |
| `POST /streams` filter — is `id` required? | **No** | `filters: [{"name":"country","mode":"accept","payload":["AU","MX"]}]` accepted without `id`; the response adds `id`/`stream_id`/`oid`. |
| `GET /streams` `filters.payload` format | **Array of strings** | Verified `"payload":["AU","MX"]` in GET responses (not a string). |
| `PUT /streams/{id}` nested ids | **Strip read-only fields** | `id`, `stream_id`, `oid`, `created_at`, `updated_at` are not sent back; `build_stream_update_payload()` does this conversion inside the adapter. Verified add/remove works. |
| `cost_auto` for CPC | **`true` accepted** | Campaign created with `"cost_auto": true`; response echoes it. |
| `action_options` vs `http` | **`action_options` stays `null`** | The URL belongs in `action_payload` (string); the task's `action_options: {url}` shape is not used. |

Adapter rule (documented for the task): every Keitaro endpoint must have a verified
Request/Response example, and all Keitaro model conversion must live inside the adapter
(`app/infrastructure/keitaro/client.py` + `app/application/services/campaign_builder.py`).

## Routing verification

Routing model: flows are ordered by `position`; the first flow whose filters match wins,
otherwise the next flow is tried. The Offer Flow has **no filters**, so it is the fallback.

| Scenario | Expected | Verified how |
|---|---|---|
| Country is in selected GEO | Google Redirect | Filter `country` `accept` + `position=1` (config verified by API) |
| Country is NOT in selected GEO | Offer Flow | Offer Flow has no filters (fallback) |
| Country unknown / not resolved | Offer Flow (fallback) | Needs a live click test — see note |
| Multiple GEO selected | Google Redirect | `payload: ["AU","MX"]` accepted |
| Offers have different weights | split by `share / sum(shares)` | Formula is pure and unit-tested; `share` range verified |

> **Not fully automated yet:** a *real* click through the campaign URL (to observe the
> redirect target for a given visitor country, and the "unknown GEO" / "no offers" edge
> cases) requires driving actual traffic with known source IPs. The click URL for a
> campaign is `<domain>/<campaign-token>/<alias-or-params>`; the domain, token and alias
> are all available from the campaign object. This should be confirmed with a manual click
> test before production use.

## Custom Reports API (analytics) — verified

The report engine is available and used by the analytics module.

- Endpoint: **`POST /report/build`** (no other `/report*` paths exist).
- Request:

```json
{
  "range": { "from": "2026-11-09", "to": "2026-11-16", "timezone": "Europe/Moscow" },
  "metrics": ["clicks", "campaign_unique_clicks", "conversions", "leads", "sales", "rejected", "cr", "cost", "revenue", "profit", "roi", "epc", "cpa"],
  "grouping": ["offer_id"],
  "filters": [{ "name": "campaign_id", "operator": "EQUALS", "expression": "211913" }],
  "sort": [{ "name": "clicks", "order": "desc" }],
  "summary": true,
  "limit": 1000
}
```

- Response: `{ "rows": [...], "summary": {...}, "total": N }` (the `summary` row has `null`
  for the grouping key).
- Verified metrics: `clicks`, `campaign_unique_clicks`, `conversions`, `leads`, `sales`,
  `rejected`, `cr`, `cost`, `revenue`, `profit`, `roi`, `epc`, `cpa`.
- Verified grouping dimensions: `campaign_id`, `stream_id`, `offer_id`, `country`, `day`
  (`day` returns `YYYY-MM-DD` rows for time series; `datetime` returns raw event rows).
- Verified filters: array of `{ "name": <column>, "operator": "EQUALS", "expression": "<value>" }`.
- `unique_clicks` is NOT a metric name; the correct key is `campaign_unique_clicks`.
- The metrics/grouping set is limited to the tracker edition; AdRobot only relies on the
  verified list above.
