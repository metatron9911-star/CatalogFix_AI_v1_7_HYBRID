# CatalogFix Apify Control Bridge

Private control bridge between Railway and the CatalogFix Apify Actor.

It never exposes the Apify token. Requests require a separate `CONTROL_API_KEY`.

Endpoints:
- `GET /health` — public health check; no secrets
- `GET /v1/status` — Actor metadata/status
- `GET /v1/runs` — recent runs
- `GET /v1/runs/{runId}` — run metadata/status
- `GET /v1/runs/{runId}/logs` — run logs
- `GET /v1/runs/{runId}/summary` — `SUMMARY.json` from the run store
- `POST /v1/build` — trigger Actor build
- `POST /v1/run` — start Actor run
- `POST /v1/runs/{runId}/abort` — abort a run

Authentication for all `/v1/*` routes:

`Authorization: Bearer $CONTROL_API_KEY`

Required environment:
- `APIFY_TOKEN`
- `CONTROL_API_KEY`
- `APIFY_ACTOR_ID` (defaults to CatalogFix Actor ID)
