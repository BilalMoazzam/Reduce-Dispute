from agents.coordinator_agent import coordinator_tool
from agents.human_gate_agent import human_gate_tool
from tools.save_shift_tool import save_shift_tool
from tools.save_issue_tool import save_issue_tool
from tools.save_action_tool import save_action_tool

# 1️⃣ Start Shift
shift = save_shift_tool.func("EMP001")
shift_id = shift["shift_id"]

# 2️⃣ Run System
result = coordinator_tool.func()
print(result)
# 3️⃣ Save Issue
issue = result["analysis"]
issue_result = save_issue_tool.func(
    shift_id,
    "ReasonerAgent",
    issue["issue"],
    issue["severity"],
    issue["score"],
    issue["description"]
)

# After self-healing
issue_id = issue_result["issue_id"] 
action_result = result["action"]

save_action_tool.func(
    issue_id= issue_id,  # yahan real issue_id use ho rahi
    action_by="SELF_HEALING",
    action_taken=action_result.get("action"),
    action_status=action_result.get("status", "SUCCESS")
)

# 4️⃣ Human Gate
approval = human_gate_tool.func(result)

print("FINAL OUTPUT:", approval)
