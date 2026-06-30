import os
import sys
import logging

def configure_logging(level=logging.INFO):
    """
    Configures the root logger to write to a unified flow log, a dedicated error log,
    and standard output. This captures the entire agentic flow.
    """
    # Ensure logs directory exists at the root of the project
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers to prevent duplicate logs if called multiple times
    logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z"
    )

    # 1. Main Agentic Flow Log (INFO and above)
    flow_log_path = os.path.join(log_dir, "agentic_flow.log")
    flow_handler = logging.FileHandler(flow_log_path, mode='a')
    flow_handler.setLevel(logging.INFO)
    flow_handler.setFormatter(formatter)
    logger.addHandler(flow_handler)

    # 2. Separate Error Log (ERROR only)
    error_log_path = os.path.join(log_dir, "error.log")
    error_handler = logging.FileHandler(error_log_path, mode='a')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    # 3. Console Output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
