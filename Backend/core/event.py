from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime

@dataclass
class QuartzEvent:
    employee_id: str
    machine_id: str
    event_type: str
    payload: Dict[str, Any]
    timestamp: datetime = datetime.utcnow()

    def to_dict(self):
        return {
            "employee_id": self.employee_id,
            "machine_id": self.machine_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat()
        }
