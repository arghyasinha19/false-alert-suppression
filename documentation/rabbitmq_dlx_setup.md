# RabbitMQ Delayed Queue Setup Guide

Even though the Python scripts (`message_broker.py` and `consumer.py`) are written to automatically declare these queues upon connection, it is highly recommended to configure them manually in production. Service accounts (like `svc_rabbitmq_noops_consumer`) often lack the `configure` permission needed to create queues on the fly.

Here is the exact step-by-step process to set up the Delayed Queue pattern via the **RabbitMQ Management UI**.

> [!IMPORTANT]
> Ensure you have selected the correct virtual host (`/noops_automation`) in the top-right corner of the RabbitMQ UI before beginning.

### Step 1: Create the Target Exchange
This exchange is responsible for routing the "expired" delayed messages into the final consumer queue.
1. Navigate to the **Exchanges** tab.
2. Scroll down to **Add a new exchange**.
3. **Name:** `dnac.exchange`
4. **Type:** `direct`
5. **Durability:** `Durable`
6. Click **Add exchange**.

### Step 2: Create the Consumer Queue
This is the final queue where messages land *after* the 15-minute wait is over. Your `consumer.py` script listens to this queue.
1. Navigate to the **Queues** tab.
2. Scroll down to **Add a new queue**.
3. **Name:** `dnac.alerts.delayed.q`
4. **Durability:** `Durable`
5. Click **Add queue**.

### Step 3: Bind the Consumer Queue to the Exchange
1. Still on the **Queues** tab, click on the name of the newly created `dnac.alerts.delayed.q` to enter its details page.
2. Scroll down to **Bindings**.
3. **From exchange:** `dnac.exchange`
4. **Routing key:** `dnac.alerts.delayed`
5. Click **Bind**.

### Step 4: Create the Wait (Delay) Queue
This is the "holding pen". Messages are sent here first, sit for 15 minutes, and then are rejected (dead-lettered) to the exchange we created in Step 1.
1. Navigate to the **Queues** tab.
2. Scroll down to **Add a new queue**.
3. **Name:** `dnac.alerts.wait.q`
4. **Durability:** `Durable`
5. Expand the **Arguments** section to add the Dead-Letter properties:
   - Add argument: `x-dead-letter-exchange` (String) = `dnac.exchange`
   - Add argument: `x-dead-letter-routing-key` (String) = `dnac.alerts.delayed`
   - Add argument: `x-message-ttl` (Number) = `900000` *(This is 15 minutes in milliseconds)*
6. Click **Add queue**.

> [!TIP]
> You will notice an orange `DLX`, `DLK`, and `TTL` badge next to `dnac.alerts.wait.q` in the Queues list. This confirms you have successfully configured the delay mechanism!

### How it Works Together
When the LangGraph pipeline finishes:
1. Agent 3 publishes the alert directly to `dnac.alerts.wait.q`.
2. It sits there with no consumers.
3. After 15 minutes (`900000` ms), RabbitMQ forcefully evicts the message.
4. Because of the DLX arguments, the message isn't deleted—it is forwarded to `dnac.exchange` with the routing key `dnac.alerts.delayed`.
5. The exchange routes it into `dnac.alerts.delayed.q`.
6. Your `consumer.py` script immediately picks it up and triggers Jenkins!
