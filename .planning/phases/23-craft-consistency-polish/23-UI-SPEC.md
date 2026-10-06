---
phase: 23
slug: craft-consistency-polish
status: approved
shadcn_initialized: false
preset: none
created: 2026-10-06
reviewed_at: 2026-10-06
---

# Phase 23 — UI Design Contract: Craft & Consistency Polish

> Visual and interaction design contract for the final polish phase of Milestone v1.9 (`UI-09-22`). Locks the 6-step typography token scale, converges all KPI cards to the executive NOC card architecture with interactive filtering states, creates the unified `EmptyState` component contract, formalizes domain abbreviation tooltips, and eliminates prototype simulation scaffolding from the production interface.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (Vanilla CSS custom design tokens) |
| Preset | not applicable |
| Component library | none (custom React 19 components) |
| Icon library | lucide-react (`Activity`, `ShieldCheck`, `Ban`, `Ticket`, `Clock`, `CheckCircle`, `AlertTriangle`, `Zap`, `FilterX`, `Inbox`, `RotateCcw`, `FileText`, `Flame`, `Timer`, `Radio`, `SearchX`) |
| Font | Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif |
| Monospace Font | ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace |

---

## 1. Strict 6-Step Typography Scale Contract (`UI-09-22`)

To ensure visual hierarchy discipline and eliminate typographic fragmentation, all typography across the application must strictly map to 6 design tokens declared in `:root` inside `dashboard/src/index.css`:

```css
/* 6-Step Typography Scale Tokens */
--font-xs: 0.75rem;     /* 12px / 0.75rem - Badges, table headers, metadata tags, captions, chips */
--font-sm: 0.8125rem;   /* 13px / 0.8125rem - Body text, table cells, form controls, filter pills */
--font-md: 0.9375rem;   /* 15px / 0.9375rem - Card titles, subheadings, drawer section labels */
--font-lg: 1.125rem;    /* 18px / 1.125rem - Section titles, modal headers, major numbers */
--font-xl: 1.5rem;      /* 24px / 1.5rem - Primary KPI card values, medium metric counters */
--font-2xl: 2.125rem;   /* 34px / 2.125rem - Executive health score & hero numbers */
```

### Typographic Roles & Hierarchy

| Token | Size | Equivalent | Weight | Line Height | Application Scope |
|-------|------|------------|--------|-------------|-------------------|
| `--font-xs` | `0.75rem` | 12px | 500 / 600 / 700 | 1.35 (16px) | `.badge`, table `<th>`, `.sr-only`, `.table-footer-status`, timestamps, metric card subtitles (`.noc-kpi-subtitle`), uppercase category tags |
| `--font-sm` | `0.8125rem` | 13px | 400 / 500 / 600 | 1.45 (19px) | Default body text, table data cells (`<td>`), `.filter-pill`, `.filter-select`, `.filter-search`, drawer field values, chat inputs |
| `--font-md` | `0.9375rem` | 15px | 600 / 700 | 1.35 (20px) | Card titles (`.card h3`, `.noc-kpi-title`), drawer section headers, empty state titles, toolbar headings |
| `--font-lg` | `1.125rem` | 18px | 700 / 800 | 1.25 (22.5px) | View section titles (`.section-title`), modal titles, drawer header device names, secondary hero metric values |
| `--font-xl` | `1.5rem` | 24px | 700 / 800 | 1.15 (27.5px) | Primary KPI values (`.noc-kpi-value`), large counter numbers |
| `--font-2xl` | `2.125rem` | 34px | 800 / 900 | 1.1 (37.5px) | Executive health score (`.fleet-health-number`), hero numbers |

> [!IMPORTANT]
> Non-standard font-size values (e.g. `0.7rem`, `0.72rem`, `0.8rem`, `0.85rem`, `0.95rem`, `1.2rem`, `1.4rem`) in `dashboard/src/App.css` and `dashboard/src/ChatPanel.css` must be converted to the nearest semantic token or its exact rem value. Automated verification in `tests/test_craft_polish_contract.py` validates compliance (exempting internal coordinate-based SVG canvas elements).

