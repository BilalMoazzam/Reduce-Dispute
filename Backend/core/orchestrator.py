from utils.agent_loader import load_agents
from core.policy_engine import PolicyEngine
from core.fallback_engine import FallbackEngine
from core.escalation import EscalationEngine
from core.department_router import DepartmentRouter
from core.agent_health import AgentHealthMonitor
from tools.database import db
import json
import os
from datetime import datetime

def extract_json(text):
    if not text:
        return {}
    if hasattr(text, "text"):
        text = text.text
    if isinstance(text, dict):
        return text
    text_str = str(text).strip()
    try:
        return json.loads(text_str)
    except:
        start = text_str.find("{")
        end = text_str.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text_str[start:end])
            except:
                pass
    return {"raw_response": text_str[:500], "error": "invalid_json"}

class QuartzOrchestrator:
    def __init__(self):
        self.config = self.load_config()
        self.agents = load_agents()
        self.policy = PolicyEngine()
        self.fallback = FallbackEngine()
        self.escalation = EscalationEngine(self.config)
        self.router = DepartmentRouter(self.config)
        self.health = AgentHealthMonitor()

    def load_config(self):
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def process_event(self, event, existing_results=None):
        outputs = []

        for name, agent in self.agents.items():
            try:
                raw = agent.evaluate(event) if hasattr(agent, "evaluate") else agent.generate_content(event.to_dict())
                parsed = extract_json(raw)
            except Exception as e:
                parsed = {
                    "risk_score": self.config.get("llm_failure_risk_score", 50),
                    "recommendation": str(e),
                    "requires_human_review": True
                }

            self.health.track(name, event.employee_id, event.machine_id, datetime.now().timestamp())
            self.router.route(name, event.employee_id, event.machine_id, json.dumps(parsed))

            outputs.append(parsed)

        try:
            final_decision = self.policy.merge(outputs)
        except:
            final_decision = self.fallback.evaluate(outputs)

        self.escalation.evaluate(
            event.employee_id,
            event.machine_id,
            final_decision.get("risk_score", 0),
            json.dumps(final_decision)
        )

        db.save("decisions", {
            "employee_id": event.employee_id,
            "machine_id": event.machine_id,
            "decision": final_decision.get("final_status"),
            "confidence": final_decision.get("risk_score"),
            "reason": json.dumps([o.get("recommendation", "") for o in outputs]),
            "recommendations": json.dumps(final_decision.get("recommendations")),
            "conditions": event.event_type,
            "agent_data": json.dumps(outputs)
        })

        return final_decision
