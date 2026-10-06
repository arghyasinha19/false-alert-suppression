---
phase: 22
slug: accessibility-hit-areas
status: approved
shadcn_initialized: false
preset: none
created: 2026-10-06
reviewed_at: 2026-10-06
---

# Phase 22 — UI Design Contract: Accessibility & Hit Areas

> Visual and interaction design contract for WCAG 2.1 AA accessibility compliance across the Cisco DNA Center Ops Center dashboard: 32px min-height hit areas with 44px touch targets (`UI-07`), non-modal docked chat panel with keyboard navigation (`UI-08`), semantic sidebar buttons with `aria-current` and focus tooltips (`UI-16`), and accessible form controls and table captions/headers (`UI-17`).

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (Vanilla CSS custom design tokens) |
| Preset | not applicable |
| Component library | none (custom React 19 components) |
| Icon library | lucide-react (`PanelLeftOpen`, `PanelLeftClose`, `MessageSquare`, `Bot`, `User`, `X`, `Send`, `Calendar`, `Search`, `Filter`, `ArrowUpDown`, `ChevronUp`, `ChevronDown`) |
| Font | Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif |
| Monospace Font | ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace |

---

## Hit Area & Touch Target Specification (`UI-07`)

### 1. Visual Min-Height Standard (32px)
All interactive controls must meet a minimum visual height of 32px (0.8125rem text + padding) to prevent compact density crowding and ensure effortless click targeting:
- **Buttons:** `.btn`, `.btn-primary`, `.btn-secondary`, `.refresh-btn`, `.export-btn`, `.time-range-btn`, `.demo-banner-reconnect-btn`, `.chat-send-btn` $\to$ `min-height: 32px;`
- **Filter Pills & Tabs:** `.filter-pill`, `.filter-btn`, `.view-mode-btn`, `.category-pill` $\to$ `min-height: 32px; padding: 0.35rem 0.75rem;`
- **Inputs & Selects:** `.filter-search`, `.date-picker-input`, `.form-select`, `.time-select` $\to$ `min-height: 32px; height: 32px; padding: 0.35rem 0.65rem;`

### 2. Touch Target Expansion (44x44px Minimum)
For compact inline icons, table row action buttons, and header icon toggles whose visual size is 24px–28px, a transparent `::before` pseudo-element touch target expander ensures compliance with WCAG 2.5.5 / 2.5.8 touch target requirements:

```css
.touch-target-expand {
  position: relative;
}

.touch-target-expand::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  min-width: 44px;
  min-height: 44px;
  width: 100%;
  height: 100%;
  pointer-events: auto;
}
```

**Applied to:**
- `.sidebar-collapse-toggle`
- `.chat-close-btn`
- `.demo-banner-dismiss-btn`
- `.table-sort-btn`
- `.table-action-icon`
- `.drawer-close-btn`

---

## Typography Scale Standard (`UI-07`)

Sub-12px font sizes (`0.7rem`, `0.72rem`) are completely eliminated across all stylesheets and components to guarantee legibility and pass WCAG AAA reading comfort.

| Role | Font Size | Line Height | Usage |
|---|---|---|---|
| **Body & Primary Data** | `0.8125rem` (13px) | 1.45 (19px) | Table body cell values, form input text, filter labels, device names, alert descriptions |
| **Headers & Metadata** | `0.75rem` (12px) | 1.35 (16.2px) | Table `<th>` headers, status badges, metadata tags, timestamps, captions, micro-labels |
| **Card / Section Titles** | `0.9375rem` (15px) | 1.35 (20px) | Metric card labels, filter toolbar titles, drawer headers |
| **KPI Values** | `1.5rem` (24px) – `2.125rem` (34px) | 1.15 | Executive KPI numeric values |

---

## Ops Assistant Chat Panel Specification (`UI-08`)

### 1. Non-Modal Docked Layout (Inset Content Area)
The Ops Assistant chat panel transforms from a blocking modal overlay into a **docked, non-modal inspector panel**:
- **Removal of Backdrop Overlay:** Remove the `.chat-overlay` backdrop element in docked mode, allowing operators to freely interact with, scroll through, and inspect dashboard tables and charts while chatting with the AI.
- **Content Area Inset:** The `.main-content` / `.content-area` smoothly insets horizontally to accommodate the docked panel width:
  ```css
  .app-shell.chat-open .content-area {
    margin-right: var(--chat-panel-width, 440px);
    transition: margin-right 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  }
  ```
- **Panel Bounds:** Resizable via existing `.chat-resize-handle` between `340px` (min) and `900px` (max), defaulting to `440px`.
- **Responsive Fallback (<= 1100px):** On screens $\le 1100px$, where horizontal space is constrained, the chat panel overlays without margin inset, and clicking outside or pressing Escape smoothly closes it.

### 2. Comprehensive Keyboard Controls
- **Escape to Close:** Pressing `Escape` while focus is anywhere inside `.chat-panel` closes the panel and returns focus to the invoking sidebar button.
- **Global Toggle Shortcut:** `Ctrl+/` (or `Cmd+/` on macOS) globally toggles the chat panel open or closed from anywhere in the application.
- **ARIA Semantics:**
  - The chat toggle button sets `aria-expanded={chatOpen}` and `aria-controls="ops-assistant-panel"`.
  - The panel element sets `id="ops-assistant-panel"`, `role="region"`, and `aria-label="DNAC Ops Assistant"`.

---

