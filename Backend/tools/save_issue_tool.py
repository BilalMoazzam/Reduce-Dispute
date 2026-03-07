from google.adk.tools import FunctionTool
from tools.db import get_db
from datetime import datetime

def save_issue(shift_id, agent_name, issue_type, severity, score, desc):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO issues
        (shift_id, agent_name, issue_type, severity, dispute_score, description, detected_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (shift_id, agent_name, issue_type, severity, score, desc, datetime.now()))
    db.commit()

    issue_id = cursor.lastrowid

    cursor.close()
    db.close()
    return {
            "status": "issue_saved",
            "issue_id": issue_id
            }


save_issue_tool = FunctionTool(save_issue)

