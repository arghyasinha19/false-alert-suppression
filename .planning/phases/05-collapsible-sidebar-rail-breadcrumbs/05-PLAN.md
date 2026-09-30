# Phase 5 Plan: Collapsible Sidebar Rail & Breadcrumbs Navigation Context

**Phase:** 5  
**Milestone:** v1.4 Complete UI/UX Expert Audit Implementation  
**Status:** In Progress  

## Goals

Implement a collapsible sidebar navigation rail that collapses from 260px down to a 72px icon-only rail with smooth animated transitions, floating hover tooltips, and centered icon alignment. Persist the user's collapse preference in `localStorage`. Additionally, introduce subtle, enterprise-grade breadcrumb context indicators in the `.content-header` above the main title to enhance spatial orientation across all three views.

## Requirements Covered

- `NAV-01`: Collapsible sidebar rail — Toggle button collapses sidebar to 72px icon rail with floating tooltips on hover, centered icon alignment, smoothly animated transition, state persisted in `localStorage`.
- `NAV-02`: Breadcrumb navigation context indicator — Breadcrumbs (`DNAC Ops Center > {View Name}`) placed in `.content-header` above or next to the main title with subtle styling and chevron separators.

## Design Contract Reference

- See `05-UI-SPEC.md` for layout dimensions, transition timing curves, floating tooltip styling, and typography specifications.

## Execution Waves

### Wave 1: CSS Architecture & Styles (`dashboard/src/App.css`)

1. **Sidebar Rail Dimensions & Transitions**:
   - Add `.sidebar { transition: width var(--transition-normal); overflow: visible; }` (allow tooltips to overflow cleanly).
   - Define `.sidebar.collapsed { width: 72px; }`.
   - Update `.content-area`: add `transition: margin-left var(--transition-normal);`.
   - Define `.content-area.sidebar-collapsed { margin-left: 72px; }`.
2. **Sidebar Header & Collapse Toggle Button**:
   - Style `.sidebar-brand`: handle collapsed state (hide text subtitle/title, center brand icon or stack collapse button).
   - Style `.sidebar-toggle-btn`: subtle border, hover state, circular or rounded pill button with `ChevronLeft`/`ChevronRight` icon.
3. **Collapsed Nav Items & Floating Tooltips**:
   - Define `.sidebar.collapsed .sidebar-nav-item`: `justify-content: center; padding: 0.75rem 0;` (hide inline text labels and active bar).
   - Style `.nav-floating-tooltip`: positioned at `left: calc(100% + 12px)`, dark high-contrast pill with subtle arrow pointer, `z-index: 1000`, hidden by default and visible on `.sidebar.collapsed .sidebar-nav-item:hover`.
   - Style `.sidebar.collapsed .sidebar-status`: compact centered connection dot/icon, hiding multi-line text.
4. **Header Breadcrumbs (`.breadcrumbs`)**:
   - Style `.breadcrumbs`: flex container with `gap: 0.4rem`, font size `0.78rem`, subtle colors.
   - Style `.breadcrumb-root`: `color: var(--text-tertiary); font-weight: 500;`.
   - Style `.breadcrumb-separator`: `color: var(--text-tertiary); opacity: 0.6;`.
   - Style `.breadcrumb-current`: `color: var(--accent-blue); font-weight: 600;`.

### Wave 2: JSX Components & State Integration (`dashboard/src/App.jsx`)

5. **Sidebar Collapse State & Persistence**:
   - Add state: `const [sidebarCollapsed, setSidebarCollapsed] = useState(() => localStorage.getItem('sidebar_collapsed') === 'true')`.
   - Add `useEffect` to sync `sidebarCollapsed` state to `localStorage.setItem('sidebar_collapsed', String(sidebarCollapsed))`.
   - Add collapse toggle button with accessible `aria-label` and `title`.
6. **Navigation Item Floating Tooltips**:
   - Enhance `navItems.map()` rendering with `<div className="nav-floating-tooltip">{item.label}</div>`.
   - Add tooltip to "Ops Assistant" chat trigger and database connection status.
7. **Breadcrumb Header Integration**:
   - Wrap header title in `.content-header-title-block`.
   - Render breadcrumb hierarchy `DNAC Ops Center > {View Name}` dynamically based on `activeView`.

### Wave 3: Verification & Visual Polish

8. **Automated Verification**:
   - Run `npm run lint` in `dashboard/` to verify zero linting errors.
   - Run `npm run build` in `dashboard/` to confirm bundle builds cleanly.
   - Run `python -m pytest -q` to ensure API tests remain 100% passing.
9. **Live Browser Verification**:
   - Use `browser_subagent` to test the collapsible sidebar on `http://localhost:5173/`.
   - Verify sidebar toggles between 260px and 72px smoothly.
   - Verify tooltips appear on hover in collapsed mode.
   - Verify breadcrumb displays properly across all views ("Alert Metrics", "Network Operations", "Alert Patterns").
   - Reload page to confirm `localStorage` persists collapsed state.
