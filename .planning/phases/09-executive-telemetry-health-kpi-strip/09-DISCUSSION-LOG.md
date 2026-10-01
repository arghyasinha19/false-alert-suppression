# Phase 9: Executive Telemetry & Health KPI Strip - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-01  
**Phase:** 09-executive-telemetry-health-kpi-strip  
**Areas discussed:** Fleet Health Score Formula & Weighting, Executive KPI Strip Layout & Card Hierarchy, Blast Radius & Site Resilience Visualization, Noise Suppression Rate & MTTR Metric Definitions  

---

## Fleet Health Score Formula & Weighting

| Option | Description | Selected |
|--------|-------------|----------|
| Weighted Severity Formula | Deduct heavier penalty for Critical devices (100% impact) and lighter penalty for Warning devices (33% impact) relative to total fleet size | ✓ |
| Tier-Weighted SLA | Core & Distribution devices carry 2x penalty compared to Campus & Access edge devices | |
| Strict Healthy Ratio | Pure percentage of devices with 0 active alerts ((healthy / total) * 100) | |

**User's choice:** Weighted Severity Formula (`critical * 1.0 + warning * 0.33`).  
**Threshold Scale:** 3-Tier Enterprise scale: `>= 95%` Green (Nominal), `85-94.9%` Amber (Degraded), `< 85%` Red (Critical Incident).

---

## Executive KPI Strip Layout & Card Hierarchy

| Option | Description | Selected |
|--------|-------------|----------|
| Hero + 4 Grid | Prominent Hero card for Fleet Health Index (with circular gauge/badge) + 4 balanced companion KPI cards in responsive row | ✓ |
| Balanced 5-Card Grid | All 5 cards share equal width and visual weight in a single responsive row | |
| 2-Tier Layout | Macro Availability Row on top, Operational Pipeline Row below | |

**User's choice:** Hero + 4 Grid with contextual micro-subtitles on all cards.

---

## Blast Radius & Site Resilience Visualization

| Option | Description | Selected |
|--------|-------------|----------|
| Degraded Devices Primary | Degraded Devices as primary value with subtext indicating affected sites | ✓ |
| Affected Sites Primary | Affected Sites as primary value with subtext indicating total impacted nodes | |

| Option | Description | Selected |
|--------|-------------|----------|
| Ratio + Micro-Bar | '8 / 9 Sites Nominal' with a sleek inline horizontal health progress bar | ✓ |
| Ratio + Percentage Chip | '8 / 9' with a styled pill badge '88.9% Nominal' | |

**User's choice:** Degraded Devices primary + Affected Locations subtext; Site Resilience with inline dual-color micro-bar.

---

## Noise Suppression Rate & MTTR Metric Definitions

| Option | Description | Selected |
|--------|-------------|----------|
| Fleet Alert Suppression Ratio | (Auto-Resolving + Backdated) / Total Alerts * 100 (aligned with False Alert Metrics) | ✓ |
| Device Ticket Prevention Rate | Percentage of devices operating with 0 SNOW tickets created | |

| Option | Description | Selected |
|--------|-------------|----------|
| Automated Resolution Window | Display average automated triage turnaround (e.g. '~15m') with subtext 'DLX verification window' | ✓ |
| Tickets Avoided Count | Display the total count of avoided SNOW tickets | |

**User's choice:** Fleet alert suppression ratio + automated resolution velocity (`~15m DLX window`).

---

## Agent's Discretion

- Choice of icons from `lucide-react` (`ShieldCheck`, `Activity`, `Flame`, `Zap`, `Radio`).
- CSS variable token application and hover elevation effects.

## Deferred Ideas

- Interactive vector geographical map — Deferred to future milestone.
- Drag-and-drop dashboard widget rearrangement — Deferred to future milestone.
