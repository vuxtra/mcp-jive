"""Health monitoring for MCP Jive Server.

Provides comprehensive health checks, monitoring, and diagnostics
for the MCP server infrastructure components.
"""

import logging
import time
import psutil
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from .config import ServerConfig
from .lancedb_manager import LanceDBManager

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Health status information."""
    component: str
    status: str  # healthy, degraded, unhealthy
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "component": self.component,
            "status": self.status,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details or {}
        }


class HealthMonitor:
    """Comprehensive health monitoring system."""
    
    def __init__(self, config: ServerConfig, lancedb_manager: Optional[LanceDBManager] = None):
        self.config = config
        self.lancedb_manager = lancedb_manager
        self.start_time = datetime.now()
        self.health_history: List[HealthStatus] = []
        self.max_history = 1000
        
    async def get_overall_health(self) -> Dict[str, Any]:
        """Get comprehensive health status of all components."""
        logger.debug("Performing overall health check")
        
        health_checks = [
            self._check_system_resources(),
            self._check_server_status(),
            self._check_database_health(),
            # AI provider check removed
            self._check_configuration()
        ]
        
        # Run all health checks concurrently
        results = await asyncio.gather(*health_checks, return_exceptions=True)
        
        # Process results
        component_statuses = []
        overall_status = "healthy"
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                status = HealthStatus(
                    component=f"check_{i}",
                    status="unhealthy",
                    message=f"Health check failed: {str(result)}"
                )
            else:
                status = result
                
            component_statuses.append(status)
            
            # Determine overall status
            if status.status == "unhealthy":
                overall_status = "unhealthy"
            elif status.status == "degraded" and overall_status == "healthy":
                overall_status = "degraded"
                
        # Store in history
        overall_health_status = HealthStatus(
            component="overall",
            status=overall_status,
            message=f"Overall system status: {overall_status}",
            details={
                "components": [status.to_dict() for status in component_statuses],
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
            }
        )
        
        self._add_to_history(overall_health_status)
        
        return overall_health_status.to_dict()
        
    async def _check_system_resources(self) -> HealthStatus:
        """Check system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024 * 1024 * 1024)
            
            # Determine status
            status = "healthy"
            messages = []
            
            if cpu_percent > 90:
                status = "unhealthy"
                messages.append(f"High CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > 70:
                status = "degraded"
                messages.append(f"Elevated CPU usage: {cpu_percent:.1f}%")
                
            if memory_percent > 90:
                status = "unhealthy"
                messages.append(f"High memory usage: {memory_percent:.1f}%")
            elif memory_percent > 70:
                if status == "healthy":
                    status = "degraded"
                messages.append(f"Elevated memory usage: {memory_percent:.1f}%")
                
            if disk_percent > 95:
                status = "unhealthy"
                messages.append(f"Disk almost full: {disk_percent:.1f}%")
            elif disk_percent > 85:
                if status == "healthy":
                    status = "degraded"
                messages.append(f"Disk usage high: {disk_percent:.1f}%")
                
            # Check memory limit (using a default of 1GB if not configured)
            memory_limit_mb = 1024  # Default 1GB limit
            if memory_available_mb < memory_limit_mb:
                if status == "healthy":
                    status = "degraded"
                messages.append(f"Available memory below limit: {memory_available_mb:.0f}MB < {memory_limit_mb}MB")
                
            message = "; ".join(messages) if messages else "System resources normal"
            
            return HealthStatus(
                component="system_resources",
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "memory_available_mb": memory_available_mb,
                    "disk_percent": disk_percent,
                    "disk_free_gb": disk_free_gb,
                    "memory_limit_mb": memory_limit_mb
                }
            )
            
        except Exception as e:
            return HealthStatus(
                component="system_resources",
                status="unhealthy",
                message=f"Failed to check system resources: {str(e)}"
            )
            
    async def _check_server_status(self) -> HealthStatus:
        """Check MCP server status."""
        try:
            uptime = datetime.now() - self.start_time
            uptime_seconds = uptime.total_seconds()
            
            # Check if server has been running for minimum time
            if uptime_seconds < 10:
                status = "degraded"
                message = "Server recently started"
            else:
                status = "healthy"
                message = "Server running normally"
                
            return HealthStatus(
                    component="mcp_server",
                    status=status,
                    message=message,
                    details={
                        "uptime_seconds": uptime_seconds,
                        "uptime_human": str(uptime),
                        "start_time": self.start_time.isoformat(),
                        "debug_mode": self.config.server.debug,
                     "log_level": self.config.server.log_level
                    }
                )
            
        except Exception as e:
            return HealthStatus(
                component="mcp_server",
                status="unhealthy",
                message=f"Failed to check server status: {str(e)}"
            )
            
    async def _check_database_health(self) -> HealthStatus:
        """Check LanceDB database health."""
        if not self.lancedb_manager:
            return HealthStatus(
                component="database",
                status="degraded",
                message="LanceDB manager not available"
            )
            
        try:
            # Simple database connection test
            if hasattr(self.lancedb_manager, 'db') and self.lancedb_manager.db is not None:
                # Try to list tables as a basic health check
                tables = self.lancedb_manager.db.table_names()
                
                return HealthStatus(
                    component="database",
                    status="healthy",
                    message="LanceDB database operational",
                    details={
                        "tables_count": len(tables),
                        "tables": tables[:5]  # Show first 5 tables
                    }
                )
            else:
                return HealthStatus(
                    component="database",
                    status="unhealthy",
                    message="Database connection not established"
                )
                
        except Exception as e:
            return HealthStatus(
                component="database",
                status="unhealthy",
                message=f"Failed to check database health: {str(e)}"
            )
            
    # AI provider check method removed
            
    async def _check_configuration(self) -> HealthStatus:
        """Check configuration validity."""
        try:
            # Basic configuration validation
            issues = []
            
            # Check debug mode in production (using log level as proxy for environment)
            if self.config.server.log_level == "DEBUG" and not self.config.server.debug:
                issues.append("Debug logging enabled but debug mode disabled")
                
            # Check for reasonable port configuration
            if self.config.server.port < 1024 and self.config.server.port != 80 and self.config.server.port != 443:
                 issues.append(f"Port {self.config.server.port} may require elevated privileges")
                
            # Check host configuration
            if self.config.server.host == "0.0.0.0":
                issues.append("Server bound to all interfaces - ensure firewall is configured")
                
            if issues:
                status = "degraded"
                message = f"Configuration issues: {'; '.join(issues)}"
            else:
                status = "healthy"
                message = "Configuration valid"
                
            return HealthStatus(
                component="configuration",
                status=status,
                message=message,
                details={
                    "issues": issues,
                    "host": self.config.server.host,
                     "port": self.config.server.port,
                    "debug_mode": self.config.server.debug,
                     "log_level": self.config.server.log_level
                }
            )
            
        except Exception as e:
            return HealthStatus(
                component="configuration",
                status="unhealthy",
                message=f"Failed to check configuration: {str(e)}"
            )
            
    def _add_to_history(self, status: HealthStatus) -> None:
        """Add health status to history."""
        self.health_history.append(status)
        
        # Trim history if too long
        if len(self.health_history) > self.max_history:
            self.health_history = self.health_history[-self.max_history:]
            
    def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health history for the specified number of hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_history = [
            status.to_dict() 
            for status in self.health_history 
            if status.timestamp >= cutoff_time
        ]
        
        return recent_history
        
    async def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics."""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Server metrics
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": uptime,
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_mb": memory.used / (1024 * 1024),
                    "memory_available_mb": memory.available / (1024 * 1024),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024 * 1024 * 1024)
                },
                "server": {
                    "environment": self.config.environment,
                    "debug_mode": self.config.server.debug,
                    "max_connections": self.config.max_connections,
                    "query_timeout": self.config.query_timeout
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }