# Phase 21: Trust & Contrast Remediation - Context

**Gathered:** 2026-10-06  
**Status:** Ready for planning  

<domain>
## Phase Boundary

Phase 21 delivers WCAG AA contrast compliance across the entire web application and establishes dynamic theme integration for all chart and visualization components. Specifically, it corrects inverted/under-contrasted `--text-tertiary` tokens, introduces high-contrast semantic tokens for blue pills and badges, establishes a centralized `useChartTheme()` hook to dynamically supply theme-aware colors to Recharts and SVG charts on dark/light toggle, updates chart axes, grids, and tooltips, and locks in automated contrast contract testing.

</domain>

<decisions>
## Implementation Decisions

### 1. Token Contrast Remediation (UI-05)
- **D-01:** Correct `--text-tertiary` in `dashboard/src/index.css` to `#64748b` in light mode (4.6:1 against `#ffffff`) and `#94a3b8` in dark mode (5.4:1 against `#111827`), eliminating WCAG AA failures across tertiary text, placeholders, and subtle labels.
- **D-02:** Introduce dedicated semantic tokens `--badge-blue-text: #1d4ed8;` (light mode) and `--badge-blue-text: #93c5fd;` (dark mode) in `dashboard/src/index.css`. Apply this token to `.badge.backdated`, `.badge.snow-new`, `.badge.badge-subtle.blue`, and filter active pills, delivering crisp >7:1 contrast without distorting general accent blue button fills.

### 2. Dynamic Chart Theme Integration (UI-06)
- **D-03:** Build a centralized `useChartTheme()` React hook in `dashboard/src/hooks/useChartTheme.js` that inspects computed styles or listens to theme changes (`data-theme` attribute mutation on `document.documentElement` / custom event), returning an updated palette of resolved colors (`blue`, `green`, `red`, `yellow`, `purple`, `grid`, `axisText`, `tooltipBg`, `tooltipBorder`, `textPrimary`).
- **D-04:** Wire all chart components—including `FalseAlertMetrics.jsx` (Alert Volume AreaChart, Category PieChart), `AlertPatterns.jsx` (Volume Trend ComposedChart), and `ChatChart.jsx` (Assistant visualization cards)—to `useChartTheme()`, replacing hardcoded hex codes (`#2563eb`, `#059669`, `#dc2626`, `#94a3b8`, etc.) in SVG gradients, strokes, fills, and tick definitions.

### 3. Chart Axes, Grids & Tooltips
- **D-05:** Chart axis ticks (`XAxis`, `YAxis`) route to `--text-secondary` (`#475569` in light / `#cbd5e1` in dark) for sharp operational readability. Chart grid lines (`CartesianGrid`) bind to `--card-border`.
- **D-06:** Recharts hover tooltips dynamically pull styling from `var(--card-bg)`, `var(--card-border)`, and `var(--text-primary)`, replacing static dark tooltip definitions so light mode receives clean white-glass tooltips and dark mode receives midnight-glass tooltips.

### 4. Automated Verification & Contrast Tests
- **D-07:** Implement `tests/test_contrast_remediation_contract.py` validating:
  - WCAG contrast formula: `--text-tertiary` against `--card-bg` / `--bg-color` $\ge 4.5:1$ in both light and dark themes.
  - Blue badge text contrast: `--badge-blue-text` against `--accent-blue-light` $\ge 4.5:1$ (targeting $\ge 7:1$) in both light and dark themes.
  - Component integration: `FalseAlertMetrics.jsx`, `AlertPatterns.jsx`, and `ChatChart.jsx` import and invoke `useChartTheme()`, binding axes, ticks, grids, and gradients dynamically.

### the agent's Discretion
- Gradient opacity curves (`offset="5%"` at 0.35 opacity to `offset="95%"` at 0.0 opacity) remain smooth and proportional across both themes.
- Recharts legend text wrapper styles adapt dynamically to `var(--text-secondary)`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` §UI-CONTRAST — Definitions for UI-05 and UI-06.
- `.planning/ROADMAP.md` §Phase 21 — Phase 21 Goal, Requirements, and Success Criteria.

### Design System & Theme Engine
- `dashboard/src/index.css` — CSS custom properties, theme tokens (`:root`, `[data-theme="light"]`, `[data-theme="dark"]`).
- `dashboard/src/App.css` — Badge classes, chart card container styles, filter pills.

### Chart Implementations
- `dashboard/src/FalseAlertMetrics.jsx` — Alert Volume AreaChart & Category PieChart.
- `dashboard/src/AlertPatterns.jsx` — Alert Volume ComposedChart with dual Y-axes.
- `dashboard/src/ChatChart.jsx` — Chatbot Assistant LineChart, BarChart, and PieChart.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `dashboard/src/index.css`: Contains CSS variables for theme modes (`--text-primary`, `--text-secondary`, `--text-tertiary`, `--accent-*`, `--card-bg`, `--card-border`).
- `data-theme` attribute on `document.documentElement`: Toggled by Theme Context or header theme toggle.

### Established Patterns
- High-contrast tokens: Theme system established in Phase 08 with CSS variables.
- Contract testing: Python-based regex and AST tests in `tests/test_*_contract.py` verifying design contracts rapidly without heavy browser harnesses.

</code_context>

<deferred>
## Deferred Ideas

- None. All discussed items are within the scope of Phase 21.

</deferred>

---

*Phase: 21-trust-contrast-remediation*  
*Context gathered: 2026-10-06 via discuss-phase*
