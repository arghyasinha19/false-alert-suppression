# False Alert Suppression Pipeline

## What This Is

An intelligent, multi-agent network alert triage and suppression platform for Cisco DNA Center events. The system ingests alerts via FastAPI webhooks, buffers events through RabbitMQ queues, orchestrates verification pipelines with Jenkins, and uses a LangGraph multi-agent decision brain to filter backdated alerts, classify issue transience, auto-resolve transient events via delayed DLX wait queues, and escalate genuine anomalies to ServiceNow. Real-time observability and KPIs are served through a FastAPI backend and React operations dashboard.

## Core Value

Accurately identify false or transient network alerts to prevent unnecessary ServiceNow ticket creation and reduce operational noise without missing genuine network degradation.

## Current Milestone: v1.5 Executive & Observability Network Operations Center (NOC) Overhaul

**Goal:** Transform the Network Operations Center into a world-class executive & observability command center featuring enterprise telemetry KPIs, multi-view representation hierarchy (Executive Topology, SRE Density Matrix, Regional Site Matrix), micro-visualizations (activity sparklines, health rings), and an interactive incident timeline drawer.

**Target features:**
- **Executive Observability KPI Strip:** Fleet Health Score (0-100%), Noise Suppression Rate, Incident Blast Radius, Mean Time to Auto-Resolution, and Site Resilience Ratio.
- **Multi-Mode Representation Engine:** Executive Grid (Topology/Role grouped), High-Density SRE Table/Matrix, and Regional Site Health Overview.
- **Rich Telemetry & Micro-Visualizations:** 24h alert activity sparkline/micro-bars per device, health gauge rings, severity breakdown mini-bars, and quick-filter pills (by Role, Health, SNOW status).
- **Interactive SRE Drawer & Incident Timeline:** Chronological decision trail (Ingest → Agent 1 Backdate → Agent 2 ML → Agent 3 Wait → Agent 4 SNOW), live Assurance telemetry metrics, and one-click actions.
- **Design System & Visual Luxury:** Subtle glassmorphic depth, status pulses, micro-interactions, responsive auto-fill grids, and full dark/light theme polish.

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

### Active

- [ ] **NOC-01**: Executive Telemetry & Health KPI Strip (Fleet Health Score %, Noise Suppression Ratio, Blast Radius / Degraded Sites, MTTR / Resolution Velocity) with animated counters.
- [ ] **NOC-02**: Multi-View Representation Engine (Executive Grid with Topology grouping, High-Density SRE Table/Matrix, Regional Site Health Matrix) with seamless view switcher.
- [ ] **NOC-03**: Multi-Dimensional Filter Bar (Quick-filter pills for Device Role: Core/Distribution/Access/Wireless/Security, Health: Healthy/Warning/Critical, SNOW status, and live search).
- [ ] **NOC-04**: Device Micro-Visualizations (24-Hour alert distribution sparkline/activity strip, inline severity bar, live pulse indicator, health score pill).
- [ ] **NOC-05**: SRE Incident Investigation Drawer (Multi-tab/chronological decision timeline: Ingest → Agent 1 → Agent 2 → Agent 3 → Agent 4, DNAC telemetry details, and one-click quick actions).
- [ ] **NOC-06**: Visual Polish & Luxury Aesthetics (Premium glassmorphism, responsive CSS grid, refined dark/light theme tokens, and fluid view transitions).

### Out of Scope

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
*Last updated: 2026-09-30 after Milestone v1.4 initialization*
