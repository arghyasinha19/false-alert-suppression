import smtplib
from email.message import EmailMessage
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class EmailClient:
    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get("enabled", False)
        self.smtp_host = config.get("smtp_host", "localhost")
        self.smtp_port = config.get("smtp_port", 25)
        self.sender_address = config.get("sender_address", "noreply@example.com")
        self.dl_address = config.get("dl_address", "")
        
    def send_email(self, subject: str, body: str) -> bool:
        if not self.enabled:
            logger.info("Email notifications are disabled in config.")
            return False
            
        if not self.dl_address:
            logger.warning("No DL address configured for email notifications.")
            return False
            
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = self.sender_address
        msg["To"] = self.dl_address
        
        try:
            logger.info(f"Sending email '{subject}' to {self.dl_address} via {self.smtp_host}:{self.smtp_port}")
            # Use a short timeout to prevent hanging the workflow
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.send_message(msg)
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
