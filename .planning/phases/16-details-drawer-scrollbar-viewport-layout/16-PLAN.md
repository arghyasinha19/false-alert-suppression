---
phase: 16
plan: 16-01
status: ready
wave: 1
depends_on: []
files_modified:
  - dashboard/src/App.css
  - dashboard/src/NetworkOperations.jsx
  - tests/test_drawer_scrollbar_contract.py
autonomous: true
requirements:
  - DRAWER-01
  - DRAWER-02
  - DRAWER-03
---

# Phase 16: Details Drawer Scrollbar & Viewport Layout — Plan

**Phase:** 16  
**Status:** Ready  
**Milestone:** v1.7 NOC Details Drawer Scrollbar & Usability Polish  
**Requirements:** DRAWER-01, DRAWER-02, DRAWER-03  
**Context:** `.planning/phases/16-details-drawer-scrollbar-viewport-layout/16-CONTEXT.md`  

---

## Overview

Phase 16 fixes the missing scrollbar and layout scrolling in the device details drawer panel (`.detail-panel`) when clicking a device in Executive Topology (and all Network Operations Center views):
1. **High-Contrast Visible Scrollbars (`DRAWER-01`):** Eliminate transparent global scrollbars on `.detail-panel-body` by adding dedicated, theme-aware scrollbar rules (`scrollbar-width: thin; scrollbar-color: ...;` and `::-webkit-scrollbar-thumb`) visible by default in both dark and light themes.
2. **Fixed-Header / Fixed-Footer Flexbox Architecture (`DRAWER-02`):** Lock `.detail-panel` to `height: 100vh; overflow: hidden; display: flex; flex-direction: column;`, anchor the header (`.detail-panel-header`) and tabs (`.noc-drawer-tabs`) at the top (`flex-shrink: 0`), pin the SRE action bar (`.noc-drawer-action-bar`) at the bottom (`flex-shrink: 0`), and make `.detail-panel-body` the single scrollable container (`flex: 1 1 auto; overflow-y: auto; min-height: 0;`).
3. **Cross-Tab Viewport Sizing & Regression Testing (`DRAWER-03`):** Ensure smooth vertical scrolling with ample bottom padding across all 4 drawer workspaces (Alert Triage, Assurance Telemetry, Device Inventory, Raw Payloads), backed by automated contract tests in `tests/test_drawer_scrollbar_contract.py`.

---

## Files Changed

| Action | File | Description |
|---|---|---|
| MODIFY | `dashboard/src/App.css` | Flex layout refactor on `.detail-panel`, `.detail-panel-body`, `.detail-panel-header`, `.noc-drawer-tabs`, `.noc-drawer-action-bar`, and dedicated visible scrollbar styling |
| MODIFY | `dashboard/src/NetworkOperations.jsx` | Ensure DOM hierarchy cleanly nests `.detail-panel-body` between fixed tabs and pinned action bar |
| CREATE | `tests/test_drawer_scrollbar_contract.py` | Automated contract test verifying CSS scrollbar rules, flex layout, and theme adaptability |

---

## Tasks

<tasks>

### Task 1 — Refactor `.detail-panel` Flexbox Architecture (`DRAWER-02`)

<read_first>
- `dashboard/src/App.css` (lines 1385-1440, 3120-3135, 3620-3650)
- `dashboard/src/NetworkOperations.jsx` (lines 1820-2010, 2275-2340)
- `.planning/phases/16-details-drawer-scrollbar-viewport-layout/16-CONTEXT.md`
</read_first>

<action>
In `dashboard/src/App.css`:
1. Refactor `.detail-panel`:
   ```css
   .detail-panel {
     position: fixed;
     top: 0; right: 0; bottom: 0;
     width: 580px;
     max-width: 94vw;
     height: 100vh;
     max-height: 100vh;
     background: var(--bg-secondary);
     border-left: 1px solid var(--card-border);
     z-index: 201;
     transform: translateX(100%);
     transition: transform var(--transition-slow);
     overflow: hidden; /* Outer container does NOT scroll */
     box-shadow: -6px 0 32px rgba(0, 0, 0, 0.25);
     display: flex;
     flex-direction: column;
   }
   ```
2. Update `.detail-panel-header`:
   ```css
   .detail-panel-header {
     padding: 1.15rem 1.5rem;
     border-bottom: 1px solid var(--card-border);
     display: flex;
     align-items: center;
     justify-content: space-between;
     background: var(--bg-secondary);
     flex-shrink: 0;
     z-index: 5;
   }
   ```
3. Update `.noc-drawer-tabs`:
   ```css
   .noc-drawer-tabs {
     display: flex;
     gap: 0.25rem;
     padding: 0.5rem 1.25rem;
     background: var(--bg-tertiary);
     border-bottom: 1px solid var(--card-border);
     flex-shrink: 0;
     z-index: 4;
     overflow-x: auto;
   }
   ```
4. Update `.detail-panel-body`:
   ```css
   .detail-panel-body {
     flex: 1 1 auto;
     min-height: 0;
     overflow-y: auto;
     overflow-x: hidden;
     padding: 1.25rem 1.5rem 2rem;
     overscroll-behavior: contain;
     -webkit-overflow-scrolling: touch;
   }
   ```
5. Update `.noc-drawer-action-bar`:
   ```css
   .noc-drawer-action-bar {
     flex-shrink: 0;
     background: var(--bg-secondary);
     border-top: 1px solid var(--card-border);
     padding: 0.75rem 1.25rem;
     display: flex;
     align-items: center;
     justify-content: space-between;
     gap: 0.5rem;
     z-index: 5;
   }
   ```
