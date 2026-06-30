import logging
import os
from logging.handlers import TimedRotatingFileHandler

def setup_file_logger(
    name: str = "consumer",
    log_file: str = None,
    level: str = None,
    when: str = "midnight",
    backup_count: int = 14,
    utc: bool = False
) -> logging.Logger:
    """
    Creates a logger that writes to a daily rotating log file.
    
    Rotation:
      - Rotates at midnight by default (when="midnight")
      - Keeps backup_count days of logs
      - utc=False rotates based on local time of the host (set utc=True for UTC)
      
    Environment variables supported:
      - LOG_LEVEL (default INFO)
      - LOG_FILE (default ./logs/consumer.log)
      - LOG_BACKUP_COUNT (default 14)
      - LOG_TO_CONSOLE (default true)
      - LOG_ROTATE_UTC (default false)
    """
    log_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    log_path = log_file or os.getenv("LOG_FILE", "./logs/consumer.log")
    
    backup_count = int(os.getenv("LOG_BACKUP_COUNT", str(backup_count)))
    utc = os.getenv("LOG_ROTATE_UTC", str(utc)).lower() == "true"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    logger.propagate = False # prevents duplicate logs via root logger
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
        
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Daily rotation handler
    file_handler = TimedRotatingFileHandler(
        filename=log_path,
        when=when,          # "midnight" for daily
        interval=1,         # every 1 day
        backupCount=backup_count,
        encoding="utf-8",
        utc=utc
    )
    
    # This makes rotated files look like: consumer.log.2026-02-11
    file_handler.suffix = "%Y-%m-%d"
    
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    
    # Optional console logging
    if os.getenv("LOG_TO_CONSOLE", "true").lower() == "true":
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(fmt)
        logger.addHandler(console_handler)
        
    logger.info(
        "Logger initialized. level=%s file=%s rotate=%s backupCount=%d utc=%s",
        log_level, log_path, when, backup_count, utc
    )
    return logger
