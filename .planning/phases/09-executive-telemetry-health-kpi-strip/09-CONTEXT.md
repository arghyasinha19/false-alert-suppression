# Phase 9: Executive Telemetry & Health KPI Strip - Context

**Gathered:** 2026-10-01  
**Status:** Ready for planning  

<domain>
## Phase Boundary

Phase 9 delivers an enterprise-grade Executive & Observability Telemetry Strip for Network Operations. It replaces the basic 4-card metric strip (`Total`, `Healthy`, `Warning`, `Critical`) with 5 executive observability KPI cards featuring weighted availability calculation, noise suppression efficiency, incident blast radius, automated resolution velocity, and site resilience ratio, with animated count-up interactions.

</domain>

<decisions>
## Implementation Decisions

### Fleet Health Score Formula & Weighting
- **D-01 (Formula):** Use a Weighted Severity Index across the device inventory:
  `Score = Math.max(0, Math.min(100, Math.round(100 - ((criticalDevices * 1.0 + warningDevices * 0.33) / totalDevices) * 100)))`
  Critical alerting nodes carry 100% deduction weight, while warning/flapping nodes carry a 33% deduction weight relative to total fleet size.
- **D-02 (Thresholds):** Enterprise 3-Tier SLA Color Coding:
  - `>= 95.0%`: Emerald/Green (`Nominal` operational status)
  - `85.0% – 94.9%`: Amber/Yellow (`Degraded` operational status)
  - `< 85.0%`: Rose/Red (`Critical Incident` alerting status)

### Executive KPI Strip Layout & Card Hierarchy
- **D-03 (Hero + 4 Structure):** The top summary strip uses a 5-card layout featuring a prominent Hero Card for the Fleet Health Score on the left (with circular status indicator/badge and health state pill) + 4 balanced companion cards in a responsive grid.
- **D-04 (Micro-Subtitles):** All cards include contextual secondary subtext explaining operational meaning:
  - Fleet Health: `"Nominal operational state"` / `"Degraded fleet conditions"`
  - Noise Suppression: `"Alerts filtered at edge"`
  - Blast Radius: `"Across X locations / sites"`
  - Resolution Velocity: `"DLX verification window"`
  - Site Resilience: `"Nominal vs degraded regions"`

### Blast Radius & Site Resilience Presentation
- **D-05 (Blast Radius Metric):** Active Blast Radius presents the Degraded Device Count as the primary numeric value (e.g. `3 Degraded Nodes`), with subtext indicating geographical distribution (e.g. `Affecting 2 / 9 locations`).
- **D-06 (Site Resilience Metric):** Site Resilience displays the operational location ratio as the primary value (e.g. `8 / 9 Sites Nominal`), complemented by a sleek inline horizontal health micro-bar showing the green nominal vs amber/red degraded site proportion.

### Noise Suppression Rate & Resolution Velocity Metrics
- **D-07 (Suppression Rate Formula):** Fleet Alert Noise Reduction Rate is calculated consistently with the executive False Alert Metrics pipeline:
  `Suppression % = ((Total Auto-Resolving + Total Backdated) / Total Alerts) * 100`
- **D-08 (Velocity Focus):** The 4th companion card highlights Automated Resolution Velocity (`~15m`) with subtext `"DLX verification window"`, reflecting the pipeline's mean turnaround time for transient auto-resolving events.

### Micro-Interactions & Animation
- **D-09 (Counter Animation):** All numeric metric values integrate with `AnimatedCounter` (`duration={800}`) for smooth easing on page load and live data polling updates.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project & Roadmap Specs
- `.planning/PROJECT.md` — Core value, system architecture, and milestone goals
- `.planning/REQUIREMENTS.md` § Milestone v1.5 — `NOC-KPI-01` through `NOC-KPI-05`
- `.planning/ROADMAP.md` § Phase 9 — Success criteria and phase deliverables

### Existing Codebase References
- `dashboard/src/NetworkOperations.jsx` (L285–314) — Current 4-card `noc-summary-grid` implementation
- `dashboard/src/AnimatedCounter.jsx` — Existing easing count-up component
- `dashboard/src/App.css` — CSS design tokens, `.glass-card`, `.kpi-card`, and responsive media queries

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AnimatedCounter`: Already imported and active in `FalseAlertMetrics.jsx`; can be directly utilized in `NetworkOperations.jsx`.
- Lucide React Icons: `ShieldCheck`, `Activity`, `Flame`, `Zap`, `CheckCircle`, `Radio`, `Timer` are available in `lucide-react`.

### Established Patterns
- Glassmorphic card styling (`.glass-card .kpi-card`) with CSS variables (`var(--accent-blue)`, `var(--accent-green)`, `var(--accent-yellow)`, `var(--accent-red)`).
- Status dot and pill badge classes (`.badge`, `.device-tile-status-dot`).

### Integration Points
- `NetworkOperations.jsx`: Replace lines 285–314 (`<div className="noc-summary-grid">`) with the new Executive Telemetry Strip.
- Add CSS styles to `dashboard/src/App.css` for `.noc-hero-card`, `.noc-resilience-bar`, and responsive grid break points.

</code_context>

<specifics>
## Specific Ideas

- The Fleet Health hero card should immediately convey system health without cognitive load (large percentage, color dot, and "96% Nominal" tag).
- The Site Resilience card's inline micro-bar adds a visual cue reminiscent of Datadog SLO monitors or AWS status dashboards.

</specifics>

<deferred>
## Deferred Ideas

- Interactive vector geographic map — Deferred to future milestone.
- Dynamic drag-and-drop KPI card rearrangement — Deferred to future milestone.

</deferred>

---

*Phase: 09-executive-telemetry-health-kpi-strip*  
*Context gathered: 2026-10-01*
