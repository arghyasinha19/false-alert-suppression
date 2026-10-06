# Phase 20: Data Visibility & Bounds - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-06  
**Phase:** 20-data-visibility-bounds  
**Areas discussed:** Topology Canvas Bounds & Scroll Hijacking, Permanent High-Contrast Table Scrollbars, Horizontal Table Edge Gradient Masks, Vertical List Capping & Counters  

---

## Topology Canvas Bounds & Scroll Hijacking (UI-03)

| Option | Description | Selected |
|--------|-------------|:--------:|
| **Ctrl/Cmd + Wheel Zoom** | Require `Ctrl` / `Cmd` + scroll to zoom; regular wheel scrolls the page smoothly (with floating hint pill) | **✓** |
| Focus/Click to Activate | Require clicking into canvas to lock zoom mode; Esc or click outside to unlock | |
| Toolbar Lock Button | Keep direct wheel zoom enabled, but provide a lock/unlock scroll button in the toolbar | |

**User's choice:** Require Ctrl / Cmd + scroll to zoom; regular wheel scrolls the page (displays a subtle toast hint "Use Ctrl + scroll to zoom").

| Option | Description | Selected |
|--------|-------------|:--------:|
| **Dynamic Viewport Height** | `calc(100vh - 280px)` clamped between 560px and 780px | **✓** |
| Fixed Height | Fixed 680px height on large screens, compacting to 520px below 1100px | |
| Resizable Canvas | Bottom drag handle with height persisted in localStorage | |

**User's choice:** Dynamic viewport-proportional height `calc(100vh - 280px)` clamped between 560px and 780px to maximize topology visibility.

| Option | Description | Selected |
|--------|-------------|:--------:|
| **Soft-Boundary Clamping** | Ensure at least 25% of the graph diagram remains visible within viewport at all times | **✓** |
| Strict Bounding Box | Clamp panning strictly within diagram outer margins | |
| Unbounded Pan | Unbounded pan with a persistent "Re-center View" floating chip | |

**User's choice:** Soft-boundary clamping: ensure at least 25% of the graph diagram remains visible within viewport at all times.

| Option | Description | Selected |
|--------|-------------|:--------:|
| **Dedicated Fullscreen Toggle** | Add a dedicated Fullscreen / Expanded View toggle in toolbar (Esc to exit) | **✓** |
| Inline Only | Keep canvas strictly inline within the Network Operations page | |

**User's choice:** Add a dedicated Fullscreen / Expanded View toggle in toolbar (Esc to exit) to allow deep topology analysis.

---

## Permanent High-Contrast Table Scrollbars (UI-04)

| Option | Description | Selected |
|--------|-------------|:--------:|
| **8px Rounded Pill Thumb** | 8px thickness (width: 8px, height: 8px) with rounded pill thumb (border-radius: 6px) | **✓** |
| 6px Slim Scrollbar | 6px slim scrollbar with expanded invisible hover padding | |
| Standard OS Scrollbar | Standard native OS scrollbar (14px–16px) | |

**User's choice:** 8px thickness (height: 8px, width: 8px) with rounded pill thumb (border-radius: 6px) for comfortable click/drag target.

| Option | Description | Selected |
|--------|-------------|:--------:|
| **High-Contrast Slate Thumb** | Dark mode `rgba(148, 163, 184, 0.45)`, Light mode `rgba(100, 116, 139, 0.4)` passing WCAG 3:1 | **✓** |
| Blue Brand-Tinted Thumb | `rgba(59, 130, 246, 0.4)` / hover `rgba(59, 130, 246, 0.8)` | |
| Solid Grey Thumb | Solid neutral grey thumb with distinct outer border | |

**User's choice:** High-contrast slate thumb: Dark mode rgba(148, 163, 184, 0.45) (hover 0.75), Light mode rgba(100, 116, 139, 0.4) (hover 0.7).

| Option | Description | Selected |
|--------|-------------|:--------:|
| **Subtle Sunken Track** | `rgba(0, 0, 0, 0.05)` in light / `rgba(255, 255, 255, 0.04)` in dark with smooth radius | **✓** |
| Transparent Track | Thumb floats directly over table rows without background channel | |
| Solid High-Contrast Track | Distinct solid track background | |

**User's choice:** Subtle sunken track: rgba(0, 0, 0, 0.05) in light / rgba(255, 255, 255, 0.04) in dark with smooth radius.

| Option | Description | Selected |
|--------|-------------|:--------:|
| **Targeted Table Classes** | Dedicated high-contrast table class applied to data tables, ranking lists, site matrix, and SRE drawer | **✓** |
| Global Override | Global override applying 8px high-contrast scrollbars across all scroll containers application-wide | |

**User's choice:** Dedicated high-contrast table class applied to data tables, ranking lists, site matrix, and SRE drawer panels.

