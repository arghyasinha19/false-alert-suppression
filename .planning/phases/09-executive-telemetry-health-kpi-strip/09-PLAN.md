---
phase: 9
plan: 1
type: implementation
prefix: NOC-KPI
wave: 1
depends_on: []
files_modified:
  - dashboard/src/NetworkOperations.jsx
  - dashboard/src/App.css
---

# Plan 09-01: Executive Telemetry & Health KPI Strip

> Transform the Network Operations top metrics into an enterprise-grade Executive & Observability Telemetry Strip with 5 cards: Fleet Health Score (Hero), Noise Suppression Efficiency, Active Blast Radius, Mean Resolution Velocity, and Site Resilience Ratio.

---

## Requirements Covered

- **NOC-KPI-01**: User can view Fleet Health Score (% index based on weighted device operational availability) with animated counter.
- **NOC-KPI-02**: User can view False Alert Noise Reduction / Suppression Rate (%) at fleet level.
- **NOC-KPI-03**: User can view Active Incident Blast Radius (# affected sites & degraded devices).
- **NOC-KPI-04**: User can view Mean Resolution Velocity / MTTA metric for auto-resolved vs escalated incidents.
- **NOC-KPI-05**: User can view Site Resilience Ratio (e.g. 8/9 Nominal sites) in the top executive summary strip.

---

## Tasks

### Task 1: Compute Executive Telemetry Metrics in `NetworkOperations.jsx`
- **File:** `dashboard/src/NetworkOperations.jsx`
- **Action:**
  - Import `AnimatedCounter` from `./AnimatedCounter.jsx`.
  - Import necessary Lucide icons: `ShieldCheck`, `Zap`, `Flame`, `Timer`, `Radio`.
  - Define `executiveKPI` memo deriving:
    1. `fleetHealthScore`: Weighted calculation `Math.max(0, Math.min(100, Math.round(100 - ((critical * 1.0 + warning * 0.33) / total) * 100)))`. Include `slaStatus`: `critical` (< 85), `degraded` (85-94.9), `nominal` (>= 95).
    2. `suppressionRate`: Ratio of `(auto_resolving + backdated) / total_alerts * 100`.
    3. `blastRadius`: Total degraded nodes (`critical + warning`) and affected unique location sites count.
    4. `resolutionVelocity`: Return `15` (minutes) representing the automated DLX verification window.
    5. `siteResilience`: Total sites count, nominal sites count (sites where all devices have 0 critical/warning alerts), and percentage.

### Task 2: Build Executive Telemetry Strip UI in `NetworkOperations.jsx`
- **File:** `dashboard/src/NetworkOperations.jsx`
- **Action:**
  - Replace `<div className="noc-summary-grid">...</div>` with `<div className="noc-executive-strip">`.
  - Render Card 1 (Hero):
    - Icon `<ShieldCheck size={22} />`.
    - Title: "Fleet Health Score".
    - Status badge: `<span className="badge health-{slaStatus}">{slaStatus.toUpperCase()}</span>`.
    - Value: `<AnimatedCounter value={fleetHealthScore} duration={800} suffix="%" />`.
    - Subtitle: Contextual availability string.
  - Render Card 2:
    - Icon `<Zap size={20} />` inside `.kpi-icon.blue`.
    - Title: "Noise Suppression".
    - Value: `<AnimatedCounter value={suppressionRate} duration={800} suffix="%" decimals={1} />`.
    - Subtitle: "Alerts filtered at edge".
  - Render Card 3:
    - Icon `<Flame size={20} />` inside `.kpi-icon` with conditional amber/red highlight.
    - Title: "Active Blast Radius".
    - Value: `<AnimatedCounter value={degradedNodesCount} duration={800} />` with " Nodes" label.
    - Subtitle: `Affecting ${affectedSitesCount} / ${totalSitesCount} locations`.
  - Render Card 4:
    - Icon `<Timer size={20} />` inside `.kpi-icon.purple`.
    - Title: "Resolution Velocity".
    - Value: `~15m`.
    - Subtitle: "DLX verification window".
  - Render Card 5:
    - Icon `<Radio size={20} />` inside `.kpi-icon.green`.
    - Title: "Site Resilience".
    - Value: `${nominalSites} / ${totalSites} Sites`.
    - Subtitle: `${resiliencePct}% regions nominal`.
    - Inline micro progress bar `.noc-resilience-bar` displaying green fill for nominal sites proportion.

### Task 3: Add Design System & Responsive Styles in `dashboard/src/App.css`
- **File:** `dashboard/src/App.css`
- **Action:**
  - Define `.noc-executive-strip` layout grid with responsive breakpoints.
  - Define `.noc-hero-card` styling with SLA variants (`.sla-nominal`, `.sla-degraded`, `.sla-critical`) and subtle glowing border.
  - Define `.noc-resilience-bar` and `.noc-resilience-fill` micro progress bar.
  - Define `.kpi-icon.purple` styling matching design tokens.
  - Ensure dark and light theme token compatibility.

### Task 4: Build Verification & Health Checks
- **Action:**
  - Run `npm run build` in `dashboard/` to verify 0 syntax or JSX compilation errors.
  - Verify live HTTP 200 response on `http://localhost:5173`.
  - Confirm animated counters render cleanly on load.

---

## Verification Checklist

- [ ] `npm run build` succeeds cleanly.
- [ ] Top summary strip renders 5 executive cards instead of 4 basic cards.
- [ ] Hero Card displays Fleet Health Score with SLA color coding (green/amber/red).
- [ ] Noise Suppression displays percentage with `AnimatedCounter`.
- [ ] Blast Radius displays degraded nodes and affected sites subtext.
- [ ] Resolution Velocity displays `~15m` with DLX window subtext.
- [ ] Site Resilience displays nominal sites ratio with inline micro progress bar.
- [ ] All 5 cards adapt seamlessly across desktop (1707px), laptop (1366px), and tablet/mobile viewports.
- [ ] Both Dark and Light themes render with high contrast and proper tokens.
