# Workflow Pipeline Restructuring and DLX Integration

## Project Architecture Restructure
The legacy `/workflow/agents`, `/workflow/graph`, and `/workflow/helper` directories have been consolidated into a clean, flat, production-standard structure:
- `workflow/nodes/`: Contains the LangGraph nodes (`node_agent_1`, `node_agent_2`, `node_agent_3_scheduler`, `node_supervisor`, `node_reporter`).
- `workflow/tools/`: Contains utility tools (`backdate_detector`, `message_broker`).
- `workflow/utils/`: Contains helpers and loggers.

> [!TIP]
> All local modules now use standard relative imports (`from .nodes...`), eliminating the need for `sys.path.append` hacks, providing a reliable execution environment for production deployments.

## Agent 3: RabbitMQ Delayed Queue Integration
To properly handle "Auto resolving" alerts without locking up worker compute threads, we've implemented a robust event-driven pattern using RabbitMQ Dead-Letter Exchanges (DLX).

### Implementation Details
1. **Configurable Delay**: `config.yaml` now has a dedicated section for defining the DLX queue names and configuring the exact TTL (`delay_ms`, which is defaulted to 15 minutes).
2. **Message Broker Tool**: A new utility (`workflow/tools/message_broker.py`) was created using `pika` to natively declare the DLX parameters (`x-dead-letter-exchange`, `x-message-ttl`, etc.) and publish messages.
3. **Agent 3 Scheduler**: A new node (`node_agent_3_scheduler.py`) has been wired directly into the LangGraph, sitting immediately after Agent 2. 

### Execution Flow
1. **Agent 1** filters out backdated alerts.
2. **Supervisor** routes fresh alerts to Agent 2.
3. **Agent 2** uses ML to classify the alert's text.
4. **Agent 3** kicks in. If the classification is `Auto resolving`, it publishes the *entire alert payload* to the RabbitMQ wait queue. The pipeline then gracefully exits.
5. 15 minutes later, the message expires in the wait queue, shifts to the active queue via the DLX routing key.

## Delayed Queue Consumer (`consumer.py`)
To process the alerts that emerge from the delayed queue, a standalone daemon script (`consumer.py`) has been added to the root directory.

### Features
- **Environment Integration**: Securely loads RabbitMQ (`RABBITMQ_USERNAME`, `RABBITMQ_PASSWORD`) and Jenkins (`JENKINS_USERNAME`, `JENKINS_TOKEN`, `JENKINS_URL`, `JENKINS_JOB_PATH`) credentials directly from the `.env` file.
- **Queue Declaration**: Automatically declares the `dnac.alerts.delayed.q` queue and binds it to the `dnac.exchange` to capture expired messages from the DLX.
- **Jenkins Trigger**: Maps the top-level keys of the JSON alert payload into `requests.post()` query parameters to dynamically trigger the downstream Jenkins job.

> [!NOTE]
> Run the consumer daemon continuously in your environment using:
> ```bash
> python consumer.py
> ```
> It will run indefinitely, processing one message at a time (QoS prefetch count = 1) to ensure reliable delivery and acknowledgment.
