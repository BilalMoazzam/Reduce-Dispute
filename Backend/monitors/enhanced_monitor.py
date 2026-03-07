import psutil
import socket
import platform
import subprocess
import time
import os
import sys
import json
import uuid
import wmi 
from datetime import datetime
import getpass
import win32api 
import win32net
import win32security

class EnhancedSystemMonitor:
    def __init__(self):
        self.system_info = self.get_system_info()
        self.user_info = self.get_user_info()
        self.monitoring_history = []
        
    def get_system_info(self):
        info = {
            "timestamp": datetime.now().isoformat(),
            "platform": platform.system(),
            "platform_version": platform.version(),
            "platform_release": platform.release(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "machine": platform.machine(),
            "hostname": socket.gethostname(),
            "fqdn": socket.getfqdn(),
            "unique_id": self.get_unique_machine_id(),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
            "os_details": {}
        }
        
        if platform.system() == "Windows":
            info["os_details"] = self.get_windows_info()
        elif platform.system() == "Linux":
            info["os_details"] = self.get_linux_info()
        elif platform.system() == "Darwin": 
            info["os_details"] = self.get_mac_info()
            
        return info
    
    def get_unique_machine_id(self):
        try:
            if platform.system() == "Windows":
                try:
                    c = wmi.WMI()
                    for system in c.Win32_ComputerSystemProduct():
                        return system.UUID
                except:
                    try:
                        import winreg
                        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
                        machine_guid = winreg.QueryValueEx(key, "MachineGuid")[0]
                        winreg.CloseKey(key)
                        return machine_guid
                    except:
                        import ctypes
                        volume_name_buffer = ctypes.create_unicode_buffer(1024)
                        file_system_name_buffer = ctypes.create_unicode_buffer(1024)
                        serial_number = ctypes.c_ulong()
                        max_component_length = ctypes.c_ulong()
                        file_system_flags = ctypes.c_ulong()
                        
                        success = ctypes.windll.kernel32.GetVolumeInformationW(
                            ctypes.c_wchar_p("C:\\"),
                            volume_name_buffer,
                            ctypes.sizeof(volume_name_buffer),
                            ctypes.byref(serial_number),
                            ctypes.byref(max_component_length),
                            ctypes.byref(file_system_flags),
                            file_system_name_buffer,
                            ctypes.sizeof(file_system_name_buffer)
                        )
                        
                        if success:
                            return str(serial_number.value)
            elif platform.system() == "Linux":
                with open("/etc/machine-id", "r") as f:
                    return f.read().strip()
            elif platform.system() == "Darwin":
                result = subprocess.run(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"], capture_output=True, text=True)
                for line in result.stdout.split("\n"):
                    if "IOPlatformUUID" in line:
                        return line.split('"')[-2]
        except:
            pass
        
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, socket.gethostname()))
    
    def get_windows_info(self):
        info = {}
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            info["product_name"] = winreg.QueryValueEx(key, "ProductName")[0]
            info["build_number"] = winreg.QueryValueEx(key, "CurrentBuildNumber")[0]
            info["release_id"] = winreg.QueryValueEx(key, "ReleaseId")[0] if "ReleaseId" in [winreg.EnumValue(key, i)[0] for i in range(winreg.QueryInfoKey(key)[1])] else "Unknown"
            winreg.CloseKey(key)
            
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            
            memory_status = MEMORYSTATUSEX()
            memory_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory_status))
            info["total_ram_gb"] = round(memory_status.ullTotalPhys / (1024**3), 2)
            
            c = wmi.WMI()
            for processor in c.Win32_Processor():
                info["cpu_name"] = processor.Name
                info["cpu_cores"] = processor.NumberOfCores
                info["cpu_logical_processors"] = processor.NumberOfLogicalProcessors
                break
            
            drives = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    drives.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent": usage.percent
                    })
                except:
                    continue
            info["disks"] = drives
            
        except Exception as e:
            info["error"] = str(e)
        
        return info
    
    def get_user_info(self):
        user = {
            "username": getpass.getuser(),
            "full_name": "",
            "domain": "",
            "sid": "",
            "groups": [],
            "login_time": "",
            "is_admin": False,
            "home_directory": os.path.expanduser("~"),
            "session_id": os.getpid()
        }
        
        try:
            if platform.system() == "Windows":
                user["full_name"] = win32api.GetUserNameEx(win32api.NameDisplay)
                
                try:
                    sid = win32security.GetTokenInformation(
                        win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32security.TOKEN_QUERY),
                        win32security.TokenUser
                    )[0]
                    user["sid"] = win32security.ConvertSidToStringSid(sid)
                    
                    user["domain"] = win32api.GetDomainName()
                except:
                    pass
                
                try:
                    import ctypes
                    user["is_admin"] = ctypes.windll.shell32.IsUserAnAdmin() != 0
                except:
                    pass
                
                user["login_time"] = datetime.fromtimestamp(psutil.Process().create_time()).isoformat()
                
            else:
                import pwd
                user_info = pwd.getpwnam(user["username"])
                user["full_name"] = user_info.pw_gecos
                user["home_directory"] = user_info.pw_dir
                
                import grp
                for group in grp.getgrall():
                    if user["username"] in group.gr_mem:
                        user["groups"].append(group.gr_name)
                
                user["is_admin"] = os.geteuid() == 0
                
                try:
                    result = subprocess.run(["who", "-u"], capture_output=True, text=True)
                    for line in result.stdout.split("\n"):
                        if user["username"] in line:
                            parts = line.split()
                            if len(parts) > 3:
                                user["login_time"] = parts[2] + " " + parts[3]
                            break
                except:
                    pass
                    
        except Exception as e:
            user["error"] = str(e)
        
        return user
    
    def check_network_advanced(self):
        result = {
            "timestamp": datetime.now().isoformat(),
            "internet_connected": False,
            "vpn_connected": False,
            "connection_method": "unknown",
            "network_interfaces": [],
            "gateway": None,
            "dns_servers": [],
            "latency_tests": {},
            "connectivity_tests": {},
            "issues": []
        }
        
        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            io_counters = psutil.net_io_counters(pernic=True)
            
            for interface, addresses in addrs.items():
                iface_info = {
                    "name": interface,
                    "status": "down",
                    "speed_mbps": 0,
                    "mtu": 1500,
                    "is_up": False,
                    "ipv4": [],
                    "ipv6": [],
                    "mac": None,
                    "bytes_sent": 0,
                    "bytes_recv": 0,
                    "packets_sent": 0,
                    "packets_recv": 0
                }
                
                if interface in stats:
                    iface_info["status"] = "up" if stats[interface].isup else "down"
                    iface_info["is_up"] = stats[interface].isup
                    iface_info["speed_mbps"] = stats[interface].speed
                    iface_info["mtu"] = stats[interface].mtu
                
                if interface in io_counters:
                    io = io_counters[interface]
                    iface_info["bytes_sent"] = io.bytes_sent
                    iface_info["bytes_recv"] = io.bytes_recv
                    iface_info["packets_sent"] = io.packets_sent
                    iface_info["packets_recv"] = io.packets_recv
                
                for addr in addresses:
                    if addr.family == socket.AF_INET:
                        iface_info["ipv4"].append({
                            "address": addr.address,
                            "netmask": addr.netmask,
                            "broadcast": addr.broadcast
                        })
                    elif addr.family == socket.AF_INET6: 
                        iface_info["ipv6"].append({
                            "address": addr.address,
                            "netmask": addr.netmask
                        })
                    elif addr.family == psutil.AF_LINK: 
                        iface_info["mac"] = addr.address
                
                vpn_keywords = ['tun', 'tap', 'ppp', 'vpn', 'wireguard', 'openvpn', 'zerotier', 'tailscale']
                if any(keyword in interface.lower() for keyword in vpn_keywords):
                    if iface_info["is_up"] and iface_info["ipv4"]:
                        result["vpn_connected"] = True
                        result["connection_method"] = "vpn"
                
                result["network_interfaces"].append(iface_info)
                
                if iface_info["is_up"]:
                    if "Wi-Fi" in interface or "WLAN" in interface:
                        result["connection_method"] = "wifi"
                    elif "Ethernet" in interface or "eth" in interface:
                        result["connection_method"] = "ethernet"
            
            test_urls = [
                ("Google DNS", "8.8.8.8", 53),
                ("Cloudflare DNS", "1.1.1.1", 53),
                ("Google HTTP", "www.google.com", 80),
                ("Cloudflare HTTP", "www.cloudflare.com", 80),
                ("Microsoft", "www.microsoft.com", 80)
            ]
            
            successful_tests = 0
            for test_name, host, port in test_urls:
                test_result = self.test_connectivity(host, port, test_name)
                result["connectivity_tests"][test_name] = test_result
                
                if test_result.get("success"):
                    successful_tests += 1
            
            result["internet_connected"] = successful_tests >= 2
            
            if not result["internet_connected"]:
                result["issues"].append("Multiple connectivity tests failed")
            
            result.update(self.get_network_config())
            
            if result["internet_connected"]:
                result["latency_tests"] = self.test_latency()
            
            return result
            
        except Exception as e:
            result["issues"].append(f"Network check error: {str(e)}")
            return result
    
    def test_connectivity(self, host, port, test_name):
        result = {
            "test": test_name,
            "host": host,
            "port": port,
            "success": False,
            "latency_ms": 0,
            "error": None,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            start_time = time.time()
            ip_address = socket.gethostbyname(host)
            dns_time = (time.time() - start_time) * 1000
            
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((ip_address, port))
            connect_time = (time.time() - start_time) * 1000
            sock.close()
            
            result["success"] = True
            result["latency_ms"] = round(dns_time + connect_time, 2)
            result["resolved_ip"] = ip_address
            
        except socket.gaierror as e:
            result["error"] = f"DNS resolution failed: {e}"
        except socket.timeout as e:
            result["error"] = f"Connection timeout: {e}"
        except ConnectionRefusedError as e:
            result["error"] = f"Connection refused: {e}"
        except Exception as e:
            result["error"] = f"Connection failed: {e}"
        
        return result
    
    def get_network_config(self):
        config = {
            "gateway": None,
            "dns_servers": [],
            "ip_config": {}
        }
        
        try:
            if platform.system() == "Windows":
                result = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
                lines = result.stdout.split("\n")
                
                current_adapter = None
                for line in lines:
                    line = line.strip()
                    
                    if "adapter" in line.lower() and ":" in line:
                        current_adapter = line.split(":")[0].strip()
                        config["ip_config"][current_adapter] = {}
                    
                    if current_adapter:
                        if "default gateway" in line.lower():
                            parts = line.split(":")
                            if len(parts) > 1:
                                config["gateway"] = parts[1].strip()
                                config["ip_config"][current_adapter]["gateway"] = config["gateway"]
                        
                        elif "dns servers" in line.lower():
                            parts = line.split(":")
                            if len(parts) > 1:
                                dns_servers = [s.strip() for s in parts[1].split(",") if s.strip()]
                                config["dns_servers"].extend(dns_servers)
                                config["ip_config"][current_adapter]["dns"] = dns_servers
                        
                        elif "ipv4 address" in line.lower() or "ip address" in line.lower():
                            parts = line.split(":")
                            if len(parts) > 1:
                                ip = parts[1].strip()
                                if "." in ip:  
                                    config["ip_config"][current_adapter]["ipv4"] = ip
                        
                        elif "subnet mask" in line.lower():
                            parts = line.split(":")
                            if len(parts) > 1:
                                config["ip_config"][current_adapter]["subnet"] = parts[1].strip()
            
            else:
                try:
                    result = subprocess.run(["route", "-n"], capture_output=True, text=True)
                    for line in result.stdout.split("\n"):
                        if "0.0.0.0" in line or "default" in line:
                            parts = line.split()
                            if len(parts) > 1:
                                config["gateway"] = parts[1]
                                break
                except:
                    pass
                
                try:
                    with open("/etc/resolv.conf", "r") as f:
                        for line in f:
                            if line.startswith("nameserver"):
                                dns = line.split()[1]
                                if dns not in config["dns_servers"]:
                                    config["dns_servers"].append(dns)
                except:
                    pass
            
            config["dns_servers"] = list(dict.fromkeys(config["dns_servers"]))
            
        except Exception as e:
            config["error"] = str(e)
        
        return config
    
    def test_latency(self):
        latency_tests = {}
        
        test_hosts = [
            ("Google DNS", "8.8.8.8"),
            ("Cloudflare DNS", "1.1.1.1"),
            ("Local Gateway", self.get_network_config().get("gateway", "192.168.1.1"))
        ]
        
        for test_name, host in test_hosts:
            if host:
                latency_tests[test_name] = self.ping_host(host)
        
        return latency_tests
    
    def ping_host(self, host):
        result = {
            "host": host,
            "success": False,
            "latency_ms": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if platform.system() == "Windows":
                cmd = ["ping", "-n", "1", "-w", "1000", host]
            else:
                cmd = ["ping", "-c", "1", "-W", "1", host]
            
            start_time = time.time()
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            elapsed = (time.time() - start_time) * 1000
            
            if process.returncode == 0:
                result["success"] = True
                result["latency_ms"] = round(elapsed, 2)
            else:
                result["error"] = f"Ping failed with code {process.returncode}"
                
        except subprocess.TimeoutExpired:
            result["error"] = "Ping timeout"
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def check_system_health_detailed(self):
        health = {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "percent": psutil.cpu_percent(interval=1),
                "cores": psutil.cpu_count(logical=False),
                "logical_cores": psutil.cpu_count(logical=True),
                "frequency_current": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                "frequency_max": psutil.cpu_freq().max if psutil.cpu_freq() else 0,
                "load_avg": psutil.getloadavg() if hasattr(psutil, "getloadavg") else []
            },
            "memory": {
                "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
                "used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
                "percent": psutil.virtual_memory().percent,
                "swap_total_gb": round(psutil.swap_memory().total / (1024**3), 2),
                "swap_used_gb": round(psutil.swap_memory().used / (1024**3), 2),
                "swap_percent": psutil.swap_memory().percent
            },
            "disk": [],
            "processes": {
                "total": len(psutil.pids()),
                "user": len([p for p in psutil.process_iter(['username']) if p.info.get('username') == self.user_info["username"]]),
                "critical": 0
            },
            "battery": None,
            "issues": []
        }
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                health["disk"].append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent": usage.percent
                })
                
                if usage.percent > 90:
                    health["issues"].append(f"High disk usage on {partition.mountpoint}: {usage.percent}%")
                    
            except:
                continue
        
        try:
            battery = psutil.sensors_battery()
            if battery:
                health["battery"] = {
                    "percent": battery.percent,
                    "power_plugged": battery.power_plugged,
                    "secsleft": battery.secsleft
                }
                
                if battery.percent < 20 and not battery.power_plugged:
                    health["issues"].append(f"Low battery: {battery.percent}%")
        except:
            pass
        
        if health["cpu"]["percent"] > 90:
            health["issues"].append(f"High CPU usage: {health['cpu']['percent']}%")
        if health["memory"]["percent"] > 90:
            health["issues"].append(f"High memory usage: {health['memory']['percent']}%")
        
        for proc in psutil.process_iter(['status']):
            try:
                if proc.info.get('status') == psutil.STATUS_ZOMBIE:
                    health["processes"]["critical"] += 1
            except:
                pass
        
        if health["processes"]["critical"] > 0:
            health["issues"].append(f"Zombie processes: {health['processes']['critical']}")
        
        return health
    
    def check_running_applications(self):
        apps = {
            "timestamp": datetime.now().isoformat(),
            "total_processes": 0,
            "user_processes": 0,
            "applications": [],
            "resource_hogs": [],
            "suspicious_processes": []
        }
        
        suspicious_keywords = ['crypt', 'miner', 'backdoor', 'rat', 'trojan', 'keylog', 'inject']
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'exe', 'cmdline']):
            try:
                pinfo = proc.info
                apps["total_processes"] += 1
                
                if pinfo.get('username') == self.user_info["username"]:
                    apps["user_processes"] += 1
                    
                    app_info = {
                        "pid": pinfo['pid'],
                        "name": pinfo['name'],
                        "cpu": pinfo.get('cpu_percent', 0),
                        "memory": pinfo.get('memory_percent', 0),
                        "exe": pinfo.get('exe', ''),
                        "cmdline": pinfo.get('cmdline', [])
                    }
                    
                    apps["applications"].append(app_info)
                    
                    if app_info["cpu"] > 50 or app_info["memory"] > 10:
                        apps["resource_hogs"].append(app_info)
                    
                    proc_name = app_info["name"].lower()
                    if any(keyword in proc_name for keyword in suspicious_keywords):
                        apps["suspicious_processes"].append(app_info)
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return apps
    
    def generate_comprehensive_report(self, employee_id):
        report = {
            "employee_id": employee_id,
            "timestamp": datetime.now().isoformat(),
            "system": self.system_info,
            "user": self.user_info,
            "network": self.check_network_advanced(),
            "system_health": self.check_system_health_detailed(),
            "applications": self.check_running_applications(),
            "overall_status": "healthy",
            "issues": [],
            "alerts": []
        }
        
        all_issues = []
        
        if not report["network"]["internet_connected"]:
            all_issues.append("NETWORK: No internet connection")
            report["alerts"].append({
                "type": "network",
                "severity": "high",
                "message": "Internet connection lost",
                "timestamp": datetime.now().isoformat()
            })
        
        if report["network"].get("issues"):
            all_issues.extend([f"NETWORK: {issue}" for issue in report["network"]["issues"]])
        
        if report["system_health"].get("issues"):
            all_issues.extend([f"SYSTEM: {issue}" for issue in report["system_health"]["issues"]])
            for issue in report["system_health"]["issues"]:
                if "High" in issue or "Low" in issue:
                    report["alerts"].append({
                        "type": "system",
                        "severity": "medium",
                        "message": issue,
                        "timestamp": datetime.now().isoformat()
                    })
        
        if report["applications"].get("suspicious_processes"):
            all_issues.append(f"SECURITY: {len(report['applications']['suspicious_processes'])} suspicious processes detected")
            report["alerts"].append({
                "type": "security",
                "severity": "high",
                "message": "Suspicious processes detected",
                "timestamp": datetime.now().isoformat()
            })
        
        report["issues"] = all_issues
        
        if all_issues:
            report["overall_status"] = "issues_detected"
        
        self.monitoring_history.append({
            "timestamp": report["timestamp"],
            "status": report["overall_status"],
            "issue_count": len(all_issues)
        })
        
        if len(self.monitoring_history) > 100:
            self.monitoring_history = self.monitoring_history[-100:]
        
        return report

enhanced_monitor = EnhancedSystemMonitor()