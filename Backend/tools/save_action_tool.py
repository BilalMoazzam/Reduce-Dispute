from google.adk.tools import FunctionTool
from tools.db import get_db
from datetime import datetime

def save_action(issue_id, action_by, action_taken, action_status):
    """
    Save action taken on an issue to the database
    """

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            INSERT INTO actions
            (issue_id, action_by, action_taken, action_status, action_time)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            issue_id,
            action_by,
            action_taken,
            action_status,
            datetime.now()
        ))

        db.commit()

        # Get the last inserted ID from the DB
        action_id = cursor.lastrowid

    except Exception as e:
        db.rollback()
        cursor.close()
        db.close()
        return {
            "status": "failed",
            "error": str(e)
        }

    cursor.close()
    db.close()

    # Return real values
    return {
        "status": "action_saved",
        "issue_id": issue_id,
        "action_id": action_id,
        "action": action_taken
    }

save_action_tool = FunctionTool(save_action)
