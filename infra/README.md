# Local Infra

This folder holds the local infra entry points expected by the challenge materials.

## Cal.com

Start the self-hosted Cal.com stack:

```bash
docker compose -f infra/docker-compose.yml up -d
```

After the containers are healthy:

1. Open your local Cal.com app URL, for example `http://127.0.0.1:3001` or `http://127.0.0.1:3004`
2. Complete the first-run setup wizard
3. Create an API key in Cal.com settings
4. Create or confirm the event type slug you want the agent to use
5. Put the resulting values in `.env`

This compose file starts the Cal.com web app and Postgres only. It does not provide a separate API service on `3003`.
If you want to use `CALCOM_API_BASE_URL=http://127.0.0.1:3003`, run a real Cal.com API process there and keep `3003` free.

Expected `.env` fields for this repo:

- `CALCOM_BASE_URL=http://127.0.0.1:3004`
- `CALCOM_APP_BASE_URL=http://127.0.0.1:3004`
- `CALCOM_API_BASE_URL=http://127.0.0.1:3003`
- `CALCOM_API_KEY=cal_...`
- `CALCOM_EVENT_TYPE_SLUG=tenacious-discovery`
- `CALCOM_USERNAME=<your_calcom_username>`
- `CALCOM_WEBHOOK_SECRET=<shared_secret_used_by_your_webhook>`

If you want Cal.com to call back into the operator server, register:

```text
http://127.0.0.1:8000/api/calcom-webhook
```

The current Python client supports:

- direct booking creation through `POST /v2/bookings`
- fallback probing for `POST /api/v2/bookings` when the API server is mounted with an `/api` prefix
- inbound webhook handling for booking create, cancel, and reschedule events

If the Docker stack is down and `CALCOM_FALLBACK_ENABLED=true`, the repo falls back to a clearly labeled simulated booking artifact instead of pretending a real booking succeeded.
