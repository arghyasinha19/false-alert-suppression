import yaml
import os
from workflow.tools.message_broker import RabbitMQBroker

def test():
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "config.yaml",
    )
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        
    rmq_config = config.get("rabbitmq", {})
    print("rmq_config:", rmq_config)
    broker = RabbitMQBroker(rmq_config)
    print("delayed_config:", broker.delayed_config)
    
    wait_queue = broker.delayed_config.get("wait_queue", "dnac.alerts.wait.q")
    print("Wait Queue used by broker:", wait_queue)

if __name__ == "__main__":
    test()
