# Phase 4 Plan: Network Operations Responsive Redesign

**Phase:** 4  
**Milestone:** v1.4 Complete UI/UX Expert Audit Implementation  
**Status:** In Progress  

## Goals

Redesign the Network Operations page from a narrow single-column layout into a modern, 2–3 column responsive device card grid that utilizes the entire available horizontal viewport without clipping or wasted whitespace. Provide clean location and infrastructure grouping, accurate count badges, and clear telemetry hierarchy on every device tile.

## Requirements Covered

- `NETOPS-01`: User can view network device inventory in a multi-column responsive grid (2–3 cols, minmax 320px) utilizing full screen width.
- `NETOPS-02`: User can view devices organized under distinct location and infrastructure group headers with device count badges and clean iconography.

## Design Contract Reference

- See `04-UI-SPEC.md` for spacing, typography, colors, and layout scale.

## Execution Waves

### Wave 1: CSS Grid & Responsive Layout (`dashboard/src/App.css`)

1. **Responsive Device Grid (`.device-grid`)**:
   - Update `.device-grid` to `display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1rem; width: 100%;`.
   - Add responsive breakpoints at `@media (max-width: 1200px)` (minmax 280px) and `@media (max-width: 768px)` (1 column).
2. **Location & Group Headers (`.location-header`, `.location-group`)**:
   - Polish `.location-header` with flex alignment, border divider, icon spacing, and device count badge.
   - Ensure `.location-group` expands across full content width with 1.75rem bottom spacing.
3. **Device Tile Cards (`.device-tile`)**:
   - Modernize card surface: glassmorphic background, subtle border, smooth hover elevation (`translateY(-2px)` + box shadow).
   - Distinct alerting border (`.device-tile.alerting`) with top accent line.
   - Clean meta telemetry row: health status icon, last alert time, total alert count, and SNOW incident pills without truncation.

### Wave 2: JSX Component Refinement (`dashboard/src/NetworkOperations.jsx`)

4. **Group Derivation & Categorization**:
   - Enhance `deriveLocation` to cleanly group devices: known geographic locations use country flags and `<MapPin>`, non-geographic devices (e.g. Core Routers, Leaf Switches) group as infrastructure tiers with `<Server>` icons.
5. **Interactive Polish & Empty State**:
   - Update empty state when search returns 0 devices to include an informative illustration, clear message, and quick "Clear Search" button.
   - Ensure the slide-out detail panel overlay and body integrate seamlessly with the multi-column card layout.

### Wave 3: Verification

6. **Static Analysis & Build Verification**:
   - Run `npm run lint` in `dashboard/` to verify zero warnings or errors.
   - Run `npm run build` in `dashboard/` to verify bundle compilation.
   - Run `python -m pytest -q` to verify backend integrity.
7. **Browser Visual & Interaction Verification**:
   - Use `browser_subagent` to inspect `http://localhost:5173/` on the Network Operations tab.
   - Verify device cards render in 3 columns on full desktop (1707px) and 2 columns on laptop (1366px).
   - Test search filtering and device detail panel slide-out.
