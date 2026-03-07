from models.azure_llm import AzureLLM

class VPNAgent:
    def __init__(self):
        self.llm = AzureLLM()

    def evaluate(self, event):
        prompt = f"""
        You are a VPN compliance validation agent.
        Detect if VPN absence during shift creates compliance risk.
        Return JSON:
        {{
            "risk_score": int,
            "risk_level": "low|medium|high",
            "confidence": int,
            "requires_human_review": true|false,
            "recommendation": str
        }}

        Event:
        {event.to_dict()}
        """

        response = self.llm.generate(prompt)
        return response
