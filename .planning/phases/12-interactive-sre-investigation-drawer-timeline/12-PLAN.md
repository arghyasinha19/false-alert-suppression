---
phase: 12
plan: 1
type: implementation
prefix: NOC-DRAWER
wave: 1
depends_on: []
files_modified:
  - dashboard/src/NetworkOperations.jsx
  - dashboard/src/App.css
---

# Plan 12-01: Interactive SRE Investigation Drawer & Incident Timeline

> Elevate the device slide-out panel into an enterprise SRE triage workstation with an interactive chronological multi-agent decision timeline (Ingest → Agent 1 → Agent 2 → Agent 3 → Agent 4), Cisco DNA Center Assurance telemetry vitals tabs, and one-click triage action bar with toast notifications.

---

## Requirements Covered

- **NOC-DRAWER-01**: User can view an interactive, multi-agent chronological decision timeline for each alert (Ingestion → Agent 1 Backdate → Agent 2 ML Transience → Agent 3 DLX Queue → Agent 4 ServiceNow).
- **NOC-DRAWER-02**: User can inspect live Cisco DNA Center Assurance telemetry attributes, device health vitals, and raw payload details in dedicated tabs.
- **NOC-DRAWER-03**: User can perform quick triage actions (e.g., Copy Incident, Simulate Alert on Device, Trigger Re-check) directly from the drawer.

---

## Tasks

### Task 1: Tabbed Drawer State & Navigation (`NOC-DRAWER-02`)
- **File:** `dashboard/src/NetworkOperations.jsx`
- **Action:**
  - Introduce `drawerTab` state with 4 options: `'triage'` (default), `'telemetry'`, `'inventory'`, `'payloads'`.
  - Insert sticky segmented tab header `.noc-drawer-tabs` directly under `.detail-panel-header`.
  - Render tab buttons with icons and alert count badge on `Alert Triage`.

### Task 2: Multi-Agent Chronological Decision Stepper (`NOC-DRAWER-01`)
- **File:** `dashboard/src/NetworkOperations.jsx`
- **Action:**
  - Build `deriveMultiAgentTimeline(alert, device)` helper synthesizing the 5 pipeline stages:
    1. **Ingestion**: Event reception, timestamp, source node, payload size.
    2. **Agent 1 (Temporal Filter)**: Checks alert age against 2-hour backdate threshold (`PASSED` or `SUPPRESSED`).
    3. **Agent 2 (ML Classifier)**: Random Forest confidence prediction, predicted class (Transient vs Persistent).
    4. **Agent 3 (DLX Hold Queue)**: Dead Letter Exchange holding duration (15m window) and live telemetry check.
    5. **Agent 4 (ServiceNow Action)**: Incident creation, reopening, commenting, or suppression without ticket.
  - Build `AgentDecisionStepper` component rendering vertical step trail, stage icons, latency tags, color badges, and toggleable "Inspect Agent Reasoning" drawer.
  - Integrate stepper into each active alert card under the `Alert Triage` tab.

### Task 3: Assurance Telemetry & Device Inventory Tabs (`NOC-DRAWER-02`)
- **File:** `dashboard/src/NetworkOperations.jsx`
- **Action:**
  - Build `getDeviceTelemetryVitals(device)` synthesizing realistic DNAC Assurance attributes:
    - CPU Utilization (%) with visual health bar.
    - Memory Utilization (GB allocated / total) with proportional track.
    - Interface Error & Packet Loss rates.
    - Power / PoE consumption and PSU redundancy.
    - Ping latency and SNMP reachability state.
  - Implement **Assurance Telemetry Tab** displaying these metrics in high-density cards.
  - Implement **Device Inventory Tab** displaying model, OS version, IP, MAC, serial number, rack position, and ServiceNow ticket history.

### Task 4: Raw Payloads Tab & JSON Viewer (`NOC-DRAWER-02`)
- **File:** `dashboard/src/NetworkOperations.jsx`
- **Action:**
  - Build `RawPayloadViewer` with search filter, formatted syntax-colored JSON presentation, and one-click "Copy JSON" button.

### Task 5: SRE Action Bar & Toast Notifications (`NOC-DRAWER-03`)
- **File:** `dashboard/src/NetworkOperations.jsx`
- **Action:**
  - Implement floating toast notification state `toasts` and helper `addToast(title, message, type)`.
  - Build sticky drawer footer `.noc-drawer-action-bar` with 4 action buttons:
    - **Copy Incident**: Copies ServiceNow incident ID and summary to clipboard with success toast.
    - **Poll DNAC Health**: Simulates on-demand assurance ping with loading spinner and health toast.
    - **Simulate Alert**: Generates test alert event with animated simulation feedback.
    - **Export Diagnostic**: Downloads `device_diagnostic_report.json` for the node.
  - Render floating toast container `.noc-toast-container` in viewport.

### Task 6: Visual Styling & Animations in `App.css`
- **File:** `dashboard/src/App.css`
- **Action:**
  - Add styles for `.noc-drawer-tabs`, `.noc-drawer-tab-btn`, `.noc-tab-badge`.
  - Add styles for `.noc-agent-stepper`, `.noc-stepper-item`, `.noc-stepper-trail`, `.noc-stepper-dot`, `.noc-stepper-content`, `.noc-stepper-reasoning`.
  - Add styles for `.noc-telemetry-grid`, `.noc-gauge-card`, `.noc-gauge-meter`, `.noc-gauge-bar`.
  - Add styles for `.noc-json-viewer`, `.noc-code-block`.
  - Add styles for `.noc-drawer-action-bar`, `.noc-action-btn`.
  - Add styles and keyframes for `.noc-toast-container`, `.noc-toast`, `@keyframes noc-toast-in`.

---

## Verification Plan

### Automated Checks
- Run `npm run lint` (`oxlint`) — ensure 0 errors and 0 warnings.
- Run `npm run build` (`vite build`) — ensure production bundle builds cleanly.

### Browser Visual & Functional Verification
- Navigate to `http://localhost:5173/` Network Operations tab.
- Click a device tile (e.g. `Switch-12` or `SG-SIN-FW01`) to open the slide-out drawer.
- Verify 4 tabs are present: `Alert Triage`, `Assurance Telemetry`, `Device Inventory`, `Raw Payloads`.
- In `Alert Triage`: verify each alert displays the 5-stage Multi-Agent Decision Stepper with status badges.
- Click to expand agent reasoning details.
- Switch to `Assurance Telemetry`: verify CPU, Memory, Packet Loss, and Reachability gauges render cleanly.
- Switch to `Device Inventory`: verify hardware specs, IP, MAC, and ticket history.
- Switch to `Raw Payloads`: test search and Copy JSON.
- Test Action Bar:
  - Click `Copy Incident` -> verify clipboard copy and floating toast.
  - Click `Poll DNAC Health` -> verify spinner and confirmation toast.
  - Click `Simulate Alert` -> verify simulation toast.
  - Click `Export Diagnostic` -> verify report export.
