#!/usr/bin/env python3
"""
Development Logs Viewer

Provides real-time log viewing and filtering for development.
"""

import sys
import os
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="View MCP Jive development logs")
    parser.add_argument("--follow", "-f", action="store_true",
                       help="Follow log output (like tail -f)")
    parser.add_argument("--lines", "-n", type=int, default=50,
                       help="Number of lines to show (default: 50)")
    parser.add_argument("--filter", type=str,
                       help="Filter logs by pattern")
    parser.add_argument("--level", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Filter by log level")
    parser.add_argument("--component", type=str,
                       help="Filter by component name")
    parser.add_argument("--since", type=str,
                       help="Show logs since time (e.g., '1h', '30m', '2023-12-01')")
    parser.add_argument("--json", action="store_true",
                       help="Output in JSON format")
    parser.add_argument("--no-color", action="store_true",
                       help="Disable colored output")
    
    args = parser.parse_args()
    
    viewer = LogViewer(
        follow=args.follow,
        lines=args.lines,
        filter_pattern=args.filter,
        log_level=args.level,
        component=args.component,
        since=args.since,
        json_output=args.json,
        colored=not args.no_color
    )
    
    try:
        return viewer.run()
    except KeyboardInterrupt:
        print("\nLog viewing stopped by user")
        return 0
    except Exception as e:
        print(f"Error viewing logs: {e}")
        return 1

class LogViewer:
    def __init__(self, follow=False, lines=50, filter_pattern=None, 
                 log_level=None, component=None, since=None, 
                 json_output=False, colored=True):
        self.follow = follow
        self.lines = lines
        self.filter_pattern = filter_pattern
        self.log_level = log_level
        self.component = component
        self.since = since
        self.json_output = json_output
        self.colored = colored and not json_output
        
        # Color codes
        self.colors = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m', # Magenta
            'RESET': '\033[0m',     # Reset
            'BOLD': '\033[1m',      # Bold
            'DIM': '\033[2m'        # Dim
        }
        
        if not self.colored:
            self.colors = {k: '' for k in self.colors}
    
    def run(self):
        """Run the log viewer"""
        log_sources = self._find_log_sources()
        
        if not log_sources:
            print("No log sources found. Logs will appear here when the server is running.")
            if self.follow:
                print("Waiting for logs... (Press Ctrl+C to exit)")
                try:
                    while True:
                        time.sleep(1)
                        log_sources = self._find_log_sources()
                        if log_sources:
                            break
                except KeyboardInterrupt:
                    return 0
            else:
                return 0
        
        if self.follow:
            return self._follow_logs(log_sources)
        else:
            return self._show_recent_logs(log_sources)
    
    def _find_log_sources(self):
        """Find available log sources"""
        log_sources = []
        
        # Common log locations
        possible_locations = [
            Path.cwd() / "logs",
            Path.cwd() / "data" / "logs",
            Path("/tmp") / "mcp-jive",
            Path.home() / ".mcp-jive" / "logs"
        ]
        
        for location in possible_locations:
            if location.exists() and location.is_dir():
                log_files = list(location.glob("*.log"))
                log_sources.extend(log_files)
        
        # Also check for systemd/journald logs if available
        if self._has_journalctl():
            log_sources.append("journalctl")
        
        return log_sources
    
    def _has_journalctl(self):
        """Check if journalctl is available"""
        try:
            subprocess.run(["which", "journalctl"], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _follow_logs(self, log_sources):
        """Follow logs in real-time"""
        print(f"{self.colors['BOLD']}Following logs from {len(log_sources)} sources...{self.colors['RESET']}")
        print(f"{self.colors['DIM']}Press Ctrl+C to exit{self.colors['RESET']}\n")
        
        if "journalctl" in log_sources:
            return self._follow_journalctl()
        elif log_sources:
            return self._follow_files(log_sources)
        else:
            print("No log sources to follow")
            return 1
    
    def _follow_journalctl(self):
        """Follow logs using journalctl"""
        cmd = ["journalctl", "-f", "-u", "mcp-jive*"]
        
        if self.since:
            cmd.extend(["--since", self.since])
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE, 
                                     universal_newlines=True)
            
            for line in process.stdout:
                if self._should_show_line(line):
                    formatted_line = self._format_line(line)
                    print(formatted_line, end='')
            
            return process.wait()
        except FileNotFoundError:
            print("journalctl not found")
            return 1
    
    def _follow_files(self, log_files):
        """Follow log files using tail"""
        if len(log_files) == 1 and isinstance(log_files[0], Path):
            cmd = ["tail", "-f", str(log_files[0])]
        else:
            # Multiple files
            file_paths = [str(f) for f in log_files if isinstance(f, Path)]
            if not file_paths:
                print("No valid log files to follow")
                return 1
            cmd = ["tail", "-f"] + file_paths
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE, 
                                     universal_newlines=True)
            
            for line in process.stdout:
                if self._should_show_line(line):
                    formatted_line = self._format_line(line)
                    print(formatted_line, end='')
            
            return process.wait()
        except FileNotFoundError:
            print("tail command not found")
            return 1
    
    def _show_recent_logs(self, log_sources):
        """Show recent log entries"""
        if "journalctl" in log_sources:
            return self._show_journalctl_logs()
        elif log_sources:
            return self._show_file_logs(log_sources)
        else:
            print("No log sources available")
            return 1
    
    def _show_journalctl_logs(self):
        """Show logs using journalctl"""
        cmd = ["journalctl", "-u", "mcp-jive*", "-n", str(self.lines)]
        
        if self.since:
            cmd.extend(["--since", self.since])
        
        try:
            result = subprocess.run(cmd, capture_output=True, 
                                  universal_newlines=True)
            
            for line in result.stdout.splitlines():
                if self._should_show_line(line):
                    formatted_line = self._format_line(line)
                    print(formatted_line)
            
            return result.returncode
        except FileNotFoundError:
            print("journalctl not found")
            return 1
    
    def _show_file_logs(self, log_files):
        """Show logs from files"""
        for log_file in log_files:
            if not isinstance(log_file, Path):
                continue
                
            if not log_file.exists():
                continue
            
            print(f"{self.colors['BOLD']}=== {log_file.name} ==={self.colors['RESET']}")
            
            try:
                cmd = ["tail", "-n", str(self.lines), str(log_file)]
                result = subprocess.run(cmd, capture_output=True, 
                                      universal_newlines=True)
                
                for line in result.stdout.splitlines():
                    if self._should_show_line(line):
                        formatted_line = self._format_line(line)
                        print(formatted_line)
                        
            except Exception as e:
                print(f"Error reading {log_file}: {e}")
            
            print()  # Empty line between files
        
        return 0
    
    def _should_show_line(self, line):
        """Check if a line should be shown based on filters"""
        if self.filter_pattern and self.filter_pattern.lower() not in line.lower():
            return False
        
        if self.log_level:
            if self.log_level not in line:
                return False
        
        if self.component:
            if self.component.lower() not in line.lower():
                return False
        
        return True
    
    def _format_line(self, line):
        """Format a log line with colors and formatting"""
        if not self.colored:
            return line
        
        # Add colors based on log level
        for level, color in self.colors.items():
            if level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                if level in line:
                    line = line.replace(level, f"{color}{level}{self.colors['RESET']}")
                    break
        
        # Highlight timestamps
        import re
        timestamp_pattern = r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})'
        line = re.sub(timestamp_pattern, 
                     f"{self.colors['DIM']}\\1{self.colors['RESET']}", line)
        
        return line

if __name__ == "__main__":
    sys.exit(main())