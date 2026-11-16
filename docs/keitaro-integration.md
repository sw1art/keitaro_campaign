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
   filters/paginates in its own backend (cached briefly).
