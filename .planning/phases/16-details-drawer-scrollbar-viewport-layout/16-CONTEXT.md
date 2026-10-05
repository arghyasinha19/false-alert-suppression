# Phase 16: Details Drawer Scrollbar & Viewport Layout - Context

**Gathered:** 2026-10-05  
**Status:** Ready for planning  

<domain>
## Phase Boundary

Phase 16 addresses the missing scrollbar and layout scrolling in the device details drawer panel (`.detail-panel`) when inspecting devices in Executive Topology and all Network Operations Center views:
1. Replace invisible/transparent scrollbar defaults with dedicated, high-contrast, theme-aware scrollbar styling (`DRAWER-01`).
2. Refactor `.detail-panel` flexbox layout so the header and tabs stay anchored at the top, the sticky action bar stays pinned at the bottom, and `.detail-panel-body` scrolls independently (`DRAWER-02`).
3. Verify that all 4 drawer workspaces (Alert Triage, Assurance Telemetry, Device Inventory, Raw Payloads) scroll smoothly across various viewport heights without layout clipping (`DRAWER-03`).

No backend changes in this phase.  
No multi-agent timeline logic changes in this phase.
</domain>

<decisions>
## Implementation Decisions

### Scrollbar Visibility & Theme System
- **D-01 (Visible Scrollbar Rules):** Override the transparent global scrollbar defaults (`scrollbar-color: transparent transparent`) specifically for the details drawer container and its body. Provide dedicated 7px-8px scrollbars with visible tracks and rounded thumbs that adapt to dark and light modes:
  - Dark mode: thumb `rgba(255, 255, 255, 0.22)` with hover `rgba(255, 255, 255, 0.38)`.
  - Light mode: thumb `rgba(0, 0, 0, 0.22)` with hover `rgba(0, 0, 0, 0.40)`.
  - Standard CSS: `scrollbar-width: thin; scrollbar-color: var(--scrollbar-thumb) transparent;`
- **D-02 (Always-Visible Affordance):** The scrollbar thumb should be visible even when the mouse is idle within the panel, so users immediately recognize that content extends below the fold.

### Flexbox Drawer Architecture
- **D-03 (Outer Panel Overflow Control):** Update `.detail-panel` to `height: 100vh; max-height: 100vh; overflow: hidden; display: flex; flex-direction: column;`. This prevents the entire drawer from scrolling and prevents jitter on sticky child elements.
- **D-04 (Anchored Header & Tabs):**
  - `.detail-panel-header`: `flex-shrink: 0;`
  - `.noc-drawer-tabs`: `flex-shrink: 0;`
- **D-05 (Scrollable Content Container):**
  - `.detail-panel-body`: `flex: 1 1 auto; overflow-y: auto; min-height: 0; overscroll-behavior: contain; -webkit-overflow-scrolling: touch;`.
- **D-06 (Pinned SRE Action Bar):**
  - `.noc-drawer-action-bar`: `flex-shrink: 0;` fixed at the base of the drawer, ensuring action buttons (Copy Incident, Poll DNAC, Simulate Alert, Export) are always accessible without scrolling.

### Cross-Tab Viewport Sizing
- **D-07 (Scroll Reset & Padding):** Ensure bottom padding in `.detail-panel-body` provides sufficient clearance (e.g. `padding-bottom: 1.5rem`) so the bottom-most items on long tabs (such as Raw Payloads or multi-agent step cards) are fully visible above the action bar border.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Frontend Components & Styling
- `dashboard/src/NetworkOperations.jsx` — Component rendering `.detail-panel`, `.detail-panel-header`, `.noc-drawer-tabs`, `.detail-panel-body`, and `.noc-drawer-action-bar`.
- `dashboard/src/App.css` — CSS styling for `.detail-panel`, `.detail-panel-body`, and `.noc-drawer-action-bar`.
- `dashboard/src/index.css` — Global CSS variables, scrollbar defaults (`::-webkit-scrollbar` and `* { scrollbar-color }`).

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` — Requirements DRAWER-01, DRAWER-02, DRAWER-03.
- `.planning/ROADMAP.md` — Phase 16 goals and success criteria.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets & Tokens
- CSS Variables in `index.css`: `--bg-secondary`, `--bg-tertiary`, `--card-border`, `--card-border-hover`, `--text-secondary`, `--text-tertiary`.
- Data attributes: `[data-theme="dark"]` and `[data-theme="light"]`.

### Root Cause
- In `dashboard/src/index.css` lines 141-161:
  `* { scrollbar-color: transparent transparent; }` and `::-webkit-scrollbar-thumb { background: transparent; }`
  Scrollbars are invisible by default and only become faintly translucent when actively hovered.
- In `dashboard/src/App.css` line 1388:
  `.detail-panel` has `overflow-y: auto; display: flex; flex-direction: column;` while child `.detail-panel-body` does not have `overflow-y: auto; flex: 1;`. The entire panel was attempting to scroll as a block while `.noc-drawer-action-bar` relied on `position: sticky; bottom: 0;`, creating conflicting scroll containers and disappearing scrollbars.

</code_context>

<specifics>
## Specific Ideas

- Create dedicated `.detail-panel-body` scrollbar selectors:
  ```css
  .detail-panel-body {
    scrollbar-width: thin;
    scrollbar-color: rgba(255, 255, 255, 0.25) transparent;
  }
  .detail-panel-body::-webkit-scrollbar {
    width: 7px;
  }
  .detail-panel-body::-webkit-scrollbar-track {
    background: transparent;
  }
  .detail-panel-body::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.25);
    border-radius: 999px;
  }
  ```
- In light theme:
  ```css
  [data-theme="light"] .detail-panel-body {
    scrollbar-color: rgba(0, 0, 0, 0.25) transparent;
  }
  [data-theme="light"] .detail-panel-body::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.25);
  }
  ```

</specifics>

<deferred>
## Deferred Ideas

None — scope is tightly focused on fixing the drawer scrollbar and viewport layout.
</deferred>

---
*Phase: 16-details-drawer-scrollbar-viewport-layout*  
*Context gathered: 2026-10-05*  
