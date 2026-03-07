import time
import yaml
import json
import getpass
import socket
import os
import traceback
from datetime import datetime
from tools.database import db
from monitors.system_monitor import system_monitor
from core.orchestrator import QuartzOrchestrator
from core.event import QuartzEvent
from core.heartbeat import HeartbeatManager
from utils.agent_loader import load_agents

def extract_json(text):
    if not text:
        return {}
    if hasattr(text, 'text'):
        text = text.text
    if isinstance(text, dict):
        return text
    text_str = str(text).strip()
    try:
        return json.loads(text_str)
    except json.JSONDecodeError:
        start = text_str.find('{')
        end = text_str.rfind('}') + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text_str[start:end])
            except:
                pass
    return {"raw_response": text_str[:500], "error": "Could not parse JSON"}

class MonitoringService:
    def __init__(self):
        self.running = False
        self.last_run = {}
        self.config = self.load_monitoring_config()
        self.global_config = self.load_global_config()
        self.orchestrator = QuartzOrchestrator()
        self.heartbeat = HeartbeatManager(self.global_config)
        self.agents = self.load_agents()
        self.table_columns = {}
        self.check_methods = {
            'network': self.check_network,
            'activity': self.check_activity,
            'compliance': self.check_compliance,
            'timekeeper': self.check_timekeeper,
            'health': self.check_health,
            'anomaly': self.check_anomaly,
            'vpn': self.check_vpn,
            'coordinator': self.check_coordinator,
            'decision': self.check_decision
        }

    def load_monitoring_config(self):
        config_path = os.path.join(os.path.dirname(__file__), "config", "monitoring_config.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            return config.get("monitoring", {})
        return {
            'network_check': 2,
            'activity_check': 3,
            'compliance_check': 4,
            'timekeeper_check': 5,
            'decision_check': 6,
            'health_check': 7,
            'anomaly_check': 8,
            'vpn_check': 9
        }

    def load_global_config(self):
        path = os.path.join(os.path.dirname(__file__), "config.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def load_agents(self):
        try:
            agents = load_agents()
            print(f"Agents loaded: {list(agents.keys())}")
            return agents
        except Exception as e:
            print(f"Failed to load agents: {e}")
            return {}

    def get_table_columns(self, table):
        if table not in self.table_columns:
            try:
                db.ensure_connection()
                db.cursor.execute(f"SHOW COLUMNS FROM {table}")
                self.table_columns[table] = [row[0] for row in db.cursor.fetchall()]
            except Exception as e:
                print(f"Failed to get columns for {table}: {e}")
                self.table_columns[table] = []
        return self.table_columns[table]

    def should_run(self, check_type):
        interval = self.config.get(f"{check_type}_check", 60)
        last = self.last_run.get(check_type, datetime.min)
        if (datetime.now() - last).total_seconds() >= interval:
            self.last_run[check_type] = datetime.now()
            return True
        return False

    def ensure_monitored_user(self):
        users = db.get_active_users()
        if users:
            return users
        current_user = getpass.getuser()
        current_machine = socket.gethostname()
        db.add_monitored_user(current_user, current_machine, is_active=True)
        return db.get_active_users()

    def safe_agent_call(self, agent, query, employee_id, machine_id, table, base_data):
        try:
            response = agent.generate_content(query)
            parsed = extract_json(response)
        except Exception as e:
            parsed = {"error": str(e), "raw_response": ""}
        for key, value in parsed.items():
            if key in base_data or key not in ['raw_response', 'error']:
                base_data[key] = value
        if 'error' in parsed:
            base_data['status'] = 'error'
            if not base_data.get('details'):
                base_data['details'] = json.dumps(parsed)
            else:
                try:
                    existing = json.loads(base_data['details'])
                    if isinstance(existing, dict):
                        existing.update(parsed)
                        base_data['details'] = json.dumps(existing)
                    else:
                        base_data['details'] = json.dumps({'error': parsed, 'original': base_data['details']})
                except:
                    base_data['details'] = json.dumps({'error': parsed, 'original': base_data['details']})
        base_data['employee_id'] = employee_id
        base_data['machine_id'] = machine_id
        allowed_columns = self.get_table_columns(table)
        filtered_data = {k: v for k, v in base_data.items() if k in allowed_columns}
        try:
            db.save(table, filtered_data)
        except Exception as e:
            print(f"Database save error in {table}: {e}")
            traceback.print_exc()
        return base_data

    def check_network(self, employee_id, machine_id):
        try:
            real_network = system_monitor.check_network()
        except Exception as e:
            real_network = {'internet_connected': False, 'issues': [str(e)]}
        query = f"Analyze network status for employee {employee_id}. Data: {json.dumps(real_network)}"
        base_data = {
            'agent_used': 'network',
            'original_query': query,
            'action': 'monitor',
            'status': 'unknown',
            'details': json.dumps({'real_network': real_network}),
            'recommendation': '',
            'vpn_access_level': 'none',
            'duration': 'N/A',
            'justification': ''
        }
        result = self.safe_agent_call(self.agents.get('network'), query, employee_id, machine_id, 'network_logs', base_data)
        if not real_network.get('internet_connected', True):
            issue = {
                'employee_id': employee_id,
                'machine_id': machine_id,
                'issue_type': 'network',
                'severity': 'high',
                'description': f"Internet disconnected. Details: {real_network.get('issues', ['Unknown'])[0]}",
                'auto_resolved': False
            }
            allowed_issue_cols = self.get_table_columns('system_issues')
            filtered_issue = {k: v for k, v in issue.items() if k in allowed_issue_cols}
            try:
                db.save('system_issues', filtered_issue)
            except Exception as e:
                print(f"Failed to save network issue: {e}")
        return result

    def check_activity(self, employee_id, machine_id):
        try:
            apps = system_monitor.check_applications()
        except Exception as e:
            apps = {'error': str(e), 'applications': []}
        query = f"Analyze application usage for employee {employee_id}. Running apps: {json.dumps(apps)}"
        base_data = {
            'agent_used': 'activity',
            'original_query': query,
            'action': 'monitor',
            'status': 'unknown',
            'details': json.dumps({'apps': apps}),
            'recommendation': '',
            'risk_level': 'low',
            'justification': ''
        }
        return self.safe_agent_call(self.agents.get('activity'), query, employee_id, machine_id, 'activity_logs', base_data)

    def check_compliance(self, employee_id, machine_id):
        query = f"Check compliance for employee {employee_id} at {datetime.now().isoformat()}"
        base_data = {
            'agent_used': 'compliance',
            'original_query': query,
            'action': 'review',
            'status': 'pending',
            'details': '',
            'recommendation': '',
            'violation_level': 'none',
            'justification': ''
        }
        return self.safe_agent_call(self.agents.get('compliance'), query, employee_id, machine_id, 'compliance_checks', base_data)

    def check_timekeeper(self, employee_id, machine_id):
        query = f"Review time tracking for employee {employee_id} at {datetime.now().isoformat()}"
        base_data = {
            'agent_used': 'timekeeper',
            'original_query': query,
            'action': 'review',
            'status': 'pending',
            'details': '',
            'recommendation': '',
            'time_correction': '0',
            'justification': ''
        }
        return self.safe_agent_call(self.agents.get('timekeeper'), query, employee_id, machine_id, 'time_entries', base_data)

    def check_health(self, employee_id, machine_id):
        try:
            health = system_monitor.check_system_health()
        except Exception as e:
            health = {'issues': [str(e)], 'cpu_usage': 0, 'memory_usage': 0, 'disk_usage': 0}
        health_data = {
            'employee_id': employee_id,
            'machine_id': machine_id,
            'check_type': 'health',
            'status': 'completed',
            'details': json.dumps(health),
            'response_time_ms': 0
        }
        allowed_health_cols = self.get_table_columns('monitoring_logs')
        filtered_health = {k: v for k, v in health_data.items() if k in allowed_health_cols}
        try:
            db.save('monitoring_logs', filtered_health)
        except Exception as e:
            print(f"Failed to save health check: {e}")
        for issue in health.get('issues', []):
            issue_data = {
                'employee_id': employee_id,
                'machine_id': machine_id,
                'issue_type': 'system',
                'severity': 'medium' if 'High' in issue else 'low',
                'description': issue,
                'auto_resolved': False
            }
            allowed_issue_cols = self.get_table_columns('system_issues')
            filtered_issue = {k: v for k, v in issue_data.items() if k in allowed_issue_cols}
            try:
                db.save('system_issues', filtered_issue)
            except Exception as e:
                print(f"Failed to save system issue: {e}")
        return health

    def check_anomaly(self, employee_id, machine_id):
        query = f"Detect anomalies for employee {employee_id} at {datetime.now().isoformat()}"
        base_data = {
            'agent_used': 'anomaly',
            'original_event': query,
            'risk_score': 0,
            'risk_level': 'low',
            'confidence': 0,
            'requires_human_review': False,
            'recommendation': ''
        }
        return self.safe_agent_call(self.agents.get('anomaly'), query, employee_id, machine_id, 'anomaly_logs', base_data)

    def check_vpn(self, employee_id, machine_id):
        query = f"Check VPN status for employee {employee_id} at {datetime.now().isoformat()}"
        base_data = {
            'agent_used': 'vpn',
            'original_event': query,
            'risk_score': 0,
            'risk_level': 'low',
            'confidence': 0,
            'requires_human_review': False,
            'recommendation': ''
        }
        return self.safe_agent_call(self.agents.get('vpn'), query, employee_id, machine_id, 'vpn_logs', base_data)

    def check_coordinator(self, employee_id, machine_id):
        query = f"Coordinate monitoring activities for employee {employee_id} at {datetime.now().isoformat()}"
        base_data = {
            'agent_used': 'coordinator',
            'original_query': query,
            'action': 'coordinate',
            'status': 'pending',
            'details': '',
            'recommendation': '',
            'justification': ''
        }
        return self.safe_agent_call(self.agents.get('coordinator'), query, employee_id, machine_id, 'coordinator_logs', base_data)

    def check_decision(self, employee_id, machine_id):
        query = f"Make decision based on monitoring data for employee {employee_id} at {datetime.now().isoformat()}"
        base_data = {
            'agent_used': 'decision',
            'original_query': query,
            'action': 'decide',
            'status': 'pending',
            'details': '',
            'recommendation': '',
            'decision': '',
            'justification': ''
        }
        return self.safe_agent_call(self.agents.get('decision'), query, employee_id, machine_id, 'decision_logs', base_data)

    def run_decision(self, employee_id, machine_id, all_checks_data):
        event = QuartzEvent(
            employee_id=employee_id,
            machine_id=machine_id,
            event_type="monitoring_cycle",
            payload=all_checks_data
        )
        try:
            return self.orchestrator.process_event(event)
        except Exception as e:
            print(f"Decision orchestration failed: {e}")
            traceback.print_exc()
            return None

    def monitoring_cycle(self):
        users = self.ensure_monitored_user()
        if not users:
            return
        for user in users:
            emp_id = user["employee_id"]
            mach_id = user["machine_id"]
            try:
                self.heartbeat.send(emp_id, mach_id)
            except Exception as e:
                print(f"Heartbeat failed for {emp_id}: {e}")
            checks_data = {}
            for check_name, method in self.check_methods.items():
                if self.should_run(check_name):
                    try:
                        checks_data[check_name] = method(emp_id, mach_id)
                    except Exception as e:
                        print(f"Check {check_name} failed for {emp_id}: {e}")
                        traceback.print_exc()
            if checks_data and self.should_run("decision"):
                self.run_decision(emp_id, mach_id, checks_data)
            time.sleep(2)

    def run_service(self):
        print("Starting Quartz AI REAL Monitoring Service")
        print(f"Check intervals: {self.config}")
        self.running = True
        try:
            initial_network = system_monitor.check_network()
            print(f"Initial Network: Internet={'connected' if initial_network.get('internet_connected') else 'disconnected'}")
        except:
            print("Initial network check failed")
        print(f"Machine ID: {system_monitor.machine_id}")
        users = self.ensure_monitored_user()
        if not users:
            print("Could not determine a user to monitor. Exiting.")
            return
        print(f"Service initialized with {len(users)} user(s)")
        print("Service running. Press Ctrl+C to stop.\n")
        cycle_count = 0
        try:
            while self.running:
                try:
                    cycle_count += 1
                    print(f"\n--- Cycle #{cycle_count} at {datetime.now()} ---")
                    self.monitoring_cycle()
                    time.sleep(self.config.get("cycle_sleep", 1))
                except KeyboardInterrupt:
                    print("\nStopping service...")
                    self.running = False
                except Exception as e:
                    print(f"Error in monitoring cycle: {e}")
                    traceback.print_exc()
                    time.sleep(60)
        finally:
            self.running = False
            print("Service stopped.")

def start_monitoring_service():
    service = MonitoringService()
    service.run_service()

if __name__ == "__main__":
    start_monitoring_service()  