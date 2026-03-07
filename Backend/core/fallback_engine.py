class FallbackEngine:
    def evaluate(self, agent_outputs):
        risk = 0
        reasons = []
        for output in agent_outputs:
            if isinstance(output, dict):
                risk += int(output.get("risk_score", 0))
                reasons.append(output.get("recommendation", ""))
        risk = min(risk, 100)
        status = "approved"
        if risk > 50:
            status = "pending"
        if risk > 80:
            status = "critical"
        return {
            "final_status": status,
            "risk_score": risk,
            "recommendations": reasons
        }
