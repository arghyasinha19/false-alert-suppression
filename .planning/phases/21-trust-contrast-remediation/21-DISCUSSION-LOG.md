# Phase 21: Trust & Contrast Remediation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-06  
**Phase:** 21-trust-contrast-remediation  
**Areas discussed:** Chart Dynamic Theme Mechanism, Blue Pill & Badge Contrast Strategy, Chart Axis Grid & Tooltip Styling, Contrast Regression Test Scope  

---

## Chart Dynamic Theme Mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| Centralized hook | Centralized `useChartTheme()` hook reading resolved CSS variables from `document.documentElement` on `data-theme` changes | ✓ |
| Static palette dictionary | Static `CHART_PALETTES` dictionary keyed by theme mode ('light' \| 'dark') imported into chart components | |
| Inline CSS variables | Inline CSS variables with fallback values directly in SVG/Recharts props (`var(--accent-blue, #2563eb)`) | |

**User's choice:** Centralized `useChartTheme()` hook reading resolved CSS variables from `document.documentElement` on `data-theme` changes.  
**Notes:** Recharts renders in SVG and often fails to compute CSS variables natively in canvas/defs contexts across all browsers. Reading resolved values through a hook ensures reliable real-time updates when toggling dark/light mode.

---

## Blue Pill & Badge Contrast Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated semantic tokens | Dedicated semantic tokens (`--badge-blue-text: #1d4ed8` light / `#93c5fd` dark) applied to all blue pills/badges | ✓ |
| Global accent adjustment | Darken `--accent-blue` token globally (`#1d4ed8` in light mode) across buttons, links, and badges | |
| Component-level CSS overrides | Component-level CSS rules in `App.css` targeting specific classes directly | |

**User's choice:** Dedicated semantic tokens (`--badge-blue-text: #1d4ed8` light / `#93c5fd` dark) applied to all blue pills/badges for crisp 7:1+ contrast.  
**Notes:** Preserves primary button aesthetics while ensuring text on light/dark translucent blue badge pills passes WCAG AA and AAA standards.

---

## Chart Axis, Grid & Tooltip Styling

| Option | Description | Selected |
|--------|-------------|----------|
| Secondary axis text + dynamic tooltips | Axis ticks on `--text-secondary` for high clarity, grid lines on `--card-border`, and tooltips dynamically using card theme tokens | ✓ |
| Tertiary axis text | Axis ticks on `--text-tertiary` for softer visual weight, keeping tooltip styles unchanged | |
| Secondary axis text + static tooltips | Axis ticks on `--text-secondary`, but keep static tooltips | |

**User's choice:** Axis ticks on `--text-secondary` for high clarity, grid lines on `--card-border`, and tooltips dynamically using card theme tokens.  
**Notes:** Telemetry values on axes require immediate legibility without squinting; tooltips should blend smoothly into active theme background.

---

## Contrast Regression Test Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Multi-level contract test | Automated WCAG contrast calculation for tokens/badges + component hook integration checks | ✓ |
| CSS token-only contract test | Pure regex test verifying hex codes in `index.css` and `App.css` | |

**User's choice:** Multi-level contract test: automated WCAG contrast calculation for tokens/badges + component hook integration checks.  
**Notes:** Prevents future token regressions and ensures chart components consistently utilize the dynamic theme hook.

---

## the agent's Discretion

- Gradient opacity stops and smooth area chart fills.
- Legend typography wrapper styling.

## Deferred Ideas

None.
