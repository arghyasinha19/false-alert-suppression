# False Alert Suppression Pipeline

## What This Is

An intelligent, multi-agent network alert triage and suppression platform for Cisco DNA Center events. The system ingests alerts via FastAPI webhooks, buffers events through RabbitMQ queues, orchestrates verification pipelines with Jenkins, and uses a LangGraph multi-agent decision brain to filter backdated alerts, classify issue transience, auto-resolve transient events via delayed DLX wait queues, and escalate genuine anomalies to ServiceNow. Real-time observability and KPIs are served through a FastAPI backend and React operations dashboard.

## Core Value

Accurately identify false or transient network alerts to prevent unnecessary ServiceNow ticket creation and reduce operational noise without missing genuine network degradation.

## Current Milestone: v1.6 Live DNAC Assurance Telemetry & Asset Integration

**Goal:** Bridge the Network Operations Center directly with live Cisco DNA Center Assurance and Device Inventory APIs, replace client-side simulated drawer vitals and poll timeouts with real backend endpoints, auto-orchestrate the background sync daemon, and provide an end-to-end testing suite with robust offline fallbacks.

**Target features:**
- **DNAC Device & Assurance API Integration:** Add real client methods in `app/dnac_client.py` for `/dna/intent/api/v1/network-device` (hardware inventory, serial, MAC, OS, IP) and `/dna/intent/api/v1/device-health` (live CPU, memory, packet drop, reachability).
- **Backend Live Telemetry & Polling Endpoints:** Implement `GET /api/devices/{name}/telemetry` and `POST /api/devices/{name}/live-poll` in `dashboard/api.py`.
- **Frontend SRE Drawer Live Wiring:** Wire the "Poll DNAC" button and Telemetry/Inventory tabs in `dashboard/src/NetworkOperations.jsx` to live backend data with real-time loading spinners and graceful offline fallback.
- **Launcher Auto-Orchestration:** Update `start_dashboard.py` to start and gracefully terminate `dashboard/dnac_sync.py` alongside FastAPI and Vite.
- **End-to-End Verification & Diagnostics Harness:** Provide an interactive step-by-step diagnostic test CLI tool (`test_dnac_integration.py`) verifying credentials, tokens, live issue status, and device telemetry.

## Requirements

### Validated

- ✓ Cisco DNA Center webhook ingestion via FastAPI (`app/main.py`) — existing
- ✓ AMQP buffering with RabbitMQ queues (`app/mq_publisher.py`, `consumer/noops_dnac_consumer.py`) — existing
- ✓ Jenkins pipeline orchestration (`jenkins/Jenkinsfile.main`) — existing
- ✓ Agent 1: Backdate detection (`workflow/nodes/node_agent_1_backdate.py`) — existing
- ✓ Agent 2: ML alert transience classification (`workflow/nodes/node_agent_2_classifier.py`) — existing
- ✓ Agent 3: Auto-resolving delayed DLX wait queue scheduler (`workflow/nodes/node_agent_3_scheduler.py`) — existing
- ✓ Agent 4: ServiceNow incident management client (`workflow/nodes/node_agent_4_servicenow.py`) — existing
- ✓ Operational email notification dispatch (`workflow/nodes/node_email_notifier.py`) — existing
- ✓ React operations dashboard with live status and alert trace matrix (`dashboard/`) — existing
- ✓ Total Processed KPI and category alignment (Milestone v1.0) — v1.0
- ✓ FastAPI Dashboard Backend & Vite React dev server bring-up and orchestration (Milestone v1.1) — v1.1
- ✓ Custom Date & Time Range Filtering with dynamic KPI recalculations (Milestone v1.2) — v1.2
- ✓ Layout overflow fixes, skeleton loading, and critical audit fixes (Milestone v1.3) — v1.3
- ✓ Multi-column responsive device card grid in Network Operations (Milestone v1.4) — v1.4
- ✓ Collapsible sidebar with 72px icon rail and tooltips (Milestone v1.4) — v1.4
- ✓ Breadcrumb / route context navigation indicator in header (Milestone v1.4) — v1.4
- ✓ Animated number counting effect (`0 → N`) for KPI values (Milestone v1.4) — v1.4
- ✓ Sticky headers and responsive styling on tables (Milestone v1.4) — v1.4
- ✓ Rich empty states for zero-match filters/searches (Milestone v1.4) — v1.4
- ✓ ServiceNow Ticket Details section divider and badge styling (Milestone v1.4) — v1.4
- ✓ Complete dark/light mode theme system with header toggle (Milestone v1.4) — v1.4
- ✓ Executive Telemetry & Health KPI Strip (Milestone v1.5) — v1.5
- ✓ Multi-Mode Representation Engine: Topology, SRE Table, Site Matrix (Milestone v1.5) — v1.5
- ✓ Multi-Dimensional Filter Bar & Micro-Visualizations (Milestone v1.5) — v1.5
- ✓ Interactive SRE Investigation Drawer & Incident Timeline (Milestone v1.5) — v1.5

### Active

- [ ] **DNAC-01**: DNAC Assurance & Device Client Extensions (`app/dnac_client.py` methods for `/dna/intent/api/v1/network-device` and `/dna/intent/api/v1/device-health` with fallback handling).
- [ ] **DNAC-02**: Backend Live Polling & Telemetry Endpoints (`dashboard/api.py` endpoints for `GET /api/devices/{name}/telemetry` and `POST /api/devices/{name}/live-poll`).
- [ ] **DNAC-03**: Frontend SRE Drawer Live Wire-Up (Wire Poll DNAC button and Telemetry/Inventory tabs to live endpoints with loading spinners and offline fallbacks in `NetworkOperations.jsx`).
- [ ] **DNAC-04**: Launcher Service Orchestration (`start_dashboard.py` auto-starts and monitors `dnac_sync.py` background process).
- [ ] **DNAC-05**: End-to-End Step-by-Step Diagnostic & Testing Harness (`test_dnac_integration.py` for token auth, issue lookup, device health, and telemetry verification).

### Out of Scope

- Bypassing DNAC RBAC or making unauthenticated calls.
- Storing unencrypted DNAC passwords in source code (always load from env vars or `config.yaml`).

- External database querying for historical data beyond currently ingested/cached pipeline alerts.
- Changing server-side timezone configuration (all comparisons performed in browser client local / UTC normalized time).

## Context

- The React dashboard defaults to connecting to `http://127.0.0.1:8004` (as defined in `VITE_API_BASE`).
- When MongoDB is offline, the FastAPI backend automatically falls back to `data/simulated_alerts.json`, providing a complete mock operations environment with 60 realistic alerts and live simulation capabilities.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Total Processed = Suppressed + Auto Resolved + Non-Auto Resolved + Uncertain | Represents the 4 mutually exclusive classification paths for every ingested alert. | ✓ Good |
| Tickets Avoided is derived (`Suppressed + Auto-Resolving`) | Avoids double-counting avoided tickets in the total processed metric. | ✓ Good |
| Scope-based KPI calculation | Distinguishes device/time scope from category filter so KPI cards display overall scope volume while the table and charts filter by category. | ✓ Good |
| Port 8004 for Dashboard API | Avoids conflict with standard dev ports (8000/8080) and matches `VITE_API_BASE` in the frontend. | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-10-05 after Milestone v1.6 initialization*
