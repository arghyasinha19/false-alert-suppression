# Phase 10: Multi-Mode Representation Engine - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-01  
**Phase:** 10-multi-mode-representation-engine  
**Areas discussed:** View Switcher Placement & Controls, Infrastructure Tier Grouping Logic, SRE High-Density Table Specifications, Regional Site Matrix Specifications  

---

## View Switcher Placement & Controls

| Option | Description | Selected |
|--------|-------------|----------|
| Consolidated in Filter Bar | Right-aligned segmented pill group alongside search and device count | ✓ |
| Dedicated Sub-Header Bar | Placed directly above the search bar as a distinct mode selection row | |

| Option | Description | Selected |
|--------|-------------|----------|
| Icon + Text Pills | [Layers] Topology \| [Table] SRE Table \| [Globe] Site Matrix with active indicator | ✓ |
| Compact Icon-Only | Clean 3-button icon cluster with tooltips to save horizontal width | |

**User's choice:** Consolidated inside the Filter Bar on the right, using icon + text segmented pills.

---

## Infrastructure Tier Grouping Logic

- **Tier 1 (Core & WAN Backbone):** Routers, Core switches, Gateways (`RT`, `Core`, `GW`).
- **Tier 2 (Distribution & Security):** Firewalls, distribution switches (`FW`, `Dist`, `SW01`).
- **Tier 3 (Campus & Access Edge):** Wireless APs, access switches (`AP`, `Access`, `Switch`, `WLC`).
- **Roll-up summary badges** per tier displaying health distribution.

---

## SRE High-Density Table Specifications

- **Columns:** Device Name, Location, Tier/Role, Health, Active Alerts, SNOW Incident, Last Seen, Actions.
- **Default sorting:** Sorted by severity / alert criticality descending.
- **Header:** Sticky table header matching Phase 7 ergonomics.

---

## Regional Site Matrix Specifications

- **Site Cards:** Physical site health status cards with flag, location name, device count, and alert counts.
- **Interaction:** Clicking site card filters inventory to that site and drills down into detailed device inspection.
