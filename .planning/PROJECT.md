# False Alert Suppression Pipeline

## What This Is

An intelligent, multi-agent network alert triage and suppression platform for Cisco DNA Center events. The system ingests alerts via FastAPI webhooks, buffers events through RabbitMQ queues, orchestrates verification pipelines with Jenkins, and uses a LangGraph multi-agent decision brain to filter backdated alerts, classify issue transience, auto-resolve transient events via delayed DLX wait queues, and escalate genuine anomalies to ServiceNow. Real-time observability and KPIs are served through a FastAPI backend and React operations dashboard.

## Core Value

Accurately identify false or transient network alerts to prevent unnecessary ServiceNow ticket creation and reduce operational noise without missing genuine network degradation.

## Current Milestone: v1.4 Complete UI/UX Expert Audit Implementation

**Goal:** Implement all remaining pointers from the UI/UX Expert Audit Report to deliver an enterprise-grade, premium DNAC Operations Center.

**Target features:**
- **Network Operations Redesign:** 2–3 column responsive device grid (`repeat(auto-fill, minmax(320px, 1fr))`), eliminate horizontal whitespace waste, clean location and device grouping.
- **Premium Collapsible Sidebar:** Expand/collapse rail toggle (260px expanded → 72px icon rail) with tooltips, plus breadcrumb context navigation indicator in the header.
- **Micro-Interactions & Polished Animations:** Real numerical counting animation (`0 → N`) on KPI values with smooth easing, fluid page crossfade transitions.
- **Tables & Empty States:** Sticky headers on all tables (Traceability Matrix, Device Ranking), informative empty state views for zero-match searches/filters.
- **Dark/Light Theme System:** Complete theme tokens, header backdrop adaptivity, theme toggle switch in header or sidebar.
- **ServiceNow Section Polish:** Enhanced section divider styling, badges, and visual hierarchy for ServiceNow Ticket Details.

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

### Active

- [ ] **UIUX-01**: Multi-column responsive device card grid (2-3 cols) in Network Operations, eliminating whitespace waste.
- [ ] **UIUX-02**: Collapsible sidebar with icon rail mode (72px) and expand/collapse toggle.
- [ ] **UIUX-03**: Breadcrumb / route context indicator in top content header.
- [ ] **UIUX-04**: Animated number counting effect (`0 → N`) for KPI values on load and refresh.
- [ ] **UIUX-05**: Sticky headers and responsive styling on Device Ranking & Traceability tables.
- [ ] **UIUX-06**: Rich empty states for zero-match filters/searches across all dashboard pages.
- [ ] **UIUX-07**: ServiceNow Ticket Details section divider styling and typography polish.
- [ ] **UIUX-08**: Complete dark mode theme tokens and header backdrop adaptivity with toggle.

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