6. Check `dashboard/src/NetworkOperations.jsx` to confirm `.detail-panel` children are strictly in order:
   - Header: `.detail-panel-header`
   - Tabs: `.noc-drawer-tabs`
   - Scrollable Body: `.detail-panel-body`
   - Sticky Action Bar: `.noc-drawer-action-bar`
</action>

<acceptance_criteria>
- `.detail-panel` has `overflow: hidden;` and `display: flex; flex-direction: column;`.
- `.detail-panel-header` has `flex-shrink: 0;`.
- `.noc-drawer-tabs` has `flex-shrink: 0;`.
- `.detail-panel-body` has `flex: 1 1 auto; min-height: 0; overflow-y: auto;`.
- `.noc-drawer-action-bar` has `flex-shrink: 0;`.
</acceptance_criteria>

---

### Task 2 — Implement Dedicated Theme-Aware Scrollbar Styling (`DRAWER-01`, `DRAWER-03`)

<read_first>
- `dashboard/src/index.css` (lines 140-165)
- `dashboard/src/App.css`
</read_first>

<action>
In `dashboard/src/App.css`, add dedicated, high-contrast scrollbar styling for `.detail-panel-body` that overrides the transparent default from `index.css`:

```css
/* ==========================================================================
   NOC Phase 16: Details Drawer Dedicated Scrollbar Styling
   ========================================================================== */

/* Dark Mode (Default) Scrollbars */
.detail-panel-body {
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.28) rgba(255, 255, 255, 0.04);
}

.detail-panel-body::-webkit-scrollbar {
  width: 7px;
  height: 7px;
  display: block;
}

.detail-panel-body::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 999px;
}

.detail-panel-body::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.28);
  border-radius: 999px;
  border: 1px solid transparent;
  background-clip: padding-box;
  transition: background 0.2s ease;
}

.detail-panel-body::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.45);
}

/* Light Mode Scrollbars */
[data-theme="light"] .detail-panel-body {
  scrollbar-color: rgba(0, 0, 0, 0.28) rgba(0, 0, 0, 0.04);
}

[data-theme="light"] .detail-panel-body::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.04);
}

[data-theme="light"] .detail-panel-body::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.28);
}

[data-theme="light"] .detail-panel-body::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.45);
}
```

Verify that in all 4 tabs (`drawerTab === 'triage'`, `'telemetry'`, `'inventory'`, `'payloads'`), content scrolls vertically inside `.detail-panel-body` with the scrollbar thumb visible even when the user is not actively hovering over the scrollbar.
</action>

<acceptance_criteria>
- `.detail-panel-body` defines `scrollbar-width: thin;` and `scrollbar-color`.
- `.detail-panel-body::-webkit-scrollbar` defines `width: 7px` and a non-transparent thumb.
- Light mode `[data-theme="light"] .detail-panel-body` defines dark-tinted non-transparent scrollbar colors.
- Scrollbar is immediately visually identifiable.
</acceptance_criteria>

---

### Task 3 — Automated Contract Test & Build Verification (`DRAWER-01`, `DRAWER-02`, `DRAWER-03`)

<read_first>
- `dashboard/src/App.css`
- `tests/test_frontend_sre_drawer_contract.py`
</read_first>

<action>
1. Create `tests/test_drawer_scrollbar_contract.py`:
   - Test 1: Verify `.detail-panel` CSS contract:
     - `overflow: hidden;`
     - `display: flex;`
     - `flex-direction: column;`
     - `height: 100vh;` or `max-height: 100vh;`
   - Test 2: Verify `.detail-panel-body` CSS contract:
     - `flex: 1` or `flex-grow`
     - `overflow-y: auto;`
     - `min-height: 0;`
   - Test 3: Verify scrollbar visibility styling:
     - `.detail-panel-body` has non-transparent `scrollbar-color`
     - `.detail-panel-body::-webkit-scrollbar-thumb` has non-transparent background
     - `[data-theme="light"] .detail-panel-body` has light-theme scrollbar rules
   - Test 4: Verify fixed header & pinned action bar:
     - `.detail-panel-header` has `flex-shrink: 0;`
     - `.noc-drawer-action-bar` has `flex-shrink: 0;`
2. Run pytest:
   ```bash
   pytest tests/test_drawer_scrollbar_contract.py -v
   ```
3. Run frontend production build:
   ```bash
   cd dashboard && npm run build
   ```
</action>

<acceptance_criteria>
- `tests/test_drawer_scrollbar_contract.py` runs and passes 100% of test assertions.
- `npm run build` completes with 0 errors.
</acceptance_criteria>

</tasks>

---

## Verification Plan

### Automated Tests
- Run `pytest tests/test_drawer_scrollbar_contract.py -v` (all tests pass).
- Run `pytest tests/ -v` (entire suite passes with 0 regressions).
- Run `cd dashboard && npm run build` (clean Vite build).

### Manual / Browser Verification
- Open [http://localhost:5173/](http://localhost:5173/)
- Navigate to "Network Operations" tab and select "Executive Topology" view
- Click any device tile (e.g. `cat9300-access-01` or `csr1000v-edge-01`)
- Verify the slide-out drawer opens smoothly
- Observe that a clear, sleek vertical scrollbar thumb is visible on the right edge of the content body
- Scroll down: Verify the header and tabs stay anchored at the top, the action bar stays pinned at the bottom, and only the body scrolls
- Switch between tabs (Alert Triage, Assurance Telemetry, Device Inventory, Raw Payloads): verify scrolling works across all tabs
- Toggle dark/light theme: verify the scrollbar thumb color shifts appropriately
