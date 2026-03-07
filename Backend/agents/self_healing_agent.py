from google.adk import Agent
from google.adk.tools import FunctionTool
import subprocess
import os
import psutil
import win32gui


def get_active_window_process():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32gui.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return process.name()
    except:
        return None


def is_cisco_cli_installed():
    result = subprocess.run(
        ["where", "vpncli"],
        capture_output=True,
        text=True,
        shell=True
    )
    return result.returncode == 0


def heal(issue):

    severity = issue.get("severity", "LOW")
    vpn_status = issue.get("vpn", "unknown")

    action_taken = "none"
    status = "NO_ACTION"

    try:

        # HIGH severity → block immediately
        if severity == "HIGH":
            return {
                "action": "manual_intervention_required",
                "status": "BLOCKED"
            }

        # MEDIUM severity → restart active app
        if severity == "MEDIUM":
            active_process = get_active_window_process()

            if active_process:
                os.system(f"taskkill /IM {active_process} /F")
                action_taken = f"restart_{active_process}"
                status = "SUCCESS"

        # VPN handling (enterprise safe)
        if vpn_status.lower() == "unconnected":

            if not is_cisco_cli_installed():
                return {
                    "action": "vpn_cli_not_installed",
                    "status": "BLOCKED"
                }

            # If CLI existed, here we would reconnect
            # But since not installed → blocked
            action_taken = "vpn_requires_manual_connect"
            status = "BLOCKED"

    except Exception as e:
        status = f"FAILED: {str(e)}"

    return {
        "action": action_taken,
        "status": status
    }


self_healing_tool = FunctionTool(heal)

self_healing_agent = Agent(
    name="self_healing_agent",
    instruction="Auto-fix safe issues. Block if VPN automation not supported.",
    tools=[self_healing_tool]
)
