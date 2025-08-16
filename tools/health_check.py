#!/usr/bin/env python3
"""
Health Check Tool

Performs comprehensive health checks on MCP Jive system components.
"""

import sys
import os
import time
import psutil
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# Add the src directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def main():
    parser = argparse.ArgumentParser(description="Perform MCP Jive health checks")
    parser.add_argument("--quick", "-q", action="store_true",
                       help="Perform quick health check only")
    parser.add_argument("--detailed", "-d", action="store_true",
                       help="Perform detailed health check")
    parser.add_argument("--system", "-s", action="store_true",
                       help="Check system resources")
    parser.add_argument("--database", "-db", action="store_true",
                       help="Check database health")
    parser.add_argument("--dependencies", "-deps", action="store_true",
                       help="Check Python dependencies")
    parser.add_argument("--all", "-a", action="store_true",
                       help="Perform all health checks")
    parser.add_argument("--json", action="store_true",
                       help="Output results in JSON format")
    
    args = parser.parse_args()
    
    if args.all:
        args.system = args.database = args.dependencies = args.detailed = True
    elif not any([args.quick, args.detailed, args.system, args.database, args.dependencies]):
        args.quick = True
    
    checker = HealthChecker(json_output=args.json)
    
    try:
        if args.quick or args.detailed:
            checker.check_basic_health()
        
        if args.system or args.detailed:
            checker.check_system_resources()
        
        if args.database or args.detailed:
            checker.check_database_health()
        
        if args.dependencies or args.detailed:
            checker.check_dependencies()
        
        if args.detailed:
            checker.check_file_permissions()
            checker.check_network_connectivity()
        
        checker.print_summary()
        return 0 if checker.is_healthy() else 1
        
    except Exception as e:
        if args.json:
            import json
            print(json.dumps({"error": str(e), "healthy": False}))
        else:
            print(f"❌ Health check failed: {e}")
        return 1

class HealthChecker:
    def __init__(self, json_output: bool = False):
        self.json_output = json_output
        self.results: Dict[str, Dict] = {}
        self.overall_healthy = True
        
    def log(self, category: str, check: str, status: str, message: str = "", details: Dict = None):
        """Log a health check result"""
        if category not in self.results:
            self.results[category] = {}
        
        self.results[category][check] = {
            "status": status,
            "message": message,
            "details": details or {}
        }
        
        if status == "FAIL":
            self.overall_healthy = False
        
        if not self.json_output:
            icon = "✅" if status == "PASS" else "⚠️" if status == "WARN" else "❌"
            print(f"{icon} {category} - {check}: {status}")
            if message:
                print(f"   {message}")
    
    def check_basic_health(self):
        """Perform basic health checks"""
        if not self.json_output:
            print("\n🔍 Basic Health Checks")
            print("-" * 30)
        
        # Check Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if sys.version_info >= (3, 8):
            self.log("Basic", "Python Version", "PASS", f"Python {python_version}")
        else:
            self.log("Basic", "Python Version", "FAIL", f"Python {python_version} (requires 3.8+)")
        
        # Check project structure
        required_dirs = ["src", "scripts", "tests"]
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            if dir_path.exists():
                self.log("Basic", f"{dir_name} Directory", "PASS", f"Found at {dir_path}")
            else:
                self.log("Basic", f"{dir_name} Directory", "FAIL", f"Missing directory: {dir_path}")
        
        # Check main entry points
        entry_points = {
            "mcp-server.py": project_root / "mcp-server.py",
            "main.py": project_root / "src" / "main.py",
            "unified CLI": project_root / "bin" / "mcp-jive"
        }
        
        for name, path in entry_points.items():
            if path.exists():
                self.log("Basic", f"{name}", "PASS", f"Found at {path}")
            else:
                self.log("Basic", f"{name}", "WARN", f"Missing: {path}")
    
    def check_system_resources(self):
        """Check system resource availability"""
        if not self.json_output:
            print("\n🖥️  System Resources")
            print("-" * 30)
        
        # Check memory
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        memory_used_pct = memory.percent
        
        if memory_gb >= 4:
            self.log("System", "Memory Total", "PASS", f"{memory_gb:.1f} GB available", 
                    {"total_gb": memory_gb, "used_percent": memory_used_pct})
        else:
            self.log("System", "Memory Total", "WARN", f"{memory_gb:.1f} GB (recommended: 4GB+)",
                    {"total_gb": memory_gb, "used_percent": memory_used_pct})
        
        if memory_used_pct < 80:
            self.log("System", "Memory Usage", "PASS", f"{memory_used_pct:.1f}% used")
        else:
            self.log("System", "Memory Usage", "WARN", f"{memory_used_pct:.1f}% used (high)")
        
        # Check disk space
        disk = psutil.disk_usage(str(project_root))
        disk_free_gb = disk.free / (1024**3)
        disk_used_pct = (disk.used / disk.total) * 100
        
        if disk_free_gb >= 1:
            self.log("System", "Disk Space", "PASS", f"{disk_free_gb:.1f} GB free",
                    {"free_gb": disk_free_gb, "used_percent": disk_used_pct})
        else:
            self.log("System", "Disk Space", "WARN", f"{disk_free_gb:.1f} GB free (low)",
                    {"free_gb": disk_free_gb, "used_percent": disk_used_pct})
        
        # Check CPU
        cpu_count = psutil.cpu_count()
        cpu_usage = psutil.cpu_percent(interval=1)
        
        self.log("System", "CPU Cores", "PASS", f"{cpu_count} cores available",
                {"cores": cpu_count, "usage_percent": cpu_usage})
        
        if cpu_usage < 80:
            self.log("System", "CPU Usage", "PASS", f"{cpu_usage:.1f}% used")
        else:
            self.log("System", "CPU Usage", "WARN", f"{cpu_usage:.1f}% used (high)")
    
    def check_database_health(self):
        """Check database health and connectivity"""
        if not self.json_output:
            print("\n🗄️  Database Health")
            print("-" * 30)
        
        # Check data directory
        data_dir = project_root / "data"
        if data_dir.exists():
            self.log("Database", "Data Directory", "PASS", f"Found at {data_dir}")
            
            # Check data directory size
            total_size = sum(f.stat().st_size for f in data_dir.rglob('*') if f.is_file())
            size_mb = total_size / (1024**2)
            
            self.log("Database", "Data Size", "PASS", f"{size_mb:.1f} MB",
                    {"size_bytes": total_size, "size_mb": size_mb})
        else:
            self.log("Database", "Data Directory", "WARN", "Data directory not found (will be created)")
        
        # Try to import database modules
        try:
            from mcp_jive import database
            self.log("Database", "Database Module", "PASS", "Module imports successfully")
        except ImportError as e:
            self.log("Database", "Database Module", "FAIL", f"Import failed: {e}")
        
        # Check for database lock files
        lock_files = list(data_dir.glob("**/*.lock")) if data_dir.exists() else []
        if lock_files:
            self.log("Database", "Lock Files", "WARN", f"Found {len(lock_files)} lock files")
        else:
            self.log("Database", "Lock Files", "PASS", "No lock files found")
    
    def check_dependencies(self):
        """Check Python dependencies"""
        if not self.json_output:
            print("\n📦 Dependencies")
            print("-" * 30)
        
        # Check requirements.txt
        requirements_file = project_root / "requirements.txt"
        if requirements_file.exists():
            self.log("Dependencies", "Requirements File", "PASS", f"Found at {requirements_file}")
            
            # Try to read and validate requirements
            try:
                with open(requirements_file, 'r') as f:
                    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
                self.log("Dependencies", "Requirements Count", "PASS", f"{len(requirements)} packages listed")
                
                # Check if key dependencies are importable
                key_deps = ['psutil', 'pathlib']
                for dep in key_deps:
                    try:
                        __import__(dep)
                        self.log("Dependencies", f"{dep}", "PASS", "Importable")
                    except ImportError:
                        self.log("Dependencies", f"{dep}", "FAIL", "Not importable")
                        
            except Exception as e:
                self.log("Dependencies", "Requirements Parsing", "FAIL", f"Error: {e}")
        else:
            self.log("Dependencies", "Requirements File", "FAIL", "requirements.txt not found")
    
    def check_file_permissions(self):
        """Check file permissions for key files"""
        if not self.json_output:
            print("\n🔐 File Permissions")
            print("-" * 30)
        
        # Check executable files
        executable_files = [
            project_root / "bin" / "mcp-jive",
            project_root / "scripts" / "testing" / "e2e.py",
            project_root / "scripts" / "server" / "start.py"
        ]
        
        for file_path in executable_files:
            if file_path.exists():
                if os.access(file_path, os.X_OK):
                    self.log("Permissions", f"{file_path.name}", "PASS", "Executable")
                else:
                    self.log("Permissions", f"{file_path.name}", "WARN", "Not executable")
            else:
                self.log("Permissions", f"{file_path.name}", "WARN", "File not found")
        
        # Check write permissions for data directory
        data_dir = project_root / "data"
        if data_dir.exists():
            if os.access(data_dir, os.W_OK):
                self.log("Permissions", "Data Directory", "PASS", "Writable")
            else:
                self.log("Permissions", "Data Directory", "FAIL", "Not writable")
    
    def check_network_connectivity(self):
        """Check network connectivity (basic)"""
        if not self.json_output:
            print("\n🌐 Network")
            print("-" * 30)
        
        # Check if we can bind to localhost
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', 0))
            port = sock.getsockname()[1]
            sock.close()
            self.log("Network", "Localhost Binding", "PASS", f"Can bind to port {port}")
        except Exception as e:
            self.log("Network", "Localhost Binding", "FAIL", f"Cannot bind: {e}")
    
    def is_healthy(self) -> bool:
        """Return overall health status"""
        return self.overall_healthy
    
    def print_summary(self):
        """Print health check summary"""
        if self.json_output:
            import json
            summary = {
                "healthy": self.overall_healthy,
                "timestamp": time.time(),
                "results": self.results
            }
            print(json.dumps(summary, indent=2))
        else:
            print("\n" + "=" * 50)
            print("HEALTH CHECK SUMMARY")
            print("=" * 50)
            
            total_checks = sum(len(category) for category in self.results.values())
            failed_checks = sum(1 for category in self.results.values() 
                              for check in category.values() 
                              if check["status"] == "FAIL")
            warning_checks = sum(1 for category in self.results.values() 
                               for check in category.values() 
                               if check["status"] == "WARN")
            
            print(f"Total Checks: {total_checks}")
            print(f"Failed: {failed_checks}")
            print(f"Warnings: {warning_checks}")
            print(f"Passed: {total_checks - failed_checks - warning_checks}")
            
            if self.overall_healthy:
                print("\n✅ Overall Status: HEALTHY")
            else:
                print("\n❌ Overall Status: UNHEALTHY")

if __name__ == "__main__":
    sys.exit(main())