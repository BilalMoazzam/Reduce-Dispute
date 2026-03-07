import psutil
from google.adk import Agent
from google.adk.tools import FunctionTool

import psutil
import win32gui

def get_active_window():
    try:
        return win32gui.GetWindowText(win32gui.GetForegroundWindow())
    except:
        return "Unknown"

def get_vpn_status():
    # Simple check: look for adapter name containing VPN
    for interface, addrs in psutil.net_if_addrs().items():
        if "vpn" in interface.lower():
            return "connected"
    return "unconnected"


def system_monitor():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    active_window = get_active_window()
    vpn = get_vpn_status()


    return {
        "cpu": cpu,
        "ram": ram,
        "disk": disk,
        "vpn": vpn,
        "active_window": active_window
    }


system_monitor_tool = FunctionTool(system_monitor)


observer_agent = Agent(
    name="observer_agent",
    instruction="""
    Monitor system and report facts only.
    Do not analyze or decide.
    """,
    tools=[system_monitor_tool]
)