---

## 2. Spacing Scale

Declared values (strictly 4px/8px multiples conforming to GSD UI brand guidelines):

| Token | Value | Rem | Usage |
|-------|-------|-----|-------|
| `xs` | 4px | 0.25rem | Icon gaps, inline tag padding, micro-spacing |
| `sm` | 8px | 0.5rem | Compact element spacing, badge padding, filter item gap |
| `md` | 16px | 1rem | Standard element margin, card body padding, table cell padding |
| `lg` | 24px | 1.5rem | Section gaps, card padding, modal interior margins |
| `xl` | 32px | 2rem | Major component gutters, grid row gaps |
| `2xl` | 48px | 3rem | View section separation |
| `3xl` | 64px | 4rem | Page-level spacing and bounds |

Exceptions: `38px` icon box dimension and `156px` min-height for `.noc-kpi-card` to match existing NOC telemetry card geometry.

---

## 3. Color System (60-30-10 Rule)

| Role | Light Value | Dark Value | Usage |
|------|-------------|------------|-------|
| **Dominant (60%)** | `#f0f2f5` (bg) / `#ffffff` (surface) | `#0a0e17` (bg) / `#111827` (surface) | Main application canvas, sidebar background, content area |
| **Secondary (30%)** | `#ffffff` (card-bg) / `#e2e8f0` (borders) | `#111827` (card-bg) / `rgba(255,255,255,0.08)` | Glass cards, table containers, docked inspector panel, dropdown menus |
| **Accent (10%)** | `#2563eb` (Blue), `#059669` (Green), `#dc2626` (Red), `#d97706` (Amber), `#7c3aed` (Purple) | `#3b82f6`, `#10b981`, `#ef4444`, `#f59e0b`, `#8b5cf6` | Reserved strictly for semantic indicators: KPI status badges, card top stripes, active filter pills, topology nodes |
| **Destructive** | `#dc2626` (Red) | `#ef4444` (Red) | Critical SLA status, P1 severity badges, reset confirmation |

### Accent Allocation Gate
Accent colors are strictly reserved for:
1. Top accent stripes (`.noc-kpi-card::after`) and category indicator badges (`.badge.badge-subtle.*`).
2. Active filter pill background / outline (`.filter-pill.active`, `.noc-kpi-card.active`).
3. Sparkline and chart trend strokes (`#2563eb`, `#059669`).
4. Interactive focus rings (`:focus-visible` outline).
*Never applied broadly to entire card surfaces, neutral text, or table rows.*

---

## 4. KPI Card Convergence Architecture Specification (`D-01`, `D-02`)

All 8 KPI cards in `FalseAlertMetrics.jsx` are refactored from their legacy `.kpi-card` markup to the unified executive NOC architecture (`.glass-card.noc-kpi-card`).

### Structural Schema
```html
<div class="glass-card noc-kpi-card highlight-{category} {isClickable ? 'clickable' : ''} {isActive ? 'active' : ''}" ...>
  <!-- 1. Top Section: 38px Icon + Status Badge -->
  <div class="noc-kpi-top">
    <div class="kpi-icon {color}">
      <!-- Lucide Icon (20px) -->
    </div>
    <span class="badge badge-subtle {color}">
      {statusBadgeText}
    </span>
  </div>

  <!-- 2. Body Section: Title, Value Row, Footer -->
  <div class="noc-kpi-body">
    <div class="noc-kpi-main">
      <h3 class="noc-kpi-title">{Title}</h3>
      <div class="noc-kpi-value-row">
        <span class="noc-kpi-value">
          <AnimatedCounter value={number} />
        </span>
        <span class="noc-kpi-unit">{Unit}</span>
      </div>
    </div>
    <div class="noc-kpi-footer">
      <p class="noc-kpi-subtitle" title="{tooltip}">{Subtitle}</p>
    </div>
  </div>
</div>
```

### Card Mapping Matrix (Row 1: Informational Overview)

