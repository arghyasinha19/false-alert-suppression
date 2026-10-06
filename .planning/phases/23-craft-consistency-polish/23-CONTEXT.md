# Phase 23: Craft & Consistency Polish - Context

**Gathered:** 2026-10-06  
**Status:** Ready for planning  

<domain>
## Phase Boundary

Phase 23 delivers visual polish and design system consistency across the operations dashboard, closing the final requirement (`UI-09-22`) of Milestone v1.9. Specifically, it standardizes the application's typographic hierarchy into 6 strict scale tokens, converges the KPI card designs across views to the executive NOC card architecture, eliminates prototype demo scaffolding from the production chrome, introduces a unified reusable `EmptyState` component for all zero-match/empty data views, and expands domain abbreviations (SNOW, DNAC, DLX, MTTR, P1–P3) with accessible tooltips and descriptive sub-labels.

</domain>

<decisions>
## Implementation Decisions

### 1. KPI Card Design Convergence
- **D-01:** Converge `FalseAlertMetrics.jsx` KPI cards to the executive NOC card architecture (`.glass-card.noc-kpi-card`). Every KPI card adopts the structured two-row architecture:
  - Top row (`.noc-kpi-top`): Icon container on left, semantic status badge on right (`<span className="badge badge-subtle ...">`).
  - Body section (`.noc-kpi-body`):
    - Title (`.noc-kpi-title`): Uppercase label using `--font-xs` (`12px`) with letter spacing.
    - Value row (`.noc-kpi-value-row`): Bold primary number (`.noc-kpi-value`) using `--font-xl` (`24px`) alongside an optional unit label (`.noc-kpi-unit`).
    - Footer (`.noc-kpi-footer`): Contextual subtitle (`.noc-kpi-subtitle`) using `--font-xs` (`12px`).
- **D-02:** Retain interactive click-to-filter functionality on Row 2 cards in `FalseAlertMetrics.jsx` (Backdated, Auto-Resolving, Non-Auto, Uncertain), enhanced with:
  - An explicit top-right status badge that displays `"FILTERABLE"` when inactive and `"ACTIVE FILTER ✓"` when selected.
  - Glowing border highlight (`.active.highlight-*`) matching the category hue when active.
  - Subtitle indicating `"Click to clear filter"` when active vs category description when idle.

### 2. Strict 6-Step Typography Scale
- **D-03:** Define 6 strict typography tokens in `dashboard/src/index.css`:
  - `--font-xs: 0.75rem;` (12px) — Badges, table headers, captions, metadata tags, timestamps, chips, micro-labels.
  - `--font-sm: 0.8125rem;` (13px) — Primary body text, table data cells, form controls, filter pills, dropdown options.
  - `--font-md: 0.9375rem;` (15px) — Card titles, subheadings, drawer section labels, chat messages.
  - `--font-lg: 1.125rem;` (18px) — View section titles, modal headers, major card numbers/stats.
  - `--font-xl: 1.5rem;` (24px) — Primary KPI card values, medium metric counters.
  - `--font-2xl: 2.125rem;` (34px) — Executive health score, hero KPI value numbers.
- **D-04:** Refactor all ad-hoc font-size declarations across `dashboard/src/App.css` and `dashboard/src/ChatPanel.css` to consume these 6 CSS variables (or their exact rem values).
- **D-05:** Enforce this 6-step scale via an automated contract test (`tests/test_craft_polish_contract.py`), strictly verifying that zero non-standard font sizes exist in the production stylesheet (exempting SVG internal diagrams with coordinate-based canvas dimensions).

### 3. Demo Scaffolding & Simulation Controls Cleanup
- **D-06:** Completely remove the prototype "⚡ Simulate +5 Alerts" button (`.filter-pill.simulate-btn`) from `FalseAlertMetrics.jsx`. The backend already loads 60 realistic seeded alerts from `simulated_alerts.json`, and live polling/mock fallback operates automatically, eliminating the need for prototype injection buttons in the production chrome.
- **D-07:** Retain the unobtrusive `[Mock / Seed Data]` connection badge and top warning banner in `App.jsx` strictly for authentic telemetry state demarcation (as locked in Phase 19).

