import mysql.connector
from datetime import datetime
import json
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'quartz')
        }
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = mysql.connector.connect(**self.config)
            self.cursor = self.conn.cursor()
            return True
        except mysql.connector.Error as e:
            print(f"Database connection error: {e}")
            return False

    def ensure_connection(self):
        try:
            self.cursor.execute("SELECT 1")
            self.cursor.fetchall()
        except (mysql.connector.Error, AttributeError):
            self.close()
            return self.connect()
        return True

    def save(self, table, data):
        if not data:
            print(f"Warning: No data provided for {table}, skipping save.")
            return None

        if not self.ensure_connection():
            print(f"Could not connect to save to {table}")
            return None

        try:
            processed_data = {}
            for key, value in data.items():
                if isinstance(value, datetime):
                    processed_data[key] = value.isoformat()
                elif isinstance(value, (dict, list)):
                    processed_data[key] = json.dumps(value)
                elif value is None:
                    processed_data[key] = None
                else:
                    processed_data[key] = value


            columns = ', '.join(processed_data.keys())
            placeholders = ', '.join(['%s'] * len(processed_data))
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

            values = list(processed_data.values())

            self.cursor.execute(sql, tuple(values))
            self.conn.commit()
            row_id = self.cursor.lastrowid

            print(f"Saved to {table} (ID: {row_id})")
            return row_id

        except mysql.connector.Error as e:
            print(f"Database save error for {table}: {e}")
            print(f"Data keys: {list(data.keys())}")
            print(f"SQL: {sql}")
            print(f"Values: {values}")
            raise
        finally:
            self.close()

    def get_active_users(self):
        if not self.ensure_connection():
            return []
        try:
            self.cursor.execute(
                "SELECT employee_id, machine_id FROM monitored_users WHERE is_active = TRUE"
            )
            rows = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Error getting users: {e}")
            return []
        finally:
            self.close()

    def add_monitored_user(self, employee_id, machine_id, is_active=True):
        query = """
            INSERT INTO monitored_users (employee_id, machine_id, is_active)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE is_active = %s
        """
        if not self.ensure_connection():
            return False
        try:
            self.cursor.execute(query, (employee_id, machine_id, is_active, is_active))
            self.conn.commit()
            print(f"Added/updated user {employee_id} to monitoring")
            return True
        except Exception as e:
            print(f"Error adding monitored user: {e}")
            return False
        finally:
            self.close()

    def close(self):
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None

db = Database()