import psutil
import socket
import platform
import subprocess
import time
from datetime import datetime
import json

class SystemMonitor:
    def __init__(self):
        self.machine_id = self.get_machine_id()
    
    def get_machine_id(self):
        try:
            if platform.system() == "Windows":
                try:
                    import wmi
                    c = wmi.WMI()
                    for system in c.Win32_ComputerSystemProduct():
                        return system.UUID
                except:
                    pass
            return socket.gethostname()
        except:
            return platform.node() or "UNKNOWN"

    def check_network(self):
        result = {
            "timestamp": datetime.now().isoformat(),
            "internet_connected": False,
            "vpn_connected": False,
            "latency_ms": 0,
            "network_interfaces": [],
            "issues": [],
            "public_ip": None
        }
        
        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            
            for interface, addresses in addrs.items():
                iface_info = {
                    "name": interface,
                    "status": "down",
                    "ipv4": [],
                    "ipv6": [],
                    "mac": None
                }
                
                if interface in stats:
                    iface_info["status"] = "up" if stats[interface].isup else "down"
                
                for addr in addresses:
                    if addr.family == socket.AF_INET:
                        iface_info["ipv4"].append(addr.address)
                        if addr.address and addr.address != "127.0.0.1":
                            result["internet_connected"] = True
                    elif addr.family == socket.AF_INET6:
                        iface_info["ipv6"].append(addr.address)
                    elif addr.family == psutil.AF_LINK:
                        iface_info["mac"] = addr.address
                
                vpn_keywords = ['tun', 'tap', 'ppp', 'vpn', 'wireguard', 'openvpn']
                if any(keyword in interface.lower() for keyword in vpn_keywords):
                    if iface_info["status"] == "up":
                        result["vpn_connected"] = True
                
                result["network_interfaces"].append(iface_info)
            
            try:
                import urllib.request
                with urllib.request.urlopen("http://www.google.com", timeout=3) as response:
                    result["internet_connected"] = True
                    
                try:
                    with urllib.request.urlopen("https://api.ipify.org", timeout=2) as response:
                        result["public_ip"] = response.read().decode('utf-8')
                except:
                    pass
                    
            except:
                result["issues"].append("No internet connection")
                result["internet_connected"] = False
            
            return result
            
        except Exception as e:
            result["issues"].append(f"Network check error: {str(e)}")
            return result
    
    def check_system_health(self):
        result = {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent if platform.system() != "Windows" else psutil.disk_usage('C:\\').percent,
            "running_processes": len(psutil.pids()),
            "uptime": time.time() - psutil.boot_time(),
            "issues": []
        }
        
        if result["cpu_usage"] > 90:
            result["issues"].append(f"High CPU usage: {result['cpu_usage']}%")
        if result["memory_usage"] > 90:
            result["issues"].append(f"High memory usage: {result['memory_usage']}%")
        if result["disk_usage"] > 90:
            result["issues"].append(f"High disk usage: {result['disk_usage']}%")
        
        return result
    
    def check_applications(self, required_apps=None):
        if required_apps is None:
            required_apps = ["chrome", "firefox", "outlook", "teams", "zoom"]
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "running_apps": [],
            "missing_apps": [],
            "all_apps_running": True
        }
        
        try:
            running_processes = []
            for proc in psutil.process_iter(['name', 'exe']):
                try:
                    proc_name = proc.info['name'].lower() if proc.info['name'] else ""
                    running_processes.append(proc_name)
                except:
                    continue
            
            result["running_apps"] = running_processes
            
            for app in required_apps:
                app_running = False
                for proc in running_processes:
                    if app.lower() in proc.lower():
                        app_running = True
                        break
                
                if not app_running:
                    result["missing_apps"].append(app)
                    result["all_apps_running"] = False
            
            return result
            
        except Exception as e:
            result["issues"] = [f"Application check error: {str(e)}"]
            return result
    
    def generate_report(self, employee_id):
        report = {
            "employee_id": employee_id,
            "machine_id": self.machine_id,
            "timestamp": datetime.now().isoformat(),
            "network": self.check_network(),
            "system_health": self.check_system_health(),
            "applications": self.check_applications(),
            "overall_status": "healthy",
            "issues": []
        }
        
        all_issues = []
        all_issues.extend(report["network"].get("issues", []))
        all_issues.extend(report["system_health"].get("issues", []))
        all_issues.extend(report["applications"].get("missing_apps", []))
        
        report["issues"] = all_issues
        
        if all_issues:
            report["overall_status"] = "issues_detected"
        
        return report

system_monitor = SystemMonitor()