| Position | Card Title | Icon | Color Accent | Top Status Badge | Value + Unit | Subtitle |
|----------|------------|------|--------------|------------------|--------------|----------|
| 1.1 | **Total Ingested** | `Activity` | `highlight-blue` | `INGESTED` | `{kpi.total}` Alerts | Contextual filtered count vs total |
| 1.2 | **Suppression Rate** | `ShieldCheck` | `highlight-green` | `SUPPRESSED` | `{kpi.suppressionRate}%` | Noise eliminated at edge |
| 1.3 | **Tickets Avoided** | `Ban` | `highlight-cyan` | `AVOIDED` | `{kpi.ticketsAvoided}` Tickets | `{kpi.backdated} suppressed · {kpi.autoResolving} resolved` |
| 1.4 | **SNOW Tickets** | `Ticket` | `highlight-red` | `ESCALATED` | `{kpi.totalSnowTickets}` Incidents | `{kpi.snowCreated} new · {kpi.snowReopened} reopen · {kpi.snowAppended} notes` |

### Card Mapping Matrix (Row 2: Interactive Filter Cards)

Row 2 cards retain full click-to-filter capability (`onClick={() => setCategoryFilter(cat)}`), with an explicit visual state toggle:

| Position | Category Filter | Icon | Color Accent | Inactive Badge | Active Badge (`isActive`) | Inactive Subtitle | Active Subtitle |
|----------|-----------------|------|--------------|----------------|---------------------------|-------------------|-----------------|
| 2.1 | `BACKDATED` | `Clock` | `highlight-blue` | `FILTERABLE` | `ACTIVE FILTER ✓` | Suppressed by Agent 1 | Click to clear filter |
| 2.2 | `AUTO` | `CheckCircle` | `highlight-green` | `FILTERABLE` | `ACTIVE FILTER ✓` | Queued for delayed check | Click to clear filter |
| 2.3 | `NON_AUTO` | `AlertTriangle` | `highlight-red` | `FILTERABLE` | `ACTIVE FILTER ✓` | Escalated to ServiceNow | Click to clear filter |
| 2.4 | `UNCERTAIN` | `Zap` | `highlight-yellow` | `FILTERABLE` | `ACTIVE FILTER ✓` | Low ML model confidence | Click to clear filter |

### Interactive Filter Styling Contract
```css
.noc-kpi-card.clickable {
  cursor: pointer;
  user-select: none;
}

.noc-kpi-card.clickable:hover {
  transform: translateY(-2px);
  border-color: var(--accent-blue);
  box-shadow: var(--shadow-md);
}

.noc-kpi-card.clickable.active {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 2px var(--accent-blue-light), var(--shadow-md);
  background: var(--bg-tertiary);
}

.noc-kpi-card.clickable.active.highlight-green {
  border-color: var(--accent-green);
  box-shadow: 0 0 0 2px var(--accent-green-light), var(--shadow-md);
}

.noc-kpi-card.clickable.active.highlight-red {
  border-color: var(--accent-red);
  box-shadow: 0 0 0 2px var(--accent-red-light), var(--shadow-md);
}

.noc-kpi-card.clickable.active.highlight-yellow {
  border-color: var(--accent-yellow);
  box-shadow: 0 0 0 2px var(--accent-yellow-light), var(--shadow-md);
}
```

---

## 5. Reusable `EmptyState.jsx` Component Contract (`D-08`, `D-09`)

A centralized, accessible empty state component (`dashboard/src/components/EmptyState.jsx`) replaces all ad-hoc empty state DOM snippets.

### Component Signature & Props
```typescript
interface EmptyStateProps {
  icon?: React.ReactNode;          // Default: <FilterX size={24} />
  title: string;                   // Main title (e.g. "No alerts match the current matrix filters")
  description?: string;             // Explanatory guidance text
  actionLabel?: string;            // Button text (e.g. "Clear filters")
  onAction?: () => void;           // Callback for action button
  compact?: boolean;               // If true, applies reduced padding for inline drawer/widget views
  className?: string;              // Optional supplementary class
}
```

