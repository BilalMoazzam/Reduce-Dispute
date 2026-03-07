from tools.database import db

class DepartmentRouter:
    def __init__(self, config):
        self.map = config.get("department_mapping", {})

    def route(self, agent_name, employee_id, machine_id, message):
        department = self.map.get(agent_name)
        if not department:
            return

        db.save("system_issues", {
            "employee_id": employee_id,
            "machine_id": machine_id,
            "issue_type": agent_name,
            "severity": "notify",
            "description": message,
            "auto_resolved": False,
            "resolved_by": department
        })
