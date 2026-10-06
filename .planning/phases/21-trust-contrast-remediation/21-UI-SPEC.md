---
phase: 21
slug: trust-contrast-remediation
status: approved
shadcn_initialized: false
preset: none
created: 2026-10-06
reviewed_at: 2026-10-06
---

# Phase 21 — UI Design Contract: Trust & Contrast Remediation

> Visual and interaction design contract for WCAG 2.1 AA/AAA color contrast remediation, high-contrast blue badge and pill text tokens, and dynamic theme integration for all chart and visualization components (`useChartTheme()`) across the Cisco DNA Center Ops Center dashboard.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (Vanilla CSS custom design tokens) |
| Preset | not applicable |
| Component library | none (custom React 19 components) |
| Chart Library | recharts 2.x (`AreaChart`, `ComposedChart`, `PieChart`, `LineChart`, `BarChart`, `ResponsiveContainer`) |
| Icon library | lucide-react (`TrendingDown`, `BarChart3`, `PieChart`, `Filter`, `Search`, `Award`, `ShieldCheck`) |
| Font | Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif |
| Monospace Font | ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace |

---

## Spacing Scale

Declared values (must be multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Icon gaps, badge padding offsets, chart legend icon gaps |
| sm | 8px | Badge vertical padding, axis tick margins, chart tooltip padding |
| md | 16px | Card inner margins, chart header padding, filter controls gap |
| lg | 24px | Section padding, charts grid gaps |
| xl | 32px | Major dashboard block separation |
| 2xl | 48px | Page-level layout breaks |
| 3xl | 64px | View boundary buffers |

**Exceptions:**
- `280px` / `300px`: Chart canvas fixed container heights (`height: 280px`, `height: 300px`). *Justification:* Standardized responsive container heights maintaining uniform horizontal alignment between adjacent chart cards.

---

## Typography Scale

Constrained to exactly 4 sizes and 2 weights:

| Role | Size | Weight | Line Height | Usage |
|------|------|--------|-------------|-------|
| Heading | 16px (1.0rem) | 600 (Semibold) | 1.35 (21.6px) | Chart card headers, KPI section titles |
| Body | 14px (0.875rem) | 400 (Regular) | 1.50 (21px) | Chart tooltip data rows, descriptive labels |
| Caption | 12px (0.75rem) | 500 (Medium) | 1.25 (15px) | Chart legends, badge and pill text (`.badge`, `.filter-pill`) |
| Micro / Tick | 10px (0.625rem) | 500 (Medium) | 1.20 (12px) | Axis ticks (`XAxis`, `YAxis`), mini sparkline labels |

---

## Color & 60/30/10 Split

| Role | Value (Dark Theme) | Value (Light Theme) | Usage |
|------|--------------------|---------------------|-------|
| Dominant (60%) | `#0a0e17` (`--bg-color`) | `#f0f2f5` (`--bg-color`) | Main page canvas and dashboard surfaces |
| Secondary (30%) | `#111827` (`--card-bg`, `--bg-secondary`) | `#ffffff` (`--card-bg`, `--bg-secondary`) | Chart cards, table containers, tooltip cards |
| Accent (10%) | `#3b82f6` (`--accent-blue`) | `#2563eb` (`--accent-blue`) | Chart primary series, active tab indicators |

---

## Contrast Remediation Contract (UI-05)

### 1. Tertiary Text Token Remediation (`--text-tertiary`)
The `--text-tertiary` token previously had inverted values that caused severe WCAG contrast failures in both themes.

| Theme | Previous Hex | New Hex | Background | New Contrast Ratio | WCAG AA Requirement | Status |
|---|---|---|---|---|---|---|
| **Light Theme** | `#94a3b8` (2.5:1 ❌) | `#64748b` | `#ffffff` | **4.64:1** | 4.5:1 (Normal Text) | **PASS (AA)** |
| **Dark Theme** | `#64748b` (2.7:1 ❌) | `#94a3b8` | `#111827` | **5.45:1** | 4.5:1 (Normal Text) | **PASS (AA)** |

**Applied to:**
- Form filter placeholders (`.filter-search::placeholder`)
- Secondary table metadata cells, timestamps, and confidence indicators
- Chart card subtitle icons and disabled indicators
- Empty state text notes and drawer timestamp labels

### 2. Blue Pill & Badge Contrast Contract (`--badge-blue-text`)
Blue pills and status badges rendered on light blue translucent tints must meet WCAG AA (and AAA for large text) with strong legibility.

| Theme | Token | Hex | Badge Tint | Contrast Ratio | Compliance |
|---|---|---|---|---|---|
| **Light Theme** | `--badge-blue-text` | `#1d4ed8` | `#eff6ff` (`--accent-blue-light`) | **7.32:1** | **PASS (AAA)** |
| **Dark Theme** | `--badge-blue-text` | `#93c5fd` | `rgba(59, 130, 246, 0.16)` on `#111827` | **9.81:1** | **PASS (AAA)** |

**Applied to:**
- `.badge.backdated`
- `.badge.snow-new`
- `.badge.badge-subtle.blue`
- Active filter pill counters and blue state tags

---

## Dynamic Chart Theme System (`UI-06`)

### 1. Centralized Hook Architecture (`useChartTheme`)
A shared hook in `dashboard/src/hooks/useChartTheme.js` reads computed CSS variables from `document.documentElement` and listens to theme changes (`data-theme` mutations and storage events).

```javascript
export function useChartTheme() {
  // Returns:
  // {
  //   theme: 'light' | 'dark',
  //   colors: {
  //     primary: '#2563eb' | '#3b82f6',
  //     success: '#059669' | '#10b981',
  //     danger: '#dc2626' | '#ef4444',
  //     warning: '#d97706' | '#f59e0b',
  //     purple: '#7c3aed' | '#8b5cf6',
  //     cyan: '#0891b2' | '#06b6d4',
  //     orange: '#ea580c' | '#f97316',
  //   },
  //   axis: {
  //     stroke: '#475569' | '#cbd5e1', // --text-secondary
  //     tickFill: '#475569' | '#cbd5e1',
  //     fontSize: 10,
  //   },
  //   grid: {
  //     stroke: 'var(--card-border)',
  //     dashArray: '3 3',
  //   },
  //   tooltip: {
  //     background: '#ffffff' | '#111827',
  //     border: 'rgba(0, 0, 0, 0.08)' | 'rgba(255, 255, 255, 0.12)',
  //     color: '#0f172a' | '#f8fafc',
  //   }
  // }
}
```

### 2. Component Refactoring Matrix

| File | Chart Component | Previous Hardcoded Values | New Dynamic Binding |
|---|---|---|---|
| `FalseAlertMetrics.jsx` | `AreaChart` (Alert Volume Trend) | `#2563eb`, `#059669`, `#dc2626`, `#d97706`, `#94a3b8` ticks | `useChartTheme().colors.*`, `useChartTheme().axis`, `gradBackdated`, `gradAuto`, `gradNonAuto` |
| `FalseAlertMetrics.jsx` | `PieChart` (Category Distribution) | Static `CATEGORY_COLORS` hex table, static `TOOLTIP_STYLE` | Dynamic category color palette via `useChartTheme()`, dynamic `tooltipStyle` |
| `AlertPatterns.jsx` | `ComposedChart` (Volume Series) | `#2563eb`, `#059669`, `#dc2626`, `#d97706`, `#7c3aed`, `#94a3b8` | `useChartTheme().colors.*`, dual Y-axes using `chartTheme.axis` |
| `ChatChart.jsx` | `LineChart`, `BarChart`, `PieChart` | `#2563eb`, `#059669`, `#dc2626`, hardcoded tooltip styles | `useChartTheme()` dynamic theme palette, axis styles, and glassmorphism tooltip |

### 3. Chart Tooltip Specification
All chart tooltips must conform to the unified glassmorphism styling:
- **Background:** `var(--card-bg)` with `backdrop-filter: blur(12px)`
- **Border:** `1px solid var(--card-border)`
- **Border Radius:** `10px`
- **Box Shadow:** `var(--shadow-md)`
- **Text Color:** `var(--text-primary)`
- **Padding:** `10px 14px`
- **Font Size:** `0.82rem`

---

## Verification & Anti-Patterns

### Anti-Patterns to Prevent:
1. ❌ **Inverted `--text-tertiary` hexes:** `#94a3b8` in light mode or `#64748b` in dark mode.
2. ❌ **Low-contrast blue badges:** Using raw `#3b82f6` or `#2563eb` on light blue backgrounds without `--badge-blue-text`.
3. ❌ **Hardcoded hexes in Recharts:** Direct strings like `stroke="#2563eb"` or `fill="#94a3b8"` in SVG definitions instead of `useChartTheme()`.
4. ❌ **Dark-only Tooltip styling:** Static `TOOLTIP_STYLE = { background: '#0f172a', ... }` that clashes with light mode.

### Automated Testing Contract:
`tests/test_contrast_remediation_contract.py` will mathematically verify:
1. WCAG AA contrast ratio $\ge 4.5:1$ for `--text-tertiary` in both modes.
2. WCAG AAA contrast ratio $\ge 7:1$ for `--badge-blue-text` in both modes.
3. CSS badge rules binding `.badge.backdated`, `.badge.snow-new`, and subtle blue pills to `--badge-blue-text`.
4. Existence and correctness of `useChartTheme.js`.
5. Dynamic consumption of `useChartTheme` across all target chart components (`FalseAlertMetrics`, `AlertPatterns`, `ChatChart`).
