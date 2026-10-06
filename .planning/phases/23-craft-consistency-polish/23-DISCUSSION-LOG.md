# Phase 23: Craft & Consistency Polish - Discussion Log

**Date:** 2026-10-06  
**Phase:** 23 — Craft & Consistency Polish  
**Participants:** Pair programming with User  

---

## Areas Discussed & User Selections

### Area 1: KPI Card Visual Convergence
- **Question:** How should FalseAlertMetrics KPI cards converge with the NOC executive card architecture?
- **Options Presented:**
  1. *(Recommended)* Adopt full NOC card structure (top icon + badge, main value + unit, footer subtitle) and retain Row 2 click-to-filter with an "ACTIVE FILTER ✓" badge state.
  2. Adopt NOC card visual structure for Row 1 only, keeping Row 2 cards as compact clickable tiles.
  3. Decouple filtering completely: make all KPI cards read-only metrics and keep filtering strictly in the filter bar above.
- **User Selection:** Option 1 — Adopt full NOC card structure for all cards, enhancing Row 2 with an explicit "ACTIVE FILTER ✓" badge state and glowing border highlight when active.

### Area 2: Typography Scale Strictness
- **Question:** How strictly should the 6-step typography scale be enforced across the codebase?
- **Options Presented:**
  1. *(Recommended)* Define `--font-xs` through `--font-2xl` in index.css, map all UI elements across App.css and ChatPanel.css to these 6 tokens, and lock via automated contract test (exempting SVG internal diagrams).
  2. Map only headers, cards, tables, and inputs to the 6 tokens, leaving secondary component font sizes as-is.
  3. Enforce the 6 tokens strictly across everything including SVG topology text.
- **User Selection:** Option 1 — Define `--font-xs` through `--font-2xl` in index.css, map all UI elements across App.css and ChatPanel.css to these 6 tokens, and lock via automated contract test (exempting SVG internal diagrams).

### Area 3: Demo Scaffolding & Simulation Controls
- **Question:** How should the "Simulate +5 Alerts" button and demo scaffolding be treated in the production dashboard?
- **Options Presented:**
  1. Move "Simulate +5 Alerts" into a secondary utility position inside the Filter Bar, styled as a standard clean button rather than a prominent hero gradient button.
  2. Remove the "⚡ Simulate +5 Alerts" button entirely from the UI (the 60 seeded alerts and mock fallback provide sufficient realistic data).
  3. Only render the simulation button when the application is actively in Demo / Offline mode, hiding it completely in Connected mode.
- **User Selection:** Option 2 — Remove the "⚡ Simulate +5 Alerts" button entirely from the UI. The 60 seeded alerts and mock fallback provide sufficient realistic data, elevating the dashboard to genuine production grade.

### Area 4: Standardized Empty States & Domain Tooltips
- **Question:** How should standardized empty states and domain shorthand expansions be implemented?
- **Options Presented:**
  1. *(Recommended)* Build a unified EmptyState reusable component with icon, title, description, and "Reset filters" action, plus explicit tooltips and visible subtitles for all domain abbreviations (SNOW, DNAC, DLX, MTTR, P1-P3).
  2. Provide inline styling for empty states per table with tooltips on abbreviations only.
  3. Add an abbreviations legend modal / drawer explaining all terms in addition to table tooltips.
- **User Selection:** Option 1 — Build a unified EmptyState reusable component with icon, title, description, and "Reset filters" action, plus explicit tooltips and visible subtitles for all domain abbreviations.

---

## Resulting Decisions Summary

- **D-01 & D-02**: Converge all KPI cards to NOC architecture with top-right badges; retain interactive filtering on Row 2 with "ACTIVE FILTER ✓" badge state.
- **D-03, D-04, D-05**: Implement 6-step typography scale (`--font-xs` to `--font-2xl`) across CSS and enforce via automated pytest contract.
- **D-06 & D-07**: Eliminate the "Simulate +5 Alerts" button from the UI.
- **D-08, D-09, D-10**: Build reusable `EmptyState.jsx` and expand domain abbreviations with descriptive tooltips and sub-labels.