### Visual Specifications
- **Container (`.table-empty-state` / `.empty-state-card`):**
  - Padding: `3rem 1.5rem` (normal), `1.75rem 1rem` (compact).
  - Centered flex layout (`flex-direction: column; align-items: center; justify-content: center;`).
- **Icon Container (`.empty-state-badge`):**
  - Dimensions: `48px × 48px` circular badge (`border-radius: 50%`).
  - Background: `rgba(100, 116, 139, 0.08)` in light mode, `rgba(148, 163, 184, 0.12)` in dark mode.
  - Icon size: `24px` Lucide icon.
  - Icon color: `var(--text-tertiary)`.
- **Title (`.empty-state-title`):**
  - Font size: `var(--font-md)` (`0.9375rem` / 15px).
  - Font weight: `700`.
  - Color: `var(--text-primary)`.
  - Margin: `0.75rem 0 0.35rem 0`.
- **Description (`.empty-state-desc`):**
  - Font size: `var(--font-sm)` (`0.8125rem` / 13px).
  - Max width: `420px`.
  - Color: `var(--text-secondary)`.
  - Line height: `1.45`.
  - Text alignment: `center`.
- **Action Button (`.empty-state-action`):**
  - Minimum visual height: `32px`.
  - Padding: `0.4rem 0.9rem`.
  - Font size: `var(--font-sm)` (`13px`).
  - Font weight: `600`.
  - Icon: `RotateCcw` (`13px`) with `6px` right margin.
  - Background: `var(--card-bg)`.
  - Border: `1px solid var(--card-border)`.
  - Hover: `border-color: var(--accent-blue); color: var(--accent-blue); background: var(--bg-tertiary);`.

### Component Replacement Locations
1. **`FalseAlertMetrics.jsx` — Alert Matrix Table:**
   - Title: `"No alerts match the current matrix filters"`
   - Description: `"Try broadening your filter criteria or reset search queries to inspect telemetry."`
   - Action: `"Clear filters"` $\to$ resets search, device, severity, category, and SNOW filters.
2. **`FalseAlertMetrics.jsx` — Device Ranking Table:**
   - Title: `"No devices found in selected scope"`
   - Description: `"No network device telemetry recorded matching active time range and filters."`
   - Action: `"Reset range"` $\to$ resets time range to ALL.
3. **`NetworkOperations.jsx` — Topology Map Zero-Match:**
   - Title: `"No network devices match current filter"`
   - Description: `"Clear active search or filter selection to restore topology visualization."`
   - Action: `"Clear search"` $\to$ resets search query.
4. **`NetworkOperations.jsx` — Details Drawer Alerts Tab:**
   - Title: `"No active alerts recorded for this device"`
   - Description: `"This node is currently operating nominally with zero active or suppressed incidents."`
5. **`AlertPatterns.jsx` — Pattern Clusters Table:**
   - Title: `"No alert patterns discovered yet"`
   - Description: `"Recurring pattern clusters will automatically appear here once alert telemetry is ingested."`

---

## 6. Domain Tooltip & Abbreviation Specification (`D-10`)

Domain acronyms and abbreviations must provide accessible browser tooltips (`title="..."`) and descriptive sub-labels to assist operators unfamiliar with system-specific abbreviations.

