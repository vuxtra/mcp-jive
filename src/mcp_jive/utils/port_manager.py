"""Port Management Utilities.

Utilities for managing port availability and graceful shutdown of existing servers.
"""

import asyncio
import logging
import socket
import psutil
import signal
import time
from typing import Optional, List, Tuple
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """Information about a process using a port."""
    pid: int
    name: str
    cmdline: List[str]
    create_time: float


class PortManager:
    """Manages port availability and graceful shutdown of existing processes."""

    def __init__(self, port: int, host: str = "localhost"):
        """Initialize the port manager.

        Args:
            port: The port to manage
            host: The host address to check
        """
        self.port = port
        self.host = host
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def is_port_available(self) -> bool:
        """Check if the port is available for binding.

        Returns:
            True if port is available, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((self.host, self.port))
                return result != 0  # Port is available if connection fails
        except Exception as e:
            self.logger.debug(f"Error checking port availability: {e}")
            return False

    def find_processes_using_port(self) -> List[ProcessInfo]:
        """Find all processes currently using the specified port.

        Returns:
            List of ProcessInfo objects for processes using the port
        """
        processes = []

        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                try:
                    # Get process connections
                    connections = proc.connections(kind='inet')

                    for conn in connections:
                        if (conn.laddr.port == self.port and
                            conn.status == psutil.CONN_LISTEN):

                            process_info = ProcessInfo(
                                pid=proc.info['pid'],
                                name=proc.info['name'],
                                cmdline=proc.info['cmdline'] or [],
                                create_time=proc.info['create_time']
                            )
                            processes.append(process_info)
                            break  # Only add each process once

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Process might have terminated or we don't have access
                    continue
                except Exception as e:
                    self.logger.debug(f"Error checking process {proc.info.get('pid', 'unknown')}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error scanning processes: {e}")

        return processes

    def is_mcp_jive_process(self, process_info: ProcessInfo) -> bool:
        """Check if a process appears to be an MCP Jive server.

        Args:
            process_info: Process information to check

        Returns:
            True if process appears to be MCP Jive, False otherwise
        """
        # Check command line for MCP Jive indicators
        cmdline_str = ' '.join(process_info.cmdline).lower()

        mcp_jive_indicators = [
            'mcp-jive',
            'mcp_jive',
            'mcp-server.py',
            'main.py',
            'server start'
        ]

        return any(indicator in cmdline_str for indicator in mcp_jive_indicators)

    async def send_graceful_shutdown_signal(self, process_info: ProcessInfo) -> bool:
        """Send a graceful shutdown signal to a process.

        Args:
            process_info: Information about the process to shutdown

        Returns:
            True if shutdown signal was sent successfully, False otherwise
        """
        try:
            # Try to get the process
            proc = psutil.Process(process_info.pid)

            self.logger.info(f"Sending SIGTERM to process {process_info.pid} ({process_info.name})")

            # Send SIGTERM for graceful shutdown
            proc.send_signal(signal.SIGTERM)

            # Wait up to 10 seconds for graceful shutdown
            for i in range(10):
                if not proc.is_running():
                    self.logger.info(f"Process {process_info.pid} shutdown gracefully")
                    return True
                await asyncio.sleep(1)

            # If still running, try SIGKILL as last resort
            if proc.is_running():
                self.logger.warning(f"Process {process_info.pid} didn't respond to SIGTERM, sending SIGKILL")
                proc.send_signal(signal.SIGKILL)

                # Wait up to 5 seconds for forced shutdown
                for i in range(5):
                    if not proc.is_running():
                        self.logger.info(f"Process {process_info.pid} terminated with SIGKILL")
                        return True
                    await asyncio.sleep(1)

                self.logger.error(f"Failed to terminate process {process_info.pid}")
                return False

            return True

        except psutil.NoSuchProcess:
            # Process already terminated
            self.logger.info(f"Process {process_info.pid} already terminated")
            return True
        except psutil.AccessDenied:
            self.logger.error(f"Access denied when trying to terminate process {process_info.pid}")
            return False
        except Exception as e:
            self.logger.error(f"Error terminating process {process_info.pid}: {e}")
            return False

    async def ensure_port_available(self, force_shutdown: bool = True) -> bool:
        """Ensure the port is available, optionally shutting down existing processes.

        Args:
            force_shutdown: If True, attempt to shutdown existing MCP Jive processes

        Returns:
            True if port is now available, False otherwise
        """
        # First check if port is already available
        if self.is_port_available():
            self.logger.debug(f"Port {self.port} is already available")
            return True

        # Find processes using the port
        processes = self.find_processes_using_port()

        if not processes:
            self.logger.warning(f"Port {self.port} appears to be in use but no processes found")
            return False

        self.logger.info(f"Found {len(processes)} process(es) using port {self.port}")

        # If not forcing shutdown, just report the issue
        if not force_shutdown:
            for proc in processes:
                self.logger.error(
                    f"Port {self.port} is in use by process {proc.pid} ({proc.name}): "
                    f"{' '.join(proc.cmdline[:3])}..."
                )
            return False

        # Try to gracefully shutdown MCP Jive processes
        shutdown_attempts = []
        for proc in processes:
            if self.is_mcp_jive_process(proc):
                self.logger.info(
                    f"Found MCP Jive process {proc.pid} ({proc.name}), attempting graceful shutdown"
                )
                shutdown_attempts.append(self.send_graceful_shutdown_signal(proc))
            else:
                self.logger.error(
                    f"Port {self.port} is in use by non-MCP Jive process {proc.pid} ({proc.name}): "
                    f"{' '.join(proc.cmdline[:3])}..."
                )

        # Wait for all shutdown attempts to complete
        if shutdown_attempts:
            results = await asyncio.gather(*shutdown_attempts, return_exceptions=True)

            # Wait a moment for the port to become available
            await asyncio.sleep(2)

            # Check if port is now available
            if self.is_port_available():
                self.logger.info(f"Port {self.port} is now available after graceful shutdown")
                return True
            else:
                self.logger.error(f"Port {self.port} is still not available after shutdown attempts")
                return False

        return False

    def get_port_status_info(self) -> dict:
        """Get detailed information about port status.

        Returns:
            Dictionary with port status information
        """
        is_available = self.is_port_available()
        processes = self.find_processes_using_port()

        return {
            "port": self.port,
            "host": self.host,
            "available": is_available,
            "processes": [
                {
                    "pid": proc.pid,
                    "name": proc.name,
                    "cmdline": proc.cmdline,
                    "create_time": proc.create_time,
                    "is_mcp_jive": self.is_mcp_jive_process(proc)
                }
                for proc in processes
            ]
        }


async def ensure_port_available_for_server(port: int, host: str = "localhost") -> bool:
    """Convenience function to ensure a port is available for server startup.

    Args:
        port: The port to check and clear
        host: The host address

    Returns:
        True if port is available, False otherwise
    """
    port_manager = PortManager(port, host)
    return await port_manager.ensure_port_available(force_shutdown=True)