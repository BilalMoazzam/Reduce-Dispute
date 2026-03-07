import requests
from datetime import datetime
from tools.database import db

class HeartbeatManager:
    def __init__(self, config):
        self.server_url = config.get("heartbeat_url")
        self.timeout = config.get("heartbeat_timeout", 5)

    def send(self, employee_id, machine_id):
        payload = {
            "employee_id": employee_id,
            "machine_id": machine_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        status = "online"

        if self.server_url:
            try:
                requests.post(self.server_url, json=payload, timeout=self.timeout)
            except:
                status = "offline"

        db.save("device_heartbeats", {
            "employee_id": employee_id,
            "machine_id": machine_id,
            "status": status
        })

        return status
