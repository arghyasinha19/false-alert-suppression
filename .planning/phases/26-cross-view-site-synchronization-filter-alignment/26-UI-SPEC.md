---
phase: 26
slug: cross-view-site-synchronization-filter-alignment
status: approved
shadcn_initialized: false
preset: none
created: 2026-10-06
reviewed_at: 2026-10-06
---

# Phase 26 — UI Design Contract: Cross-View Site Synchronization & Filter Alignment

> Visual and interaction design contract for cross-view site synchronization across Regional Site Matrix, SRE High-Density Table, and Multi-Site Topology views (`SITE-07`, `SITE-08`).

---

## Design System Tokens & Properties

| Property | Value |
|----------|-------|
| Framework | React 19 + Native SVG (Vanilla CSS) |
| Typography Tokens | `--font-xs` (12px), `--font-sm` (13px), `--font-md` (15px), `--font-lg` (18px), `--font-xl` (24px), `--font-2xl` (34px) |
| Color Tokens | `--card-bg`, `--card-border`, `--text-primary`, `--text-secondary`, `--text-tertiary`, `--accent-blue`, `--accent-emerald`, `--accent-amber`, `--accent-rose`, `--accent-purple` |
| Touch Target Min | `32px` interactive element visible height |
| Contrast Ratio | WCAG AAA compliant (>= 7:1 for normal text, >= 4.5:1 for badges/accents) |
| Icons (`lucide-react`) | `Globe`, `Building`, `ChevronRight`, `RotateCcw`, `Filter`, `Server`, `Activity`, `CheckCircle`, `AlertTriangle` |

---

## 1. Filter Bar Site Cluster Specification (`SITE-08`)

A dedicated `Site:` filter cluster is added to the top multi-dimensional filter bar:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Site: [🌐 All Sites (Global) 8] [🇬🇧 UK-LON 3] [🇩🇪 DE-FRA 2] [🇺🇸 US-NY 3] [🇸🇬 SG-SIN 2] ...        │
└────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Component Details
- **Cluster Label**: `.noc-filter-cluster-label` with text `Site:`.
- **All Sites Pill**:
  - Class: `.noc-filter-chip`
  - Content: `<Globe size={11} /> <span>All Sites (Global)</span> <span className="noc-chip-count">{totalSites}</span>`
  - Active when `!selectedSite`.
- **Individual Site Pills**:
  - Class: `.noc-filter-chip` (with `.active` when `selectedSite === site.code`)
  - Content: `<span>{site.code}</span> <span className="noc-chip-count">{site.devices.length}</span>`
  - Clicking sets `selectedSite = site.code` and `topologyLevel = 'lan'`.
  - Clicking an active site pill toggles back to `All Sites` (`selectedSite = null`, `topologyLevel = 'wan'`).

---

## 2. SRE Table Location Cell Interaction (`SITE-08`)

In the SRE High-Density Table (`viewMode === 'table'`), location values in the Location column are rendered as interactive buttons `.noc-table-loc-btn`:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Device Name        │ Tier     │ Location                          │ Health    │ Alerts │ Actions   │
├────────────────────┼──────────┼───────────────────────────────────┼───────────┼────────┼───────────┤
│ lon-core-01        │ CORE     │ [🇬🇧 UK-LON (London Core DC) ↗]     │ NOMINAL   │ 0      │ [Inspect] │
└────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

- **Interactive Element**: `<button type="button" className="noc-table-loc-btn">`
- **Behavior**: Clicking sets `selectedSite = siteCode`, updates active site filter, and displays a toast notification: `Filtered view to ${locationLabel}`.

---

## 3. Regional Site Matrix Synchronization (`SITE-07`)

In the Regional Site Matrix view (`viewMode === 'matrix'`), each card reflects selection state and triggers immediate topology LAN drilldown:

- **Active Card State**:
  - Class: `.noc-site-card.active-site` when `selectedSite === site.code`.
  - Border: `2px solid var(--accent-purple, #a855f7)`.
  - Box Shadow: `0 0 16px rgba(168, 85, 247, 0.25)`.
- **Drilldown Button**:
  - Class: `.noc-site-drilldown-btn`
  - Text: `Inspect Site Topology →`
  - Clicking transitions to `viewMode = 'topology'`, `selectedSite = site.code`, `topologyLevel = 'lan'`.
