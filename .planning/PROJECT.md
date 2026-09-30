# False Alert Suppression Pipeline

## What This Is

An intelligent, multi-agent network alert triage and suppression platform for Cisco DNA Center events. The system ingests alerts via FastAPI webhooks, buffers events through RabbitMQ queues, orchestrates verification pipelines with Jenkins, and uses a LangGraph multi-agent decision brain to filter backdated alerts, classify issue transience, auto-resolve transient events via delayed DLX wait queues, and escalate genuine anomalies to ServiceNow. Real-time observability and KPIs are served through a FastAPI backend and React operations dashboard.

## Core Value

Accurately identify false or transient network alerts to prevent unnecessary ServiceNow ticket creation and reduce operational noise without missing genuine network degradation.

## Current Milestone: v1.0 False Alert Metrics Alignment

**Goal:** Ensure the "Total Processed" metric in False Alert Metrics accurately reflects the total number of alerts processed by the system (the sum of Suppressed/Backdated, Auto-Resolving, Non-Auto-Resolving, and Uncertain alerts) and maintains system-wide visibility during category filtering.

**Target features:**
- Align "Total Processed" calculation to strictly equal `Suppressed + Auto-Resolving + Non-Auto-Resolving + Uncertain`.
- Treat "Tickets Avoided" as a derived KPI (`Suppressed + Auto-Resolving`) without double-counting.
- Preserve system-wide total visibility on KPI cards when category filters are applied, showing active filtered counts in sub-values.
- Enable toggle behavior and active visual states on category KPI cards.

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

### Active

- [ ] **METRIC-01**: Total Processed field in False Alert Metrics calculates the total alerts processed by the system as `Suppressed + Auto-Resolving + Non-Auto-Resolving + Uncertain`.
- [ ] **METRIC-02**: Tickets Avoided is verified and maintained as a derived KPI (`Suppressed + Auto-Resolving`) preventing duplicate counting.
- [ ] **METRIC-03**: Total Processed card retains the total system alert volume when category filters are active, displaying the filtered alert count as a sub-value.
- [ ] **METRIC-04**: Category KPI cards (Backdated/Suppressed, Auto-Resolving, Non-Auto-Resolving, Uncertain) support toggle filtering with active highlight styling and maintain category totals.
- [ ] **METRIC-05**: Backend `/api/kpi/summary` in `dashboard/api.py` and `dashboard/chat_agent.py` verified for KPI sum consistency.

### Out of Scope

- Redesigning the ML classification model weights or training pipelines in this milestone.
- Altering the RabbitMQ DLX queue TTL or Jenkins orchestration timings.

## Context

- In `dashboard/src/FalseAlertMetrics.jsx`, previously `filteredAlerts` applied category filtering prior to computing `kpi.total`. This resulted in "Total Processed" collapsing to only the selected category count, and non-selected category cards showing 0.
- Tickets Avoided is inherently the sum of backdated alerts suppressed by Agent 1 plus transient auto-resolving alerts suppressed by Agent 2 & 3.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Total Processed = Suppressed + Auto Resolved + Non-Auto Resolved + Uncertain | Represents the 4 mutually exclusive classification paths for every ingested alert. | ✓ Good |
| Tickets Avoided is derived (`Suppressed + Auto-Resolving`) | Avoids double-counting avoided tickets in the total processed metric. | ✓ Good |
| Scope-based KPI calculation | Distinguishes device/time scope from category filter so KPI cards display overall scope volume while the table and charts filter by category. | ✓ Good |

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
*Last updated: 2026-09-30 after Milestone v1.0 initialization*
