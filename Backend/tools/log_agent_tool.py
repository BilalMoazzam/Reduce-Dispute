import mysql.connector
from tools.db import get_connection

def log_agent(agent_name, level, message):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO agent_logs (agent_name, log_level, message)
            VALUES (%s, %s, %s)
        """

        cursor.execute(query, (agent_name, level, message))
        conn.commit()

        cursor.close()
        conn.close()

    except Exception as e:
        print("Logging Error:", e)