---

## Horizontal Table Edge Gradient Masks (UI-04)

| Option | Description | Selected |
|--------|-------------|:--------:|
| **Pseudo-Element Wrapper Overlays** | Wrapper with `::before` and `::after` gradient overlays (`pointer-events: none`) dynamically toggled by scroll | **✓** |
| CSS Mask-Image | Pure CSS `mask-image` with linear gradient | |
| Floating Edge Arrows | Floating edge pills with chevron indicators that pulse when un-scrolled | |

**User's choice:** Wrapper with ::before and ::after gradient overlays (pointer-events: none) dynamically toggled by scroll position.

| Option | Description | Selected |
|--------|-------------|:--------:|
| **Dynamic Fade-Out at Boundary** | Smoothly fade right/left mask to opacity 0 within 5px of the end so edge columns are 100% crisp | **✓** |
| Static Mask | Always display subtle gradient on edge regardless of scroll position | |
| Box-Shadow Drop Line | Elevated box-shadow drop line instead of gradient fade | |

**User's choice:** Dynamic fade-out: smoothly fade right mask to opacity 0 when scrolled to the end so final columns are fully crisp.

| Option | Description | Selected |
|--------|-------------|:--------:|
| **28px Gradient Falloff** | 28px width blending from transparent to `var(--card-bg)` for seamless theme integration | **✓** |
| 16px Narrow Band | 16px narrow gradient band for minimal column coverage | |
| 40px Wide Prominent Gradient | 40px wide prominent gradient with inset chevron indicator | |

**User's choice:** 28px width blending from transparent to var(--card-bg) for seamless dark and light mode integration.

| Option | Description | Selected |
|--------|-------------|:--------:|
| **All 5 Wide Tables** | All 5 wide tables across the dashboard (Traceability Matrix, Device Ranking, SRE Table, Site Matrix, Pattern Analysis) | **✓** |
| Two Widest Tables Only | Only Traceability Matrix and SRE Table | |

**User's choice:** All 5 wide tables across the dashboard (Traceability Matrix, Device Ranking, SRE Table, Site Matrix, Pattern Analysis).

---

## Vertical List Capping & Counters (UI-04)

| Option | Description | Selected |
|--------|-------------|:--------:|
| **Max-Height + Sticky Header + Count** | Explicit max-height with sticky header + "Showing X of Y" counter badge and optional "Show all / Show 10" toggle | **✓** |
| Strict Pagination Bar | Strict pagination bar with Previous / Next and page size selector (10, 25, 50) | |
| Infinite Virtualized Scroll | Virtualized rendering for 100+ items | |

**User's choice:** Explicit max-height with sticky header + "Showing X of Y" counter badge and optional "Show all / Show 10" toggle.

| Option | Description | Selected |
|--------|-------------|:--------:|
| **Header Pill Badge** | Prominent header pill badge: "Showing X of Y {items}" with filtered indicator when active | **✓** |
| Footer Status Strip | Footer status strip at the bottom of the card | |
| Header + Footer | Both header count chip and footer summary strip | |

**User's choice:** Prominent header pill badge: "Showing X of Y {items}" with filtered indicator when active.

| Option | Description | Selected |
|--------|-------------|:--------:|
| **Cap Drawer Alerts at 5** | Cap drawer alerts at 5 items with a "Show {N - 5} more alerts" expansion button and "Showing 5 of {N}" count chip | **✓** |
| Fixed 320px Container | Keep all alerts visible inside a 320px scrollable container without item-level truncation | |
| Severity Accordions | Group and collapse alerts into severity accordions | |

**User's choice:** Cap drawer alerts at 5 items with a "Show {N - 5} more alerts" expansion button and "Showing 5 of {N}" count chip.

| Option | Description | Selected |
|--------|-------------|:--------:|
| **Enforce Sticky Headers** | Enforce sticky headers (`position: sticky; top: 0; backdrop-filter: blur(8px)`) across all capped table containers | **✓** |
| Standard Headers | Allow table headers to scroll with content without sticky locking | |

**User's choice:** Enforce sticky headers (position: sticky; top: 0; backdrop-filter: blur(8px)) across all capped table containers.

---

## the agent's Discretion

- Micro-timing for the wheel zoom modifier toast hint animation (`0.2s fadeIn`, 2s auto-dismiss).
- Exact debounce timing (50ms) for scroll position calculation on horizontal table wrappers.
- Icon selection for expansion controls (`ChevronDown`, `ChevronUp`, `Maximize2`, `Minimize2`).

## Deferred Ideas

- Drag-and-drop custom node pinning saved to localStorage (tracked in REQUIREMENTS.md as future enhancement).
- Virtualized infinite scrolling tables (future performance enhancement if alert fleet exceeds 1,000+ items; current max is <100 items).
