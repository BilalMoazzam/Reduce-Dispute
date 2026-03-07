import yaml

class PolicyEngine:
    def __init__(self, config_path='config/policy_rules.yaml'):
        with open(config_path, 'r') as f:
            self.rules = yaml.safe_load(f)['rules']

    def merge(self, agent_outputs):
        highest_risk = 0
        requires_review = False
        recommendations = []
        final_status = "approved"

        for output in agent_outputs:
            if not isinstance(output, dict):
                continue
            risk = output.get("risk_score", 0)
            if risk > highest_risk:
                highest_risk = risk
            if output.get("requires_human_review"):
                requires_review = True
            rec = output.get("recommendation")
            if rec:
                recommendations.append(rec)

            for rule in self.rules:
                if "risk_score > 70" in rule['condition'] and output.get("risk_score", 0) > 70:
                    final_status = rule['action']
                if "risk_level == 'high'" in rule['condition'] and output.get("risk_level") == 'high':
                    final_status = rule['action']
                if "requires_human_review == True" in rule['condition'] and output.get("requires_human_review"):
                    final_status = rule['action']

        if highest_risk > 70:
            final_status = "rejected"
        if requires_review:
            final_status = "pending"

        return {
            "final_status": final_status,
            "risk_score": highest_risk,
            "recommendations": recommendations
        }