# False Alert Suppression: Backend Production-Readiness Review

**Date:** 6 Oct 2026  **Scope:** `app/` (DNAC webhook ingest), `consumer/`, `workflow/` (LangGraph agents, ServiceNow, delayed check), `jenkins/`, the dashboard backend (`dashboard/*.py`), `config.yaml`, `requirements.txt`
**Method:** I read the code line by line. Then I ran the LangGraph flow and the delayed-check API in a sandbox with DNAC, RabbitMQ, ServiceNow and MongoDB stubbed out. I checked the DNAC API paths and parameters against Cisco's Catalyst Center docs and the official `dnacentersdk` (v2.3.7.9).

> **Verdict: not ready for production.** There are 9 blockers. Several of them let a *genuine* alert end with no ServiceNow ticket and no visible error. For a suppression system that's the worst way to fail.

Tags: **[Verified]** = reproduced at runtime. **[Code]** = clear from reading the code. **[Verify on your DNAC]** = depends on your DNAC/SNOW version or setup, so please check it.

---

## 1. Blockers (fix before prod)

### B1. Delayed-check path loses its result and always fails in Jenkins [Verified]
`workflow/api.py:258` and `workflow/run_delayed.py:266` both do `initial_state = email_notifier(initial_state)`. `email_notifier` returns `{"ok":..,"data":..,"remarks":..}`, not the state, so the alert and its results are thrown away before `reporter()` runs. The effects:
- The response comes back as `overall_status="unknown"` with `results={}`. Every delayed Jenkins build exits 1, even when a ticket was raised.
- MongoDB saves the record under `alert_id="unknown_event_id"` with no alert details, so dashboard KPIs for auto-resolve outcomes are wrong.

Also, `agent_4_servicenow` is called directly without `safe_node`, so its result has no `status` key and is never counted.
**Fix:** wrap both calls with `safe_node(...)` and keep `state` as the return value. Don't reassign from `email_notifier`.

### B2. Any node exception crashes the whole graph [Verified]
In `workflow/utils/helpers.py:58`, `safe_node` appends to `state["errors"]`, but it only ever initialises `state["remarks"]` (as a dict). The first exception in any node raises `KeyError('errors')` and aborts the run. Reproduced with an alert that has no description: **CRASH: KeyError 'errors'**.

It's triggered easily. Agents 3 and 4 do `agent2_result.get("data", {}).get(...)`, and when Agent 2 fails, `data` is `None` (the key exists, so the default `{}` is not used). That gives an `AttributeError`, then the `KeyError`, then the graph aborts and **no ticket is raised**.
**Fix:** `state.setdefault("errors", [])`, use `(x.get("data") or {})` everywhere, and add `errors` and `overall_status` to `GraphState`. LangGraph currently drops `overall_status` (verified: it returns `None`).

### B3. Several fail-open paths suppress genuine alerts with no ticket [Verified / Code]
| Path | What happens |
|---|---|
| ML model fails to load (`node_agent_2.py:367`) | Falls back to `MockClassifier`, which labels **every** alert *Auto resolving* at 0.92 confidence and still reports `used_model: ML_TFIDF`. Verified: "Core router chassis power supply failed" was classified Auto resolving. |
| Agent 3 cannot publish to the wait queue | Agent 4 still skips SNOW because the prediction is Auto resolving. The alert is never delayed-checked and never ticketed (verified). The `except` branch in `node_agent_3_scheduler.py` has no `return`, so a crash there is recorded as **success**. |
| Missing or invalid timestamp (`backdate_detector.py:360`) | Marked "backdated" and suppressed. The comment calls this "fail closed", but for alerting it is fail-open. |
| Agent 2 gives no category (`node_agent_4_servicenow.py:171`) | Agent 4 returns "Skipped". |
| Delayed consumer fails (`consumer-delay-queue.py:360`) | `basic_nack(requeue=False)` on `dnac.alerts.delayed.q`, which has **no DLX**, so the message is deleted. The consumer also has no reconnect loop; any broker blip during consume kills the process. |

**Fix (principle):** any uncertainty or failure should escalate to SNOW, not suppress. Refuse to start if the model is missing. Route "unknown" outcomes to Agent 4. Give the delayed queue a DLQ and a reconnect loop.

### B4. DNAC issue lookup ignores the device filter [Code + SDK verified]
`app/dnac_client.py:296-299` sends `deviceUuid` and `deviceName` to `GET /dna/intent/api/v1/issues`. The API only accepts `deviceId` (plus `siteId`, `macAddress`, `priority`, `issueStatus`, `aiDriven`, `startTime`, `endTime`), and unknown parameters are ignored. So the "device fallback" check really searches the **whole network's** issues. It then uses a loose substring `is_match` (`target in itext or itext in target`) on generic names like "Device unreachable".

**Impact:** a still-active alert on switch A can be marked *resolved* because switch B has a resolved issue with the same name, and the alert is suppressed.
**Fix:** use `deviceId`. Match on the issue ID first, then on the name **and** the device.

