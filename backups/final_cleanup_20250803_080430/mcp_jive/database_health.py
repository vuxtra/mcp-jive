
"""Database Health Monitoring Module"""

import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DatabaseHealthMonitor:
    """Monitors database health and connection status."""
    
    def __init__(self, lancedb_manager):
        self.lancedb_manager = lancedb_manager
        self.health_metrics = {
            "last_check": None,
            "connection_status": "unknown",
            "response_time_ms": None,
            "error_count": 0,
            "success_count": 0,
            "uptime_percentage": 100.0
        }
        self.check_interval = 30  # seconds
        self.monitoring_task = None
        
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self.monitoring_task is None:
            self.monitoring_task = asyncio.create_task(self._monitor_loop())
            logger.info("Database health monitoring started")
            
    async def stop_monitoring(self):
        """Stop health monitoring."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
            logger.info("Database health monitoring stopped")
            
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while True:
            try:
                await self.check_health()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(self.check_interval)
                
    async def check_health(self) -> Dict[str, Any]:
        """Check database health and update metrics."""
        start_time = time.time()
        
        try:
            # Simple health check - try to get cluster info
            if hasattr(self.lancedb_manager, 'client') and self.lancedb_manager.client:
                cluster_info = self.lancedb_manager.client.cluster.get_nodes_status()
                
                response_time = (time.time() - start_time) * 1000
                
                self.health_metrics.update({
                    "last_check": datetime.now().isoformat(),
                    "connection_status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "success_count": self.health_metrics["success_count"] + 1
                })
                
                logger.debug(f"Database health check passed in {response_time:.2f}ms")
                
            else:
                raise Exception("Weaviate client not available")
                
        except Exception as e:
            self.health_metrics.update({
                "last_check": datetime.now().isoformat(),
                "connection_status": "unhealthy",
                "response_time_ms": None,
                "error_count": self.health_metrics["error_count"] + 1,
                "last_error": str(e)
            })
            
            logger.warning(f"Database health check failed: {e}")
            
        # Calculate uptime percentage
        total_checks = self.health_metrics["success_count"] + self.health_metrics["error_count"]
        if total_checks > 0:
            self.health_metrics["uptime_percentage"] = (
                self.health_metrics["success_count"] / total_checks
            ) * 100
            
        return self.health_metrics.copy()
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return self.health_metrics.copy()
        
    def is_healthy(self) -> bool:
        """Check if database is currently healthy."""
        return self.health_metrics["connection_status"] == "healthy"
