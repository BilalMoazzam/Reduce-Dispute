from google.adk import Agent
from google.adk.tools import FunctionTool

def human_gate(data):

    analysis = data.get("analysis", {})
    action = data.get("action", {})

    severity = analysis.get("severity", "LOW")
    action_status = action.get("status", "NO_ACTION")

    approval_required = False
    reason = "Auto-approved"

    # High severity always needs approval
    if severity == "HIGH":
        approval_required = True
        reason = "High severity detected"

    # If system blocked something
    elif action_status == "BLOCKED":
        approval_required = True
        reason = "Automated action blocked"

    return {
        "approval_required": approval_required,
        "reason": reason
    }


human_gate_tool = FunctionTool(human_gate)

human_gate_agent = Agent(
    name="human_gate_agent",
    instruction="""
    Evaluate risk and decide if human approval is required.
    """,
    tools=[human_gate_tool]
)
