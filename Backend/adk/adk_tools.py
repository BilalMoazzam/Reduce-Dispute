from core.orchestrator import QuartzOrchestrator
from core.event import QuartzEvent

orchestrator = QuartzOrchestrator()

def evaluate_employee_event(employee_id: str, machine_id: str, event_type: str, payload: dict):
    event = QuartzEvent(
        employee_id=employee_id,
        machine_id=machine_id,
        event_type=event_type,
        payload=payload
    )
    return orchestrator.process_event(event)
