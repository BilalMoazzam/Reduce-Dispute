from google.adk import Agent
from agents.observer_agent import observer_agent
from agents.reasoner_agent import reasoner_agent
from agents.self_healing_agent import self_healing_agent
from google.adk.tools import FunctionTool

def coordinate():
    obs = observer_agent.tools[0].func()
    analysis = reasoner_agent.tools[0].func(obs)
    action = self_healing_agent.tools[0].func(analysis)
    return {
        "observer": obs,
        "analysis": analysis,
        "action": action
    }


coordinator_tool = FunctionTool(coordinate)

coordinator_agent = Agent(
    name="coordinator_agent",
    instruction="Orchestrate all agents",
    tools=[coordinator_tool]
)
