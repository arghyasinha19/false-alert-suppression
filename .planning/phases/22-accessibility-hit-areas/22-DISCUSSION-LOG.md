# Phase 22: Accessibility & Hit Areas - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-06  
**Phase:** 22-accessibility-hit-areas  
**Areas discussed:** Chat Panel Mode (UI-08), Hit Area Enforcement & Typography (UI-07), Sidebar Keyboard Navigation & Focus Mechanics (UI-16), Form Labels & Table Semantics (UI-17)  

---

## 1. Ops Assistant Chat Panel Mode (UI-08)

| Option | Description | Selected |
|--------|-------------|----------|
| Non-Modal Inset (Docked) | Content area insets so operators can interact with charts/tables while chatting with the AI assistant, without any blocking backdrop | ✓ |
| Accessible Modal Drawer | Fixed overlay with focus trap, aria-modal="true", role="dialog", Escape to close, focus return, and dimmed backdrop | |
| Responsive Hybrid | Non-modal side-by-side on wide screens (>1300px), switching to modal focus-trapped drawer on smaller screens | |

**User's choice:** Non-Modal Inset (Docked)
**Notes:** Added keyboard accessibility: Escape closes when inside panel, `Ctrl+/` (or `Cmd+/`) global hotkey toggles panel open/close, focus returns to toggle button on close.

---

## 2. Hit Area Enforcement & Typography Calibration (UI-07)

| Option | Description | Selected |
|--------|-------------|----------|
| 32px visible + 44px touch target | 32px visible min-height on buttons/pills/inputs, plus transparent ::before pseudo-element expanding touch target to 44x44px on compact icons | ✓ |
| Direct 40-44px visual height | Direct 40-44px visual height across all buttons, filter pills, and inputs | |
| Strict 32px visual height | Strict 32px visual height without 44px pseudo-element expansion | |

**User's choice:** 32px visible min-height on buttons/pills/inputs, plus transparent `::before` pseudo-element expanding touch target to 44x44px on compact icons.
**Notes:** Typography standardized to 13px (0.8125rem) for table body cells and filter controls, and 12px (0.75rem) for table headers, badges, and metadata tags (no sub-12px text anywhere).

---

## 3. Sidebar Keyboard Navigation & Focus Mechanics (UI-16)

| Option | Description | Selected |
|--------|-------------|----------|
| Accent-blue focus ring & hover/focus tooltips | 2px solid accent-blue outline with 2px offset on :focus-visible, and show floating tooltip on both :hover and :focus-visible when sidebar is collapsed | ✓ |
| Inset box-shadow ring | 2px glowing focus ring without offset (box-shadow ring), tooltips on focus-visible only | |
| Browser native | Native browser focus outline style without custom styling | |

**User's choice:** 2px solid accent-blue outline with 2px offset on :focus-visible, and show floating tooltip on both :hover and :focus-visible when sidebar is collapsed.
**Notes:** Refactor items from `<div>` to semantic `<button type="button">`, set `aria-current="page"` on active view, set `aria-expanded` and `aria-controls` on chat toggle.

---

## 4. Form Labels & Screen-Reader Table Architecture (UI-17)

| Option | Description | Selected |
|--------|-------------|----------|
| Compact micro-labels, aria-sort, scope="col", and sr-only captions | Compact micro-labels for date/time/filter controls with htmlFor association; aria-sort and scope="col" on all headers; and <caption className="sr-only"> on every data table | ✓ |
| Stacked full-height labels | Stacked full-height labels above every control; standard scope="col" and captions without aria-sort | |
| Minimal label tags | Minimal label tags and basic scope="col" only | |

**User's choice:** Compact micro-labels for date/time/filter controls with htmlFor association; aria-sort and scope="col" on all headers; and `<caption className="sr-only">` on every data table.
**Notes:** Ensures 100% WCAG 1.3.1 / 3.3.2 compliance without breaking toolbar grid alignments.

---

## Agent's Discretion

- In non-modal mode on screens `<= 1100px`, allow floating/overlay fallback if screen width is constrained.
- Smooth transition timing for layout insetting (`0.25s ease-out`).

## Deferred Ideas

- None. All discussed items are in scope for Phase 22.
