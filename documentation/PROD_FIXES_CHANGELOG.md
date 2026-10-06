# Production-Readiness Fixes: Change Log & Deployment Steps

These changes implement the findings in `PROD_READINESS_REVIEW.md` (6 Oct 2026).
Regression tests: `python -m pytest tests/test_prod_hardening.py test_dnac_fallback.py -q` (31 tests; 22 of them fail on the previous code).

## What changed

| Review item | Fix | Files |
|---|---|---|
| B1: delayed path lost results / always failed | Delayed flow moved to `workflow/delayed.py`; nodes wrapped with `safe_node`; reporter **merges** `results.<key>` so main-run results are kept | `workflow/delayed.py` (new), `workflow/api.py`, `workflow/run_delayed.py`, `node_reporter.py` |
| B2: `KeyError 'errors'` crashed graph | `safe_node` initialises `errors`; `result_data()` safe accessor; `GraphState` declares `errors` / `overall_status` | `workflow/utils/helpers.py`, `workflow/state.py` |
| B3: fail-open suppression | No silent mock classifier (opt-in `ALLOW_MOCK_CLASSIFIER` for tests only); model loaded at API startup; Agent 3 failure → Agent 4 escalates; no classification → escalate; missing / future timestamp no longer suppressed; delayed consumer never drops (DLQ or requeue) and reconnects | `node_agent_2.py`, `node_agent_3_scheduler.py`, `node_agent_4_servicenow.py`, `backdate_detector.py`, `consumer/consumer-delay-queue.py` |
| B4: issues query ignored device filter | `deviceId` param; refuses unfiltered query; match by issueId, then name **on that device only** | `app/dnac_client.py`, `workflow/tools/dnac_status.py` (new) |
| B5: wrong ID / endpoint | `issueId` extracted from `ciscoDnaEventLink` at ingest and carried end-to-end (`ISSUE_ID` Jenkins param); status via `GET /dna/data/api/v1/assuranceIssues/{id}` with device-scan fallback; one shared checker for workflow + dashboard | `app/main.py`, `app/dnac_client.py`, `jenkins_helpers.py`, `workflow/tools/dnac_status.py`, `dashboard/dnac_monitor.py` |
| B6: resolution webhooks treated as alerts | Supervisor routes `status=resolved/cleared/ignored` to the reporter; no SNOW action | `node_supervisor.py` |
| B7: Jenkins shell injection | Single-quoted `sh '''`; values read from env vars inside Python; API token from Jenkins credential; request timeout | `jenkins/Jenkinsfile.main`, `jenkins/Jenkinsfile.delayed` |
| B8: hard-coded RabbitMQ password | Removed; fails fast if env not set | `consumer/config/rabbitmq.py` |
| B9: no auth | Webhook: shared-secret header (`X-Webhook-Token`), added to DNAC subscription; subscription admin endpoints: `X-Admin-Token`; workflow API: `X-API-Token`; dashboard: CORS allow-list, simulate endpoint off, chat DNAC tool **GET-only + path allow-list** | `app/main.py`, `app/dnac_client.py`, `workflow/api.py`, `dashboard/api.py`, `dashboard/chat_agent.py` |
| H1/H2: silent message loss | Publisher confirms + `mandatory=True`; configurable `rabbitmq.routing_key`; webhook returns **503** if any event isn't published; handler runs in a thread pool | `app/mq_publisher.py`, `app/main.py`, `config.yaml` |
| H3: telemetry for the wrong device | `get_device_health` uses `/device-detail?identifier=uuid&searchBy=<uuid>` and `/network-device/{id}`; `cpu`/`memory` keys now populated | `app/dnac_client.py`, `dashboard/chat_agent.py` |
| H4: DNAC robustness | Timeouts on every call; 401 retry everywhere; status checked before JSON parse; CA bundle via `DNAC_CA_BUNDLE` | `app/dnac_client.py` |
| H5: ServiceNow | All calls raise on error (no create-on-lookup-failure); idempotency via `correlation_id`; exact device match; open = not Resolved/Closed/Canceled; reopen only Resolved (verified after PATCH); Closed → new linked incident; field values / states configurable by env; failure email | `workflow/tools/servicenow_client.py`, `node_agent_4_servicenow.py`, `node_email_notifier.py` |
| H6: duplicate Jenkins builds | Consumer no longer blocks 120 s for the build number (opt-in, 20 s); Jenkins TLS configurable | `consumer/noops_dnac_consumer.py`, `jenkins_helpers.py` |
| H7: API serialised | Workflow API endpoints are sync `def` (thread pool); bind to 127.0.0.1 | `workflow/api.py` |
| H8: missing deps | Added `uvicorn`, `langchain-openai`, `sentence-transformers` (5.7.0, compatible with transformers 4.57), `hdbscan` | `requirements.in`, `requirements.txt` |
| H9: fake data in prod | Simulated fallback off unless `DASHBOARD_ALLOW_SIMULATED=true` | `dashboard/api.py` |
| Medium items | `.env` no longer overrides real env; full payload logging opt-in; backdate age measured from webhook receipt (`received_at`); live-poll updated only its own document (was all alerts with the same eventId); Mongo `$regex` inputs escaped; chat no longer disables TLS process-wide; dashboard sync throttled for the DNAC rate limit | various |

