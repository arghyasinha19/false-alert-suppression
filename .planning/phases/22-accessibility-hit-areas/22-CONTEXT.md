# Phase 22: Accessibility & Hit Areas - Context

**Gathered:** 2026-10-06  
**Status:** Ready for planning  

<domain>
## Phase Boundary

Phase 22 delivers WCAG AA accessibility compliance across the operations dashboard, focusing on hit areas, keyboard navigation, form labeling, table screen-reader semantics, and chat panel interaction. Specifically, it expands interactive hit areas to 32px minimum with 44px touch targets (`UI-07`), converts the Ops Assistant chat panel to a non-modal docked inset layout with keyboard controls (`UI-08`), refactors sidebar navigation to semantic `<button>` elements with `aria-current="page"` and keyboard-activated tooltips (`UI-16`), and equips all form controls with accessible labels and all tables with `scope="col"` headers and visually-hidden captions (`UI-17`).

</domain>

<decisions>
## Implementation Decisions

### 1. Ops Assistant Chat Panel Mode (UI-08)
- **D-01:** Implement the Ops Assistant chat panel as a **Non-Modal Inset (Docked)** drawer. When open, the panel docks alongside the `.content-area`, insetting the main view so operators can simultaneously inspect telemetry charts, tables, and device details while chatting with the AI assistant without any blocking modal backdrop.
- **D-02:** Remove the blocking `chat-overlay` backdrop element in non-modal mode. Retain the user-resizable drag handle (`chat-resize-handle`) with min/max bounds (340px to 900px, default 440px).
- **D-03:** Provide comprehensive keyboard accessibility:
  - Pressing `Escape` while focus is inside the chat panel closes it and returns focus to the sidebar trigger button.
  - Global hotkey `Ctrl+/` (or `Cmd+/`) toggles the chat panel open or closed.
  - The chat toggle button sets `aria-expanded={chatOpen}` and `aria-controls="ops-assistant-panel"`.

### 2. Hit Area Enforcement & Typography Calibration (UI-07)
- **D-04:** Enforce a visible `min-height: 32px` on all standard buttons, filter pills, search inputs, and selects in `dashboard/src/App.css`.
- **D-05:** For compact inline icons and table action buttons (e.g., 24px-28px visual size), implement a transparent `::before` pseudo-element touch target expander with `min-width: 44px; min-height: 44px;` positioned centrally with negative inset to satisfy the 44px touch target requirement without bloating visual layout density.
- **D-06:** Raise and standardize typography:
  - `0.8125rem` (13px) for primary table body cells, filter controls, inputs, and body text.
  - `0.75rem` (12px) for table headers, badges, metadata tags, and captions.
  - Completely eliminate sub-12px (`0.7rem`, `0.72rem`) text styling across all views and components.

### 3. Sidebar Keyboard Navigation & Focus Mechanics (UI-16)
- **D-07:** Refactor sidebar navigation items from `<div>` elements with ad-hoc keyboard listeners to semantic `<button type="button" className="sidebar-nav-item ...">` elements in `dashboard/src/App.jsx`.
- **D-08:** Apply `aria-current="page"` to the currently active view navigation button.
- **D-09:** Add high-contrast `:focus-visible` styling in `dashboard/src/App.css`: 2px solid `var(--accent-blue)` outline with `outline-offset: 2px` (and subtle `box-shadow: 0 0 0 3px rgba(37,99,235,0.25)`), ensuring crystal-clear keyboard indicator without appearing on mouse clicks.
- **D-10:** Update tooltip activation in `dashboard/src/App.css` so that `.sidebar.collapsed .nav-floating-tooltip` renders visibly on both `:hover` and `:focus-visible`.

### 4. Form Labels & Screen-Reader Table Architecture (UI-17)
- **D-11:** Ensure all form controls (date/time pickers, search fields, role/site/category selects) have accessible labels. Use compact inline/micro-labels with explicit `htmlFor` association (`<label htmlFor="...">`) with clean 12px font, supplemented with `<label className="sr-only">` where appropriate to maintain compact toolbar alignment.
- **D-12:** Inject `scope="col"` on every `<th>` element across all data tables (`FalseAlertMetrics`, `AlertPatterns`, `NocDeviceTable`). On sortable column headers, provide explicit `aria-sort="ascending" | "descending" | "none"`.
- **D-13:** Inject an accessible `<caption className="sr-only">` at the start of every `<table>` describing the table purpose and row content for screen-reader users.

### the agent's Discretion
- In non-modal mode, on screens `<= 1100px`, if horizontal width is constrained, the chat panel can float or overlay temporarily with touch dismissal, preserving responsive layout stability.
- CSS transitions for `.content-area` insetting remain smooth (`transition: margin-right 0.25s ease-out` or flex container resizing).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` §UI-A11Y — Requirements UI-07, UI-08, UI-16, UI-17.
- `.planning/ROADMAP.md` §Phase 22 — Phase 22 Goal, Requirements, and Success Criteria.

### Application Shell & Navigation
- `dashboard/src/App.jsx` — Shell layout, sidebar navigation, view routing, chat open state, and header controls.
- `dashboard/src/App.css` — Sidebar styles, buttons, filter pills, table styles, hit area tokens, and focus rings.

### Assistant Chat Panel
- `dashboard/src/ChatPanel.jsx` — Chat drawer component, message list, input area, and resize handler.
- `dashboard/src/ChatPanel.css` — Chat layout, overlay backdrop, panel drawer styling, and animations.

### Data Tables & Form Controls
- `dashboard/src/FalseAlertMetrics.jsx` — Filter controls, date/time inputs, and alert suppression data table.
- `dashboard/src/AlertPatterns.jsx` — Patterns search, filters, and clustered alert table.
- `dashboard/src/components/executive/NocDeviceTable.jsx` — High-density SRE device table with sorting and filtering.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets & Tokens
- `dashboard/src/index.css`: Design tokens including `--accent-blue`, `--card-bg`, `--card-border`, `--text-primary`, `--text-secondary`, `--text-tertiary`.
- `.sr-only` utility: Accessible visually-hidden pattern (`position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0;`).

### Established Patterns
- Focus-visible: Modern CSS `:focus-visible` pseudo-class for keyboard-only focus indicators.
- Semantic HTML: Refactoring from generic `<div>` with `role="button"` to native `<button type="button">` preserves native form submission suppression and screen-reader semantics.

</code_context>

<deferred>
## Deferred Ideas

- None. All discussed items are within the scope of Phase 22.

</deferred>

---

*Phase: 22-accessibility-hit-areas*  
*Context gathered: 2026-10-06 via discuss-phase*
