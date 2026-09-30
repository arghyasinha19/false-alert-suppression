# Phase 6 Plan: Micro-Interactions & Animated Counters

**Phase:** 6  
**Milestone:** v1.4 Complete UI/UX Expert Audit Implementation  
**Status:** In Progress  

## Goals

Implement high-polish micro-interactions across the dashboard: animated numerical count-up effects (`0 → N`) for all primary KPI card metrics, smooth view crossfade transitions when switching between sidebar tabs, and an enhanced section divider and badge styling for ServiceNow Ticket Details.

## Requirements Covered

- `ANIM-01`: User sees an animated numerical count-up (`0 → N`) for primary KPI card values on load and refresh.
- `ANIM-02`: User experiences smooth crossfade transitions when switching between sidebar views.
- `STATE-02`: User sees an enhanced section divider and styled badges for ServiceNow Ticket Details.

## Design Contract Reference

- See `06-UI-SPEC.md` for animation timing curves, keyframes, typography tokens, and ServiceNow badge hierarchy.

## Execution Waves

### Wave 1: CSS Animation & ServiceNow Section Styling (`dashboard/src/App.css`)

1. **View Crossfade Animations (`ANIM-02`)**:
   - Define `.view-transition-container` with `@keyframes viewCrossfade`.
   - Smooth vertical entrance (`transform: translateY(6px) → translateY(0)` with `opacity: 0 → 1`, duration `0.28s cubic-bezier(0.16, 1, 0.3, 1)`).
2. **ServiceNow Section Divider & Header Polish (`STATE-02`)**:
   - Style `.snow-section-header`: flex layout, icon badge pill, uppercase title, and total activity counter chip.
   - Style `.snow-section-divider`: subtle gradient accent line separating the KPI cards from ServiceNow activity.
3. **ServiceNow Cards & Incident Badges (`STATE-02`)**:
   - Add card top-border accents: `.snow-detail-card.card-blue` (`3px solid var(--accent-blue)`), `.card-purple` (`3px solid var(--accent-purple)`), `.card-orange` (`3px solid var(--accent-orange)`).
   - Style `.snow-card-count-badge`: pill badge displaying incident count inside card headers.
   - Style `.snow-device-inc`: monospace badge pill (`font-family: monospace; background: rgba(37, 99, 235, 0.08); color: var(--accent-blue); padding: 0.15rem 0.5rem; border-radius: 4px;`) with interactive hover glow.
   - Add hover elevation and smooth background transition to `.snow-device-list li`.

### Wave 2: Component Architecture & Integration (`dashboard/src/FalseAlertMetrics.jsx` & `dashboard/src/App.jsx`)

4. **Reusable `AnimatedCounter` Component (`ANIM-01`)**:
   - Create `AnimatedCounter` using `requestAnimationFrame` with cubic ease-out easing (`progress => 1 - Math.pow(1 - progress, 3)`).
   - Support `value`, `duration = 800`, `suffix = ''`, `decimals = 0`.
   - Smoothly interpolate from `previousValue` to `newValue` on filter changes, poll intervals, or simulations.
5. **Integrate KPI Counters in `FalseAlertMetrics.jsx`**:
   - Wire `AnimatedCounter` into all 8 KPI cards:
     - Row 1: Total Processed, Suppression Rate (`decimals={1}`, `suffix="%"`, color `var(--accent-green)`), Tickets Avoided, SNOW Tickets.
     - Row 2: Backdated / Suppressed, Auto-Resolving, Non-Auto Resolving, Uncertain.
6. **Update ServiceNow Ticket Details JSX (`STATE-02`)**:
   - Restructure section into `.snow-section-header` with Lucide `<FileText />`, title "ServiceNow Incident Activity", and dynamic `<span className="snow-total-badge">{totalRecords} Total Impact</span>`.
   - Update the 3 cards with distinct accent classnames and count badges.
7. **View Crossfade Integration in `App.jsx` (`ANIM-02`)**:
   - Wrap view component rendering in `<div key={activeView} className="view-transition-container">`.

### Wave 3: Verification & Visual Polish

8. **Automated Verification**:
   - Run `npm run lint` in `dashboard/` to verify zero linting errors.
   - Run `npm run build` in `dashboard/` to verify clean bundle compilation.
   - Run `python -m pytest -q` to verify backend integrity.
9. **Live Browser Verification**:
   - Use `browser_subagent` to test `http://localhost:5173/`.
   - Verify KPI cards animate numbers from `0 → N` on page load.
   - Verify clicking "+5 Simulate Alerts" or changing filters smoothly animates numbers to new values.
   - Verify tab switching transitions smoothly via `.view-transition-container`.
   - Verify ServiceNow Ticket Details display enhanced divider, colored card borders, and monospace incident pills.
