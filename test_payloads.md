# DNAC Test Scenarios Payload Collection

Below are 10 sample JSON payloads representing various scenarios (active vs. resolved, auto-resolving vs. non-auto-resolving) that you can use to test your classifier, consumer scripts, and Jenkins pipeline. 

### 1. Active AP Flap (Typically Auto-Resolving)
```json
{
  "version": "1.0.0",
  "instanceId": "alert-001-ap-flap-active",
  "eventId": "NETWORK-DEVICES-3-107",
  "category": "WARN",
  "severity": 3,
  "timestamp": 1776942958800,
  "details": {
    "Type": "Network Device",
    "Assurance Issue Details": "AP UK-MAL-DEV-AP02 has flapped",
    "Device": "UK-MAL-DEV-AP02",
    "Assurance Issue Name": "AP UK-MAL-DEV-AP02 has flapped",
    "Assurance Issue Status": "active"
  },
  "network": { "deviceId": "dev-001" },
  "correlationId": "corr-001",
  "_source": "dnac-webhook"
}
```

### 2. Resolved AP Flap 
```json
{
  "version": "1.0.0",
  "instanceId": "alert-002-ap-flap-resolved",
  "eventId": "NETWORK-DEVICES-3-107",
  "category": "WARN",
  "severity": 3,
  "timestamp": 1776943958800,
  "details": {
    "Type": "Network Device",
    "Assurance Issue Details": "AP UK-MAL-DEV-AP02 has flapped",
    "Device": "UK-MAL-DEV-AP02",
    "Assurance Issue Name": "AP UK-MAL-DEV-AP02 has flapped",
    "Assurance Issue Status": "resolved"
  },
  "network": { "deviceId": "dev-001" },
  "correlationId": "corr-002",
  "_source": "dnac-webhook"
}
```

### 3. Active BGP Peer Down (Typically Non-Auto-Resolving)
```json
{
  "version": "1.0.0",
  "instanceId": "alert-003-bgp-down",
  "eventId": "NETWORK-ROUTING-1-100",
  "category": "ERROR",
  "severity": 1,
  "timestamp": 1776944958800,
  "details": {
    "Type": "Network Device",
    "Assurance Issue Details": "BGP peer 10.0.0.1 on Core-Router-01 is down",
    "Device": "Core-Router-01",
    "Assurance Issue Name": "BGP Peer is Down",
    "Assurance Issue Status": "active"
  },
  "network": { "deviceId": "dev-002" },
  "correlationId": "corr-003",
  "_source": "dnac-webhook"
}
```

### 4. Active High CPU (Typically Auto-Resolving)
```json
{
  "version": "1.0.0",
  "instanceId": "alert-004-high-cpu",
  "eventId": "NETWORK-DEVICES-2-200",
  "category": "WARN",
  "severity": 2,
  "timestamp": 1776945958800,
  "details": {
    "Type": "Network Device",
    "Assurance Issue Details": "Device Access-Switch-05 CPU utilization is at 95%",
    "Device": "Access-Switch-05",
    "Assurance Issue Name": "High CPU Utilization",
    "Assurance Issue Status": "active"
  },
  "network": { "deviceId": "dev-003" },
  "correlationId": "corr-004",
  "_source": "dnac-webhook"
}
```

### 5. Resolved High CPU
```json
{
  "version": "1.0.0",
  "instanceId": "alert-005-high-cpu-resolved",
  "eventId": "NETWORK-DEVICES-2-200",
  "category": "WARN",
  "severity": 2,
  "timestamp": 1776946958800,
  "details": {
    "Type": "Network Device",
    "Assurance Issue Details": "Device Access-Switch-05 CPU utilization is at 95%",
    "Device": "Access-Switch-05",
    "Assurance Issue Name": "High CPU Utilization",
    "Assurance Issue Status": "resolved"
  },
  "network": { "deviceId": "dev-003" },
  "correlationId": "corr-005",
  "_source": "dnac-webhook"
}
```

### 6. Active Switch Port Down (Typically Auto-Resolving or Low Priority)
```json
{
  "version": "1.0.0",
  "instanceId": "alert-006-port-down",
  "eventId": "NETWORK-INTERFACES-3-300",
  "category": "WARN",
  "severity": 3,
  "timestamp": 1776947958800,
  "details": {
    "Type": "Network Interface",
    "Assurance Issue Details": "Interface GigabitEthernet1/0/1 on Switch-12 has gone down",
    "Device": "Switch-12",
    "Assurance Issue Name": "Interface State Down",
    "Assurance Issue Status": "active"
  },
  "network": { "deviceId": "dev-004" },
  "correlationId": "corr-006",
  "_source": "dnac-webhook"
}
```

### 7. Active OSPF Neighbor Down (Typically Non-Auto-Resolving)
```json
{
  "version": "1.0.0",
  "instanceId": "alert-007-ospf-down",
  "eventId": "NETWORK-ROUTING-1-101",
  "category": "ERROR",
  "severity": 1,
  "timestamp": 1776948958800,
  "details": {
    "Type": "Network Device",
    "Assurance Issue Details": "OSPF neighbor 192.168.1.1 on Dist-Router is down",
    "Device": "Dist-Router",
    "Assurance Issue Name": "OSPF Neighbor Down",
    "Assurance Issue Status": "active"
  },
  "network": { "deviceId": "dev-005" },
  "correlationId": "corr-007",
  "_source": "dnac-webhook"
}
```

### 8. Active High Memory (Typically Auto-Resolving)
```json
{
  "version": "1.0.0",
  "instanceId": "alert-008-high-memory",
  "eventId": "NETWORK-DEVICES-2-201",
  "category": "WARN",
  "severity": 2,
  "timestamp": 1776949958800,
  "details": {
    "Type": "Network Device",
    "Assurance Issue Details": "Memory utilization is consistently above 90%",
    "Device": "Core-Switch-02",
    "Assurance Issue Name": "High Memory Utilization",
    "Assurance Issue Status": "active"
  },
  "network": { "deviceId": "dev-006" },
  "correlationId": "corr-008",
  "_source": "dnac-webhook"
}
```

### 9. Active Power Supply Failure (Hardware / Non-Auto-Resolving)
```json
{
  "version": "1.0.0",
  "instanceId": "alert-009-psu-fail",
  "eventId": "NETWORK-HARDWARE-1-001",
  "category": "ERROR",
  "severity": 1,
  "timestamp": 1776950958800,
  "details": {
    "Type": "Network Device",
    "Assurance Issue Details": "Power Supply 2 on Core-Router-01 has failed",
    "Device": "Core-Router-01",
    "Assurance Issue Name": "Power Supply Failure",
    "Assurance Issue Status": "active"
  },
  "network": { "deviceId": "dev-002" },
  "correlationId": "corr-009",
  "_source": "dnac-webhook"
}
```

### 10. Active AP Offline (Typically Non-Auto-Resolving / Service Impacting)
```json
{
  "version": "1.0.0",
  "instanceId": "alert-010-ap-offline",
  "eventId": "NETWORK-DEVICES-1-108",
  "category": "ERROR",
  "severity": 1,
  "timestamp": 1776951958800,
  "details": {
    "Type": "Network Device",
    "Assurance Issue Details": "AP US-NY-HQ-AP05 is unreachable",
    "Device": "US-NY-HQ-AP05",
    "Assurance Issue Name": "AP is Offline",
    "Assurance Issue Status": "active"
  },
  "network": { "deviceId": "dev-007" },
  "correlationId": "corr-010",
  "_source": "dnac-webhook"
}
```
