# Phase 25: Site-Specific LAN Topology Drill-Down & Breadcrumbs — Summary

**Status:** Complete  
**Date:** 2026-10-06  
**Milestone:** v2.0 Multi-Site Hierarchical Topology & WAN Observability  
**Requirements:** SITE-04, SITE-05, SITE-06  

---

## One-liner

Delivered the complete Level 2 Site LAN Drill-Down topology view featuring 3-tier local hierarchy (Core ↔ Distribution ↔ Access), responsive breadcrumb trail (`Global WAN Interconnect > Site`), an accessible site-switcher dropdown for instant site hopping, and site-scoped device filtering.

---

## What Was Built

### 1. Level 2 Site LAN Drill-Down (`SITE-04`)
- **Site-Scoped Hardware Fleet:**
  - In Level 2 (`topologyLevel === 'lan'`), scoped devices dynamically to `selectedSite`.
  - Grouped devices across 3 hierarchical tiers: Core & WAN Backbone, Distribution & Security Perimeter, and Campus & Access Edge.
  - Calculated tier statistics (device count, critical, warning, healthy) strictly within the site's fleet.
- **Accessible Site Switcher Dropdown (`.noc-site-switcher-select`):**
  - Integrated directly in the toolbar alongside the breadcrumbs.
  - Lists all registered locations with health indicators (`● NOM`, `⚠ DEGR`, `✖ CRIT`) and device counts.
  - Enables operators to jump between sites (e.g. from `UK-LON` directly to `SG-SIN`) in one click without returning to Level 1.

### 2. Responsive Breadcrumb Navigation & Global Return (`SITE-05`)
- **Breadcrumb Trail (`.noc-topology-breadcrumbs`):**
  - Clickable root: `<button className="noc-breadcrumb-root" onClick={onReturnToWan}><Globe size={13} /> Global WAN Interconnect</button>`.
  - Chevron divider: `<ChevronRight size={13} className="noc-breadcrumb-separator" />`.
  - Active site indicator: Flag emoji, site code, and descriptive label.
- **Single-Click Global Return:**
  - Added `.noc-wan-back-btn` with `<ArrowLeft size={13} /> Back to Global WAN`.
  - Clicking either the back button or the breadcrumb root resets view to the Level 1 Global WAN overview.

### 3. Site-Scoped Device Filtering (`SITE-06`)
- **Context-Preserving Filter Match Badge:**
  - Displays `Filtered: X of Y devices in [Site Code]`.
  - Single-click reset button clears filter queries while keeping the operator locked into the active site view.
- **Pointer-Down Safety Guards:**
  - Excluded breadcrumbs and site switcher from pointer capture to prevent accidental canvas panning when interacting with navigation controls.

### 4. Design & Standards Compliance
- Minimum interactive height >= 32px.
- Zero sub-12px CSS declarations.
- High contrast tokens adhering to WCAG AAA standards.
- Automated contract test suite `tests/test_site_lan_drilldown_contract.py` passing 7/7 tests.

---

## Verification Evidence

1. **Phase 25 Contract Tests (`tests/test_site_lan_drilldown_contract.py`):**
   - 7/7 passed in 0.28s.
2. **Full Regression Suite (`tests/`):**
   - 94 passed, 7 skipped (hardware integration), 0 failed in 6.56s.
3. **Frontend Production Build:**
   - `npm run build`: built in 1.19s without errors.
