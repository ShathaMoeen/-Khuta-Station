# KHUTA RFID / NFC integration

## Backend address

Use the backend base URL provided by the KHUTA deployment owner. For a local development run, the documented command serves `http://127.0.0.1:8000`. The ESP32 must use a reachable LAN/deployment address rather than `127.0.0.1`.

The reader sends a card tap to `POST /taps`. This is the same FastAPI route used by the browser simulator; there is no RFID-specific AI pipeline.

## Card identifiers

Demo cards created through `POST /visitors` receive an ID in the form `KH-` plus 12 uppercase hexadecimal characters. In production, an authorized onboarding client may register the RFID UID itself as `card_id`; subsequent tap calls send that exact stored ID. A raw unknown UID is rejected. Never place a visitor's language, level, identity, or interests in the UID.

## Station identifier

Send the stable station `code`, for example `WAHY-01` or `BADR-01`. Do not send the database's numeric station ID. The current exhibition station codes can be listed with `GET /stations`.

## Create a demo visitor session

```http
POST /visitors
Content-Type: application/json

{"lang":"ar","level":"beginner","consent":true}
```

Example response:

```json
{"card_id":"KH-4A91B6D02C7F","expires_at":"2026-10-05T20:00:00+00:00"}
```

The demo visitor session lasts 12 hours. Consent is required. For a physical UID registration, provide `card_id` and include the production device bearer token.

## Tap a station

```http
POST /taps
Content-Type: application/json
Authorization: Bearer <DEVICE_API_KEY>

{
  "card_id":"KH-4A91B6D02C7F",
  "station_code":"WAHY-01",
  "request_id":"reader-03-0001842"
}
```

`request_id` is an idempotency key. Keep the same value when retrying a timed-out request; a repeated request returns the original interaction instead of inserting a duplicate. If the reader cannot preserve request IDs, it should not automatically replay a timed-out tap.

The success response includes the interaction ID, selected controlled fallback or validated AI explanation, visitor profile, database-backed citations, permitted media, crowding estimate, and next-station recommendation. Values are produced per request; the following is a response shape, not a captured database transcript:

```text
{
  "interaction_id": <database interaction id>,
  "request_id": "reader-03-0001842",
  "idempotent_replay": false,
  "station": {"id": <id>, "code": "WAHY-01", ...},
  "visitor": {"card_id": "<demo-card>", "language": "ar", "level": "beginner", ...},
  "content": {"title": "<controlled station title>", "body": "<controlled fallback>", ...},
  "personalized_explanation": "<validated generated text or controlled fallback>",
  "explanation_source": "ai or controlled_fallback",
  "ai_generated": false,
  "sources": ["<retrieved PostgreSQL citations, with current rights/verification state>"],
  "media": ["<verified and permitted assets only>"],
  "crowding": {"status": "<derived estimate>"},
  "recommended_station": {"recommended_station": "<station code>", ...}
}
```

The response's actual sources, content, crowding and recommendation are computed from PostgreSQL. `ai_generated` is true only after a configured provider returns a valid structured answer whose source IDs and citation metadata pass validation. In the current database, source records remain unverified and rights need review; station-mapped citations are returned with that state visible. The media registry is empty, so no media is returned. In production, taps require `Authorization: Bearer <DEVICE_API_KEY>`.

## Errors

| HTTP | Meaning | Reader action |
|---:|---|---|
| 400 | Invalid consent or registration input | Correct registration payload |
| 401 / 403 | Invalid device key or missing consent | Stop and ask the operator |
| 404 | Unknown/expired card or unknown station | Ask the visitor to re-register or verify station code |
| 409 | Reused request ID belongs to a different tap | Generate a new request ID; do not change it for a retry |
| 422 | Malformed request | Correct JSON and field values |
| 429 | Rate limited | Wait before sending another request |
| 503 | Production device authentication is not configured | Contact the backend operator |

The AI provider is not required for tap success. When unavailable, the backend returns the approved controlled station text and sets `ai_generated=false`.

## Timeout and retry

The request includes database work and may call a provider with a 30-second client timeout. Use a 35-second HTTP timeout. Retry once after a transport timeout using the *same* `request_id`; never mint a new ID for that retry. The backend rate limit is 60 requests per minute per client address. The reader only needs to read the UID, send the stored card ID and station code, and present the returned screen data.

## Related compatibility routes

`POST /stations/{station_id}/interact` and `POST /interactions` remain available for existing clients and delegate to the same tap service. `POST /interactions/{interaction_id}/duration`, `GET /visitors/{card_id}/summary`, and `DELETE /visitors/{card_id}` remain available. The root `app_server.py` imports this same FastAPI application.
