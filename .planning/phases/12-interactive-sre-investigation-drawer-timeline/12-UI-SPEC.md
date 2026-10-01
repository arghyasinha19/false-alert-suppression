# Phase 12: Interactive SRE Investigation Drawer & Incident Timeline - UI Design Contract

**Phase:** 12  
**Milestone:** v1.5 Executive & Observability Network Operations Center (NOC) Overhaul  
**Status:** Approved Specification  

---

## 1. Visual Hierarchy & Drawer Layout Architecture

The slide-out detail drawer (`.detail-panel`) is upgraded into a multi-tab enterprise SRE investigation workstation (width: 580px, responsive on mobile):

```
┌────────────────────────────────────────────────────────────────────────┐
│ [🔴 CRITICAL] Switch-12 (dev-004)                   [🔄 Recheck] [✖]  │
├────────────────────────────────────────────────────────────────────────┤
│ [ ⚡ Alert Triage (2) ] [ 📊 Assurance ] [ 🖥️ Inventory ] [ 📄 JSON ]  │
├────────────────────────────────────────────────────────────────────────┤
│ TAB 1: ALERT TRIAGE & TIMELINE                                         │
│  Alert Card: "High Interface Error Rate on Te1/0/1"                    │
│   ├── [SEV 1] [DNAC ACTIVE] [INC0091823]                               │
│   └── Multi-Agent Decision Stepper (Vertical Flow):                    │
│       ├── 📥 Ingested: 2026-09-01 16:31:20 UTC (+0ms)                 │
│       ├── ⏱️ Agent 1 (Temporal): Alert is fresh (0.2h old) → PASSED     │
│       ├── 🤖 Agent 2 (ML Transience): P(Transient)=8.4% → PERSISTENT   │
│       ├── ⏳ Agent 3 (DLX Hold): 15m verification window → ESCALATED   │
│       └── 🎫 Agent 4 (ITSM): INC0091823 created (Priority 1) → TICKET  │
│                                                                        │
│ TAB 2: ASSURANCE TELEMETRY                                             │
│  ├── CPU Utilization: [██████████░░░░░░] 68% Nominal                   │
│  ├── Memory Usage:    [█████████████░░░] 82% Warning                   │
│  ├── Interface Drops: 0.04% packet loss, 12 CRC errors / min           │
│  └── Vitals Grid: Reachability, Temperature, PoE Consumption, Latency  │
│                                                                        │
│ TAB 3: DEVICE INVENTORY                                                │
│  ├── Specs: Cisco Catalyst 9300-48UXM, IOS-XE 17.9.4a                  │
│  ├── Network: IP 10.14.20.12, MAC 00:2A:6A:9B:4C:12, Site SG-SIN       │
│  └── Historical Ticket Log: 3 total incidents, 2 auto-resolved         │
│                                                                        │
│ TAB 4: RAW PAYLOADS                                                    │
│  ├── Searchable, syntax-colored JSON payload viewer with Copy button    │
├────────────────────────────────────────────────────────────────────────┤
│ SRE Action Bar (Sticky Footer):                                        │
│ [ 📋 Copy Incident ]  [ ⚡ Simulate Alert ]  [ 📥 Export Diagnostic ]   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Specifications

### 2.1 Drawer Tabs Navigation (`.noc-drawer-tabs`)
- **Container**: Sticky beneath the drawer header.
  - `display: flex; gap: 4px; padding: 0.5rem 1.25rem; background: var(--bg-tertiary); border-bottom: 1px solid var(--card-border);`
- **Tabs**:
  - `triage`: **Alert Triage** (with alert count badge)
  - `telemetry`: **Assurance Telemetry**
  - `inventory`: **Device Inventory**
  - `payloads`: **Raw Payloads**
- **Active State**:
  - `color: var(--accent-blue); border-bottom: 2px solid var(--accent-blue); font-weight: 600;`

### 2.2 Multi-Agent Chronological Decision Stepper (`.noc-agent-stepper`)
- **Vertical Pipeline Tracker**:
  - Continuous vertical trail line: `border-left: 2px dashed var(--border-color); margin-left: 14px;`
  - 5 Distinct Stages per alert:
    1. **Ingestion**: Event arrival timestamp, raw event ID, DNAC Assurance webhook trigger.
    2. **Agent 1 (Temporal / Backdate Filter)**: Timestamp delta verification against 2h suppression threshold.
    3. **Agent 2 (ML Transience Classifier)**: Random Forest model output, confidence score badge (e.g. `94.2%`), feature weights.
    4. **Agent 3 (DLX Verification Queue)**: Dead Letter Exchange holding period with live health check status.
    5. **Agent 4 (ServiceNow Auto-Ticketing Engine)**: ServiceNow incident number, action (`INCIDENT_CREATED`, `INCIDENT_REOPENED`, `SUPPRESSED_NO_TICKET`), urgency.
- **Node Status Badges**:
  - `PASSED` / `VERIFIED`: Green badge (`--health-healthy`)
  - `SUPPRESSED` / `AUTO-RESOLVED`: Cyan / Teal badge (`--accent-cyan`)
  - `ESCALATED` / `PERSISTENT`: Amber badge (`--health-warning`)
  - `CRITICAL TICKET`: Red badge (`--health-critical`)
- **Expandable Metrics Drawer / Accordion**:
  - Each step has a toggleable "View Agent Metrics" button revealing raw latency, confidence percentages, and decision rationale.

### 2.3 Assurance Telemetry Vitals (`.noc-telemetry-grid`)
- **Key Visual Gauges**:
  - **CPU Utilization Meter**: Circular ring or horizontal proportional bar with thresholds (Green `<70%`, Orange `70-85%`, Red `>85%`).
  - **Memory Utilization Bar**: Memory allocation gauge (e.g., `6.4 GB / 8.0 GB`).
  - **Interface Health & Error Rates**: CRC errors, packet drop percentage, link status.
  - **Power & PoE Status**: Wattage draw, redundant PSU operational state.
  - **Reachability & Latency**: ICMP ping response (ms) and SNMP health status.

### 2.4 Device Inventory & Specs (`.noc-inventory-section`)
- Clean, structured key-value meta grid:
  - Device Hostname, Device ID, Serial Number, MAC Address.
  - Hardware Model, Firmware / OS Version, Architectural Tier & Role.
  - Physical Site, Location Coordinates, Rack Placement.
  - ServiceNow Incident Lifetime History (Total Incidents, Auto-Suppressed, Backdated).

### 2.5 Raw Payloads Viewer (`.noc-json-viewer`)
- Formatted, monospace JSON code block with syntax color highlights.
- Search input to filter JSON keys/values.
- "Copy JSON" button with immediate clipboard copy.

### 2.6 SRE Action Bar (`.noc-drawer-action-bar`)
- **Sticky Footer Bar**:
  - Fixed at drawer bottom with subtle frosted glass backdrop: `background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(8px);`
  - Action Buttons:
    - **`Copy Incident`**: Copies ticket ID + alert summary to clipboard.
    - **`Poll DNAC`**: Simulates live API ping with loading spinner and health re-check.
    - **`Simulate Alert`**: Triggers synthetic alert event for device testing.
    - **`Export Diagnostic`**: Downloads `device-diagnostic-report.json`.

### 2.7 Toast Notification System (`.noc-toast`)
- Floating toast message container at top-right of the viewport.
- Smooth slide-in/slide-out animations (`@keyframes noc-toast-in`).
- Auto-dismisses after 3 seconds.

---

## 3. Theme & Design Token Standards

- Uses existing dark/light CSS variables:
  - Backgrounds: `--bg-primary`, `--bg-secondary`, `--bg-tertiary`
  - Borders: `--card-border`, `--border-color`
  - Status Accents: `--health-critical`, `--health-warning`, `--health-healthy`, `--accent-blue`, `--accent-purple`, `--accent-cyan`
- Zero external charting or component libraries required.