## Sidebar Keyboard Navigation & Semantics (`UI-16`)

### 1. Semantic Button Elements
The sidebar navigation items are converted from `<div role="button">` to native HTML `<button type="button">` elements:

```jsx
<button
  type="button"
  key={item.id}
  className={`sidebar-nav-item ${activeView === item.id ? 'active' : ''}`}
  onClick={() => setActiveView(item.id)}
  aria-current={activeView === item.id ? 'page' : undefined}
  aria-label={item.label}
>
  {item.icon}
  <span className="sidebar-nav-label">{item.label}</span>
  <div className="nav-floating-tooltip" role="tooltip">{item.label}</div>
</button>
```

### 2. High-Contrast `:focus-visible` Ring
Keyboard focus indicators must be sharp and distinguishable against both dark and light backgrounds:

```css
.sidebar-nav-item:focus-visible,
.sidebar-collapse-toggle:focus-visible,
.btn:focus-visible,
.filter-btn:focus-visible {
  outline: 2px solid var(--accent-blue);
  outline-offset: 2px;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.25);
}
```

### 3. Tooltip Activation on Focus
When the sidebar is in its collapsed 72px icon rail state, floating tooltips must be triggered by both mouse hover and keyboard focus:

```css
.sidebar.collapsed .sidebar-nav-item:hover .nav-floating-tooltip,
.sidebar.collapsed .sidebar-nav-item:focus-visible .nav-floating-tooltip,
.sidebar.collapsed .sidebar-collapse-toggle:hover .nav-floating-tooltip,
.sidebar.collapsed .sidebar-collapse-toggle:focus-visible .nav-floating-tooltip,
.sidebar.collapsed .sidebar-status:hover .nav-floating-tooltip,
.sidebar.collapsed .sidebar-status:focus-visible .nav-floating-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateX(0);
}
```

---

## Form Controls & Table Semantics (`UI-17`)

### 1. Accessible Form Labels
Every input, select, and textarea control must have an accessible name via explicit `<label htmlFor="...">`:
- **Date & Time Controls:** Compact micro-labels `<label htmlFor="start-date" className="filter-field-label">Start</label>` and `<label htmlFor="end-date" className="filter-field-label">End</label>`.
- **Search Inputs:** Explicit `<label htmlFor="alert-search" className="sr-only">Search alerts</label>`.
- **Filter Dropdowns:** Explicit `<label htmlFor="category-select" className="sr-only">Filter by alert category</label>`.
- **Chat Input:** `<label htmlFor="chat-prompt-input" className="sr-only">Message DNAC Ops Assistant</label>`.

### 2. Accessible Table Headers (`scope="col"` & `aria-sort`)
All data tables must provide semantic column scopes and sort state declarations:
- Every table header cell must specify `scope="col"`.
- Sortable column headers (`<th>`) must specify `aria-sort="ascending" | "descending" | "none"` and include accessible button controls with `aria-label`.

### 3. Accessible Table Captions (`<caption className="sr-only">`)
Every data table must include a visually-hidden caption element as the first child of `<table>`:
- **Alert Suppression Table (`FalseAlertMetrics.jsx`):**
  `<caption className="sr-only">Ingested Cisco DNA Center network alerts with suppression decisions, confidence scores, and ServiceNow ticket status</caption>`
- **Device Health Table (`NocDeviceTable.jsx`):**
  `<caption className="sr-only">Network devices inventory with health scores, alert counts, and live DNAC assurance status</caption>`
- **Pattern Clusters Table (`AlertPatterns.jsx`):**
  `<caption className="sr-only">Clustered network alert patterns categorized by recurrence and suppression efficiency</caption>`

---

## Verification & Anti-Patterns

### Anti-Patterns to Prevent:
1. ❌ **Divs masquerading as buttons:** `<div role="button" tabIndex={0}>` in navigation without native `<button type="button">`.
2. ❌ **Invisible focus indicators:** Relying on `outline: none` without providing an explicit `:focus-visible` replacement.
3. ❌ **Sub-12px typography:** Any `font-size: 0.7rem`, `0.72rem`, or `10px/11px` in tables, badges, or filter labels.
4. ❌ **Blocking modal chat overlay:** Using a full-page modal backdrop that prevents side-by-side dashboard investigation while chatting.
5. ❌ **Unlabelled form inputs:** `<input placeholder="...">` without an associated `<label htmlFor="...">` or `.sr-only` element.
6. ❌ **Tables without `scope="col"` or `<caption>`:** Data tables that fail screen reader column and landmark navigation.

### Automated Testing Contract:
`tests/test_accessibility_hit_areas_contract.py` will automatically verify:
1. **Interactive Hit Areas:** CSS rules enforce `min-height: 32px` on buttons, filter pills, and inputs; `.touch-target-expand::before` enforces 44x44px.
2. **Typography Minimums:** Zero occurrences of sub-12px font sizes in CSS for tables, badges, and filters.
3. **Sidebar Semantics:** `App.jsx` uses `<button className="sidebar-nav-item"` with `aria-current="page"`, `aria-expanded`, and `:focus-visible` tooltips in `App.css`.
4. **Chat Panel Non-Modal & Hotkeys:** `ChatPanel.jsx` and `App.jsx` implement non-modal inset, `Escape` key close listener, `Ctrl+/` shortcut, and `aria-controls`.
5. **Form Labels & Table Captions:** All 3 data tables contain `<caption className="sr-only">`, `scope="col"`, and form inputs contain associated labels.