### B5. The primary status check uses the wrong ID and the wrong endpoint [Code; Verify on your DNAC]
`get_issue_status(instance_id)` calls `GET /dna/intent/api/v1/issues/{id}`, and there are two problems:
1. That GET-by-ID path isn't in the documented Intent API or the SDK. Single-issue lookups are `GET /dna/data/api/v1/assuranceIssues/{id}` (2.3.7.x and later) or `GET /dna/intent/api/v1/issue-enrichment-details` (with `entity_type=issue_id` and `entity_value` headers).
2. The webhook's `instanceId` is the *event-notification* instance, not the Assurance `issueId`. In real DNAC payloads the issue ID appears in `ciscoDnaEventLink` (`...issueDetails?issueId=<id>`).

**Net effect:** the primary check never works, so every delayed check goes to the broken fallback in B4.
**Fix:** at ingest, pull `issueId` out of `ciscoDnaEventLink` and pass it through RabbitMQ, Jenkins and the API. Then query the correct endpoint for your DNAC version.

### B6. Resolution notifications are treated as new alerts [Code]
DNAC sends a second webhook when an issue clears (`details."Assurance Issue Status": "resolved"`; see `test_payloads.md` #2 and #5). No part of the pipeline checks `status`. A "resolved" event is classified like a new one and can append to, reopen or create a SNOW incident.
**Fix:** route `status == resolved` events to a separate path that only updates or closes the stored record. This also gives you a cheaper resolution signal than polling after 15 minutes.

### B7. Shell injection in both Jenkinsfiles [Code]
`Jenkinsfile.main:64` and `Jenkinsfile.delayed:153` use Groovy `"${params.ISSUE_DETAILS}"` (and the other parameters) inside `sh """ ... """`. The values come from webhook text. A description containing `"`, `` ` `` or `$(...)` runs commands on the Jenkins agent, and the webhook is unauthenticated (B9).
**Fix:** use single-quoted `sh '''...'''` and read the values from the environment (`os.environ['ISSUE_DETAILS']`), or use `withEnv`. Never interpolate them into the shell.

### B8. Hard-coded RabbitMQ password in source [Code]
`consumer/config/rabbitmq.py:23` has `RABBIT_PASS` defaulting to `"JustCheck@2025"` for `svc_rabbitmq_noops_consumer`. **Rotate the password** and remove the default; fail fast if it isn't set.

### B9. No authentication on any HTTP surface [Code]
- **Webhook receiver** `:8000/api/v1/webhook`: plain HTTP, no shared secret or header check. Anyone on the network can inject alerts, which feeds B7.
- **Workflow API** `:8001/api/v1/invoke*`: bound to `0.0.0.0` with no auth. Anyone can create or reopen SNOW incidents.
- **Dashboard API**: `CORS *`, no auth. `/api/chat` gives the LLM a `call_dnac_rest_api` tool that can **POST to any DNAC endpoint** using the service account. Alert text is in the LLM's context, so this is a prompt-injection path to DNAC. `/api/alerts/simulate` is also exposed.

**Fix:** add a header token to the DNAC subscription and validate it. Use HTTPS. Bind 8001 to 127.0.0.1. Put the dashboard behind SSO. Make the chat tool GET-only with an allow-list of paths.

---

## 2. High priority

**H1. Main publisher's routing key probably doesn't match the binding [Verify on RabbitMQ].** `app/mq_publisher.py` publishes to `dnac.exchange` with routing key `dnac.alerts.q`. The consumer config says the binding key is `router` (`RK_MAIN`, "matches your binding output"). There are no publisher confirms and no `mandatory=True`, so unroutable messages are **silently dropped** while the webhook returns 200. Check the binding, and turn on `confirm_delivery()` with `mandatory=True`.

**H2. The webhook returns 200 even when nothing was published** (`app/main.py:138`), so DNAC never retries. The handler is also `async` but calls blocking pika with `time.sleep` retries (up to about 62 s), which freezes the event loop for every request. Return 503 when `published < len(events)` and make the handler `def`.

**H3. Device telemetry is for the wrong device [Docs verified].** `GET /dna/intent/api/v1/device-health` has **no `deviceId` parameter**, so it returns a page of all devices and `get_device_health` takes `[0]`. Field names are also wrong for this API: reachability is `reachabilityHealth`, not `reachabilityStatus`, so `reachable` is always False. Packet drop, uptime and PoE don't exist here and are always `None`. Use `GET /dna/intent/api/v1/device-detail?identifier=uuid&searchBy=<uuid>` or `/dna/data/api/v1/networkDevices/{id}` (2.3.7.x and later). This affects the dashboard drawer and live-poll.

**H4. DNAC client robustness.**
- No `timeout=` on any DNAC request, so Jenkins jobs and API workers can hang forever.
- `list_event_subscriptions`, `register_webhook` and `deregister_webhook` skip the 401 retry.
- `list_event_subscriptions` calls `response.json()` before checking the status, so an HTML error page raises `JSONDecodeError`.

**H5. ServiceNow integration.**
- `find_incident` swallows errors and returns `None`, so a SNOW blip leads to a **new duplicate incident**.
- `append_comment` and `reopen_incident` return `False` on failure, but Agent 4 ignores this. It reports `comment_appended` / `incident_reopened` and sends the "Action Required" email anyway.
- Dedup uses `short_descriptionLIKE<device>`: `sw1` matches `sw10`. Every issue type on a device is also merged into one incident.
- `active=true` includes **Resolved** incidents (out-of-the-box SNOW keeps them active until Closed), so comments land on resolved tickets instead of reopening them. `active=false` includes **Canceled**. Reopening **Closed** (state 7) is normally blocked by business rules, and the PUT will fail quietly (see the second point).
- No idempotency key: RabbitMQ redelivery or Jenkins retries create duplicates. Store `eventId` / `issueId` in `correlation_id` and look that up first.
- Severity isn't mapped to impact or urgency. `category="Inciden_Infrastructure & Network"` looks like a typo; confirm the exact choice value. The assignment group (`…Dyson`) and CI `Network` are hard-coded and must exist in prod.

**H6. The main consumer can create duplicate Jenkins builds.** The callback blocks for up to 120 s (`wait_for_build_number`) on a connection with a 60 s heartbeat. The broker may drop the connection, the message is redelivered, and a second build starts. Ack after the trigger and don't wait for the build number. Jenkins TLS verification is also off.

**H7. Workflow API serialises all alerts.** `async def invoke_workflow` runs the blocking `graph.invoke` (ML, DNAC, SNOW, SMTP) on the event loop, so one slow alert blocks all others and `/health`. Change it to `def`. Also note that the Jenkins `urlopen` has no timeout, and `agent any` calls `127.0.0.1:8001`, which only works if the agent is that same host.

**H8. Deployment artefacts.**
- `requirements.txt` is missing **uvicorn**, **langchain-openai**, **sentence-transformers** and **hdbscan**, so a clean prod install won't start.
- `config.yaml` points the DL model at `models/checkpoints/checkpoint-651`, which isn't in the repo. The DL fallback is silently mocked out.

**H9. The dashboard shows simulated data in prod** when MongoDB is empty or unreachable (`dashboard/api.py:98-108`, which also auto-generates 60 fake alerts). Turn this off in prod with an env flag. `/api/alerts` also loads the whole collection with no limit.

---

## 3. Medium / hygiene
- `verify_ssl: false` for DNAC; TLS warnings are disabled globally; the Gemini client uses `verify=False`. Use the corporate CA bundle.
- Full payloads are logged at INFO (webhook, consumer and agents). That's noisy and may contain sensitive device and topology data.
- `load_dotenv(override=True)` in `app/main.py` makes `.env` override real environment and secret-manager values.
- Alert age is measured when Jenkins runs, not when the alert arrived. A queue backlog can make fresh alerts look "backdated". Stamp `_received_at` in the webhook and use that.
- MongoDB dedup key: once B1 is fixed, the delayed run upserts the same key with `$set: {results: ...}` and **overwrites** the main run's Agent 1–3 results. Store delayed results under their own key.
- `check_dnac_status` is copied three times (`workflow/api.py`, `run_delayed.py`, `dashboard/dnac_monitor.py`). Fix it once.
- `RabbitMQBroker` opens a new connection and re-declares the wait queue for every alert, without publisher confirms.
- `webhook_registration.enabled` is never read. `receiver_url` is plain HTTP.

---

## 4. What looks correct
- DNAC auth (`/dna/system/api/v1/auth/token`, `X-Auth-Token`) and the one-shot 401 re-auth in `_request_with_retry`.
- Device lookup on `/network-device` by `hostname` or `managementIpAddress`, with curated and raw output.
- Webhook subscription payload for `/event/subscription/rest`, including the idempotent name check.
- Payload extraction for the standard Assurance notification format. `instanceId`, `eventId`, `network.deviceId`, `details.Device`, `details.Assurance Issue Name/Details/Status`, `severity`, `category` and `timestamp` map correctly into the Jenkins parameters (the issue is *which* ID is used later; see B5).
- Backdate detector logic: epoch ms/s/ISO parsing, future-skew guard, sanity limit.
- Retry and DLQ via `x-death` count on the main consumer.

---

## 5. Suggested order of work
1. **Safety first:** B2, B3 and B1, so failures escalate instead of suppressing and results are recorded.
2. **Security:** B8 (rotate the password today), B7, B9.
3. **DNAC correctness:** B5 (carry `issueId`), B4, B6, H3, H4. Then test against the real DNAC with one active and one resolved issue.
4. **SNOW correctness:** H5, then a test on a non-prod SNOW instance covering create, append, reopen, SNOW down, and a duplicate event.
5. **Delivery guarantees:** H1, H2, H6, plus the delayed-queue DLQ and reconnect loop.
6. **Packaging:** H8, H9, H7.

Before go-live, run end-to-end tests that **must** produce a SNOW ticket: model file missing, RabbitMQ down during Agent 3, DNAC down during the delayed check, an alert with no description, and an alert with a missing timestamp.
