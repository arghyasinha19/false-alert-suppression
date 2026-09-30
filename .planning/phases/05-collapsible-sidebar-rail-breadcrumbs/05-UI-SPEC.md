---
phase: 5
slug: collapsible-sidebar-rail-breadcrumbs
status: approved
shadcn_initialized: false
preset: none
created: 2026-09-30
---

# Phase 5 — UI Design Contract: Collapsible Sidebar Rail & Breadcrumbs

> Visual and interaction contract for 72px icon-only sidebar rail mode, expand/collapse toggle, floating tooltips, and header breadcrumb context.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (Vanilla CSS custom design tokens) |
| Preset | not applicable |
| Component library | none (custom React components) |
| Icon library | lucide-react (`ChevronLeft`, `ChevronRight`, `PanelLeftClose`, `PanelLeftOpen`) |
| Font | Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif |

---

## Layout & Dimensions

| State | Sidebar Width | Content Margin Left | Nav Item Layout | Brand Display |
|-------|---------------|---------------------|-----------------|---------------|
| Expanded (Default) | `260px` | `260px` | Icon + Text label + badges | Icon + Title ("DNAC Ops Center") + Subtitle |
| Collapsed (Rail) | `72px` | `72px` | Centered Icon only + floating hover tooltip | Centered Icon + collapse toggle |
| Transition | `0.25s cubic-bezier(0.4, 0, 0.2, 1)` | `0.25s cubic-bezier(0.4, 0, 0.2, 1)` | Smooth opacity/width | Smooth crossfade |

---

## Floating Tooltip Contract (Collapsed Mode)

- When `.sidebar.collapsed`, hover over any `.sidebar-nav-item` displays a floating tooltip:
  - `position: absolute; left: 78px;`
  - `background: var(--text-primary); color: #ffffff;`
  - `padding: 0.35rem 0.65rem; border-radius: var(--radius-sm);`
  - `font-size: 0.75rem; font-weight: 600; white-space: nowrap;`
  - `box-shadow: var(--shadow-md); z-index: 100; pointer-events: none;`

---

## Breadcrumb Navigation Contract

- Placed in `.content-header` above or next to page title:
  - Structure: `<span>DNAC Ops Center</span> <ChevronRight size={12} /> <span class="active">{Page Name}</span>`
  - Parent item: `color: var(--text-tertiary); font-size: 0.78rem; font-weight: 500;`
  - Chevron divider: `color: var(--text-tertiary); opacity: 0.6;`
  - Active page item: `color: var(--accent-blue); font-size: 0.78rem; font-weight: 600;`

---

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** Approved 2026-09-30