## Deployment checklist (do these in order)

1. **Rotate the RabbitMQ password** for `svc_rabbitmq_noops_consumer` (it was in source control). Purge it from git history if the repo is shared.
2. **Create secrets** (see `.env.example`): `WEBHOOK_AUTH_TOKEN`, `INGEST_ADMIN_TOKEN`, `WORKFLOW_API_TOKEN`, plus DNAC / RabbitMQ / Jenkins / SNOW credentials.
3. **Jenkins:** add a *Secret text* credential with ID `false-alert-workflow-api-token` (same value as `WORKFLOW_API_TOKEN`). Run each job once so the new `ISSUE_ID` / `RECEIVED_AT` parameters register. Pin the jobs to the API host (agent label).
4. **RabbitMQ:** confirm the binding of `dnac.alerts.q` on `dnac.exchange` and set `rabbitmq.routing_key` to it (the consumer config mentions `router`). Confirm the `dnac.dlq` exchange exists and is bound.
5. **DNAC:** re-register the webhook (`POST /api/v1/subscriptions/register` with `X-Admin-Token`) so DNAC sends the auth header. Use an **https** receiver URL. Delete and re-create the subscription if it already exists by name.
6. **DNAC API version:** confirm `GET /dna/data/api/v1/assuranceIssues/{id}` exists on your release (2.3.7.x+). If not, the code falls back to the device-scoped `/issues` scan automatically. Check one real webhook payload has `ciscoDnaEventLink` containing `issueId=`.
7. **ServiceNow:** confirm `SNOW_CATEGORY` (current default `Inciden_Infrastructure & Network` looks like a typo), assignment group, CI `Network`, and state values. Check that the integration user can write `correlation_id`. Test create / append / reopen / closed→new on a non-prod instance.
8. **Run** the workflow API with `uvicorn workflow.api:app --host 127.0.0.1 --port 8001`. Check the startup log does **not** say "NO CLASSIFIER LOADED".
9. **Dashboard:** set `DASHBOARD_CORS_ORIGINS` to the real frontend URL. Put the dashboard behind SSO / a reverse proxy; it has no user authentication of its own.

## Behaviour changes to be aware of
- Alerts that previously were silently dropped (classifier missing, delay-queue down, no timestamp, SNOW lookup errors) now **create tickets or fail visibly**. Expect more tickets / failed Jenkins builds until the underlying issue is fixed. That is intended.
- New incidents use short description `Monitoring Alert: <device> - <issue>`. Existing `Monitoring Alert: <device>` incidents still match.
- Webhook calls without the token get **401**. Register the subscription with the token **before** enabling `WEBHOOK_AUTH_TOKEN` in prod, or set `ALLOW_UNAUTHENTICATED_WEBHOOK=true` briefly during cut-over.