### 4. Standardized Empty States & Domain Abbreviations
- **D-08:** Create a dedicated, reusable `EmptyState.jsx` component (`dashboard/src/components/EmptyState.jsx`) featuring:
  - Theme-aware circular icon container (48px diameter) with subtle accent background.
  - Heading in `--font-md` (`15px`, font-weight: 700).
  - Helper description in `--font-sm` (`13px`, color: `var(--text-secondary)`).
  - Optional action button (`actionLabel`, `onAction`) with `--font-sm` (`13px`) min-height 32px styling (e.g. "Clear filters" or "Reset search").
- **D-09:** Replace ad-hoc empty state messages across all views and tables with `EmptyState.jsx`:
  - `FalseAlertMetrics.jsx`: Detailed Traceability Matrix (zero-match alerts) & Device Ranking Table.
  - `NetworkOperations.jsx`: Topology zero-match view, SRE table zero-match view, and Details Drawer alerts tab empty state.
  - `AlertPatterns.jsx`: Pattern table zero-match view & cluster alerts empty state.
- **D-10:** Expand domain shorthand throughout the interface with clear tooltips (`title="..."`) and accessible visual labels:
  - `SNOW` → "ServiceNow ITSM Ticketing System"
  - `DNAC` → "Cisco DNA Center (Catalyst Center) Controller"
  - `DLX` → "Dead Letter Exchange (RabbitMQ delayed retry queue)"
  - `MTTR` → "Mean Time to Resolve (Incident triage duration)"
  - `SRE` → "Site Reliability Engineering"
  - `NOC` → "Network Operations Center"
  - `P1 / P2 / P3` → "Priority 1 (Critical) / Priority 2 (Major) / Priority 3 (Warning)"

### the agent's Discretion
- For the `EmptyState.jsx` component, provide graceful fallback icon defaults (e.g. `FilterX` or `Inbox`) when no custom icon is passed.
- Ensure all KPI card layout refactoring preserves responsive grid flexibility across both `1100px` tablet and desktop widths.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` §UI-POLISH — Requirement UI-09-22.
- `.planning/ROADMAP.md` §Phase 23 — Phase 23 Goal, Requirements, and Success Criteria.
- `.planning/v1.9-MILESTONE-AUDIT.md` — Milestone audit gap analysis.

### Stylesheets & Design System
- `dashboard/src/index.css` — Global CSS tokens, theme definitions, and typography variables.
- `dashboard/src/App.css` — KPI card styles, layout grids, tables, buttons, and empty states.
- `dashboard/src/ChatPanel.css` — Chat assistant typography and message bubbles.

### Views & Components
- `dashboard/src/FalseAlertMetrics.jsx` — KPI card grids, simulation button, filter bar, and alert tables.
- `dashboard/src/NetworkOperations.jsx` — Reference NOC executive KPI cards (`.glass-card.noc-kpi-card`) and empty states.
- `dashboard/src/AlertPatterns.jsx` — Pattern tables, granularity toggles, and empty states.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets & Patterns
- Reference NOC KPI Card (`NetworkOperations.jsx` L1292-1370):
  - `.glass-card.noc-kpi-card`
  - `.noc-kpi-top`: `.kpi-icon` + `.badge.badge-subtle`
  - `.noc-kpi-body`: `.noc-kpi-main` (`.noc-kpi-title`, `.noc-kpi-value-row`), `.noc-kpi-footer` (`.noc-kpi-subtitle`)
- Existing Card Grids: `.kpi-grid` uses CSS Grid `grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));` with `0.75rem` / `1rem` gap.
- Lucide React icons available: `Activity`, `ShieldCheck`, `Clock`, `CheckCircle`, `AlertTriangle`, `HelpCircle`, `FilterX`, `Inbox`, `RotateCcw`, `Sparkles`.

</code_context>

<deferred>
## Deferred Ideas

- None. All discussed items are strictly within the scope of Phase 23.

</deferred>

---

*Phase: 23-craft-consistency-polish*  
*Context gathered: 2026-10-06 via discuss-phase*
