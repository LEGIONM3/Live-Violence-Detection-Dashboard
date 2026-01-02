import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AlertManager:
    def __init__(self):
        self.services = {}

    async def configure_service(self, name: str, config: Dict[str, Any]):
        logger.info(f"Configuring alert service: {name}")
        self.services[name] = {"config": config, "status": "active"}

    async def cleanup(self):
        self.services = {}

    def get_service_status(self):
        return self.services

    async def send_alert(self, message: str):
        logger.info(f"Sending alert: {message}")
        # Mock sending
        pass

alert_manager = AlertManager()