| Abbreviation | Expanded Definition | Component Locations | Visual Treatment |
|--------------|----------------------|---------------------|------------------|
| **SNOW** | ServiceNow ITSM Ticketing System | KPI Card 1.4, Section Header, Table Headers, Filter Dropdowns | `title="ServiceNow ITSM Ticketing System"`, subtitle "ITSM Incidents" |
| **DNAC** | Cisco DNA Center (Catalyst Center) Controller | Sidebar Brand, Breadcrumbs, Event ID table headers | `title="Cisco DNA Center (Catalyst Center) Controller"` |
| **DLX** | Dead Letter Exchange (RabbitMQ delayed retry queue) | KPI Card 4 in Network Operations, Agent 3 telemetry | `title="Dead Letter Exchange (RabbitMQ delayed verification queue)"` |
| **MTTR** | Mean Time to Resolve (Incident triage duration) | NOC velocity metrics, incident response tables | `title="Mean Time to Resolve (Incident triage duration)"` |
| **SRE** | Site Reliability Engineering | Investigation Drawer header, SRE table tab | `title="Site Reliability Engineering"` |
| **NOC** | Network Operations Center | View Switcher button, Executive KPI strip header | `title="Network Operations Center"` |
| **P1** | Priority 1 (Critical Severity) | Severity badges, filter dropdowns | `title="Priority 1: Critical — Immediate intervention required"` |
| **P2** | Priority 2 (Major Severity) | Severity badges, filter dropdowns | `title="Priority 2: Major — Service degraded"` |
| **P3** | Priority 3 (Warning / Minor Severity) | Severity badges, filter dropdowns | `title="Priority 3: Warning — Informational or low impact"` |

---

## 7. Demo Button Scaffolding Removal Specification (`D-06`, `D-07`)

- **Eliminated Component:** The `"⚡ Simulate +5 Alerts"` button (`.filter-pill.simulate-btn`) and its wrapper layout `<div>` are completely removed from `FalseAlertMetrics.jsx`.
- **Backend Architecture Continuity:** The seeded 60 alerts in `simulated_alerts.json` and the mock fallback in `api.py` remain fully active, ensuring rich, realistic network operational telemetry without prototype UI scaffolding.
- **Connection Badge Retention:** The header connection badge (`[Mock / Seed Data]` / `[Connected]`) and banner in `App.jsx` are preserved as authentic operational telemetry state indicators.

---

## 8. Copywriting Contract

| Element | Copy |
|---------|------|
| **Primary Matrix Reset CTA** | "Clear filters" |
| **Empty State: Matrix** | Heading: "No alerts match the current matrix filters"<br>Body: "Try broadening your filter criteria or reset search queries to inspect telemetry." |
| **Empty State: Devices** | Heading: "No devices found in selected scope"<br>Body: "No network device telemetry recorded matching active time range and filters." |
| **Empty State: Topology** | Heading: "No network devices match current filter"<br>Body: "Clear active search or filter selection to restore topology visualization." |
| **Empty State: Drawer** | Heading: "No active alerts recorded for this device"<br>Body: "This node is currently operating nominally with zero active or suppressed incidents." |
| **KPI Filter Status (Idle)** | "FILTERABLE" |
| **KPI Filter Status (Active)** | "ACTIVE FILTER ✓" |
| **KPI Filter Action Hint (Active)** | "Click to clear filter" |

---

## 9. Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| Custom CSS Design System | None (custom CSS variables) | not required |
| Lucide React | Standard icons | not required |

---

## 10. Checker Sign-Off

- [x] **Dimension 1 Copywriting:** PASS — Action-oriented button verbs ("Clear filters", "Reset range"), precise empty state explanations, and expanded domain definitions.
- [x] **Dimension 2 Visuals:** PASS — NOC card two-row geometry (`.noc-kpi-top`, `.noc-kpi-body`, `.noc-kpi-footer`), 3px top accent stripes, circular 48px empty state badges.
- [x] **Dimension 3 Color:** PASS — Strict 60-30-10 palette adhering to WCAG AA/AAA luminance standards from Phase 21, semantic color accents.
- [x] **Dimension 4 Typography:** PASS — Strict 6-step scale (`--font-xs` through `--font-2xl`), eliminating all sub-12px and fractional arbitrary font sizes.
- [x] **Dimension 5 Spacing:** PASS — Standard 4px/8px multiple scale (4px, 8px, 16px, 24px, 32px, 48px, 64px) with fixed KPI card geometry.
- [x] **Dimension 6 Registry Safety:** PASS — Zero external third-party UI registries required; 100% native React 19 + vanilla CSS design tokens.

**Approval:** Approved 2026-10-06
