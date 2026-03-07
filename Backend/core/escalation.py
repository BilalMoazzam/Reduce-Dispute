from tools.database import db

class EscalationEngine:
    def __init__(self, config):
        self.thresholds = config.get("risk_thresholds", {})

    def evaluate(self, employee_id, machine_id, risk_score, reason):
        level = None
        for name, value in self.thresholds.items():
            if risk_score >= value:
                level = name

        if level:
            db.save("system_issues", {
                "employee_id": employee_id,
                "machine_id": machine_id,
                "issue_type": "risk_escalation",
                "severity": level,
                "description": reason,
                "auto_resolved": False
            })

        return level
