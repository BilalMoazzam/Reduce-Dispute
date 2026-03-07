from google.adk.tools import FunctionTool
from tools.db import get_db
from datetime import datetime

def save_shift(user_id: str):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO shifts (user_id, shift_date, shift_start, approval_status)
        VALUES (%s, CURDATE(), %s, 'PENDING')
    """, (user_id, datetime.now()))
    db.commit()
    shift_id = cur.lastrowid
    cur.close()
    db.close()
    return {"shift_id": shift_id}

save_shift_tool = FunctionTool(save_shift)
