import json
import datetime

def validate_agent_response(response_text):
    try:
        response_data = json.loads(str(response_text))
        required_fields = ["action", "status", "details"]
        
        for field in required_fields:
            if field not in response_data:
                return False, f"Missing required field: {field}"
        
        return True, response_data
    except json.JSONDecodeError:
        return False, "Invalid JSON response"
    except Exception as e:
        return False, f"Error: {str(e)}"

def format_monitor_response(monitor_data, agent_name):
    if isinstance(monitor_data, dict):
        monitor_data["agent_used"] = agent_name
        monitor_data["timestamp"] = datetime.now().isoformat()
        return monitor_data
    return {
        "agent_used": agent_name,
        "action": "monitor",
        "status": "error",
        "details": "Invalid monitor response"
    }