# Control Flow Architecture

This diagram illustrates the logical decision path and processing stages that an alert passes through, from ingestion to final resolution or ticketing.

```mermaid
graph TD
    %% Styling
    classDef Ingress fill:#eff6ff,stroke:#2563eb,stroke-width:2px,color:#1e3a8a;
    classDef Decision fill:#fff7ed,stroke:#c2410c,stroke-width:2px,color:#7c2d12;
    classDef Process fill:#f0fdf4,stroke:#15803d,stroke-width:2px,color:#14532d;
    classDef Done fill:#faf5ff,stroke:#6b21a8,stroke-width:2px,color:#581c87;

    A[Cisco DNAC Webhook] -->|Alert Received| B(Agent 1: Backdate Detector)
    class A Ingress;
    class B Process;

    B --> C{Is Alert Backdated?}
    class C Decision;

    C -->|Yes: Old/Stale| D[Suppress Alert]
    class D Process;
    D --> E[Email Notifier]
    class E Process;
    E --> F[Dashboard / DB Update]
    class F Done;

    C -->|No: Current Alert| G(Agent 2: ML/DL Classifier)
    class G Process;

    G --> H{Classifier Prediction}
    class H Decision;

    H -->|Auto-Resolving| I[Agent 3: Schedule 15m Wait]
    class I Process;
    I --> J[RabbitMQ Delayed Exchange]
    class J Ingress;
    J -->|Timer Expires| K(Delayed Check: Recheck DNAC Status)
    class K Process;
    
    K --> L{Still Active in DNAC?}
    class L Decision;
    L -->|No: Resolved| M[Mark Suppressed & Skip Ticket]
    class M Process;
    M --> E;
    
    L -->|Yes: Still Active| N[Agent 4: ServiceNow Orchestrator]
    class N Process;

    H -->|Non-Auto Resolving / Uncertain| N;

    N --> O{Incident Status}
    class O Decision;

    O -->|Active Incident Exists| P[Append Comment]
    class P Process;
    O -->|Recently Closed <= 3 days| Q[Re-open Incident]
    class Q Process;
    O -->|No/Old Incident| R[Create New Incident]
    class R Process;

    P --> E
    Q --> E
    R --> E
```

### Flow Breakdown

1. **Ingestion & Validation**: Cisco DNA Center pushes live alert webhooks.
2. **Backdate Check (Agent 1)**: If the alert timestamp is older than 24 hours (backdated), it is suppressed immediately.
3. **Classification (Agent 2)**: For fresh alerts, Agent 2 runs the TF-IDF and DistilBERT models to predict if the issue is a transient, self-healing event.
4. **Delayed Mitigation (Agent 3)**: Auto-resolving alerts are sent to a 15-minute wait queue. After the delay, the system queries DNAC to verify if the alert is still active before taking action.
5. **Escalation (Agent 4)**: Alerts classified as critical or still active after the delay queue generate a ticket in ServiceNow.
