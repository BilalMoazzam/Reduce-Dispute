from models.azure_llm import AzureLLM

class AnomalyAgent:
    def __init__(self):
        self.llm = AzureLLM()

    def evaluate(self, event):
        prompt = f"""
        You are a workforce behavioral anomaly detection agent.
        Analyze the event and return JSON:
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
