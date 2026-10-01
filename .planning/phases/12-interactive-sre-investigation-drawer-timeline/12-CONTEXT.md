# Phase 12: Interactive SRE Investigation Drawer & Incident Timeline - Context

**Gathered:** 2026-10-01  
**Status:** Ready for planning  
**Milestone:** v1.5 Executive & Observability Network Operations Center (NOC) Overhaul  

---

<domain>
## Phase Boundary

Phase 12 elevates the device slide-out drawer from a basic static alert list into an enterprise SRE triage workstation:
1. **Multi-Agent Chronological Decision Timeline (`NOC-DRAWER-01`)**:
   - For any selected device and its active/historical alerts, render an interactive chronological step-tracker detailing the 5 pipeline stages:
     1. **Alert Ingestion**: Raw webhook/event receipt from Cisco DNA Center with payload timestamp and source node.
     2. **Agent 1: Backdate Filter**: Temporal comparison against backdate window (e.g., >2h old suppress check).
     3. **Agent 2: ML Transience Classification**: Random Forest / ML inference evaluating whether the alert is transient auto-clearing or persistent genuine failure.
     4. **Agent 3: DLX Verification Queue**: Dead Letter Exchange holding buffer with timed verification against live DNAC Assurance telemetry.
     5. **Agent 4: ServiceNow Action**: Automated ITSM ticketing decision (Created, Reopened, Suppressed / No Incident).
   - Display status badges for each agent (`Passed`, `Suppressed`, `Escalated`, `Pending`) and expandable cards showing confidence scores, latency, and reasoning explanations.
2. **Dedicated 4-Tab SRE Workspace Navigation (`NOC-DRAWER-02`)**:
   - Tab 1: **Alert Triage & Timeline** — Active alerts with severity badges, multi-agent decision steps, and auto-resolution flags.
   - Tab 2: **Assurance Telemetry** — Live Cisco DNA Center Assurance vitals: CPU utilization, memory usage, interface packet drop rates, link reachability, and PoE status.
   - Tab 3: **Device Inventory** — Device hardware specs, IP address, MAC, serial number, role, location, uptime, and ServiceNow incident historical summary.
   - Tab 4: **Raw Payloads** — Syntax-highlighted, formatted JSON payload viewer with search and one-click clipboard copy.
3. **Interactive SRE Action Bar & Feedback (`NOC-DRAWER-03`)**:
   - **Copy SNOW Incident / Triage Summary**: Copies formatted incident markdown / ticket reference to system clipboard.
   - **Poll / Re-check DNAC Health**: Triggers on-demand health verification against backend/assurance API with simulated pulse feedback.
   - **Simulate Test Alert on Device**: Triggers synthetic test alert generation to observe the multi-agent pipeline in real-time.
   - **Export Alert Report (JSON)**: Generates and downloads a complete diagnostic report JSON for the selected node.
   - **Toast Notifications**: Non-intrusive, animated floating toasts confirming successful action execution.

</domain>

---

<decisions>
## Implementation Decisions

### Decision Timeline Architecture (`NOC-DRAWER-01`)
- **D-01 (Vertical Stepper Layout):**
  - Implement vertical chronological timeline (`.noc-agent-stepper`) with distinct agent node icons, connecting vertical trail lines, and color-coded status pills:
    - *Success / Suppressed:* Green / Emerald (`--health-healthy`)
    - *Escalated / Ticketed:* Blue / Purple (`--accent-blue`)
    - *Transient Warning:* Amber (`--health-warning`)
    - *Critical Failure:* Red (`--health-critical`)
  - Each step contains:
    - Agent title, role label, and relative execution latency (e.g. `+14ms`, `+120ms`).
    - Summary reasoning message (e.g. *"ML Classifier predicted Transient Link Flap with 94.2% confidence"*).
    - Expandable "Inspect Decision Metrics" button revealing threshold details, feature weights, or queue delay parameters.

### Tab Navigation Architecture (`NOC-DRAWER-02`)
- **D-02 (Segmented Drawer Tabs):**
  - Position a sticky segmented tab header directly below the drawer title bar:
    - `[ Alert Triage (N) ]` | `[ Assurance Telemetry ]` | `[ Device Inventory ]` | `[ Raw Payloads ]`
  - Active tab persists during device inspection and smoothly transitions content without layout jumps.
  - Badge on `Alert Triage` tab indicates the number of active alerts needing operator attention.

### Cisco DNA Center Assurance Telemetry Integration
- **D-03 (Assurance Vitals Visualizer):**
  - Render gauge / progress meters for:
    - **CPU Utilization (%)**: Color-coded threshold (0-70% Green, 70-85% Orange, 85-100% Red).
    - **Memory Utilization (%)**: Proportional bar with allocated vs total RAM.
    - **Interface Error Rate / Packet Loss**: Percentage and dropped packet counts.
    - **PoE / Power Consumption**: Wattage and power supply redundancy status.
    - **Uptime / Reachability Status**: Continuous ping reachability and SNMP response latency.

### SRE Action Bar & Toast Feedback (`NOC-DRAWER-03`)
- **D-04 (Action Bar Placement):**
  - Sticky drawer footer action bar (`.noc-drawer-action-bar`) containing primary and secondary SRE actions:
    - Primary: `Copy Incident / Triage Details` (with clipboard API).
    - Secondary: `Poll DNAC Health`, `Simulate Alert`, `Export Diagnostic Report`.
  - Floating toast system (`.noc-toast-container`) rendering micro-toasts with icon, title, and auto-dismiss after 3 seconds.

</decisions>

---

<canonical_refs>
## Canonical References

### Wireframes & Mockups
- Phase 10 & 11 UI specifications (`10-UI-SPEC.md`, `11-UI-SPEC.md`).
- Multi-Agent Pipeline Specifications from project README (`README.md`):
  - Agent 1: Temporal / Backdate Suppressor
  - Agent 2: Machine Learning Transience Classifier
  - Agent 3: Dead Letter Exchange (DLX) Delayed Verification Queue
  - Agent 4: ServiceNow Auto-Ticketing Engine

### Requirements
- `NOC-DRAWER-01`: Multi-agent chronological decision timeline.
- `NOC-DRAWER-02`: Live Cisco DNA Center Assurance telemetry attributes and 4 dedicated tabs.
- `NOC-DRAWER-03`: Quick triage action bar with toast notifications.
</canonical_refs>

---

<deferred_ideas>
## Deferred Ideas (Out of Scope for Phase 12)

- Direct SSH terminal emulator or WebRTC console into the Cisco IOS-XE/NX-OS device (belongs in future Remote Terminal phase).
- Multi-user collaborative notes on incidents (belongs in Enterprise Team Collaboration milestone).
- Custom alert rule authoring from the drawer (belongs in Policy Configuration milestone).
</deferred_ideas>
