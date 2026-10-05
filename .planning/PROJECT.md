# False Alert Suppression Pipeline

## What This Is

An intelligent, multi-agent network alert triage and suppression platform for Cisco DNA Center events. The system ingests alerts via FastAPI webhooks, buffers events through RabbitMQ queues, orchestrates verification pipelines with Jenkins, and uses a LangGraph multi-agent decision brain to filter backdated alerts, classify issue transience, auto-resolve transient events via delayed DLX wait queues, and escalate genuine anomalies to ServiceNow. Real-time observability and KPIs are served through a FastAPI backend and React operations dashboard.

## Core Value

Accurately identify false or transient network alerts to prevent unnecessary ServiceNow ticket creation and reduce operational noise without missing genuine network degradation.

## Current Milestone: v1.9 UI/UX Audit Remediation

**Goal:** Address the critical, high, and medium UI/UX flaws identified in the DNAC Ops Center audit report to ensure responsive layouts, reliable status indicators, trustworthy contrast, and accessible interactions.

**Target features:**
- **Critical Layout & Status Fixes**: Fix the 1100px breakpoint collapse in `.content-area` and ensure the API connection status correctly reflects offline states.
- **Data Visibility & Bounds**: Implement persistent scrollbars, table edge masks, and strict independent scroll bounds for the topology graph canvas.
- **Trust & Contrast Remediation**: Fix `text-tertiary` contrast ratios, route chart colours through CSS tokens for dark mode reliability, and ensure text contrast passes minimums.
- **Accessibility & Hit Areas**: Increase interactive hit areas to a 32px minimum, fix sidebar keyboard navigation, add `aria-current`, and ensure tables/forms have accessible names.
- **Craft & Consistency Polish**: Standardize typography scale, KPI card designs, empty states, and eliminate demo scaffolding from the chrome.

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
- ✓ DNAC Client Assurance & Device Extensions (`app/dnac_client.py`, `app/exceptions.py`) — v1.6
- ✓ Backend Live Polling & Telemetry Endpoints (`GET /api/devices/{name}/telemetry`, `POST /api/devices/{name}/live-poll`) — v1.6
- ✓ Frontend SRE Drawer Live Wire-Up (Real-time polling, loading spinners, provenance badges, honest null states) — v1.6
- ✓ Detail drawer high-contrast theme-aware visible scrollbar (`DRAWER-01`) — v1.7
- ✓ Fixed-header, fixed-tabs, and pinned-footer flexbox drawer architecture (`DRAWER-02`) — v1.7
- ✓ Unclipped cross-tab viewport scrolling across all 4 SRE workspaces (`DRAWER-03`) — v1.7

- ✓ **TOPO-01**: User can view network devices in an interactive topology graph diagram with nodes and connecting links between tiers. — v1.8
- ✓ **TOPO-02**: Topology graph links visually represent hierarchical connections (Core ↔ Distribution ↔ Access) with status indicators for link degradation or interface errors. — v1.8
- ✓ **TOPO-03**: Graph canvas supports pan, zoom, fit-to-view, and responsive layout adapting to dark and light modes. — v1.8
- ✓ **TOPO-04**: Clicking any device node in the graph diagram opens the slide-out SRE details drawer with full triage, telemetry, inventory, and action bar support. — v1.8

### Active

- [ ] **UI-01**: Fix responsive collapse below 1100px to ensure the dashboard remains usable on smaller screens.
- [ ] **UI-02**: Ensure the sidebar connection status accurately reflects API failures and offline states instead of false positives.
- [ ] **UI-03**: Constrain the topology graph canvas to its own bounds to prevent overflowing the main window.
- [ ] **UI-04**: Add permanently visible scrollbars and edge masks to data tables for usability.
- [ ] **UI-05**: Adjust `text-tertiary` colors for accessible contrast in both light and dark modes.
- [ ] **UI-06**: Route chart colors through CSS tokens to guarantee theme integration (dark mode).
- [ ] **UI-07**: Expand interactive element hit areas to a comfortable 32px minimum.
- [ ] **UI-08**: Ensure the chat panel does not trap focus globally with an invisible overlay.
- [ ] **UI-09-22**: Address medium priority consistency fixes including typography scales, KPI card unified design, unlabelled form controls, keyboard navigation (aria-current), and empty states.

### Out of Scope

- Bypassing DNAC RBAC or making unauthenticated calls.
- Storing unencrypted DNAC passwords in source code (always load from env vars or `config.yaml`).
- Daemon supervisor bundling (`start_dashboard.py` auto-starting `dnac_sync.py`) and standalone CLI diagnostic script — Removed per user decision; existing independent `dnac_sync.py` and pytest test suites satisfy operational and testing needs.
- External database querying for historical data beyond currently ingested/cached pipeline alerts.
- Changing server-side timezone configuration (all comparisons performed in browser client local / UTC normalized time).

## Context

- The React dashboard defaults to connecting to `http://127.0.0.1:8004` (as defined in `VITE_API_BASE`).
- When MongoDB is offline, the FastAPI backend automatically falls back to `data/simulated_alerts.json`, providing a complete mock operations environment with 60 realistic alerts and live simulation capabilities.
- Live DNAC Assurance vitals and hardware inventory are cached in MongoDB collection `device_telemetry`.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Total Processed = Suppressed + Auto Resolved + Non-Auto Resolved + Uncertain | Represents the 4 mutually exclusive classification paths for every ingested alert. | ✓ Good |
| Tickets Avoided is derived (`Suppressed + Auto-Resolving`) | Avoids double-counting avoided tickets in the total processed metric. | ✓ Good |
| Scope-based KPI calculation | Distinguishes device/time scope from category filter so KPI cards display overall scope volume while the table and charts filter by category. | ✓ Good |
| Port 8004 for Dashboard API | Avoids conflict with standard dev ports (8000/8080) and matches `VITE_API_BASE` in the frontend. | ✓ Good |
| Two-tier UUID resolution in `device_service.py` | Fast lookups via MongoDB cache with dynamic DNAC fallback. | ✓ Good |
| Non-blocking HTTP 200 fallbacks on offline DNAC | Prevents UI crashes and preserves offline demoability. | ✓ Good |
| Dual provenance badges in header and tab banners | SREs know data origin at a glance. | ✓ Good |
| Fleet-wide `onRefresh()` after live poll | Synchronizes device state across all 3 representation modes. | ✓ Good |

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
*Last updated: 2026-10-05 after Milestone v1.6 completion*
