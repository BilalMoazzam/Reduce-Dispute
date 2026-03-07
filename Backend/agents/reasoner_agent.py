from google.adk import Agent
from google.adk.tools import FunctionTool

def analyze(obs: dict):
    """
    Analyze system metrics and generate issue info with severity and score.
    """
    issue_type = "System Load"
    score = 0
    severity = "LOW"

    cpu = obs.get("cpu", 0)
    ram = obs.get("ram", 0)
    vpn = obs.get("vpn", "unknown")

    # CPU Severity
    if cpu >= 85:
        severity = "HIGH"
        score += 10
    elif cpu >= 70:
        if severity != "HIGH":
            severity = "MEDIUM"
        score += 5

    # RAM Severity
    if ram >= 85:
        severity = "HIGH"
        score += 10
    elif ram >= 75:
        if severity != "HIGH":
            severity = "MEDIUM"
        score += 5

    # VPN check
    if vpn.lower() == "unconnected":
        if severity != "HIGH":
            severity = "MEDIUM"
        score += 3

    description = f"CPU {cpu}%, RAM {ram}%, VPN {vpn}"

    return {
    "issue": issue_type,
    "severity": severity,
    "score": score,
    "vpn": vpn,
    "description": description
}


# Wrap in FunctionTool
reasoner_tool = FunctionTool(analyze)

reasoner_agent = Agent(
    name="reasoner_agent",
    instruction="Analyze observer data and generate risk score for self-healing",
    tools=[reasoner_tool]
)
