import time
from tools.database import db

class AgentHealthMonitor:
    def track(self, agent_name, employee_id, machine_id, start_time):
        duration = int((time.time() - start_time) * 1000)

        db.save("monitoring_logs", {
            "employee_id": employee_id,
            "machine_id": machine_id,
            "check_type": agent_name,
            "status": "executed",
            "response_time_ms": duration
        })
