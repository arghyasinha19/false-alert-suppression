# Phase 13: Discussion Log

**Phase:** 13 — DNAC Client Assurance & Device Extensions
**Date:** 2026-10-05
**Mode:** Interactive (default)
**Areas discussed:** Device lookup contract, Token refresh strategy, Health API query form, Return type shape

---

## Area 1: Device Lookup Contract

| Question | Options presented | Selected |
|---|---|---|
| Multi-match behavior | Return first silently / Return None on ambiguity / Return a list always | Return a list always |
| Zero-match behavior | Return [] / Return None / Raise DeviceNotFoundError | Raise DeviceNotFoundError |
| Query param routing | Hostname only / Hostname OR IP detect / Both parallel | Hostname OR IP detect (re.fullmatch IPv4) |
| Network error behavior | Propagate / Return [] / Re-raise as DNACConnectionError | Re-raise as DNACConnectionError |
| Response field shape | Raw DNAC fields / Curated snake_case subset / Both with raw_response | Both curated + raw_response |

## Area 2: Token Refresh Strategy

| Question | Options presented | Selected |
|---|---|---|
| 401 handling | Retry once / Pre-validate expiry / No retry, raise | Retry once via _request_with_retry |
| Retrofit scope | Yes, retrofit existing methods / No, new methods only / You decide | Yes — retrofit get_issue_status and get_device_issues too |

## Area 3: Health API Query Form

| Question | Options presented | Selected |
|---|---|---|
| Input identifier | UUID only / Hostname/IP (resolve internally) / Accept either | UUID only |
| Failure behavior | Offline fallback dict / Return None / Raise DNACConnectionError | Raise DNACConnectionError |
| Telemetry fields | Core 4 (DNAC-02) / Richer Phase 12 set / Minimal | Richer set (Phase 12 drawer design) |

## Area 4: Return Type Shape

| Question | Options presented | Selected |
|---|---|---|
| Return typing | Plain dicts / TypedDicts / dataclasses | Plain dicts |
| Exception location | In dnac_client.py / New app/exceptions.py / You decide | New app/exceptions.py |
| Test coverage | Mocked unit tests / Integration tests only / Both | Integration tests only (@pytest.mark.integration) |

---

*No deferred ideas.*
*Discussion log written: 2026-10-05*
